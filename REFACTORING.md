# Current Application Structure

The application is organized around a small Flask entry point, route
blueprints, service handlers, and Jinja templates.

## Application and routes

- `app.py` creates the Flask application, registers the route blueprints, and
  starts and stops the MQTT client.
- `routes_web.py` serves the dashboard (`/`), the device list (`/iot.htm`),
  and the dashboard's heating status and setpoint endpoints.
- `routes_status.py` provides JSON status endpoints for roller shutters,
  garage, lights, and solar power.
- `routes_actions.py` provides activity and action management routes.

The former standalone `/strom` and `/heizung` page routes have been removed.
Strom and Heizung are dashboard sections; their data endpoints remain in use.

## Dashboard templates

`templates/top.htm` defines the dashboard shell, navigation, JavaScript, and
section visibility observer. Each section's HTML is a Jinja partial in
`templates/partials/`:

- `wetter.htm`
- `rollos.htm`
- `garage.htm`
- `leuchten.htm`
- `wasser.htm`
- `heizung.htm`
- `strom.htm`

The dashboard uses anchor navigation within the page. Polling is visibility
aware: Rollos, Garage, Leuchten, and Strom update every 10 seconds while
visible; Heizung fetches readings when visible and refreshes every 5 minutes
while visible. Polling stops when the section leaves the viewport.

The other full-page templates (`iot.htm`, `actions.htm`, `action.htm`, and
`addaction.htm`) serve their respective pages.

## Service and data modules

- `database.py` contains database access, including weather, device, and
  activity data.
- `mqtt_handler.py` manages the MQTT client and irrigation state.
- `modbus_handler.py` and `modbus_config.py` provide Modbus-related
  communication and register definitions.
- `fritz_handler.py` handles FRITZ!Box authentication and Smart Home
  thermostat requests. Its SID is retained and logged out after 15 minutes
  without activity.
- `netzwerk.py` contains network checks used by the device list.

## Important routes

| Route | Purpose |
| --- | --- |
| `/` | Main dashboard |
| `/iot.htm` | IoT device list |
| `/status_r` | Roller shutter status |
| `/status_g` | Garage status |
| `/status_l` | Light status |
| `/status_s` | Solar and household power status |
| `/heizung/status` | Heating readings for the dashboard |
| `/heizung/sollwert` (`POST`) | Set a thermostat target |
| `/actions` and `/action/...` | Activity and action management |

## Container templates

The `Dockerfile` copies top-level templates to `/templates/` and dashboard
partials to `/templates/partials/`. Keep these paths aligned with the Jinja
include paths in `templates/top.htm`.

Configuration is read from `db.cnf`, `mq.cnf`, and `fritz.cnf`. Keep actual
credentials out of source control.
