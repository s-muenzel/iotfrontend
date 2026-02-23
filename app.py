"""app.py: Web-Frontend.

Zeigt die aktuellen Wetter-Daten
Listet alle IOT-Devices
Listet alle konfigurierte Aktionen und
 bietet die Möglichtkeit zum Editieren
"""
import logging
from os import _exit, X_OK
from signal import signal, SIGTERM, SIGINT
import urllib.request
import json

from matplotlib import scale
from flask import Flask, render_template, request, redirect
# , send_from_directory
import mysql.connector as mariadb
import paho.mqtt.client as mqtt_client
import yaml
import enum

import pymodbus.client as ModbusClient
from pymodbus import (
    FramerType,
    ModbusException,
    pymodbus_apply_logging_config,
)


class registerTyp(enum.Enum):
    UINT16 = 1
    UINT32 = 2
    UINT64 = 3
    INT16 = 4
    SCALE = 5
    ACC32 = 6
    FLOAT32 = 7
    SEFLOAT = 8
    INT32 = 9
    STRING = 10


INVERTER_STATUS_MAP = [
    "Undefined",
    "Off",
    "Sleeping",
    "Grid Monitoring",
    "Producing",
    "Producing (Throttled)",
    "Shutting Down",
    "Fault",
    "Standby"
]

Inverter_registers = {
    # name, address, length, type, description, unit, scaling
    # "c_id": (0x9c40, 2, registerTyp.STRING, "SunSpec ID", "", False),
    # "c_did": (0x9c42, 1, registerTyp.UINT16, "SunSpec DID", "", False),
    # "c_length": (0x9c43, 1, registerTyp.UINT16, "SunSpec Length", "16Bit Words", False),
    # "c_manufacturer": (0x9c44, 16, registerTyp.STRING, "Manufacturer", "", False),
    # "c_model": (0x9c54, 16, registerTyp.STRING, "Model", "", False),
    # "c_version": (0x9c6c, 8, registerTyp.STRING, "Version", "", False),
    # "c_serialnumber": (0x9c74, 16, registerTyp.STRING, "Serial", "", False),
    # "c_deviceaddress": (0x9c84, 1, registerTyp.UINT16, "Modbus ID", "", False),
    # "c_sunspec_did": (0x9c85, 1, registerTyp.UINT16, "SunSpec DID", C_SUNSPEC_DID_MAP, False),
    # "c_sunspec_length": (0x9c86, 1, registerTyp.UINT16, "Length", "16Bit Words", False),

    # "current": (0x9c87, 1, registerTyp.UINT16, "Current", "A", True),
    # "l1_current": (0x9c88, 1, registerTyp.UINT16, "L1 Current", "A", True),
    # "l2_current": (0x9c89, 1, registerTyp.UINT16, "L2 Current", "A", True),
    # "l3_current": (0x9c8a, 1, registerTyp.UINT16, "L3 Current", "A", True),
    # "current_scale": (0x9c8b, 1, registerTyp.SCALE, "Current Scale Factor", ""),

    # "l1_voltage": (0x9c8c, 1, registerTyp.UINT16, "L1 Voltage", "V", True),
    # "l2_voltage": (0x9c8d, 1, registerTyp.UINT16, "L2 Voltage", "V", True),
    # "l3_voltage": (0x9c8e, 1, registerTyp.UINT16, "L3 Voltage", "V", True),
    # "l1n_voltage": (0x9c8f, 1, registerTyp.UINT16, "L1-N Voltage", "V", True),
    # "l2n_voltage": (0x9c90, 1, registerTyp.UINT16, "L2-N Voltage", "V", True),
    # "l3n_voltage": (0x9c91, 1, registerTyp.UINT16, "L3-N Voltage", "V", True),
    # "voltage_scale": (0x9c92, 1, registerTyp.SCALE, "Voltage Scale Factor", "", False),

    "power_ac": (0x9c93, 1, registerTyp.INT16, "Power", "W", True),
    "power_ac_scale": (0x9c94, 1, registerTyp.SCALE, "Power Scale Factor", "", True),

    # "frequency": (0x9c95, 1, registerTyp.UINT16, "Frequency", "Hz", True),
    # "frequency_scale": (0x9c96, 1, registerTyp.SCALE, "Frequency Scale Factor", "", False),

    # "power_apparent": (0x9c97, 1, registerTyp.INT16, "Power (Apparent)", "VA", True),
    # "power_apparent_scale": (0x9c98, 1, registerTyp.SCALE, "Power (Apparent) Scale Factor", "", False),
    # "power_reactive": (0x9c99, 1, registerTyp.INT16, "Power (Reactive)", "VAr", True),
    # "power_reactive_scale": (0x9c9a, 1, registerTyp.SCALE, "Power (Reactive) Scale Factor", "", False),
    # "power_factor": (0x9c9b, 1, registerTyp.INT16, "Power Factor", "%", True),
    # "power_factor_scale": (0x9c9c, 1, registerTyp.SCALE, "Power Factor Scale Factor", "", False),

    "energy_total": (0x9c9d, 2, registerTyp.ACC32, "Total Energy", "Wh", True),
    "energy_total_scale": (0x9c9f, 1, registerTyp.SCALE, "Total Energy Scale Factor", "", True),

    # "current_dc": (0x9ca0, 1, registerTyp.UINT16, "DC Current", "A", True),
    # "current_dc_scale": (0x9ca1, 1, registerTyp.SCALE, "DC Current Scale Factor", "", False),

    # "voltage_dc": (0x9ca2, 1, registerTyp.UINT16, "DC Voltage", "V", True),
    # "voltage_dc_scale": (0x9ca3, 1, registerTyp.SCALE, "DC Voltage Scale Factor", "", False),

    # "power_dc": (0x9ca4, 1, registerTyp.INT16, "DC Power", "W"),
    # "power_dc_scale": (0x9ca5, 1, registerTyp.SCALE, "DC Power Scale Factor", "", False  ),

    "temperature": (0x9ca7, 1, registerTyp.INT16, "Temperature", "°C", True),
    "temperature_scale": (0x9caa, 1, registerTyp.SCALE, "Temperature Scale Factor", "", True),

    "status": (0x9cab, 1, registerTyp.UINT16, "Status", INVERTER_STATUS_MAP, False),
    # "vendor_status": (0x9cac, 1, registerTyp.UINT16, "Vendor Status", "", False),

    # "rrcr_state": (0xf000, 1, registerTyp.UINT16, "RRCR State", "", False),
    # "active_power_limit": (0xf001, 1, registerTyp.UINT16, "Active Power Limit", "%", False),
    # "cosphi": (0xf002, 2, registerTyp.FLOAT32, "CosPhi", "", False),

    # "commit_power_control_settings": (0xf100, 1, registerTyp.INT16, "Commit Power Control Settings", "", False),
    # "restore_power_control_default_settings": (0xf101, 1, registerTyp.INT16, "Restore Power Control Default Settings", "", False),

    # # Documentation 'application_note_power_control_configuration-v1.3.pdf' page 7 indicates 0xf104
    # "reactive_power_config": (0xf103, 2, registerTyp.INT32, "Reactive Power Config", REACTIVE_POWER_CONFIG_MAP, False),
    # # Documentation 'application_note_power_control_configuration-v1.3.pdf' page 7 indicates 0xf106
    # "reactive_power_response_time": (0xf105, 2, registerTyp.UINT32, "Reactive Power Response Time", "ms", False),

    # # Documentation 'application_note_power_control_configuration-v1.3.pdf' page 4 indicates Int32 instead of UINT16
    # "advanced_power_control_enable": (0xf142, 2, registerTyp.INT32, "Advanced Power Control Enable", "", False),

    # "export_control_mode": (0xf700, 1, registerTyp.UINT16, "Export Control Mode", ""),
    # "export_control_limit_mode": (0xf701, 1, registerTyp.UINT16, "Export Control Limit Mode", EXPORT_CONTROL_LIMIT_MAP, False),
    # "export_control_site_limit": (0xf702, 2, registerTyp.FLOAT32, "Export Control Site Limit", "W", False),

    # "storage_control_mode": (0xe004, 1, registerTyp.UINT16, "Storage Control Mode", "", False),
    # "storage_ac_charge_policy": (0xe005, 1, registerTyp.UINT16, "Storage AC Charge Policy", "", False),
    # "storage_ac_charge_limit": (0xe006, 2, registerTyp.FLOAT32, "Storage AC Charge Limit", "", False),
    # "storage_backup_reserved_setting": (0xe008, 2, registerTyp.FLOAT32, "Storage Backup Reserved Setting", "%", False),
    # "storage_default_mode": (0xe00a, 1, registerTyp.UINT16, "Storage Charge/Discharge Default Mode", "", False),
    # "rc_cmd_timeout": (0xe00B, 2, registerTyp.UINT32, "Remote Control Command Timeout", "s", False),
    # "rc_cmd_mode": (0xe00d, 1, registerTyp.UINT16, "Remote Control Command Mode", "", False),
    # "rc_charge_limit": (0xe00e, 2, registerTyp.FLOAT32, "Remote Control Command Charge Limit", "W", False),
    # "rc_discharge_limit": (0xe010, 2, registerTyp.FLOAT32, "Remote Control Command Discharge Limit", "W", False)
    }

