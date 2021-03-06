"""app.py: Web-Frontend
   Zeigt die aktuellen Wetter-Daten
   Listet alle IOT-Devices
   Listet alle konfigurierte Aktionen und
    bietet die Möglichtkeit zum Editieren
"""
import logging
from os import _exit, X_OK
from signal import signal, SIGTERM, SIGINT
from flask import Flask, render_template, request
import mysql.connector as mariadb


def cb_signal_handler(signum, frame):
    """signal_handler: beendet das Programm, wenn eines der Signale kommt
    """
    logging.info("ACHTUNG SIG %d, exiting", signum)
    _exit(X_OK)


FLASK_APP = Flask(import_name=__name__)


@FLASK_APP.route('/')
def top():
    """top: Web-Handler für /"""
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
        cursor.execute("SELECT device.name AS name, device.url AS url,"
                       " device_description.description AS description "
                       "FROM device INNER JOIN `device_description` ON device.name"
                       " = device_description.name WHERE device.status = 'up'")
        entries = []
        for name, url, description in cursor:
            entries.append([name, url, description])
        cursor.close()
        db_connection.close()
        return render_template('top.htm', T=temp, F=feucht, H=hell, eintraege=entries)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except:  # pylint: disable=W0702
        logging.error("General failure")
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></h1></body>'


@FLASK_APP.route('/devices')
def devices():
    """devices: Web-Handler für /devices"""
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT name, url, ip_1, ip_2, ip_3, ip_4, status, timestamp FROM device")
        entries = []
        for name, url, ip_1, ip_2, ip_3, ip_4, status, timestamp in cursor:
            entries.append([name, url, ip_1, ip_2, ip_3, ip_4, status, timestamp])
        cursor.close()
        db_connection.close()
        return render_template('devices.htm', eintraege=entries)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except:  # pylint: disable=W0702
        logging.error("General failure")
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


@FLASK_APP.route('/actions')
def actions():
    """actions: Web-Handler für /actions: listet die Aktionen auf (ohne Details)"""
    try:
        aktionen = []
        logging.warning("/actions")
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT id, name FROM activities")
        for id, name in cursor:  # pylint: disable=W0622,C0103
            logging.warning("DB result: %d %s", id, name)
            aktionen.append([name, id])
        cursor.close()
        return render_template('actions.htm', eintraege=aktionen)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except:  # pylint: disable=W0702
        logging.warning("General failure")
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


@FLASK_APP.route('/action/<int:actionid>')
def action(actionid):  # pylint: disable=R0914
    """action: Web-Handler für /action/x: listet die Details für die Aktion x auf"""
    logging.warning("/action, actionid: %d", actionid)
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM activities WHERE"
                       " id='{}'".format(actionid))
        actionname = "unbekannt"
        for name in cursor:  # pylint: disable=W0622
            actionname = name[0]
        cursor.close()
        trigger = []
        cursor = db_connection.cursor()
        cursor.execute("SELECT lfdnr, topic, min, max  FROM activity_trigger WHERE"
                       " id='{}'".format(actionid))
        for lfdnr, topic, min, max in cursor:  # pylint: disable=W0622
            trigger.append([topic, min, max, lfdnr])
        cursor.close()
        cursor = db_connection.cursor()
        cursor.execute("SELECT lfdnr, typ, min, max  FROM activity_conditions WHERE"
                       " id='{}'".format(actionid))
        conditions = []
        for lfdnr, typ, min, max in cursor:
            conditions.append([typ, min, max, lfdnr])
        cursor.close()
        aktion = []
        cursor = db_connection.cursor()
        cursor.execute("SELECT lfdnr, typ, arg1, arg2 FROM activity_actions WHERE"
                       " id='{}'".format(actionid))
        for lfdnr, typ, arg1, arg2 in cursor:
            aktion.append([typ, arg1, arg2, lfdnr])
        cursor.close()
        return render_template('action.htm', trigger=trigger, conditions=conditions,
                               action=aktion, actionid=actionid, actionname=actionname)
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    except:  # pylint: disable=W0702
        logging.warning("General failure")
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>allgemeiner Fehler</h1></body>'


