"""FRITZ!Box Smart Home thermostat access."""
import hashlib
import json
import logging
import math
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import yaml


CONFIG_PATH = "fritz.cnf"

_CONFIG = {"url": None, "username": None, "password": None}
_RAUM_UID_MAP = {"Tim", "Eva", "Hobbykeller", "Wintergarten"}
LOGIN_SID_ROUTE = "/login_sid.lua?version=2"
SMART_HOME_REST_ROUTE = "/api/v0/smarthome"
ROOMS = ()
MIN_TEMPERATURE = 8.0
MAX_TEMPERATURE = 28.0
SESSION_IDLE_TIMEOUT = 15 * 60

_SID = None
_SID_LAST_USED = None
_SID_TIMER = None
_SID_LOCK = threading.RLock()


def _schedule_sid_logout(sid: str) -> None:
    """Reset the idle timer for the active FRITZ!Box session."""
    global _SID, _SID_LAST_USED, _SID_TIMER
    with _SID_LOCK:
        if _SID_TIMER is not None:
            _SID_TIMER.cancel()
        _SID = sid
        _SID_LAST_USED = time.monotonic()
        _SID_TIMER = threading.Timer(
            SESSION_IDLE_TIMEOUT, _logout_expired_sid, args=(sid,)
        )
        _SID_TIMER.daemon = True
        _SID_TIMER.start()


def _logout_expired_sid(sid: str) -> None:
    """Log out the session if it has remained idle until the timer expires."""
    global _SID, _SID_LAST_USED, _SID_TIMER
    with _SID_LOCK:
        if _SID != sid or _SID_LAST_USED is None:
            return

        remaining = SESSION_IDLE_TIMEOUT - (
            time.monotonic() - _SID_LAST_USED
        )
        if remaining > 0:
            _SID_TIMER = threading.Timer(
                remaining, _logout_expired_sid, args=(sid,)
            )
            _SID_TIMER.daemon = True
            _SID_TIMER.start()
            return

        _SID = None
        _SID_LAST_USED = None
        _SID_TIMER = None
        try:
            if not logout(_CONFIG["url"], sid):
                logging.warning("FRITZ!Box session logout was not confirmed")
        except (OSError, ValueError, ET.ParseError):
            logging.warning("Could not close idle FRITZ!Box session", exc_info=True)


def _load_config():
    try:
        if (_CONFIG["url"] is None or _CONFIG["username"] is None or _CONFIG["password"] is None):
            with open(CONFIG_PATH, encoding="utf-8") as config_file:
                config = yaml.safe_load(config_file)
            _CONFIG["url"] = config.get("fritz").get("url")
            _CONFIG["username"] = config.get("fritz").get("username")
            _CONFIG["password"] = config.get("fritz").get("password")
            logging.info("Loaded FRITZ!Box config from %s: url=%s, username=%s", Path(
                CONFIG_PATH).resolve(), _CONFIG["url"], _CONFIG["username"])
        else:
            logging.info("Using cached FRITZ!Box config")
    except OSError as err:
        raise RuntimeError("Could not read fritz.cnf") from err
    except yaml.YAMLError as err:
        raise ValueError("fritz.cnf must contain valid YAML") from err


class LoginState:
    def __init__(self, sid: str, challenge: str, blocktime: int):
        self.sid = sid
        self.challenge = challenge
        self.blocktime = blocktime


class InvalidTargetError(ValueError):
    """Raised when a user supplies an invalid thermostat target value."""


def get_sid() -> str:
    """Check login state.
    If already logged in, return the existing sid.
    Otherwise, get a new sid by solving the PBKDF2 (or MD5) challenge-response process."""
    global _SID, _SID_LAST_USED, _SID_TIMER
    _load_config()
    with _SID_LOCK:
        if _SID and _SID_LAST_USED is not None:
            if time.monotonic() - _SID_LAST_USED < SESSION_IDLE_TIMEOUT:
                sid = _SID
                _schedule_sid_logout(sid)
                return sid
            _logout_expired_sid(_SID)

    try:
        # state = get_login_state(_CONFIG["url"])
        logging.info("Getting FRITZ!Box login state from %s", _CONFIG["url"])
        url = _CONFIG["url"] + LOGIN_SID_ROUTE
        http_response = urllib.request.urlopen(url)
        xml = ET.fromstring(http_response.read())
        sid = xml.find("SID").text
        challenge = xml.find("Challenge").text
        blocktime = int(xml.find("BlockTime").text)
    except Exception as ex:
        raise Exception("failed to get challenge") from ex
    if (sid != "0000000000000000"):
        logging.info("FRITZ!Box already logged in with sid: %s", sid)
        _schedule_sid_logout(sid)
        return sid

    logging.info("FRITZ!Box login challenge: %s", challenge)
    challenge_response = calculate_pbkdf2_response(
        challenge, _CONFIG["password"]
    )

    if blocktime > 0:
        logging.info("Waiting for %d seconds...", blocktime)
        time.sleep(blocktime)

    try:
        sid = send_response(
            _CONFIG["url"], _CONFIG["username"], challenge_response)
    except Exception as ex:
        raise Exception("failed to login") from ex

    logging.info("FRITZ!Box login sid: %s", sid)
    if sid == "0000000000000000":
        raise Exception("wrong username or password")

    _schedule_sid_logout(sid)
    return sid



