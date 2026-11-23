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

`templates/base.htm` defines shared document metadata and common assets.
`templates/site_page.htm` adds the standard sidebar, responsive page frame,
header, and content blocks used by the dashboard, devices, and rules pages.
The history page remains on its existing shell pending migration. The
activity form extends the document base but keeps its focused layout and does
not include the site navigation.

Common presentation and sidebar/top-bar behavior live in `static/site.css`
and `static/site.js`. Page-specific CSS and scripts remain with their
templates where they are not shared. The dashboard's section visibility
observer and status polling remain in `templates/top.htm`. Each dashboard
section's HTML is a Jinja partial in `templates/partials/`:

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

`iot.htm` and `actions.htm` extend the shared site page. `historie.htm` is
still a placeholder page using its existing standalone shell. `action.htm`
handles both creating and editing an activity and extends only the shared
document base.

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
| `/historie.htm` | History placeholder for applied rules |
| `/status_r` | Roller shutter status |
| `/status_g` | Garage status |
| `/status_l` | Light status |
| `/status_s` | Solar and household power status |
| `/heizung/status` | Heating readings for the dashboard |
| `/heizung/sollwert` (`POST`) | Set a thermostat target |
| `/actions` and `/action/...` | Activity and action management |

## Container templates

The `Dockerfile` copies top-level templates to `/templates/`, dashboard
partials to `/templates/partials/`, and static assets to `/static/`. Keep
these paths aligned with the Jinja references in the templates.

Configuration is read from `db.cnf`, `mq.cnf`, and `fritz.cnf`. Keep actual
credentials out of source control.
