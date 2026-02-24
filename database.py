"""database.py: Database operations for IoT Frontend.

Handles all MySQL/MariaDB operations
"""
import logging
import mysql.connector as mariadb


def get_connection():
    """Create and return a MariaDB connection.
    
    Returns:
        Connection: MariaDB database connection
        
    Raises:
        mariadb.Error: If connection fails
    """
    return mariadb.connect(option_files="db.cnf", database="iot")


def get_weather_data():
    """Fetch current weather data from MQTT messages.
    
    Returns:
        dict: Dictionary with keys 'temp', 'feucht', 'hell', 'proz'
    """
    weather_data = {
        'temp': 'N/A',
        'feucht': 'N/A',
        'hell': 'N/A',
        'proz': 'N/A'
    }
    
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        
        # Get temperature
        cursor.execute("SELECT message FROM mqtt_msgs WHERE topic='Sensor/WZTuF/EG/WZ//T'")
        for message in cursor:
            weather_data['temp'] = message[0]
        cursor.close()
        
        # Get humidity
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs WHERE topic='Sensor/WZTuF/EG/WZ//F'")
        for message in cursor:
            weather_data['feucht'] = message[0]
        cursor.close()
        
        # Get brightness
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs WHERE topic='Sensor/WZTuF/EG/WZ//H'")
        for message in cursor:
            weather_data['hell'] = message[0]
        cursor.close()
        
        # Get cistern percentage
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs WHERE topic='Sensor/Garage/Zisterne///P'")
        for message in cursor:
            weather_data['proz'] = message[0]
        cursor.close()
        
        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        
    return weather_data


def get_devices():
    """Fetch all active devices.
    
    Returns:
        list: List of [name, url, description] for each device
    """
    entries = []
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT device.name AS name, device.url AS url,"
                       " device_description.description AS description "
                       "FROM device INNER JOIN `device_description` "
                       "ON device.name = device_description.name "
                       "WHERE device.status = 'up'")
        for name, url, description in cursor:
            entries.append([name, url, description])
        cursor.close()
        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
    
    return entries


def get_all_devices():
    """Fetch all devices with detailed information.
    
    Returns:
        list: List of [name, url, ip_1, ip_2, ip_3, ip_4, status, timestamp]
    """
    entries = []
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT name, url, ip_1, ip_2, ip_3, ip_4, status, timestamp FROM device")
        for name, url, ip_1, ip_2, ip_3, ip_4, status, timestamp in cursor:
            entries.append([name, url, ip_1, ip_2, ip_3, ip_4, status, timestamp])
        cursor.close()
        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
    
    return entries


def get_activities():
    """Fetch all activities (actions).
    
    Returns:
        list: List of [name, id, activ] for each activity
    """
    activities = []
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT id, name, activ FROM activities ORDER BY name")
        for activity_id, name, activ in cursor:
            activities.append([name, activity_id, activ])
        cursor.close()
        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
    
    return activities


