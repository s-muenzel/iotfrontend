"""mqtt_handler.py: MQTT handling and Bewässerung (irrigation) state management."""
import json
import logging
import paho.mqtt.client as mqtt_client
import yaml

mqtt_client_instance = None
MQTT_PUBLISH_TIMEOUT = 5
MQTT_RECONNECT_MIN_DELAY = 1
MQTT_RECONNECT_MAX_DELAY = 30

# Global state variable for Solar/Electricity data
_solar_data = {
    'p_solar': 0,
    'p_haus': 0,
    'p_grid': 0,
    'p_battery': 0,
    'soc': 0,
}


MQTT_TOPICS = ["Sensor/Solar/////+"]

def on_message(client, userdata, msg):
    """Callback for MQTT messages.
    
    Processes MQTT messages, particularly for
    "Sensor/Solar/////S*" topic to update solar/electricity data.
    
    Args:
        client: MQTT client instance
        userdata: User data
        msg: MQTT message
    """
    
    logging.debug("Received topic %s Msg %s", msg.topic, msg.payload.decode())
    
    if msg.topic == "Sensor/Solar/////SSs":
        _solar_data['p_solar'] = float(msg.payload.decode())
    if msg.topic == "Sensor/Solar/////SSh":
        _solar_data['p_haus'] = float(msg.payload.decode())
    if msg.topic == "Sensor/Solar/////SSn":
        _solar_data['p_grid'] = float(msg.payload.decode())
    if msg.topic == "Sensor/Solar/////SGc":
        _solar_data['p_battery'] = float(msg.payload.decode())
    if msg.topic == "Sensor/Solar/////SGs":
        _solar_data['soc'] = float(msg.payload.decode())


def on_connect(client, userdata, connect_flags, reason_code, properties):
    """Log successful connections and restore subscriptions after reconnect."""
    if reason_code != 0:
        logging.error("MQTT broker rejected connection: %s", reason_code)
        return

    logging.info("Connected to MQTT broker")
    for topic in MQTT_TOPICS:
        result, _ = client.subscribe(topic)
        if result != mqtt_client.MQTT_ERR_SUCCESS:
            logging.error(
                "MQTT subscribe to %s failed with code %s", topic, result
            )
        else:
            logging.info("Subscribed to topic: %s", topic)


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """Log MQTT connection loss."""
    if reason_code == 0:
        logging.info("Disconnected from MQTT broker")
    else:
        logging.warning("Disconnected from MQTT broker: %s", reason_code)


def init_mqtt():
    """Initialize MQTT client and connect to broker.
    
    Returns:
        mqtt_client.Client: The MQTT client instance
    """
    global mqtt_client_instance

    if mqtt_client_instance is not None:
        stop_mqtt()
    mqtt_client_instance = None
    client = None
    try:
        mqtt_config = yaml.safe_load(open("mq.cnf"))
        client = mqtt_client.Client(
            mqtt_client.CallbackAPIVersion.VERSION2,
            client_id="iotfrontend"
        )
        client.on_message = on_message
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.reconnect_delay_set(
            min_delay=MQTT_RECONNECT_MIN_DELAY,
            max_delay=MQTT_RECONNECT_MAX_DELAY
        )
        paho_logger = logging.getLogger("mqtt_handler.paho")
        paho_logger.setLevel(logging.WARNING)
        client.enable_logger(paho_logger)

        client.connect_async(
            host=mqtt_config["mqtt"]["mqttserver"],
            port=mqtt_config["mqtt"]["mqttport"]
        )
        loop_result = client.loop_start()
        if loop_result != mqtt_client.MQTT_ERR_SUCCESS:
            raise RuntimeError(
                f"MQTT network loop failed to start with code {loop_result}"
            )

        mqtt_client_instance = client
        logging.info("MQTT client started; connecting to broker")
        return client
    except Exception as err:
        mqtt_client_instance = None
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                logging.debug("Failed to disconnect MQTT client after init error",
                              exc_info=True)
            try:
                client.loop_stop()
            except Exception:
                logging.debug("Failed to stop MQTT loop after init error",
                              exc_info=True)
        logging.exception("Failed to initialize MQTT: %s", err)
        return None


def publish_message(topic, payload):
    """Publish a message to MQTT broker.
    
    Args:
        topic: Topic to publish to
        payload: Message payload

    Raises:
        RuntimeError: If the client is unavailable or publishing fails.
        TimeoutError: If the broker does not acknowledge the message in time.
    """
    client = mqtt_client_instance
    if client is None:
        raise RuntimeError("MQTT client not initialized")
    if not client.is_connected():
        raise RuntimeError("MQTT client is not connected")

    result = client.publish(topic=topic, payload=payload, qos=1)
    if result.rc != mqtt_client.MQTT_ERR_SUCCESS:
        raise RuntimeError(
            f"MQTT publish to {topic!r} failed with code {result.rc}"
        )

    result.wait_for_publish(timeout=MQTT_PUBLISH_TIMEOUT)
    if not result.is_published():
        raise TimeoutError(f"MQTT publish to {topic!r} was not acknowledged")
    logging.info(
        "MQTT broker acknowledged publish to %s (mid=%s)",
        topic, result.mid
    )
    return result


def stop_mqtt():
    """Stop MQTT client and cleanup."""
    global mqtt_client_instance
    client = mqtt_client_instance
    mqtt_client_instance = None
    if client is not None:
        try:
            client.disconnect()
        finally:
            client.loop_stop()


def get_solar_status():
    """Get current solar status from Modbus handler.
    
    Returns:
        dict: Dictionary with solar data or None if unavailable
    """
    return _solar_data


def reload_actions():
    """Send reload signal to action processor."""
    logging.debug("MQTT reload action")
    publish_message("DB", "AKTION")
