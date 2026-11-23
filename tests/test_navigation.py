import unittest
from pathlib import Path

from flask import Flask
from jinja2 import Environment, FileSystemLoader

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


if __name__ == "__main__":
    unittest.main()
