"""routes_web.py: Web routes for main pages and device information."""
import logging
from flask import Blueprint, redirect, render_template, request, url_for
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
            R=weather['regen'],
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


@web_bp.route('/heizung')
def heizung():
    """Web handler for /heizung - Show thermostat temperatures."""
    from fritz_handler import get_Temperatur_Daten

    try:
        return render_template(
            'heizung.htm',
            rooms=get_Temperatur_Daten(),
            updated=request.args.get('updated'),
            error=None
        )
    except Exception:
        logging.exception("Error loading heating status")
        return render_template(
            'heizung.htm',
            rooms={},
            updated=None,
            error="Heizungsdaten konnten nicht geladen werden. "
                  "Bitte Verbindung und fritz.cnf pr\u00fcfen."
        ), 503


@web_bp.route('/heizung/sollwert', methods=['POST'])
def heizung_sollwert():
    """Set the target temperature for a configured room."""
    from fritz_handler import (
        InvalidTargetError, ROOMS, set_target_temperature
    )

    room = request.form.get('room', '')
    if room not in ROOMS:
        return _error_response("Unbekannter Heizungsraum"), 400

    try:
        set_target_temperature(room, request.form.get('target', ''))
        return redirect(url_for('web.heizung', updated=room), code=303)
    except InvalidTargetError as err:
        logging.info("Invalid heating target for %s: %s", room, err)
        return render_template(
            'heizung.htm',
            rooms={},
            updated=None,
            error=str(err)
        ), 400
    except Exception:
        logging.exception("Error setting heating target for %s", room)
        return render_template(
            'heizung.htm',
            rooms={},
            updated=None,
            error="Solltemperatur konnte nicht gesetzt werden."
        ), 502


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
