import unittest
from unittest.mock import MagicMock, patch

from flask import Flask
import database
import routes_web


class ActivityHistoryTests(unittest.TestCase):
    def test_database_reads_activity_history_from_view(self):
        cursor = MagicMock()
        cursor.__iter__.return_value = iter([
            (2, 8, "Rule B", "Kitchen", "2024-05-01 10:00:00"),
            (1, 7, "Rule A", "Living room", "2024-04-30 09:00:00"),
        ])
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(database, "get_connection", return_value=connection):
            entries = database.get_activities_history()

        self.assertEqual(len(entries), 2)
        query = cursor.execute.call_args.args[0]
        self.assertIn("FROM Aktivitaeten", query)
        self.assertIn("nummer, id, name, raum, time", query)
        self.assertIn("ORDER BY time DESC, nummer DESC", query)
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_history_route_renders_database_rows(self):
        app = Flask(__name__, template_folder="../templates")
        app.register_blueprint(routes_web.web_bp)
        entries = [
            (2, 8, "Rule B", "Kitchen", "2024-05-01 10:00:00"),
            (1, 7, "Rule A", "Living room", "2024-04-30 09:00:00"),
        ]

        with patch.object(
                database, "get_activities_history", return_value=entries
        ) as get_history:
            response = app.test_client().get("/historie.htm")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Regel-ID", response.data)
        self.assertIn(b"Rule B", response.data)
        self.assertIn(b"Kitchen", response.data)
        self.assertIn(b"2024-05-01 10:00:00", response.data)
        get_history.assert_called_once_with()

    def test_history_route_renders_empty_state(self):
        app = Flask(__name__, template_folder="../templates")
        app.register_blueprint(routes_web.web_bp)

        with patch.object(database, "get_activities_history", return_value=[]):
            response = app.test_client().get("/historie.htm")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Noch keine erfolgreich angewendeten Regeln.", response.data)
        self.assertNotIn(b"<table", response.data)


if __name__ == "__main__":
    unittest.main()
