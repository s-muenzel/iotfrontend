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


def getColor(type, value):
    """Return an interpolated hex color."""
    # Definition der MinMax-Werte für jeden Typ
    MinMax = {
        "T": (-10, 40),  # Temperature range in Celsius
        "F": (0, 100),   # Humidity range in percentage
        "H": (0, 1000),  # Brightness range in lux
        "R": (0, 15),    # Rain range in mm
        "P": (0, 100)    # Cistern percentage range in percentage
    }
    # Definition der 4 Farbpunkte als RGB-Tupel
    colors: dict[str, list[tuple[int, int, int]]] = {
        "T": [
            (0, 0, 255),        # 0% -> #0000FF
            (0, 255, 0),        # 33% -> #00ff00
            (255, 255, 0),      # 66% -> #ffff00
            (255, 0, 0)         # 100% -> #ff0000
        ],
        "F": [
            (210, 180, 140),    # 0% -> #D2B48C
            (143, 188, 143),    # 33% -> #8FBC8F
            (76, 175, 80),      # 66% -> #4CAF50
            (26, 82, 118)       # 100% -> #1A5276
        ],
        "H": [
            (1, 1, 1),          # 0% -> #010101
            (96, 96, 96),       # 33% -> #606060
            (192, 192, 192),    # 66% -> #C0C0C0
            (255, 255, 255)     # 100% -> #FFFFFF
        ],
        "R": [
            (255, 225, 0),  # 0% -> #E4C293
            (75, 150, 15),  # 33% -> #788CA8
            (0,  75, 255),  # 66% -> #788CA8
            (0,   0, 255)   # 100% -> #2B5C8F
        ],
        "P": [
            (210, 180, 140),  # 0% -> #D2B48C
            (143, 188, 143),  # 33% -> #8FBC8F
            (76, 175, 80),    # 66% -> #4CAF50
            (26, 82, 118)     # 100% -> #1A5276
        ],
    }

    # Werte für den angegebenen Typ abrufen
    min_v = MinMax[type][0]
    max_v = MinMax[type][1]

    clamped_value = max(min_v, min(max_v, value))
    p = (clamped_value - min_v) / (max_v - min_v)

    # Bestimmen, in welchem Segment sich der Wert befindet, und Faktor berechnen
    if p <= 0.33:
        c1, c2 = colors[type][0], colors[type][1]
        factor = p / 0.33
    elif p <= 0.66:
        c1, c2 = colors[type][1], colors[type][2]
        factor = (p - 0.33) / 0.33  # (0.66 - 0.33) ist ebenfalls 0.33
    else:
        c1, c2 = colors[type][2], colors[type][3]
        factor = (p - 0.66) / 0.34  # (1.0 - 0.66) ist 0.34

    # Lineare Interpolation für jeden RGB-Kanal
    r = int(c1[0] + factor * (c2[0] - c1[0]))
    g = int(c1[1] + factor * (c2[1] - c1[1]))
    b = int(c1[2] + factor * (c2[2] - c1[2]))

    # Rückgabe als Hex-String (z.B. "#4CAF50")
    return f"#{r:02X}{g:02X}{b:02X}"


def getContrastColor(bg_color):
    """Return a contrasting text color for a given background color."""
    if not bg_color:
        return "#1A1A1A"

    color_map = {
        "white": "#FFFFFF",
        "black": "#000000",
        "red": "#FF0000",
        "blue": "#0000FF",
        "green": "#00FF00",
        "yellow": "#FFFF00"
    }

    normalized_color = bg_color.strip().lower()
    if normalized_color in color_map:
        bg_color = color_map[normalized_color]

    if not bg_color.startswith("#"):
        return "#1A1A1A"

    hex_color = bg_color.lstrip("#")
    if len(hex_color) != 6:
        return "#1A1A1A"

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "#1A1A1A" if yiq >= 128 else "#FFFFFF"


