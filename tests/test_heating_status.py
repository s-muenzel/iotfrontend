import unittest
from unittest.mock import MagicMock, patch

from flask import Flask
import database
import mqtt_handler
import routes_web


class HeatingStatusTests(unittest.TestCase):
    def setUp(self):
        routes_web._get_heating_rooms.cache_clear()

    def tearDown(self):
        routes_web._get_heating_rooms.cache_clear()

    def test_database_returns_rooms_with_recent_heating_values(self):
        cursor = MagicMock()
        cursor.__iter__.return_value = iter([
            ("Eva",),
            ("Tim",),
        ])
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(database, "get_connection", return_value=connection):
            rooms = database.get_heating_rooms()

        self.assertEqual(rooms, ["Eva", "Tim"])
        query = cursor.execute.call_args.args[0]
        self.assertIn("typ IN ('ist', 'soll')", query)
        self.assertIn("timestamp >= NOW() - INTERVAL 1 DAY", query)
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_database_returns_latest_values_in_degrees_celsius(self):
        cursor = MagicMock()
        cursor.__iter__.return_value = iter([
            ("Tim", "ist", 205),
            ("Tim", "soll", 220),
            ("Eva", "ist", 198),
            ("Eva", "soll", None),
        ])
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(database, "get_connection", return_value=connection):
            status = database.get_heating_data()

        self.assertEqual(status, {
            "Tim": {"actual": 20.5, "target": 22.0},
            "Eva": {"actual": 19.8, "target": None},
        })
        query = cursor.execute.call_args.args[0]
        self.assertIn("newer_value.timestamp > current_value.timestamp", query)
        self.assertIn("newer_value.id > current_value.id", query)
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_status_route_reads_from_database(self):
        app = Flask(__name__)
        app.register_blueprint(routes_web.web_bp)
        expected = {"Tim": {"actual": 20.5, "target": 22.0}}

        with patch.object(
            database, "get_heating_data", return_value=expected
        ) as get_data:
            response = app.test_client().get("/heizung/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"rooms": expected})
        get_data.assert_called_once_with()

    def test_dashboard_uses_cached_room_list(self):
        weather = {
            "temp": {},
            "feucht": {},
            "hell": {},
            "regen": {},
            "proz": {},
        }
        with patch.object(database, "get_weather_data", return_value=weather), \
                patch.object(
                    database, "get_heating_rooms", return_value=["Studio"]
                ) as get_rooms, \
                patch.object(
                    routes_web, "render_template", return_value="rendered"
                ) as render:
            response = routes_web._render_top()

        self.assertEqual(response, "rendered")
        self.assertEqual(render.call_args.kwargs["heating_rooms"], ("Studio",))
        get_rooms.assert_called_once_with()

    def test_set_target_rounds_and_publishes_using_cached_room_list(self):
        app = Flask(__name__)
        app.register_blueprint(routes_web.web_bp)

        with patch.object(
            database, "get_heating_rooms", return_value=["Tim"]
        ) as get_rooms, \
                patch.object(mqtt_handler, "mqtt_client_instance", object()), \
                patch.object(mqtt_handler, "publish_message") as publish:
            response = app.test_client().post("/heizung/sollwert", data={
                "room": "Tim",
                "target": "21.3",
            })
            self.assertEqual(routes_web._get_heating_rooms(), ("Tim",))

        self.assertEqual(response.status_code, 303)
        publish.assert_called_once_with("Aktor/Fritz////Tim", "21.5")
        get_rooms.assert_called_once_with()

    def test_set_target_accepts_zero(self):
        app = Flask(__name__)
        app.register_blueprint(routes_web.web_bp)

        with patch.object(database, "get_heating_rooms", return_value=["Eva"]), \
                patch.object(mqtt_handler, "mqtt_client_instance", object()), \
                patch.object(mqtt_handler, "publish_message") as publish:
            response = app.test_client().post("/heizung/sollwert", data={
                "room": "Eva",
                "target": "0",
            })

        self.assertEqual(response.status_code, 303)
        publish.assert_called_once_with("Aktor/Fritz////Eva", "0")

    def test_set_target_rejects_invalid_temperature_without_publishing(self):
        app = Flask(__name__)
        app.register_blueprint(routes_web.web_bp)

        with patch.object(database, "get_heating_rooms", return_value=["Tim"]), \
                patch.object(routes_web, "_render_top", return_value="invalid"), \
                patch.object(mqtt_handler, "publish_message") as publish:
            response = app.test_client().post("/heizung/sollwert", data={
                "room": "Tim",
                "target": "7.9",
            })

        self.assertEqual(response.status_code, 400)
        publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