Meter_registers =  {
    # "c_manufacturer": (0x9cbb, 16, registerTyp.STRING, "Manufacturer", "", False),
    # "c_model": (0x9ccb, 16, registerTyp.STRING, "Model", "", False),
    # "c_option": (0x9cdb, 8, registerTyp.STRING, "Mode", "", False),
    # "c_version": (0x9ce3, 8, registerTyp.STRING, "Version", "", False),
    # "c_serialnumber": (0x9ceb, 16, registerTyp.STRING, "Serial", "", False),
    # "c_deviceaddress": (0x9cfb, 1, registerTyp.UINT16, "Modbus ID", "", False),
    # "c_sunspec_did": (0x9cfc, 1, registerTyp.UINT16, "SunSpec DID", C_SUNSPEC_DID_MAP, False),
    # "c_sunspec_length": (0x9cfd, 1, registerTyp.UINT16, "SunSpec Length", "16Bit Words", False),

    # "current": (0x9cfe, 1, registerTyp.INT16, "Current", "A", True),
    # "l1_current": (0x9cff, 1, registerTyp.INT16, "L1 Current", "A", True),
    # "l2_current": (0x9d00, 1, registerTyp.INT16, "L2 Current", "A", True),
    # "l3_current": (0x9d01, 1, registerTyp.INT16, "L3 Current", "A", True),
    # "current_scale": (0x9d02, 1, registerTyp.SCALE, "Current Scale Factor", "", True

    # "voltage_ln": (0x9d03, 1, registerTyp.INT16, "L-N Voltage", "V", True),
    # "l1n_voltage": (0x9d04, 1, registerTyp.INT16, "L1-N Voltage", "V", True),
    # "l2n_voltage": (0x9d05, 1, registerTyp.INT16, "L2-N Voltage", "V", True),
    # "l3n_voltage": (0x9d06, 1, registerTyp.INT16, "L3-N Voltage", "V", True),
    # "voltage_ll": (0x9d07, 1, registerTyp.INT16, "L-L Voltage", "V", True),
    # "l12_voltage": (0x9d08, 1, registerTyp.INT16, "L1-l2 Voltage", "V", True),
    # "l23_voltage": (0x9d09, 1, registerTyp.INT16, "L2-l3 Voltage", "V", True),
    # "l31_voltage": (0x9d0a, 1, registerTyp.INT16, "L3-l1 Voltage", "V", True),
    # "voltage_scale": (0x9d0b, 1, registerTyp.SCALE, "Voltage Scale Factor", "", True

    # "frequency": (0x9d0c, 1, registerTyp.INT16, "Frequency", "Hz", True),
    # "frequency_scale": (0x9d0d, 1, registerTyp.SCALE, "Frequency Scale Factor", "", True

    "power": (0x9d0e, 1, registerTyp.INT16, "Power", "W", True),
    # "l1_power": (0x9d0f, 1, registerTyp.INT16, "L1 Power", "W", True),
    # "l2_power": (0x9d10, 1, registerTyp.INT16, "L2 Power", "W", True),
    # "l3_power": (0x9d11, 1, registerTyp.INT16, "L3 Power", "W", True),
    "power_scale": (0x9d12, 1, registerTyp.SCALE, "Power Scale Factor", "", True),

    "power_apparent": (0x9d13, 1, registerTyp.INT16, "Power (Apparent)", "VA", True),
    # "l1_power_apparent": (0x9d14, 1, registerTyp.INT16, "L1 Power (Apparent)", "VA", True),
    # "l2_power_apparent": (0x9d15, 1, registerTyp.INT16, "L2 Power (Apparent)", "VA", True),
    # "l3_power_apparent": (0x9d16, 1, registerTyp.INT16, "L3 Power (Apparent)", "VA", True),
    "power_apparent_scale": (0x9d17, 1, registerTyp.SCALE, "Power (Apparent) Scale Factor", "", True),

    "power_reactive": (0x9d18, 1, registerTyp.INT16, "Power (Reactive)", "VAr", True),
    # "l1_power_reactive": (0x9d19, 1, registerTyp.INT16, "L1 Power (Reactive)", "VAr", True),
    # "l2_power_reactive": (0x9d1a, 1, registerTyp.INT16, "L2 Power (Reactive)", "VAr", True),
    # "l3_power_reactive": (0x9d1b, 1, registerTyp.INT16, "L3 Power (Reactive)", "VAr", True),
    "power_reactive_scale": (0x9d1c, 1, registerTyp.SCALE, "Power (Reactive) Scale Factor", "", True),

    "power_factor": (0x9d1d, 1, registerTyp.INT16, "Power Factor", "", True),
    # "l1_power_factor": (0x9d1e, 1, registerTyp.INT16, "L1 Power Factor", "", True),
    # "l2_power_factor": (0x9d1f, 1, registerTyp.INT16, "L2 Power Factor", "", True),
    # "l3_power_factor": (0x9d20, 1, registerTyp.INT16, "L3 Power Factor", "", True),
    "power_factor_scale": (0x9d21, 1, registerTyp.SCALE, "Power Factor Scale Factor", "", True),

    "export_energy_active": (0x9d22, 2, registerTyp.UINT32, "Total Exported Energy (Active)", "Wh", True),
    "energy_active_scale1": (0x9d32, 1, registerTyp.SCALE, "Energy (Active) Scale Factor", "", True),
    # "l1_export_energy_active": (0x9d24, 2, registerTyp.UINT32, "L1 Exported Energy (Active)", "Wh", True),
    # "l2_export_energy_active": (0x9d26, 2, registerTyp.UINT32, "L2 Exported Energy (Active)", "Wh", True),
    # "l3_export_energy_active": (0x9d28, 2, registerTyp.UINT32, "L3 Exported Energy (Active)", "Wh", True),
    "import_energy_active": (0x9d2a, 2, registerTyp.UINT32, "Total Imported Energy (Active)", "Wh", True),
    # "l1_import_energy_active": (0x9d2c, 2, registerTyp.UINT32, "L1 Imported Energy (Active)", "Wh", True),
    # "l2_import_energy_active": (0x9d2e, 2, registerTyp.UINT32, "L2 Imported Energy (Active)", "Wh", True),
    # "l3_import_energy_active": (0x9d30, 2, registerTyp.UINT32, "L3 Imported Energy (Active)", "Wh", True),
    "energy_active_scale": (0x9d32, 1, registerTyp.SCALE, "Energy (Active) Scale Factor", "", True),

    "export_energy_apparent": (0x9d33, 2, registerTyp.UINT32, "Total Exported Energy (Apparent)", "VAh", True),
    "energy_apparent_scale2": (0x9d43, 1, registerTyp.SCALE, "Energy (Apparent) Scale Factor", "", True),
    # "l1_export_energy_apparent": (0x9d35, 2, registerTyp.UINT32, "L1 Exported Energy (Apparent)", "VAh", True),
    # "l2_export_energy_apparent": (0x9d37, 2, registerTyp.UINT32, "L2 Exported Energy (Apparent)", "VAh", True),
    # "l3_export_energy_apparent": (0x9d39, 2, registerTyp.UINT32, "L3 Exported Energy (Apparent)", "VAh", True),
    "import_energy_apparent": (0x9d3b, 2, registerTyp.UINT32, "Total Imported Energy (Apparent)", "VAh", True),
    # "l1_import_energy_apparent": (0x9d3d, 2, registerTyp.UINT32, "L1 Imported Energy (Apparent)", "VAh", True),
    # "l2_import_energy_apparent": (0x9d3f, 2, registerTyp.UINT32, "L2 Imported Energy (Apparent)", "VAh", True),
    # "l3_import_energy_apparent": (0x9d41, 2, registerTyp.UINT32, "L3 Imported Energy (Apparent)", "VAh", True),
    "energy_apparent_scale": (0x9d43, 1, registerTyp.SCALE, "Energy (Apparent) Scale Factor", "", True),

    # "import_energy_reactive_q1": (0x9d44, 2, registerTyp.UINT32, "Total Imported Energy (Reactive) Quadrant 1", "VArh", True),
    # "energy_reactive_scale2": (0x9d64, 1, registerTyp.SCALE, "Energy (Reactive) Scale Factor", "", True),
    # # "l1_import_energy_reactive_q1": (0x9d46, 2, registerTyp.UINT32, "L1 Imported Energy (Reactive) Quadrant 1", "VArh", True),
    # # "l2_import_energy_reactive_q1": (0x9d48, 2, registerTyp.UINT32, "L2 Imported Energy (Reactive) Quadrant 1", "VArh", True),
    # # "l3_import_energy_reactive_q1": (0x9d4a, 2, registerTyp.UINT32, "L3 Imported Energy (Reactive) Quadrant 1", "VArh", True),
    # "import_energy_reactive_q2": (0x9d4c, 2, registerTyp.UINT32, "Total Imported Energy (Reactive) Quadrant 2", "VArh", True),
    # "energy_reactive_scale3": (0x9d64, 1, registerTyp.SCALE, "Energy (Reactive) Scale Factor", "", True),
    # # "l1_import_energy_reactive_q2": (0x9d4e, 2, registerTyp.UINT32, "L1 Imported Energy (Reactive) Quadrant 2", "VArh", True),
    # # "l2_import_energy_reactive_q2": (0x9d50, 2, registerTyp.UINT32, "L2 Imported Energy (Reactive) Quadrant 2", "VArh", True),
    # # "l3_import_energy_reactive_q2": (0x9d52, 2, registerTyp.UINT32, "L3 Imported Energy (Reactive) Quadrant 2", "VArh", True),
    # "export_energy_reactive_q3": (0x9d54, 2, registerTyp.UINT32, "Total Exported Energy (Reactive) Quadrant 3", "VArh", True),
    # "energy_reactive_scale4": (0x9d64, 1, registerTyp.SCALE, "Energy (Reactive) Scale Factor", "", True),
    # # "l1_export_energy_reactive_q3": (0x9d56, 2, registerTyp.UINT32, "L1 Exported Energy (Reactive) Quadrant 3", "VArh", True),
    # # "l2_export_energy_reactive_q3": (0x9d58, 2, registerTyp.UINT32, "L2 Exported Energy (Reactive) Quadrant 3", "VArh", True),
    # # "l3_export_energy_reactive_q3": (0x9d5a, 2, registerTyp.UINT32, "L3 Exported Energy (Reactive) Quadrant 3", "VArh", True),
    # "export_energy_reactive_q4": (0x9d5c, 2, registerTyp.UINT32, "Total Exported Energy (Reactive) Quadrant 4", "VArh", True),
    # # "l1_export_energy_reactive_q4": (0x9d5e, 2, registerTyp.UINT32, "L1 Exported Energy (Reactive) Quadrant 4", "VArh", True),
    # # "l2_export_energy_reactive_q4": (0x9d60, 2, registerTyp.UINT32, "L2 Exported Energy (Reactive) Quadrant 4", "VArh", True),
    # # "l3_export_energy_reactive_q4": (0x9d62, 2, registerTyp.UINT32, "L3 Exported Energy (Reactive) Quadrant 4", "VArh", True),
    # "energy_reactive_scale": (0x9d64, 1, registerTyp.SCALE, "Energy (Reactive) Scale Factor", "", True)
    }