def calculate_pbkdf2_response(challenge: str, password: str) -> str:
    """Calculate the response for a given challenge via PBKDF2."""
    challenge_parts = challenge.split("$")

    # Extract all necessary values encoded into the challenge
    iter1 = int(challenge_parts[1])
    salt1 = bytes.fromhex(challenge_parts[2])
    iter2 = int(challenge_parts[3])
    salt2 = bytes.fromhex(challenge_parts[4])

    # Hash twice, once with static salt...
    hash1 = hashlib.pbkdf2_hmac("sha256", password.encode(), salt1, iter1)

    # Once with dynamic salt.
    hash2 = hashlib.pbkdf2_hmac("sha256", hash1, salt2, iter2)
    return f"{challenge_parts[4]}${hash2.hex()}"


def send_response(
    box_url: str, username: str, challenge_response: str
) -> str:
    """Send the response and return the parsed sid. Raises an Exception on error."""
    # Build response params
    post_data_dict = {"username": username, "response": challenge_response}
    post_data = urllib.parse.urlencode(post_data_dict).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = box_url + LOGIN_SID_ROUTE

    # Send response
    http_request = urllib.request.Request(url, post_data, headers)
    http_response = urllib.request.urlopen(http_request)

    # Parse SID from resulting XML.
    xml = ET.fromstring(http_response.read())
    return xml.find("SID").text


def logout(box_url: str, sid: str) -> bool:
    """Log out the FRITZ!Box session and report whether it was invalidated."""
    if not sid:
        raise ValueError("sid must not be empty")

    query = urllib.parse.urlencode({"logout": "1", "sid": sid})
    url = box_url.rstrip("/") + "/login_sid.lua?" + query
    http_response = urllib.request.urlopen(url)
    xml = ET.fromstring(http_response.read())
    sid_element = xml.find("SID")
    if sid_element is None or sid_element.text is None:
        raise ValueError("FRITZ!Box logout response did not contain a SID")
    return sid_element.text == "0000000000000000"


def _smart_home_rest_request(
    box_url: str,
    sid: str,
    path: str,
    method: str = "GET",
    payload: Optional[Mapping[str, Any]] = None,
) -> bytes:
    """Send an authenticated JSON request to the Smart Home REST API."""
    headers = {
        "Authorization": f"AVM-SID {sid}",
        "Accept": "application/json",
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    url = (
        box_url.rstrip("/")
        + SMART_HOME_REST_ROUTE
        + path
    )
    request = urllib.request.Request(
        url, data=body, headers=headers, method=method
    )
    http_response = urllib.request.urlopen(request)
    return http_response.read()


def _get_smart_home_devices(box_url: str, sid: str) -> list[dict[str, Any]]:
    """Fetch devices and their current unit data from the REST overview."""
    response = _smart_home_rest_request(box_url, sid, "/overview")
    overview = json.loads(response)
    if not isinstance(overview, dict):
        raise ValueError("FRITZ!Box REST overview must be a JSON object")

    devices = overview.get("devices")
    units = overview.get("units")
    if not isinstance(devices, list) or not isinstance(units, list):
        raise ValueError("FRITZ!Box REST overview lacks devices or units")

    units_by_uid = {
        unit["UID"]: unit
        for unit in units
        if isinstance(unit, dict) and isinstance(unit.get("UID"), str)
    }
    devices_with_units = []
    for device in devices:
        if not isinstance(device, dict):
            raise ValueError(
                "FRITZ!Box REST overview contains an invalid device")
        unit_uids = device.get("unitUids")
        if not isinstance(unit_uids, list):
            raise ValueError(
                "FRITZ!Box REST device is missing its unitUids list")
        device_with_units = dict(device)
        device_with_units["units"] = []
        for unit_uid in unit_uids:
            unit = units_by_uid.get(unit_uid)
            if unit is None:
                raise ValueError(
                    f"FRITZ!Box REST overview is missing unit {unit_uid!r}"
                )
            device_with_units["units"].append(unit)
        devices_with_units.append(device_with_units)

    return devices_with_units


def get_Temperatur_Daten():
    """Return actual and target temperatures indexed by room name."""

    # get the current session ID (SID) or get a new one from the FRITZ!Box
    sid = get_sid()
    devices = _get_smart_home_devices(_CONFIG["url"], sid)
    ret_val = _temperatures_from_devices(devices)
    logging.info(f"Temperaturdaten: {ret_val}")
    return ret_val


def _read_url(url, request=None):
    """Open a URL with an optional prebuilt request object."""
    return urllib.request.urlopen(url if request is None else request, timeout=10)


def _smart_home_request(box_url, sid, path, method="GET", payload=None):
    headers = {"Authorization": f"AVM-SID {sid}", "Accept": "application/json"}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        box_url.rstrip("/") + SMART_HOME_REST_ROUTE + path,
        data=body,
        headers=headers,
        method=method
    )
    with _read_url(None, request) as response:
        return response.read()