SELECT_TEXTE = {
    "trigger": "SELECT topic AS a_0, min AS a_1, max AS a_2 FROM activity_trigger",
    "condition": "SELECT typ AS a_0, min AS a_1, max AS a_2 FROM activity_conditions",
    "action": "SELECT typ AS a_0, arg1 AS a_1, arg2 AS a_2 FROM activity_actions",
    "fehler": ""
}


@FLASK_APP.route('/edit/<string:typ>/<int:lfdnr>')
def edit(typ, lfdnr):
    """editentry: Web-Handler für /edittrigger/x"""
    logging.warning("edit %d %s", lfdnr, typ)
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        cursor.execute(SELECT_TEXTE[typ]+" WHERE lfdnr='{}'".format(lfdnr))
        arg0 = ""
        arg1 = ""
        arg2 = ""
        for a_0, a_1, a_2 in cursor:  # pylint: disable=W0622
            arg0 = a_0
            arg1 = a_1
            arg2 = a_2
        logging.warning("Edit:Values: %s %s %s", arg0, arg1, arg2)
        cursor.close()
        return render_template('editentry.htm', typ=typ, lfdnr=lfdnr,
                               label0="a", arg0=arg0,
                               label1="b", arg1=arg1,
                               label2="c", arg2=arg2
                               )
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)


@FLASK_APP.route('/condition/remove/<int:lfdnr>')
def removecondition(lfdnr):
    """removecondition: Web-Handler für /removecondition/x"""
    logging.warning("removecondition %d", lfdnr)
    return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>TODO</title></head>'\
           '<body><h1>TODO</h1>removecondition {}</body>'.format(lfdnr)


@FLASK_APP.route('/condition/add/<int:actionid>')
def addcondition(actionid):
    """addcondition: Web-Handler für /addcondition/x"""
    logging.warning("addcondition %d", actionid)
    return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>TODO</title></head>'\
           '<body><h1>TODO</h1>addcondition {}</body>'.format(actionid)


UPDATE_TEXTE = {
    "trigger": "UPDATE activity_trigger SET topic='{}',min='{}',max='{}' WHERE lfdnr={}",
    "condition": "UPDATE activity_conditions SET typ='{}',min='{}',max='{}' WHERE lfdnr={}",
    "action": "UPDATE activity_actions SET typ='{}',arg1='{}',arg2='{}' WHERE lfdnr={}",
    "fehler": ""
}


@FLASK_APP.route('/submitchange', methods=["GET"])
def submitchange():
    """submitchange: Web-Handler für /submitchange"""
    logging.warning("submitchange")
    arg0 = request.values.get("a0", "")
    arg1 = request.values.get("a1", "")
    arg2 = request.values.get("a2", "")
    typ = request.values.get("typ", "fehler")
    lfdnr = request.values.get("lfdnr", -1)
    try:
        db_connection = mariadb.connect(option_files="db.cnf", database="iot")
        cursor = db_connection.cursor()
        logging.warning(UPDATE_TEXTE[typ].format(arg0, arg1, arg2, lfdnr))
        cursor.execute(UPDATE_TEXTE[typ].format(arg0, arg1, arg2, lfdnr))
        db_connection.commit()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Fehler</title></head>'\
               '<body><h1>Datenbank Fehler</h1>{f}</h1></body>'.format(f=err)
    return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Ok</title></head>'\
           '<body><h1>Gespeichert</h1><a href="/actions">zurück zur Übersicht</a></body>'


if __name__ == '__main__':
    signal(SIGTERM, cb_signal_handler)
    signal(SIGINT, cb_signal_handler)

    FLASK_APP.run(host='0.0.0.0', port=80)
