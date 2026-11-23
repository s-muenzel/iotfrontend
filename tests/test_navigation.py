import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from jinja2 import Environment, FileSystemLoader

import routes_actions
import routes_web


TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.environment = Environment(loader=FileSystemLoader(TEMPLATES))

    def test_management_links_are_hidden_outside_management(self):
        navigation = self.environment.get_template(
            "partials/navigation.htm"
        ).render(active_page="dashboard")

        self.assertNotIn(">Ger&auml;te</a>", navigation)
        self.assertNotIn(">Regeln</a>", navigation)
        self.assertNotIn(">Historie</a>", navigation)

    def test_management_pages_show_indented_subnavigation(self):
        navigation = self.environment.get_template(
            "partials/navigation.htm"
        ).render(active_page="devices")

        self.assertIn('style="margin-left:16px;border-left:4px solid #009688"', navigation)
        self.assertIn('href="/iot.htm"', navigation)
        self.assertIn('href="/actions"', navigation)
        self.assertIn('href="/historie.htm"', navigation)
        self.assertIn('aria-current="page">Ger&auml;te</a>', navigation)
        self.assertEqual(navigation.count("w3-teal"), 2)

    def test_history_route_renders_shared_navigation(self):
        app = Flask(
            __name__,
            template_folder=str(TEMPLATES),
        )
        app.register_blueprint(routes_web.web_bp)

        response = app.test_client().get("/historie.htm")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Verwaltung...", response.data)
        self.assertIn(b"Historie", response.data)
        self.assertIn(b"Historie", response.data)

    def test_dashboard_device_and_rules_pages_use_shared_site_layout(self):
        app = Flask(__name__, template_folder=str(TEMPLATES))
        app.register_blueprint(routes_web.web_bp)
        app.register_blueprint(routes_actions.actions_bp)
        weather = {
            "temp": {},
            "feucht": {},
            "hell": {},
            "regen": {},
            "proz": {},
        }

        with patch.object(routes_web.db, "get_weather_data", return_value=weather), \
                patch.object(routes_web, "_get_heating_rooms", return_value=()), \
                patch.object(routes_web.db, "get_device_list", return_value=[]), \
                patch.object(routes_web, "check_netzwerkfehler", return_value=[]), \
                patch.object(routes_actions.db, "get_activities", return_value=[]), \
                patch.object(
                    routes_web.db, "get_activities_history",
                    return_value=[("2024-05-01", "Rule", "Kitchen", "temp", "20")]
                ):
            client = app.test_client()
            responses = [
                client.get("/"),
                client.get("/iot.htm"),
                client.get("/actions"),
                client.get("/historie.htm"),
            ]

        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"/static/site.css", response.data)
            self.assertIn(b'id="mySidebar"', response.data)

        for response in responses[1:]:
            self.assertIn(b"data-sortable-filterable", response.data)
            self.assertIn(b"data-table-view-toggle", response.data)
            self.assertIn(b"data-filter-toggle", response.data)

    def test_activity_form_uses_document_base_without_site_navigation(self):
        app = Flask(__name__, template_folder=str(TEMPLATES))
        app.register_blueprint(routes_actions.actions_bp)

        with patch.object(
                routes_actions.db, "get_activity_devices", return_value=[]), \
                patch.object(
                    routes_actions.db, "get_heating_rooms", return_value=[]), \
                patch.object(
                    routes_actions.db, "get_triggers", return_value=[]):
            response = app.test_client().get("/aktion/add")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/static/site.css", response.data)
        self.assertNotIn(b'id="mySidebar"', response.data)
        self.assertIn(b'id="activity-form"', response.data)


if __name__ == "__main__":
    unittest.main()
