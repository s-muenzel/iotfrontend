import unittest
from unittest.mock import MagicMock, patch

from flask import Flask
import database
import routes_web


class HeatingStatusTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
