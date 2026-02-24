# Project Structure

## Application Architecture

```
iotfrontend/
├── app.py                    # Flask application entry point (45 lines)
│
├── modbus_config.py          # Modbus register definitions
├── database.py               # Database access layer (all SQL operations)
├── mqtt_handler.py           # MQTT client and messaging
├── modbus_handler.py         # Modbus TCP communication
│
├── routes_web.py             # Blueprint: Main web pages
├── routes_actions.py         # Blueprint: Activity/Action management
├── routes_status.py          # Blueprint: Status and monitoring
│
├── templates/                # Flask HTML templates
│   ├── action.htm
│   ├── actions.htm
│   ├── addaction.htm
│   ├── bewaesserung.htm
│   ├── devices.htm
│   ├── iot.htm
│   ├── strom.html
│   └── top.htm
│
├── static/                   # Static files (CSS, JS, etc.)
├── db.cnf                    # Database configuration
├── mq.cnf                    # MQTT configuration
└── Dockerfile
```

## Module Dependencies

```
app.py (Entry Point)
├── imports: routes_web, routes_actions, routes_status, mqtt_handler
│
routes_web.py ──→ database.py
routes_actions.py ──→ database.py, mqtt_handler.py
routes_status.py ──→ database.py, mqtt_handler.py, modbus_handler.py
│
mqtt_handler.py ──→ (reads mq.cnf)
modbus_handler.py
modbus_config.py ──→ (standalone, enum definitions)
database.py ──→ (reads db.cnf)
```

## Data Flow

### Web Request → Response
1. Flask receives HTTP request
2. Blueprint route handler processes request
3. Handler imports and uses module functions:
   - `database.*` for DB queries
   - `mqtt_handler.*` for MQTT operations
   - `modbus_handler.*` for hardware reads
4. Response rendered using template or JSON

### MQTT Message Handling
1. `mqtt_handler.init_mqtt()` starts MQTT client
2. `on_message()` callback receives messages
3. Updates global state in `mqtt_handler` module
4. Routes read state via `get_bewaesserung_status()`

### Database Operations
All database operations go through `database.py`:
- Connection pooling via `get_connection()`
- Query functions with error handling
- Returns Python objects or tuples
- No SQL directly in route handlers

## API Examples

### Using Database Module
```python
import database as db

# Get devices
devices = db.get_devices()

# Create activity
db.create_activity(activity_id, name, device, desc, trigger, action, condition)

# Update record
db.update_record('trigger', typ, arg1, arg2, lfdnr)
```

### Using MQTT Handler
```python
import mqtt_handler

# Initialize once
mqtt_handler.init_mqtt()

# Get irrigation status
status = mqtt_handler.get_bewaesserung_status()

# Set parameter
mqtt_handler.set_bewaesserung_value('Dauer', 30)

# Publish message
mqtt_handler.publish_message('topic', 'payload')
```

### Using Modbus Handler
```python
import modbus_handler

# Read power data
data = modbus_handler.get_power_status()
if data:
    print(f"Solar: {data['p_solar']}W")
    print(f"House: {data['p_haus']}W")
    +grid
    +batterie
```

## Running the Application

```bash
# Start the application
python app.py

# The app will:
# 1. Initialize MQTT connection
# 2. Start Flask web server on 0.0.0.0:80
# 3. Handle incoming requests via blueprint routes
# 4. Respond to signals for graceful shutdown
```

## Testing Individual Modules

```python
# Test database module
python -c "import database as db; print(db.get_devices())"

# Test MQTT module
python -c "import mqtt_handler; mqtt_handler.init_mqtt()"

# Test modbus module
python -c "import modbus_handler; print(modbus_handler.get_power_status())"
```

## Error Handling Strategy

- **Database errors**: Caught, logged, return empty/default values
- **MQTT errors**: Logged, non-blocking, application continues
- **Modbus errors**: Caught, logged, return None
- **HTTP errors**: Rendered as HTML error pages with descriptive messages

## Configuration Files

- `db.cnf`: MariaDB connection parameters
- `mq.cnf`: MQTT broker connection parameters
- Both are read manually (not using Flask config system for legacy reasons)

## Future Improvements

1. Convert to Flask application factory pattern
2. Add database connection pooling
3. Implement request logging middleware
4. Add API endpoint documentation (OpenAPI/Swagger)
5. Create comprehensive unit tests
6. Implement graceful error pages
7. Add rate limiting for status endpoints