def cb_signal_handler(signum, frame):
    """signal_handler: beendet das Programm, wenn ein  Signale kommt."""
    logging.info("ACHTUNG SIG %d, exiting", signum)
    _exit(X_OK)


FLASK_APP = Flask(import_name=__name__)


@FLASK_APP.route('/')
def top():
    """top: Web-Handler für /."""
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs "
                       "WHERE topic='Sensor/WZTuF/EG/WZ//T'")
        for message in cursor:
            temp = message[0]
        cursor.close()
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs "
                       "WHERE topic='Sensor/WZTuF/EG/WZ//F'")
        for message in cursor:
            feucht = message[0]
        cursor.close()
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs "
                       "WHERE topic='Sensor/WZTuF/EG/WZ//H'")
        for message in cursor:
            hell = message[0]
        cursor.close()
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs "
                       "WHERE topic='Sensor/Garage/Zisterne///P'")
        for message in cursor:
            proz = message[0]
        cursor.close()
        cursor = db_connection.cursor()
        cursor.execute("SELECT device.name AS name, device.url AS url,"
                       " device_description.description AS description "
                       "FROM device INNER JOIN `device_description` "
                       "ON device.name"
                       " = device_description.name WHERE device.status = 'up'")
        entries = []
        for name, url, description in cursor:
            entries.append([name, url, description])
        cursor.close()
        db_connection.close()
        return render_template('top.htm', T=temp, F=feucht, H=hell, P=proz,
                               eintraege=entries)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></h1></body>'


