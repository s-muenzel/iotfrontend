"""app.py: Web-Frontend for IoT Central.

Main application entry point that combines all modules and blueprints.
Zeigt die aktuellen Wetter-Daten
Listet alle IOT-Devices
Listet alle konfigurierte Aktionen und bietet die Möglichtkeit zum Editieren

WSGI Compliant: This module exports an 'app' object at module level for WSGI servers.
"""
import logging
import atexit
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
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application
    """
    flask_app = Flask(import_name=__name__)
    
    # Register blueprints
    flask_app.register_blueprint(web_bp)
    flask_app.register_blueprint(actions_bp)
    flask_app.register_blueprint(status_bp)
    
    return flask_app


# Create the WSGI application instance
app = create_app()

# Initialize MQTT at module load time
mqtt_handler.init_mqtt()

# Register cleanup function to be called on exit
atexit.register(mqtt_handler.stop_mqtt)


if __name__ == '__main__':
    # Development server only
    try:
        app.run(host='0.0.0.0', port=80)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logger.error("Error running development server: %s", e)
        raise

