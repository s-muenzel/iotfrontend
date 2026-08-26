"""routes_web.py: Web routes for main pages and device information."""
import logging
from flask import Blueprint, render_template
import database as db
import mqtt_handler
from netzwerk import check_netzwerkfehler


web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def top():
    """Web handler for / - Top/Home page with weather and device info."""
    try:
        weather = db.get_weather_data()
        
        return render_template(
            'top.htm',
            T=weather['temp'],
            F=weather['feucht'],
            H=weather['hell'],
            P=weather['proz']
        )
    except Exception as err:
        logging.warning("Error in top(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@web_bp.route('/iot.htm')
def iot():
    """Web handler for /iot.htm - List all devices and their information."""
    try:
        devices = db.get_device_list()
        netzfehler = check_netzwerkfehler(devices)
        return render_template('iot.htm', eintraege=devices, netzfehler=netzfehler)
    except Exception as err:
        logging.warning("Error in iot(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@web_bp.route('/strom')
def strom():
    """Web handler for /strom - Show power information."""
    try:
        return render_template('strom.htm')
    except Exception as err:
        logging.warning("Error in strom(): %s", str(err))
        return _error_response("allgemeiner Fehler")


def _error_response(message):
    """Generate error response HTML.
    
    Args:
        message: Error message to display
        
    Returns:
        str: HTML error page
    """
    return ('<!DOCTYPE html><html><head><meta charset="UTF-8">'
            '<title>Fehler</title></head>'
            '<body><h1>{}</h1></body></html>'.format(message))
