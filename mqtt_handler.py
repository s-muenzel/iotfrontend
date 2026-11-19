"""mqtt_handler.py: MQTT handling and Bewässerung (irrigation) state management."""
import json
import logging
import time
import paho.mqtt.client as mqtt_client
import yaml

mqtt_client_instance = None
MQTT_CONNECT_TIMEOUT = 10
MQTT_PUBLISH_TIMEOUT = 5

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
    """Log the broker's connection response."""
    if reason_code == 0:
        logging.info("Connected to MQTT broker")
    else:
        logging.error("MQTT broker rejected connection: %s", reason_code)


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """Log MQTT connection loss."""
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
    loop_started = False
    try:
        mqtt_config = yaml.safe_load(open("mq.cnf"))
        client = mqtt_client.Client(
            mqtt_client.CallbackAPIVersion.VERSION2,
            client_id="iotfrontend"
        )
        client.on_message = on_message
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect

        connect_result = client.connect(
            host=mqtt_config["mqtt"]["mqttserver"],
            port=mqtt_config["mqtt"]["mqttport"]
        )
        if connect_result != mqtt_client.MQTT_ERR_SUCCESS:
            raise RuntimeError(
                f"MQTT connect failed with code {connect_result}"
            )

        client.loop_start()
        loop_started = True
        deadline = time.monotonic() + MQTT_CONNECT_TIMEOUT
        while not client.is_connected() and time.monotonic() < deadline:
            time.sleep(0.1)
        if not client.is_connected():
            raise TimeoutError("Timed out waiting for MQTT connection")

        for topic in MQTT_TOPICS:
            result, _ = client.subscribe(topic)
            if result != mqtt_client.MQTT_ERR_SUCCESS:
                raise RuntimeError(
                    f"MQTT subscribe to {topic!r} failed with code {result}"
                )
            logging.info("Subscribed to topic: %s", topic)

        mqtt_client_instance = client
        return client
    except Exception as err:
        mqtt_client_instance = None
        if client is not None:
            try:
                client.disconnect()
            except Exception:
                logging.debug("Failed to disconnect MQTT client after init error",
                              exc_info=True)
            if loop_started:
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
