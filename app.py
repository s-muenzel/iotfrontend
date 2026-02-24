"""app.py: Web-Frontend for IoT Central.

Main application entry point that combines all modules and blueprints.
Zeigt die aktuellen Wetter-Daten
Listet alle IOT-Devices
Listet alle konfigurierte Aktionen und bietet die Möglichtkeit zum Editieren
"""
import logging
from os import _exit, X_OK
from signal import signal, SIGTERM, SIGINT
from flask import Flask

import mqtt_handler
from routes_web import web_bp
from routes_actions import actions_bp
from routes_status import status_bp

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def cb_signal_handler(signum, frame):
    """Signal handler: terminate the program when signals arrive."""
    logging.info("ACHTUNG SIG %d, exiting", signum)
    mqtt_handler.stop_mqtt()
    _exit(X_OK)


def create_app():
    """Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application
    """
    FLASK_APP = Flask(import_name=__name__)
    
    # Register blueprints
    FLASK_APP.register_blueprint(web_bp)
    FLASK_APP.register_blueprint(actions_bp)
    FLASK_APP.register_blueprint(status_bp)
    
    return FLASK_APP


if __name__ == '__main__':
    signal(SIGTERM, cb_signal_handler)
    signal(SIGINT, cb_signal_handler)
    
    # Initialize MQTT
    mqtt_handler.init_mqtt()
    
    # Create and run the Flask application
    app = create_app()
    app.run(host='0.0.0.0', port=80)
    
    # Cleanup
    mqtt_handler.stop_mqtt()