def get_activity_details(action_id):
    """Fetch detailed information for a specific activity.
    
    Args:
        action_id: The activity ID
        
    Returns:
        dict: Dictionary with activity details and related data
    """
    result = {
        'actionname': 'unbekannt',
        'devicename': 'unbekannt',
        'geraetname': 'unbekannt',
        'trigger_liste': [],
        'trigger': [],
        'cond_liste': [],
        'conditions': [],
        'action_liste': [],
        'actions': []
    }
    
    try:
        db_connection = get_connection()
        
        # Get activity info
        cursor = db_connection.cursor()
        cursor.execute("SELECT activities.name as name, activities.device as device,"
                       " device_description.name as geraet "
                       "FROM activities INNER JOIN device_description ON"
                       " activities.device = device_description.mqtt_name "
                       "WHERE id='{}'".format(action_id))
        for name, device, geraet in cursor:
            result['actionname'] = name
            result['devicename'] = device
            result['geraetname'] = geraet
        cursor.close()
        
        # Get all available triggers
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT topic FROM activity_trigger")
        result['trigger_liste'] = [topic[0] for topic in cursor]
        cursor.close()
        
        # Get triggers for this activity
        cursor = db_connection.cursor()
        cursor.execute("SELECT lfdnr, topic, min, max FROM activity_trigger WHERE id='{}'".format(action_id))
        result['trigger'] = [[topic, min_val, max_val, lfdnr] for lfdnr, topic, min_val, max_val in cursor]
        cursor.close()
        
        # Get all available condition types
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT typ FROM activity_conditions")
        result['cond_liste'] = [typ[0] for typ in cursor]
        cursor.close()
        
        # Get conditions for this activity
        cursor = db_connection.cursor()
        cursor.execute("SELECT lfdnr, typ, min, max FROM activity_conditions WHERE id='{}'".format(action_id))
        result['conditions'] = [[typ, min_val, max_val, lfdnr] for lfdnr, typ, min_val, max_val in cursor]
        cursor.close()
        
        # Get all available action types
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT arg1 FROM activity_actions")
        result['action_liste'] = [arg1[0] for arg1 in cursor]
        cursor.close()
        
        # Get actions for this activity
        cursor = db_connection.cursor()
        cursor.execute("SELECT lfdnr, typ, arg1, arg2 FROM activity_actions WHERE id='{}'".format(action_id))
        result['actions'] = [[typ, arg1, arg2, lfdnr] for lfdnr, typ, arg1, arg2 in cursor]
        cursor.close()
        
        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
    
    return result


def get_mqtt_devices():
    """Fetch list of MQTT device names.
    
    Returns:
        list: List of mqtt_name values
    """
    devices = []
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT mqtt_name FROM device_description WHERE NOT mqtt_name = ''")
        devices = [mqtt_name[0] for mqtt_name in cursor]
        cursor.close()
        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
    
    return devices


def get_triggers():
    """Fetch all unique MQTT topics for triggers.
    
    Returns:
        list: List of unique topic names
    """
    triggers = []
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT topic FROM mqtt_msgs WHERE max_age = 0")
        triggers = [topic[0] for topic in cursor]
        cursor.close()
        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
    
    return triggers


def get_action_types():
    """Fetch all available action types.
    
    Returns:
        list: List of action type names
    """
    types = []
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT typ FROM activity_actions")
        types = [typ[0] for typ in cursor]
        cursor.close()
        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
    
    return types


def get_condition_types():
    """Fetch all available condition types.
    
    Returns:
        list: List of condition type names
    """
    types = []
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT typ FROM activity_conditions")
        types = [typ[0] for typ in cursor]
        cursor.close()
        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
    
    return types


def create_activity(new_id, name, device, description, trigger_data, action_data, condition_data):
    """Create a new activity with all related data.
    
    Args:
        new_id: The new activity ID
        name: Activity name
        device: Device name
        description: Activity description
        trigger_data: Tuple of (topic, min, max)
        action_data: Tuple of (typ, arg1, arg2)
        condition_data: Tuple of (typ, min, max)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        
        # Insert activity
        sql_str = ("INSERT INTO activities (id, name, device, description) "
                   "VALUES ({}, '{}', '{}', '{}')".format(new_id, name, device, description))
        cursor.execute(sql_str)
        cursor.close()
        
        # Insert trigger
        cursor = db_connection.cursor()
        sql_str = ("INSERT INTO activity_trigger (id, topic, min, max) "
                   "VALUES ({}, '{}', {}, '{}')".format(new_id, trigger_data[0], trigger_data[1], trigger_data[2]))
        cursor.execute(sql_str)
        cursor.close()
        
        # Insert action
        cursor = db_connection.cursor()
        sql_str = ("INSERT INTO activity_actions (id, typ, arg1, arg2) "
                   "VALUES ({}, '{}', '{}', '{}')".format(new_id, action_data[0], action_data[1], action_data[2]))
        cursor.execute(sql_str)
        cursor.close()
        
        # Insert condition
        cursor = db_connection.cursor()
        sql_str = ("INSERT INTO activity_conditions (id, typ, min, max) "
                   "VALUES ({}, '{}', {}, {})".format(new_id, condition_data[0], condition_data[1], condition_data[2]))
        cursor.execute(sql_str)
        cursor.close()
        
        db_connection.commit()
        db_connection.close()
        return True
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return False


def get_next_activity_id():
    """Get the next available activity ID.
    
    Returns:
        int: The next ID to use
    """
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT MAX(id) FROM activities")
        result = cursor.fetchall()
        cursor.close()
        db_connection.close()
        return result[0][0] + 1 if result[0][0] else 1
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return 1


def update_activity_status(activity_id):
    """Toggle activity status (activ) between 0 and 1.
    
    Args:
        activity_id: The activity ID to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        sql_str = ("UPDATE activities SET activ = (SELECT COUNT(activ) FROM activities "
                   "WHERE id='{}' AND activ=0) WHERE id='{}'".format(activity_id, activity_id))
        cursor.execute(sql_str)
        cursor.close()
        db_connection.commit()
        db_connection.close()
        return True
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return False