@FLASK_APP.route('/iot.htm')
def iot():
    """top: Web-Handler für /iot.htm"""
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT device.name AS name, device.url AS url,"
                       " device_description.description AS description "
                       "FROM device INNER JOIN `device_description` "
                       "ON device.name"
                       " = device_description.name WHERE device.status = 'up'")
        entries = []
        for name, url, description in cursor:
            entries.append([name, url, description])
        cursor.close()
        db_connection.close()
        return render_template('iot.htm', eintraege=entries)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></h1></body>'


@FLASK_APP.route('/devices')
def devices():
    """devices: Web-Handler für /devices."""
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT name, url, ip_1, ip_2, ip_3, ip_4, status,"
                       " timestamp FROM device")
        entries = []
        for name, url, ip_1, ip_2, ip_3, ip_4, status, timestamp in cursor:
            entries.append([name, url, ip_1, ip_2, ip_3, ip_4,
                            status, timestamp])
        cursor.close()
        db_connection.close()
        return render_template('devices.htm', eintraege=entries)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


@FLASK_APP.route('/actions')
def actions():
    """Webpage Generator: actions.

    Web-Handler für /actions: listet die Aktionen auf
    (ohne Details)
    """
    try:
        aktionen = []
        logging.debug("/actions")
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT id, name, activ FROM activities ORDER BY name")
        for id, name, activ in cursor:  # pylint: disable=W0622,C0103
            logging.debug("DB result: %d %s", id, name)
            aktionen.append([name, id, activ])
        cursor.close()
        return render_template('actions.htm', eintraege=aktionen)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


