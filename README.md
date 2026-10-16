# iotfrontend

Web-Frontend
   Zeigt die aktuellen Wetter-Daten
   Listet alle IOT-Devices
   Listet alle konfigurierte Aktionen und
   bietet die Möglichtkeit zum Editieren

## Heizung

The `/heizung` page shows the actual and target temperatures for Tim, Eva,
Hobbykeller, and Wintergarten. Setpoints can be changed in 0.5 degree
increments from 8 to 28 degrees C using the FRITZ!OS Smart Home REST API
(FRITZ!OS 8.20+).

Zugangsdaten liegen in `fritz.cnf`

```yaml
fritz:
  url: http://fritz.box
  username: your-fritz-user
  password: your-fritz-password
```

