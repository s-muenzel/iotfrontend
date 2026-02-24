"""routes_actions.py: Web routes for action management."""
import logging
from flask import Blueprint, render_template, request, redirect
import database as db
import mqtt_handler

actions_bp = Blueprint('actions', __name__)


@actions_bp.route('/actions')
def actions():
    """Web handler for /actions - List all actions."""
    try:
        logging.debug("/actions")
        activities = db.get_activities()
        return render_template('actions.htm', eintraege=activities)
    except Exception as err:
        logging.warning("Error in actions(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@actions_bp.route('/aktion/add')
def aktion_add():
    """Web handler for /aktion/add - Form to create new action."""
    logging.info("aktion_add")
    try:
        mqtt_devices = db.get_mqtt_devices()
        triggers = db.get_triggers()
        action_types = db.get_action_types()
        condition_types = db.get_condition_types()
        
        return render_template(
            'addaction.htm',
            devices=mqtt_devices,
            trigger=triggers,
            actiontyp=action_types,
            condtyp=condition_types
        )
    except Exception as err:
        logging.warning("Error in aktion_add(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@actions_bp.route('/addaktion', methods=["GET"])
def add_aktion():
    """Web handler for /addaktion - Create new action from form data."""
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
        
        new_id = db.get_next_activity_id()
        logging.info("New Activity ID is %d", new_id)
        
        trigger_data = (t_topic, t_min, t_max)
        action_data = (ak_typ, ak_arg1, ak_arg2)
        condition_data = (c_typ, c_arg1, c_arg2)
        
        if db.create_activity(new_id, a_name, a_dev, a_desc, trigger_data, action_data, condition_data):
            return redirect("/actions", code=307)
        else:
            return _error_response("Fehler beim Erstellen der Aktion")
    except Exception as err:
        logging.warning("Error in add_aktion(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@actions_bp.route('/aktion/SchalteUm/<int:action_id>')
def aktion_schalte_an_aus(action_id):
    """Web handler for /aktion/SchalteUm/<id> - Toggle action status."""
    logging.info("/aktion/SchalteUm/action_id: %d", action_id)
    
    try:
        if db.update_activity_status(action_id):
            return redirect("/actions", code=307)
        else:
            return _error_response("Fehler beim Aktualisieren der Aktion")
    except Exception as err:
        logging.warning("Error in aktion_schalte_an_aus(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@actions_bp.route('/aktiondelete', methods=["GET"])
def aktion_delete():
    """Web handler for /aktiondelete - Delete an action."""
    logging.debug("aktiondelete")
    action_id = request.values.get("actionid", -1)
    logging.info("Bestätige Löschen der Aktion: %s", action_id)
    
    try:
        if db.delete_activity(int(action_id)):
            return redirect("/actions", code=307)
        else:
            return _error_response("Fehler beim Löschen der Aktion")
    except Exception as err:
        logging.warning("Error in aktion_delete(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@actions_bp.route('/action/<int:action_id>')
def action(action_id):
    """Web handler for /action/<id> - Show action details."""
    logging.debug("/action, action_id: %d", action_id)
    
    try:
        details = db.get_activity_details(action_id)
        
        return render_template(
            'action.htm',
            device=details['geraetname'],
            deviceid=details['devicename'],
            trigger_liste=details['trigger_liste'],
            trigger=details['trigger'],
            cond_liste=details['cond_liste'],
            conditions=details['conditions'],
            action_liste=details['action_liste'],
            action=details['actions'],
            actionid=action_id,
            actionname=details['actionname']
        )
    except Exception as err:
        logging.warning("Error in action(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@actions_bp.route('/delete_condition', methods=["GET"])
def delete_condition():
    """Web handler for /delete_condition - Delete a condition."""
    lfdnr = request.values.get("lfdnr", -1)
    logging.info("Lösche Bedingung %s", lfdnr)
    
    try:
        local_id = db.delete_condition(int(lfdnr))
        if local_id != -1:
            return redirect("/action/{}".format(local_id), code=307)
        else:
            return _error_response("Fehler beim Löschen der Bedingung")
    except Exception as err:
        logging.warning("Error in delete_condition(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@actions_bp.route('/add_condition', methods=["GET"])
def add_condition():
    """Web handler for /add_condition - Add a new condition."""
    logging.debug("add_condition")
    arg0 = request.values.get("a0", "")
    arg1 = request.values.get("a1", "")
    arg2 = request.values.get("a2", "")
    action_id = request.values.get("actionid", "")
    
    logging.info("adding condition: a0=%s a1=%s a2=%s id=%s", arg0, arg1, arg2, action_id)
    
    try:
        if db.add_condition(int(action_id), arg0, arg1, arg2):
            return redirect("/action/{}".format(action_id), code=307)
        else:
            return _error_response("Fehler beim Hinzufügen der Bedingung")
    except Exception as err:
        logging.warning("Error in add_condition(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@actions_bp.route('/submitchange', methods=["GET"])
def submitchange():
    """Web handler for /submitchange - Update action/trigger/condition."""
    arg0 = request.values.get("a0", "")
    arg1 = request.values.get("a1", "")
    arg2 = request.values.get("a2", "")
    typ = request.values.get("typ", "fehler")
    lfdnr = request.values.get("lfdnr", -1)
    action_id = request.values.get("actionid", -1)
    
    logging.info("change of %s: %s %s %s", typ, arg0, arg1, arg2)
    
    try:
        if db.update_record(typ, arg0, arg1, arg2, int(lfdnr)):
            return redirect("/action/{}".format(action_id), code=307)
        else:
            return _error_response("Fehler beim Aktualisieren")
    except Exception as err:
        logging.warning("Error in submitchange(): %s", str(err))
        return _error_response("allgemeiner Fehler")


@actions_bp.route('/reloadaktions')
def reload_aktions():
    """Web handler for /reloadaktions - Reload actions."""
    logging.info("reloadaktions")
    mqtt_handler.reload_actions()
    return redirect("/actions", code=307)


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
