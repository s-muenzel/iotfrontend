"""mqtt_handler.py: MQTT handling and Bewässerung (irrigation) state management."""
import json
import logging
import paho.mqtt.client as mqtt_client
import yaml

# Global state variables for Bewässerung
_bewaesserung_state = {
    'dauer': -1,
    'frequenz': -1,
    'next': -1,
    'wasser': False,
}
mqtt_client_instance = None

# Global state variable for Solar/Electricity data
_solar_data = {
    'p_solar': 0,
    'p_haus': 0,
    'p_grid': 0,
    'p_battery': 0,
    'soc': 0,
}


MQTT_TOPICS = ["Bewaesserung/Ist", "Sensor/Solar/////+"]

def on_message(client, userdata, msg):
    """Callback for MQTT messages.
    
    Processes MQTT messages, particularly for
    "Bewaesserung/Ist" topic to update irrigation system state
    "Sensor/Solar/////S*" topic to update solar/electricity data.
    
    Args:
        client: MQTT client instance
        userdata: User data
        msg: MQTT message
    """
    global _bewaesserung_state
    
    logging.debug("Received topic %s Msg %s", msg.topic, msg.payload.decode())
    
    if msg.topic == "Bewaesserung/Ist":
        try:
            bew = json.loads(msg.payload.decode())
            if "Dauer" in bew:
                _bewaesserung_state['dauer'] = bew["Dauer"]
                _bewaesserung_state['frequenz'] = bew["Frequenz"]
                _bewaesserung_state['next'] = bew["Next"]
                _bewaesserung_state['wasser'] = bew["Wasser"]
        except json.JSONDecodeError as err:
            logging.warning("Failed to decode MQTT message: %s", err)
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
        
        for topic in MQTT_TOPICS:
            mqtt_client_instance.subscribe(topic)
            logging.info("Subscribed to topic: %s", topic)
        # erg = mqtt_client_instance.subscribe("Bewaesserung/Ist")
        # logging.info("MQTT subscribe result: %s", erg)
        
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
        logging.debug("Published to topic %s: %s", topic, payload)
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
    return _bewaesserung_state
# {
#         'dauer': _bewaesserung_state['dauer'],
#         'frequenz': _bewaesserung_state['frequenz'],
#         'next': _bewaesserung_state['next'],
#         'wasser': _bewaesserung_state['wasser'],
#     }

def get_solar_status():
    """Get current solar status from Modbus handler.
    
    Returns:
        dict: Dictionary with solar data or None if unavailable
    """
    return _solar_data

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
    logging.debug("MQTT reload action")
    publish_message("DB", "AKTION")