@FLASK_APP.route('/aktion/add')
def aktionadd():
    """aktionadd: Füllt die Seite zum Erstellen einer Aktion."""
    logging.info("aktionadd")
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT mqtt_name FROM device_description"
                       " WHERE NOT mqtt_name = ''")
        mqttdevices = []
        for mqtt_name in cursor:
            mqttdevices.append(mqtt_name[0])
        cursor.close()
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT topic FROM mqtt_msgs"
                       " WHERE max_age = 0")
        trigger = []
        for topic in cursor:
            trigger.append(topic[0])
        cursor.close()
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT typ FROM activity_actions")
        actiontyp = []
        for typ in cursor:
            actiontyp.append(typ[0])
        cursor.close()
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT typ FROM activity_conditions")
        condtyp = []
        for typ in cursor:
            condtyp.append(typ[0])
        cursor.close()
        return render_template('addaction.htm',
                               devices=mqttdevices, trigger=trigger,
                               actiontyp=actiontyp, condtyp=condtyp)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


@FLASK_APP.route('/addaktion', methods=["GET"])
def addaktion():
    """addaktion.

    Trägt eine neue Regel in die verschiedenen Tabellen ein."""
    logging.info("addaktion")

    try:
        a_name = request.values.get("a_name", "")
        a_desc = request.values.get("a_desc", "")
        a_dev = request.values.get("a_dev", "")

        t_topic = request.values.get("t_topic", "")
        t_min = request.values.get("t_min", "")
        t_max = request.values.get("t_max", "")

        ak_typ = request.values.get("ak_typ", "")
        ak_arg1 = request.values.get("ak_arg1", "")
        ak_arg2 = request.values.get("ak_arg2", "")

        c_typ = request.values.get("c_typ", "")
        c_arg1 = request.values.get("c_arg1", "")
        c_arg2 = request.values.get("c_arg2", "")

        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT MAX(id) FROM activities")
        result = cursor.fetchall()
        new_id = result[0][0]+1
        logging.info("New Activity ID is %d", new_id)
        cursor.close()
        cursor = db_connection.cursor()
        sql_str = "INSERT INTO activities "\
                  "(id, name, device, description) VALUES ({}, '{}',"\
                  " '{}', '{}')".format(new_id, a_name, a_dev, a_desc)
        logging.debug("activities: %s", sql_str)
        cursor.execute(sql_str)
        cursor.close()
        cursor = db_connection.cursor()
        sql_str = "INSERT INTO activity_trigger "\
                  "(id, topic, min, max) VALUES ({}, '{}',"\
                  " {}, '{}')".format(new_id, t_topic, t_min, t_max)
        logging.debug("trigger: %s", sql_str)
        cursor.execute(sql_str)
        cursor.close()
        cursor = db_connection.cursor()
        sql_str = "INSERT INTO activity_actions "\
                  "(id, typ, arg1, arg2) VALUES ({}, '{}',"\
                  " '{}', '{}')".format(new_id, ak_typ, ak_arg1, ak_arg2)
        logging.debug("actions: %s", sql_str)
        cursor.execute(sql_str)
        cursor.close()
        cursor = db_connection.cursor()
        sql_str = "INSERT INTO activity_conditions "\
                  "(id, typ, min, max) VALUES ({}, '{}',"\
                  " {}, {})".format(new_id, c_typ, c_arg1, c_arg2)
        logging.debug("conditions: %s", sql_str)
        cursor.execute(sql_str)
        cursor.close()
        db_connection.commit()
        return redirect("/actions", code=307)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


@FLASK_APP.route('/aktion/SchalteUm/<int:actionid>')
def aktion_schalte_an_aus(actionid):
    """Webpage Generator: /aktion/SchalteAn/x.

    Setzt den Wert der Aktion auf das Gegenteil des aktuellen Wertes
    """
    logging.info("/aktion/SchalteAn/actionid: %d", actionid)
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        sql_str = "UPDATE activities "\
                  "SET activ = ( SELECT COUNT(activ) FROM activities "\
                  "WHERE id='{actionid}' AND activ=0 ) "\
                  "WHERE id='{actionid}'".format(actionid=actionid)
        logging.debug("Sql Update activ: %s", sql_str)
        cursor.execute(sql_str)
        cursor.close()
        db_connection.commit()
        return redirect("/actions", code=307)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


