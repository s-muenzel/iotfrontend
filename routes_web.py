"""routes_web.py: Web routes for main pages and device information."""
from functools import lru_cache
import logging
import math
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
import database as db
import mqtt_handler
from netzwerk import check_netzwerkfehler


web_bp = Blueprint('web', __name__)


@lru_cache(maxsize=1)
def _get_heating_rooms():
    """Load the available heating rooms once for this process."""
    return tuple(db.get_heating_rooms())


@web_bp.route('/')
def top():
    """Web handler for / - Top/Home page with weather and device info."""
    try:
        return _render_top()
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


@web_bp.route('/historie.htm')
def historie():
    """Render the history of successfully applied activities."""
    try:
        eintraege = db.get_activities_history()
        return render_template('historie.htm', eintraege=eintraege)
    except Exception as err:
        logging.warning("Error in historie(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@web_bp.route('/heizung/status')
def heizung_status():
    """Return the latest thermostat readings stored in the database."""
    try:
        return jsonify(rooms=db.get_heating_data())
    except Exception:
        logging.exception("Error loading heating status")
        return jsonify(error="Heizungsdaten konnten nicht geladen werden."), 503


@web_bp.route('/heizung/sollwert', methods=['POST'])
def heizung_sollwert():
    """Set a room's target temperature through MQTT."""
    room = request.form.get('room', '')
    if room not in _get_heating_rooms():
        return _error_response("Unbekannter Heizungsraum"), 400

    target_value = request.form.get('target', '')
    try:
        target = float(target_value)
    except (TypeError, ValueError):
        error = "Bitte eine g\u00fcltige Solltemperatur eingeben."
        return _render_top(heating_error=error), 400

    if (not math.isfinite(target)
            or (target != 0 and not 8 <= target <= 28)):
        error = (
            "Die Solltemperatur muss 0 oder zwischen 8 und 28 \u00b0C liegen."
        )
        return _render_top(heating_error=error), 400

    if target != 0:
        target = math.floor(target * 2 + 0.5) / 2
    target_payload = "0" if target == 0 else f"{target:g}"

    try:
        if mqtt_handler.mqtt_client_instance is None:
            raise RuntimeError("MQTT client not initialized")
        mqtt_handler.publish_message(
            f"Aktor/Fritz////{room}", target_payload
        )
        return redirect(url_for('web.top') + '#heizung', code=303)
    except Exception:
        logging.exception("Error publishing heating target for %s", room)
        return _render_top(
            heating_error="Solltemperatur konnte nicht gesetzt werden."
        ), 502


def _render_top(heating_error=None):
    """Render the dashboard with optional heating form feedback."""
    weather = db.get_weather_data()
    return render_template(
        'top.htm',
        T=weather['temp'],
        F=weather['feucht'],
        H=weather['hell'],
        R=weather['regen'],
        P=weather['proz'],
        heating_error=heating_error,
        heating_rooms=_get_heating_rooms()
    )


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