def delete_activity(activity_id):
    """Delete an activity and all related records.
    
    Args:
        activity_id: The activity ID to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        
        # Delete in order of dependencies
        cursor.execute("DELETE FROM activity_trigger WHERE id='{}'".format(activity_id))
        cursor.close()
        
        cursor = db_connection.cursor()
        cursor.execute("DELETE FROM activity_conditions WHERE id='{}'".format(activity_id))
        cursor.close()
        
        cursor = db_connection.cursor()
        cursor.execute("DELETE FROM activity_actions WHERE id='{}'".format(activity_id))
        cursor.close()
        
        cursor = db_connection.cursor()
        cursor.execute("DELETE FROM activities WHERE id='{}'".format(activity_id))
        cursor.close()
        
        db_connection.commit()
        db_connection.close()
        return True
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return False


def delete_condition(lfdnr):
    """Delete a specific condition.
    
    Args:
        lfdnr: The condition line number
        
    Returns:
        int: The activity ID or -1 if failed
    """
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT id FROM activity_conditions WHERE lfdnr='{}'".format(lfdnr))
        rows = cursor.fetchall()
        activity_id = rows[0][0] if rows else -1
        cursor.close()
        
        cursor = db_connection.cursor()
        cursor.execute("DELETE FROM activity_conditions WHERE lfdnr={}".format(lfdnr))
        db_connection.commit()
        cursor.close()
        db_connection.close()
        
        return activity_id
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return -1


def add_condition(activity_id, typ, min_val, max_val):
    """Add a new condition to an activity.
    
    Args:
        activity_id: The activity ID
        typ: Condition type
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        sql_str = ("INSERT INTO activity_conditions (id, typ, min, max) "
                   "VALUES ({}, '{}', '{}', '{}')".format(activity_id, typ, min_val, max_val))
        cursor.execute(sql_str)
        db_connection.commit()
        cursor.close()
        db_connection.close()
        return True
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return False


def update_record(table_name, typ, arg1, arg2, lfdnr):
    """Update a record in activity tables.
    
    Args:
        table_name: 'trigger', 'condition', or 'action'
        typ: Type/first value
        arg1: Second value
        arg2: Third value
        lfdnr: The line number to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        
        if table_name == "trigger":
            sql_str = ("UPDATE activity_trigger SET topic='{}', min='{}', max='{}' "
                       "WHERE lfdnr={}".format(typ, arg1, arg2, lfdnr))
        elif table_name == "condition":
            sql_str = ("UPDATE activity_conditions SET typ='{}', min='{}', max='{}' "
                       "WHERE lfdnr={}".format(typ, arg1, arg2, lfdnr))
        elif table_name == "action":
            sql_str = ("UPDATE activity_actions SET typ='{}', arg1='{}', arg2='{}' "
                       "WHERE lfdnr={}".format(typ, arg1, arg2, lfdnr))
        else:
            return False
            
        cursor.execute(sql_str)
        db_connection.commit()
        cursor.close()
        db_connection.close()
        return True
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)
        return False