@FLASK_APP.route('/aktiondelete', methods=["GET"])
def aktiondelete():
    """aktiondelete: Web-Handler für /aktiondelete."""
    logging.debug("aktiondelete")
    actionid = request.values.get("actionid", -1)
    logging.info("Bestätige Löschen der Aktion: %s", actionid)
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        sql_str = "DELETE FROM activity_trigger "\
                  "WHERE id='{}'".format(actionid)
        logging.debug("Deleting: %s", sql_str)
        cursor.execute(sql_str)
        cursor.close()
        cursor = db_connection.cursor()
        sql_str = "DELETE FROM activity_conditions "\
                  "WHERE id='{}'".format(actionid)
        logging.debug("Deleting: %s", sql_str)
        cursor.execute(sql_str)
        cursor.close()
        cursor = db_connection.cursor()
        sql_str = "DELETE FROM activity_actions "\
                  "WHERE id='{}'".format(actionid)
        logging.debug("Deleting: %s", sql_str)
        cursor.execute(sql_str)
        cursor.close()
        cursor = db_connection.cursor()
        sql_str = "DELETE FROM activities "\
                  "WHERE id='{}'".format(actionid)
        logging.debug("Deleting: %s", sql_str)
        cursor.execute(sql_str)
        cursor.close()
        db_connection.commit()
        return redirect("/actions", code=307)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


@FLASK_APP.route('/action/<int:actionid>')
def action(actionid):  # pylint: disable=R0914
    """Webpage Generator: action.

    Web-Handler für /action/x: listet die Details für die
    Aktion x auf
    """
    logging.debug("/action, actionid: %d", actionid)
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT activities.name as name,"
                       " activities.device as device,"
                       " device_description.name as geraet "
                       "FROM activities INNER JOIN device_description ON"
                       " activities.device = device_description.mqtt_name "
                       "WHERE id='{}'".format(actionid))
        actionname = "unbekannt"
        devicename = "unbekannt"
        geraetname = "unbekannt"
        for name, device, geraet in cursor:  # pylint: disable=W0622
            actionname = name
            devicename = device
            geraetname = geraet
        cursor.close()
        trigger_liste = []
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT topic FROM activity_trigger")
        for topic in cursor:
            trigger_liste.append(topic[0])
        cursor.close()
        trigger = []
        cursor = db_connection.cursor()
        cursor.execute("SELECT lfdnr, topic, min, max  FROM activity_trigger"
                       " WHERE id='{}'".format(actionid))
        for lfdnr, topic, min, max in cursor:  # pylint: disable=W0622
            trigger.append([topic, min, max, lfdnr])
        cursor.close()
        cond_liste = []
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT typ FROM activity_conditions")
        for typ in cursor:
            cond_liste.append(typ[0])
        cursor.close()
        cursor = db_connection.cursor()
        cursor.execute("SELECT lfdnr, typ, min, max  FROM activity_conditions"
                       " WHERE id='{}'".format(actionid))
        conditions = []
        for lfdnr, typ, min, max in cursor:
            conditions.append([typ, min, max, lfdnr])
        cursor.close()
        action_liste = []
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT arg1 FROM activity_actions")
        for arg1 in cursor:
            action_liste.append(arg1[0])
        cursor.close()
        aktion = []
        cursor = db_connection.cursor()
        cursor.execute("SELECT lfdnr, typ, arg1, arg2 FROM activity_actions"
                       " WHERE id='{}'".format(actionid))
        for lfdnr, typ, arg1, arg2 in cursor:
            aktion.append([typ, arg1, arg2, lfdnr])
        cursor.close()
        return render_template('action.htm',
                               device=geraetname, deviceid=devicename,
                               trigger_liste=trigger_liste, trigger=trigger,
                               cond_liste=cond_liste, conditions=conditions,
                               action_liste=action_liste, action=aktion,
                               actionid=actionid, actionname=actionname)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


SELECT_TEXTE = {
    "trigger": "SELECT topic AS a_0, min AS a_1, max AS a_2"
               " FROM activity_trigger",
    "condition": "SELECT typ AS a_0, min AS a_1, max AS a_2"
                 " FROM activity_conditions",
    "action": "SELECT typ AS a_0, arg1 AS a_1, arg2 AS a_2"
              " FROM activity_actions",
    "fehler": ""
}


@FLASK_APP.route('/delete_condition', methods=["GET"])
def delete_condition():
    """delete_condition: Web-Handler für /delete."""
    lfdnr = request.values.get("lfdnr", -1)
    logging.info("Lösche Bedingung %s", lfdnr)
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM activity_conditions "
                       "WHERE lfdnr='{}'".format(lfdnr))
        rows = cursor.fetchall()
        local_id = rows[0][0]
        cursor.close()
        logging.debug("id: %s", local_id)
        cursor = db_connection.cursor()
        cursor.execute("DELETE FROM activity_conditions "
                       "WHERE lfdnr={}".format(lfdnr))
        db_connection.commit()
        cursor.close()
        return redirect("/action/{}".format(local_id), code=307)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


