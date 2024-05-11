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
from flask import Flask, render_template, request, redirect
# , send_from_directory
import mysql.connector as mariadb
import paho.mqtt.client as mqtt_client
import yaml


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


@FLASK_APP.route('/status')
def send_status():
    """send_status: asynchrones Laden der aktuellen Status-Infos

    Returns:
        String: JSON mit den Daten
    """
    x = {
        "wz_lampe": "?",
        "rollo_bad": "?",
        "rollo_eva": "?",
        "rollo_sz": "?",
        "rollo_tim": "?",
        "garage_tor": "?",
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
    try:
        with urllib.request.urlopen("http://shellyswitch25-b8afc3.fritz.box/roller/0",
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
        with urllib.request.urlopen("http://shellyswitch25-B8A5AD.fritz.box/roller/0",
                                    timeout=5) as response:
            html = response.read().decode('utf-8')
            rollerstat = json.loads(html)
            x["rollo_tim"] = rollerstat["current_pos"]
    except urllib.error.URLError as err:
        logging.debug("URL Error: %s", err.reason)
    try:
        with urllib.request.urlopen("http://192.168.2.97/Status",
                                    timeout=5) as response:
            html = response.read().decode('utf-8')
            rollerstat = json.loads(html)
            x["garage_tor"] = rollerstat["Tor"]
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