def get_weather_data():
    """Fetch current weather data from MQTT messages.

    Returns:
        dict: Dictionary with keys 'temp', 'feucht', 'hell', 'proz'
    """
    weather_data = {
        'temp': {'value': 'N/A', "fg_color": "black", "bg_color": "white"},
        'feucht': {'value': 'N/A', "fg_color": "black", "bg_color": "white"},
        'hell': {'value': 'N/A', "fg_color": "black", "bg_color": "white"},
        'regen': {'value': 'N/A', "fg_color": "black", "bg_color": "white"},
        'proz': {'value': 'N/A', "fg_color": "black", "bg_color": "white"}
    }

    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()

        # Get temperature
        cursor.execute("SELECT message FROM mqtt_msgs WHERE type='Tb'")
        for message in cursor:
            temp_value = float(message[0])
            weather_data['temp']['value'] = f"{temp_value:.1f}"
            weather_data['temp']['bg_color'] = getColor("T", temp_value)
            weather_data['temp']['fg_color'] = getContrastColor(
                weather_data['temp']['bg_color'])
        cursor.close()

        # Get humidity
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs WHERE type='Fb'")
        for message in cursor:
            humidity_value = float(message[0])
            weather_data['feucht']['value'] = f"{humidity_value:.0f}"
            weather_data['feucht']['bg_color'] = getColor("F", humidity_value)
            weather_data['feucht']['fg_color'] = getContrastColor(
                weather_data['feucht']['bg_color'])
        cursor.close()

        # Get brightness
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs WHERE type='H'")
        for message in cursor:
            brightness_value = float(message[0])
            weather_data['hell']['value'] = f"{brightness_value:.0f}"
            weather_data['hell']['bg_color'] = getColor("H", brightness_value)
            weather_data['hell']['fg_color'] = getContrastColor(
                weather_data['hell']['bg_color'])
        cursor.close()

       # Get rain
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT SUM(value) FROM `env_values` WHERE type= 'Rdb' AND timestamp  >= NOW() - INTERVAL 1 DAY")
        for message in cursor:
            rain_value = float(message[0])
            weather_data['regen']['value'] = f"{rain_value:.1f}"
            weather_data['regen']['bg_color'] = getColor("R", rain_value)
            weather_data['regen']['fg_color'] = getContrastColor(
                weather_data['regen']['bg_color'])
        cursor.close()

        # Get cistern percentage
        cursor = db_connection.cursor()
        cursor.execute("SELECT message FROM mqtt_msgs WHERE type='P'")
        for message in cursor:
            percentage_value = float(message[0])
            weather_data['proz']['value'] = f"{percentage_value:.0f}"
            weather_data['proz']['bg_color'] = getColor("P", percentage_value)
            weather_data['proz']['fg_color'] = getContrastColor(
                weather_data['proz']['bg_color'])
        cursor.close()

        db_connection.close()
    except mariadb.Error as err:
        logging.warning("Database failure: %s", err)

    return weather_data


def get_device_list():
    """Fetch all devices with all their details from the database.

    Returns:
        list: List of [name, ip, mac, description, type, com_type, mqtt_name, status, timestamp] for each device
    """
    entries = []
    try:
        db_connection = get_connection()
        cursor = db_connection.cursor()
        cursor.execute("SELECT device.name AS name, device.ip_v4 AS ip_v4, "
                       "HEX(device.mac) AS mac, device.description AS description, device.type AS type, "
                       "device.com_type AS com_type, device.mqtt_name AS mqtt_name, device.status AS status, "
                       "device.timestamp AS timestamp "
                       "FROM device ")
        for name, ip_v4, mac, description, type, com_type, mqtt_name, status, timestamp in cursor:
            entries.append([name, ip_v4, mac, description, type,
                           com_type, mqtt_name, status, timestamp])
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
        cursor.execute("SELECT activities.name as name, activities.device as device, "
                       "device.name as geraet "
                       "FROM activities INNER JOIN device ON "
                       "activities.device = device.mqtt_name "
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
        cursor.execute(
            "SELECT lfdnr, topic, min, max FROM activity_trigger WHERE id='{}'".format(action_id))
        result['trigger'] = [[topic, min_val, max_val, lfdnr]
                             for lfdnr, topic, min_val, max_val in cursor]
        cursor.close()

        # Get all available condition types
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT typ FROM activity_conditions")
        result['cond_liste'] = [typ[0] for typ in cursor]
        cursor.close()

        # Get conditions for this activity
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT lfdnr, typ, min, max FROM activity_conditions WHERE id='{}'".format(action_id))
        result['conditions'] = [[typ, min_val, max_val, lfdnr]
                                for lfdnr, typ, min_val, max_val in cursor]
        cursor.close()

        # Get all available action types
        cursor = db_connection.cursor()
        cursor.execute("SELECT DISTINCT arg1 FROM activity_actions")
        result['action_liste'] = [arg1[0] for arg1 in cursor]
        cursor.close()

        # Get actions for this activity
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT lfdnr, typ, arg1, arg2 FROM activity_actions WHERE id='{}'".format(action_id))
        result['actions'] = [[typ, arg1, arg2, lfdnr]
                             for lfdnr, typ, arg1, arg2 in cursor]
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
        cursor.execute(
            "SELECT DISTINCT mqtt_name FROM device WHERE NOT mqtt_name = ''")
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
        cursor.execute(
            "SELECT DISTINCT topic FROM mqtt_msgs WHERE max_age = 0")
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
        cursor.execute(
            "DELETE FROM activity_trigger WHERE id='{}'".format(activity_id))
        cursor.close()

        cursor = db_connection.cursor()
        cursor.execute(
            "DELETE FROM activity_conditions WHERE id='{}'".format(activity_id))
        cursor.close()

        cursor = db_connection.cursor()
        cursor.execute(
            "DELETE FROM activity_actions WHERE id='{}'".format(activity_id))
        cursor.close()

        cursor = db_connection.cursor()
        cursor.execute(
            "DELETE FROM activities WHERE id='{}'".format(activity_id))
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
        cursor.execute(
            "SELECT id FROM activity_conditions WHERE lfdnr='{}'".format(lfdnr))
        rows = cursor.fetchall()
        activity_id = rows[0][0] if rows else -1
        cursor.close()

        cursor = db_connection.cursor()
        cursor.execute(
            "DELETE FROM activity_conditions WHERE lfdnr={}".format(lfdnr))
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