@FLASK_APP.route('/add_condition', methods=["GET"])
def add_condition():
    """add_condition: Web-Handler für /addcond."""
    logging.debug("addcond")
    arg0 = request.values.get("a0", "")
    arg1 = request.values.get("a1", "")
    arg2 = request.values.get("a2", "")
    actionid = request.values.get("actionid", "")
    logging.info("adding condition: a0=%s a1=%s a2=%s id=%s",
                 arg0, arg1, arg2, actionid)
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        sql_str = "INSERT INTO activity_conditions "\
                  "(id, typ, min, max) VALUES ({}, '{}',"\
                  " '{}', '{}' )".format(actionid, arg0, arg1, arg2)
        logging.debug("Neue bedingung: %s", sql_str)
        cursor.execute("INSERT INTO activity_conditions "
                       "(id, typ, min, max) VALUES ({}, '{}',"
                       " '{}', '{}' )".format(actionid, arg0, arg1, arg2))
        db_connection.commit()
        cursor.close()
        return redirect("/action/{}".format(actionid), code=307)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


UPDATE_TEXTE = {
    "trigger": "UPDATE activity_trigger SET topic='{}',min='{}',max='{}'"
               " WHERE lfdnr={}",
    "condition": "UPDATE activity_conditions SET typ='{}',min='{}',max='{}'"
                 " WHERE lfdnr={}",
    "action": "UPDATE activity_actions SET typ='{}',arg1='{}',arg2='{}'"
              " WHERE lfdnr={}",
    "fehler": ""
}


@FLASK_APP.route('/submitchange', methods=["GET"])
def submitchange():
    """submitchange: Web-Handler für /submitchange."""
    arg0 = request.values.get("a0", "")
    arg1 = request.values.get("a1", "")
    arg2 = request.values.get("a2", "")
    typ = request.values.get("typ", "fehler")
    lfdnr = request.values.get("lfdnr", -1)
    actionid = request.values.get("actionid", -1)
    logging.info("change of %s: %s %s %s", typ, arg0, arg1, arg2)
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        logging.debug(UPDATE_TEXTE[typ].format(arg0, arg1, arg2, lfdnr))
        cursor.execute(UPDATE_TEXTE[typ].format(arg0, arg1, arg2, lfdnr))
        db_connection.commit()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    return redirect("/action/{}".format(actionid), code=307)


@FLASK_APP.route('/reloadaktions')
def reloadaktions():
    """reloadaktions: Web-Handler für /reloadaktions."""
    logging.info("reloadaktions")
    # mqtt_config = yaml.safe_load(open("mq.cnf"))
    # publish.single("DB", payload="AKTION",
    #                hostname=mqtt_config["mqtt"]["mqttserver"],
    #                port=mqtt_config["mqtt"]["mqttport"])
    mqtt_client.publish(topic="DB", payload="AKTION")
    return redirect("/actions", code=307)


@FLASK_APP.route('/status_r')
def send_status_r():
    """send_status: asynchrones Laden der aktuellen Status-Infos Rollos

    Returns:
        String: JSON mit den Daten
    """
    x = {
        "rollo_bad": "?",
        "rollo_eva": "?",
        "rollo_sz": "?",
        "rollo_tim": "?",
    }
    try:
        with urllib.request.urlopen("http://shellyswitch25-4C752533F665.fritz.box/roller/0",
                                    timeout=5) as response:
            html = response.read().decode('utf-8')
            rollerstat = json.loads(html)
            x["rollo_bad"] = rollerstat["current_pos"]
    except urllib.error.URLError as err:
        logging.debug("URL Error: %s", err.reason)
    try:
        with urllib.request.urlopen("http://shellyswitch25-68666D.fritz.box/roller/0",
                                    timeout=5) as response:
            html = response.read().decode('utf-8')
            rollerstat = json.loads(html)
            x["rollo_eva"] = rollerstat["current_pos"]
    except urllib.error.URLError as err:
        logging.debug("URL Error: %s", err.reason)
    try:
        with urllib.request.urlopen("http://shellyswitch25-B8AC9B.fritz.box/roller/0",
                                    timeout=5) as response:
            html = response.read().decode('utf-8')
            rollerstat = json.loads(html)
            x["rollo_sz"] = rollerstat["current_pos"]
    except urllib.error.URLError as err:
        logging.debug("URL Error: %s", err.reason)
    try:
        with urllib.request.urlopen("http://shellyswitch25-4C752534C604.fritz.box/roller/0",
                                    timeout=5) as response:
            html = response.read().decode('utf-8')
            rollerstat = json.loads(html)
            x["rollo_tim"] = rollerstat["current_pos"]
    except urllib.error.URLError as err:
        logging.debug("URL Error: %s", err.reason)
    return json.dumps(x)

@FLASK_APP.route('/status_g')
def send_status_g():
    """send_status: asynchrones Laden der aktuellen Status-Infos Garage

    Returns:
        String: JSON mit den Daten
    """
    x = {
        "garage_tor": "?",
    }
    try:
        with urllib.request.urlopen("http://192.168.2.97/Status",
                                    timeout=5) as response:
            html = response.read().decode('utf-8')
            rollerstat = json.loads(html)
            x["garage_tor"] = rollerstat["Tor"]
    except urllib.error.URLError as err:
        logging.debug("URL Error: %s", err.reason)
    return json.dumps(x)

@FLASK_APP.route('/status_l')
def send_status_l():
    """send_status: asynchrones Laden der aktuellen Status-Infos der Lampen

    Returns:
        String: JSON mit den Daten
    """
    x = {
        "wz_lampe": "?",
    }
    try:
        with urllib.request.urlopen("http://wz-lampe.fritz.box",
                                    timeout=5) as response:
            html = response.read().decode('utf-8')
            if html == "Aus":
                x["wz_lampe"] = "0"
            else:
                x["wz_lampe"] = html
    except urllib.error.URLError as err:
        logging.debug("URL Error: %s", err.reason)
    return json.dumps(x)