def _get_devices(box_url, sid):
    """Fetch all Smart Home devices with their units attached."""
    overview = json.loads(_smart_home_request(box_url, sid, "/overview"))
    if not isinstance(overview, dict):
        raise ValueError("FRITZ!Box Smart Home overview is invalid")
    devices = overview.get("devices")
    units = overview.get("units")
    if not isinstance(devices, list) or not isinstance(units, list):
        raise ValueError("FRITZ!Box overview lacks devices or units")

    units_by_uid = {
        unit["UID"]: unit for unit in units
        if isinstance(unit, dict) and isinstance(unit.get("UID"), str)
    }
    results = []
    for device in devices:
        if not isinstance(device, dict) or not isinstance(
                device.get("unitUids"), list):
            raise ValueError("FRITZ!Box overview contains an invalid device")
        device_with_units = dict(device)
        device_with_units["units"] = []
        for unit_uid in device["unitUids"]:
            unit = units_by_uid.get(unit_uid)
            if unit is None:
                raise ValueError(
                    f"FRITZ!Box overview is missing unit {unit_uid!r}"
                )
            device_with_units["units"].append(unit)
        results.append(device_with_units)
    return results


def _thermostat(device):
    for unit in device.get("units", []):
        if (isinstance(unit, dict)
                and unit.get("unitType") == "avmThermostat"
                and unit.get("isConnected", False)):
            return unit
    return None


def _temperatures_from_devices(devices, rooms=None):
    global ROOMS
    if rooms is None:
        rooms = []
        for device in devices:
            room = device.get("name")
            if isinstance(room, str) and _thermostat(device) is not None and room not in rooms:
                rooms.append(room)
        ROOMS = tuple(rooms)
    status = {room: None for room in rooms}
    for device in devices:
        room = device.get("name")
        if room not in status:
            continue
        unit = _thermostat(device)
        if unit is None:
            continue
        interfaces = unit.get("interfaces")
        if not isinstance(interfaces, Mapping):
            continue
        temperature = interfaces.get("temperatureInterface")
        thermostat = interfaces.get("thermostatInterface")
        set_point = (
            thermostat.get("setPointTemperature")
            if isinstance(thermostat, Mapping) else None
        )
        if not isinstance(temperature, Mapping) or not isinstance(
                set_point, Mapping):
            continue
        actual = temperature.get("celsius")
        if set_point.get("mode") != "temperature":
            # nicht im Temperaturmodus, z.B. "off" oder "holiday"
            target = 0
        else:
            target = set_point.get("celsius")
        if isinstance(actual, (int, float)) and isinstance(target, (int, float)):
            status[room] = {"actual": actual, "target": target}
    return status


def set_target_temperature(room, value):
    """Set a room thermostat target in degrees Celsius."""
    if room not in ROOMS:
        raise InvalidTargetError("Unknown heating room")
    try:
        target = float(value)
    except (TypeError, ValueError) as err:
        raise InvalidTargetError(
            "Bitte eine g\u00fcltige Solltemperatur eingeben."
        ) from err
    if (not math.isfinite(target) or target < MIN_TEMPERATURE
            or target > MAX_TEMPERATURE or target * 2 != int(target * 2)):
        raise InvalidTargetError(
            "Die Solltemperatur muss zwischen 8 und 28 \u00b0C "
            "in 0,5-\u00b0C-Schritten liegen."
        )

    sid = get_sid()
    
    device = next(
        (item for item in _get_devices(_CONFIG["url"], sid)
            if item.get("name") == room),
        None
    )
    unit = _thermostat(device) if device is not None else None
    if unit is None:
        raise RuntimeError(
            f"Kein verbundener Thermostat f\u00fcr {room} gefunden."
        )
    unit_uid = unit.get("UID")
    if not isinstance(unit_uid, str) or not unit_uid:
        raise RuntimeError(f"Thermostat-UID f\u00fcr {room} fehlt.")
    _smart_home_request(
        _CONFIG["url"],
        sid,
        "/overview/units/" + urllib.parse.quote(unit_uid, safe=""),
        method="PUT",
        payload={
            "interfaces": {
                "thermostatInterface": {
                    "setPointTemperature": {
                        "mode": "temperature",
                        "celsius": target
                    }
                }
            }
        }
    )