"""routes_status.py: Web routes for status and monitoring."""
import json
import logging
import urllib.request
from flask import Blueprint, render_template, request
import modbus_handler
import mqtt_handler

status_bp = Blueprint('status', __name__)


@status_bp.route('/status_r')
def status_rollos():
    """Get status of roller shutters from Shelly devices (async).
    
    Returns:
        JSON: Dictionary with roller positions
    """
    result = {
        "rollo_bad": "?",
        "rollo_eva": "?",
        "rollo_sz": "?",
        "rollo_tim": "?",
    }
    
    shelly_devices = {
        "rollo_bad": "http://shellyswitch25-4C752533F665.fritz.box/roller/0",
        "rollo_eva": "http://shellyswitch25-68666D.fritz.box/roller/0",
        "rollo_sz": "http://shellyswitch25-B8AC9B.fritz.box/roller/0",
        "rollo_tim": "http://shellyswitch25-4C752534C604.fritz.box/roller/0",
    }
    
    for device_key, url in shelly_devices.items():
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                html = response.read().decode('utf-8')
                roller_stat = json.loads(html)
                result[device_key] = roller_stat["current_pos"]
        except urllib.error.URLError as err:
            logging.debug("URL Error for %s: %s", device_key, err.reason)
    
    return json.dumps(result)


@status_bp.route('/status_g')
def status_garage():
    """Get status of garage door (async).
    
    Returns:
        JSON: Dictionary with garage door status
    """
    result = {"garage_tor": "?"}
    
    try:
        with urllib.request.urlopen("http://192.168.2.97/Status", timeout=5) as response:
            html = response.read().decode('utf-8')
            garage_stat = json.loads(html)
            result["garage_tor"] = garage_stat["Tor"]
    except urllib.error.URLError as err:
        logging.debug("URL Error for garage: %s", err.reason)
    
    return json.dumps(result)


@status_bp.route('/status_l')
def status_lampen():
    """Get status of lamps (async).
    
    Returns:
        JSON: Dictionary with lamp status
    """
    result = {"wz_lampe": "?"}
    
    try:
        with urllib.request.urlopen("http://wz-lampe.fritz.box", timeout=5) as response:
            html = response.read().decode('utf-8')
            result["wz_lampe"] = "0" if html == "Aus" else html
    except urllib.error.URLError as err:
        logging.debug("URL Error for lights: %s", err.reason)
    
    return json.dumps(result)


@status_bp.route('/bewaesserung')
def bewaesserung():
    """Web handler for /bewaesserung - Irrigation system page."""
    logging.debug("bewaesserung")
    
    try:
        status = mqtt_handler.get_bewaesserung_status()
        
        # Request latest values if not available
        if status['dauer'] == -1:
            mqtt_handler.publish_message("Bewaesserung/Ist", "{}")
        
        return render_template(
            'bewaesserung.htm',
            D=status['dauer'],
            F=status['frequenz'] / 3600.0 if status['frequenz'] != -1 else -1,
            N=status['next'] / 3600.0 if status['next'] != -1 else -1,
            W=status['wasser']
        )
    except Exception as err:
        logging.warning("Error in bewaesserung(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@status_bp.route('/set_bew', methods=["GET"])
def set_bew():
    """Set irrigation system parameter values.
    
    Query parameters:
        was: Parameter name (Dauer, Frequenz, Next)
        wieviel: Parameter value
        
    Returns:
        JSON: Success response
    """
    was = request.values.get("was", "?")
    wieviel = request.values.get("wieviel", "-1")
    
    logging.info("Neue Bewaesserungswerte was:%s wieviel:%s", was, wieviel)
    
    try:
        if was != "?":
            mqtt_handler.set_bewaesserung_value(was, wieviel)
        return '{"ok"}'
    except Exception as err:
        logging.warning("Error in set_bew(): %s", str(err))
        return '{"error": "' + str(err) + '"}'


@status_bp.route('/strom.htm')
def strom():
    """Web handler for /strom - Display current power info via Modbus."""
    logging.debug("strom")
    
    try:
        power_data = modbus_handler.get_power_status()
        
        if power_data is None:
            return _error_response("keine Verbindung zum Solaredge")
        
        return ('<!DOCTYPE html><html><head><meta charset="UTF-8">'
                '<title>Strom</title></head><body>'
                '<h1>Leistung Solaranlage: {p_solar}W</h1>'
                '<h1>Leistung Haus: {p_haus}W</h1>'
                '<h1>Leistung Netz: {p_grid}W</h1>'
                '<h1>Leistung Batterie: {p_batterie}W</h1>'
                '</body></html>'.format(
                    p_solar=int(power_data['p_solar']),
                    p_haus=int(power_data['p_haus']),
                    p_grid=int(power_data['p_grid']),
                    p_batterie=int(power_data['p_battery'])
                ))
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