@FLASK_APP.route('/bewaesserung')
def bewaesserung():
    """bewaesserung: Web-Handler für /bewaesserung
    Füllt die letzten bekannten "Ist" Werte ein und zeigt die Webseite
    """
    # global _bewaesserung_dauer, _bewaesserung_frequenz, _bewaesserung_next, _bewaesserung_wasser
    logging.debug("bewaesserung")
    try:
        if _bewaesserung_dauer == -1:
            mqtt_client.publish("Bewaesserung/Ist", "{}")
        return render_template('bewaesserung.htm', D=_bewaesserung_dauer,
                               F=_bewaesserung_frequenz/3600., N=_bewaesserung_next/3600., W=_bewaesserung_wasser)
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></h1></body>'


@FLASK_APP.route('/set_bew', methods=["GET"])
def set_bew():
    """submitchange: Web-Handler für /set_ber.
    Neue Werte für die Bewässerung:
    Wert 0: Dauer
    Wert 1: Frequenz (ist eigentlich Periode)
    Wert 2: Next"""
    was = request.values.get("was", "?")
    wieviel = request.values.get("wieviel", "-1")
    logging.info(
        "Neue Bewaesesrungswerte WaS:%s wieviel:%d", was, wieviel)
    if was != "?":
        mqtt_client.publish("Bewaesserung/Soll", '{"'+was+'":'+wieviel+'}')
    return "{'ok'}"


def on_message(client, userdata, msg):
    """on_message: callback für MQTT Nachricht
    Nach Empfang einer MQTT Nachricht topic "Bewaesserung/Ist" die Daten merken
    """
    global _bewaesserung_dauer, _bewaesserung_frequenz, _bewaesserung_next, _bewaesserung_wasser
    print("Thema %s Msg %s", msg.topic, msg.payload.decode())
    logging.debug("Received topic %s Msg %s", msg.topic, msg.payload.decode())
    bew = json.loads(msg.payload.decode())
    if "Dauer" in bew:
        _bewaesserung_dauer = bew["Dauer"]
        _bewaesserung_frequenz = bew["Frequenz"]
        _bewaesserung_next = bew["Next"]
        _bewaesserung_wasser = bew["Wasser"]


# def on_connect(client, userdata, flags, rc):
#     print("on_connect")


# def on_subscribe(client, userdata, mid, granted_qos):
#     print("on_subscribe")


@FLASK_APP.route('/strom.htm')
def strom():
    """strom: Web-Handler für /strom
    Holt per modbus die aktuellen Werte von der Stromzähler und zeigt sie an
    """
    logging.debug("strom")
    # print("get client")
    modclient = ModbusClient.ModbusTcpClient(
        host = "192.168.2.56",
        port="1502"
        # ,
        # framer=FramerType.SOCKET,
        # timeout=10,
        # retries=3,
        # source_address=("localhost", 0),
    )
    # print("connect to server")
    if not modclient.connect():
        logging.error("Unable to connect to modbus server")
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>keine Verbindung zum Solaredge</h1></h1></body>'
    try:
        rr = modclient.read_holding_registers(0x9c93,count=2)
        values = modclient.convert_from_registers(rr.registers, data_type=modclient.DATATYPE.INT16)
        P_Solar = values[0] * ( 10 ** values[1])
        rr = modclient.read_holding_registers(0x9d0e,count=5)
        values = modclient.convert_from_registers(rr.registers, data_type=modclient.DATATYPE.INT16)
        P_Haus = values[0] * ( 10 ** values[4])
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Strom</title></head><body>'\
               '<h1>Leistung Solaranlage: {P_Solar}W</h1>'\
               '<h1>Leistung Haus: {P_Haus}W</h1>'\
               '</body>'.format(P_Solar=P_Solar,P_Haus=P_Haus)
        # return render_template('bewaesserung.htm', D=_bewaesserung_dauer,
                            #    F=_bewaesserung_frequenz/3600., N=_bewaesserung_next/3600., W=_bewaesserung_wasser)
    except ModbusException as exc:  # pragma: no cover
        logging.error(f"Received ModbusException({exc}) from library")
        modclient.close()
        return  '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>Modbus Fehler</h1></h1>{exc}</body>'
    except ModbusException as exc:  # pragma: no cover
        logging.error(f"Received ModbusException({exc}) from library")
        modclient.close()
        return  '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>keinen ModbusWert bekommen</title></head>'\
               '<body><h1>Modbus kein Wert</h1></h1>{exc}</body>'
        return
    except Exception as err:  # pylint: disable=W0703
        logging.warning("General failure %s", str(err))
        return '<!DOCTYPE html><html><head><meta charset="UTF-8">'\
               '<title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></h1></body>'


if __name__ == '__main__':
    signal(SIGTERM, cb_signal_handler)
    signal(SIGINT, cb_signal_handler)

# {"Dauer":20,"Frequenz":10800,"Next":4769,"Wasser":"ok"}
    _bewaesserung_dauer = -1
    _bewaesserung_frequenz = -1
    _bewaesserung_next = -1
    _bewaesserung_wasser = False
    mqtt_config = yaml.safe_load(open("mq.cnf"))
    mqtt_client = mqtt_client.Client(client_id="bew-test")
    mqtt_client.on_message = on_message
    erg = mqtt_client.connect(host=mqtt_config["mqtt"]["mqttserver"],
                              port=mqtt_config["mqtt"]["mqttport"])
    print("connect:", erg)
    erg = mqtt_client.subscribe("Bewaesserung/Ist")
    print("subscribe:", erg)
    mqtt_client.loop_start()

    FLASK_APP.run(host='0.0.0.0', port=80)

    mqtt_client.loop_stop()
