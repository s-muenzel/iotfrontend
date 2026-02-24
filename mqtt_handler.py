"""mqtt_handler.py: MQTT handling and Bewässerung (irrigation) state management."""
import json
import logging
import paho.mqtt.client as mqtt_client
import yaml

# Global state variables for Bewässerung
_bewaesserung_dauer = -1
_bewaesserung_frequenz = -1
_bewaesserung_next = -1
_bewaesserung_wasser = False
mqtt_client_instance = None


def on_message(client, userdata, msg):
    """Callback for MQTT messages.
    
    Processes MQTT messages, particularly for "Bewaesserung/Ist" topic
    to update irrigation system state.
    
    Args:
        client: MQTT client instance
        userdata: User data
        msg: MQTT message
    """
    global _bewaesserung_dauer, _bewaesserung_frequenz, _bewaesserung_next, _bewaesserung_wasser
    
    logging.debug("Received topic %s Msg %s", msg.topic, msg.payload.decode())
    
    if msg.topic == "Bewaesserung/Ist":
        try:
            bew = json.loads(msg.payload.decode())
            if "Dauer" in bew:
                _bewaesserung_dauer = bew["Dauer"]
                _bewaesserung_frequenz = bew["Frequenz"]
                _bewaesserung_next = bew["Next"]
                _bewaesserung_wasser = bew["Wasser"]
        except json.JSONDecodeError as err:
            logging.warning("Failed to decode MQTT message: %s", err)


def init_mqtt():
    """Initialize MQTT client and connect to broker.
    
    Returns:
        mqtt_client.Client: The MQTT client instance
    """
    global mqtt_client_instance
    
    try:
        mqtt_config = yaml.safe_load(open("mq.cnf"))
        mqtt_client_instance = mqtt_client.Client(client_id="iotfrontend")
        mqtt_client_instance.on_message = on_message
        
        erg = mqtt_client_instance.connect(
            host=mqtt_config["mqtt"]["mqttserver"],
            port=mqtt_config["mqtt"]["mqttport"]
        )
        logging.info("MQTT connect result: %s", erg)
        
        erg = mqtt_client_instance.subscribe("Bewaesserung/Ist")
        logging.info("MQTT subscribe result: %s", erg)
        
        mqtt_client_instance.loop_start()
        return mqtt_client_instance
    except Exception as err:
        logging.error("Failed to initialize MQTT: %s", err)
        return None


def publish_message(topic, payload):
    """Publish a message to MQTT broker.
    
    Args:
        topic: Topic to publish to
        payload: Message payload
    """
    if mqtt_client_instance:
        mqtt_client_instance.publish(topic=topic, payload=payload)
    else:
        logging.warning("MQTT client not initialized")


def stop_mqtt():
    """Stop MQTT client and cleanup."""
    global mqtt_client_instance
    if mqtt_client_instance:
        mqtt_client_instance.loop_stop()
        mqtt_client_instance = None


def get_bewaesserung_status():
    """Get current irrigation system status.
    
    Returns:
        dict: Dictionary with Dauer, Frequenz, Next, Wasser
    """
    return {
        'dauer': _bewaesserung_dauer,
        'frequenz': _bewaesserung_frequenz,
        'next': _bewaesserung_next,
        'wasser': _bewaesserung_wasser
    }


def set_bewaesserung_value(parameter, value):
    """Set a new value for irrigation system.
    
    Args:
        parameter: Parameter name (e.g., "Dauer", "Frequenz")
        value: New value
    """
    payload = '{"' + parameter + '":' + str(value) + '}'
    publish_message("Bewaesserung/Soll", payload)


def reload_actions():
    """Send reload signal to action processor."""
    publish_message("DB", "AKTION")
