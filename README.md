# IoT Zentrale Frontend

Flask web frontend for the home's IoT devices and services. The application
shows weather and device status, controls roller shutters and lights, displays
solar power and heating information, and provides activity management.

## Dashboard

The home page (`/`) contains the Wetter, Rollos, Garage, Leuchten, Wasser,
Heizung, and Strom sections. Its navigation links scroll to each section.
Dashboard markup is in `templates/top.htm`, with section content organized as
Jinja partials in `templates/partials/`.

Status requests are only polled while their section is visible:

- Rollos, Garage, Leuchten, and Strom: every 10 seconds.
- Heizung: immediately when first visible, then every 5 minutes.

Heizung readings use the FRITZ!Box Smart Home API. The cached FRITZ!Box session
is reused and logged out after 15 minutes without a request. Heating setpoints
can be set in 0.5 degree increments from 8 to 28 degrees C.

## Other pages

- `/iot.htm` lists configured IoT devices.
- `/actions` and related routes manage configured activities and actions.

There are no separate `/strom` or `/heizung` pages. Their content is part of
the home dashboard. The dashboard uses `/status_s` for power data and
`/heizung/status` to retrieve heating readings. Heating setpoints are submitted
to `/heizung/sollwert`.

## Configuration

The application reads configuration from `db.cnf`, `mq.cnf`, and `fritz.cnf`.
Keep credentials private and do not commit real passwords.

Example `fritz.cnf`:

```yaml
fritz:
  url: http://fritz.box
  username: your-fritz-user
  password: your-fritz-password
```

## Running

Install the Python dependencies used by the application (see `Dockerfile`),
provide the configuration files, then run:

```powershell
python app.py
```

The development server listens on port 80. The Docker image copies the
dashboard partials into Flask's `templates/partials/` directory.
