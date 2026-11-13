import unittest
from unittest.mock import patch

from flask import Flask
import routes_actions


class ActivityFormRouteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__, template_folder="../templates")
        app.register_blueprint(routes_actions.actions_bp)
        self.client = app.test_client()

    def test_actions_table_has_sortable_status_name_and_description(self):
        with patch.object(
                routes_actions.db, "get_activities",
                return_value=[["Rule", 7, 1, "Description"]]):
            response = self.client.get("/actions")

        self.assertEqual(response.status_code, 200)
        for column, heading in (
                (1, "Status"), (2, "Regel"), (3, "Beschreibung")):
            self.assertIn(
                f'onclick="sortTable({column})" aria-sort="none">{heading}'.encode(),
                response.data
            )
            self.assertIn(
                f'class="fa sort-indicator" data-column="{column}"'.encode(),
                response.data
            )
        self.assertIn(b'data-sort="1"', response.data)
        self.assertIn(b'function sortTable(column)', response.data)
        self.assertIn(b'fa-sort-up", "fa-sort-down"', response.data)
        self.assertIn(b'class="status-header"', response.data)
        self.assertIn(b'class="action-controls" data-sort="1"', response.data)
        self.assertIn(b'<span class="w3-tooltip">', response.data)
        self.assertNotIn(b'<p class="w3-tooltip">', response.data)

    def test_create_and_edit_pages_use_one_shared_form(self):
        with patch.object(
                routes_actions.db, "get_activity_devices",
                return_value=[["Device", "mqtt/device"]]), \
                patch.object(
                    routes_actions.db, "get_triggers",
                    return_value=["sensor/temp"]):
            create_response = self.client.get("/aktion/add")

        details = {
            "actionname": "Rule",
            "description": "Description",
            "devicename": "mqtt/device",
            "geraetname": "Device",
            "trigger_liste": ["sensor/temp"],
            "trigger": [["mqtt", "sensor/temp", "", "", 1]],
            "cond_liste": ["temp"],
            "conditions": [["temp", "20", "", 2]],
            "action_liste": [],
            "actions": [["mqtt", "topic", "value", 3]],
        }
        with patch.object(
                routes_actions.db, "get_activity_devices",
                return_value=[["Device", "mqtt/device"]]), \
                patch.object(
                    routes_actions.db, "get_activity_details",
                    return_value=details):
            edit_response = self.client.get("/action/7")

        for response in (create_response, edit_response):
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data.count(b"<form"), 1)
            self.assertNotIn(b'data-add-row="trigger"', response.data)
            self.assertEqual(
                response.data.count(
                    b'<fieldset class="w3-card-2 w3-white" data-row="trigger">'
                ),
                1
            )
            self.assertNotIn(b'data-add-row="action"', response.data)
            self.assertIn(b'data-add-row="condition"', response.data)
            self.assertEqual(
                response.data.count(
                    b'<fieldset class="w3-card-2 w3-white" data-row="action">'
                ),
                1
            )
            self.assertIn(b"<fieldset>\n    <legend>Bedingungen</legend>", response.data)
            self.assertIn(b"<div data-row=\"condition\">", response.data)
            self.assertNotIn(b"<fieldset data-row=\"condition\">", response.data)

        self.assertIn(b'value="Rule"', edit_response.data)
        self.assertIn(b'value="sensor/temp"', edit_response.data)
        self.assertIn(b'name="trigger_type"', edit_response.data)
        self.assertIn(b'value="mqtt"', edit_response.data)

    def test_create_page_renders_duration_controls(self):
        with patch.object(
                routes_actions.db, "get_activity_devices",
                return_value=[]), \
                patch.object(
                    routes_actions.db, "get_triggers",
                    return_value=[]):
            response = self.client.get("/aktion/add")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-duration-days', response.data)
        self.assertIn(b'data-duration-time', response.data)

    def test_save_activity_persists_one_trigger_and_action(self):
        submitted = []
        with patch.object(
                routes_actions.db, "get_next_activity_id",
                return_value=23), \
                patch.object(
                    routes_actions.db, "save_activity",
                    side_effect=lambda *args, **kwargs:
                    submitted.append((args, kwargs)) or True):
            response = self.client.post("/save_activity", data={
                "a_name": "New rule",
                "a_desc": "Description",
                "a_dev": "mqtt/device",
                "trigger_topic": ["topic/one"],
                "trigger_min": [""],
                "trigger_max": [""],
                "action_type": ["mqtt"],
                "action_arg1": ["first"],
                "action_arg2": [""],
                "condition_type": ["tag", "temp"],
                "condition_min": ["1", "20"],
                "condition_max": ["", ""],
            })

        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.location.endswith("/actions"))
        args, kwargs = submitted[0]
        self.assertEqual(args[0], 23)
        self.assertEqual(args[4], [("mqtt", "topic/one", "", "")])
        self.assertEqual(args[5], [("mqtt", "first", "")])
        self.assertEqual(args[6][0], ("tag", "1", "0"))
        self.assertTrue(kwargs["create"])

    def test_save_activity_updates_existing_rule(self):
        submitted = []
        with patch.object(
                routes_actions.db, "save_activity",
                side_effect=lambda *args, **kwargs:
                submitted.append((args, kwargs)) or True):
            response = self.client.post("/save_activity", data={
                "actionid": "7",
                "a_name": "Updated rule",
                "a_desc": "",
                "a_dev": "mqtt/device",
                "trigger_topic": "topic",
                "trigger_min": "",
                "trigger_max": "",
                "action_type": "mqtt",
                "action_arg1": "topic",
                "action_arg2": "value",
                "condition_type": "temp",
                "condition_min": "20",
                "condition_max": "",
            })

        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.location.endswith("/action/7"))
        args, kwargs = submitted[0]
        self.assertEqual(args[0], 7)
        self.assertEqual(args[5], [("mqtt", "topic", "value")])
        self.assertFalse(kwargs["create"])

    def test_save_activity_stores_time_trigger_without_topic(self):
        submitted = []
        with patch.object(
                routes_actions.db, "save_activity",
                side_effect=lambda *args, **kwargs:
                submitted.append((args, kwargs)) or True):
            response = self.client.post("/save_activity", data={
                "a_name": "Time rule",
                "trigger_type": "time",
                "trigger_topic": "must be ignored",
                "trigger_min": "82800",
                "trigger_max": "3600",
                "action_type": "mqtt",
                "action_arg1": "topic",
                "action_arg2": "value",
                "condition_type": "temp",
                "condition_min": "20",
                "condition_max": "",
            })

        self.assertEqual(response.status_code, 303)
        self.assertEqual(submitted[0][0][4], [("time", "", "82800", "3600")])

    def test_save_activity_rejects_time_trigger_seconds(self):
        with patch.object(routes_actions.db, "save_activity") as save:
            response = self.client.post("/save_activity", data={
                "a_name": "Time rule",
                "trigger_type": "time",
                "trigger_topic": "",
                "trigger_min": "82801",
                "trigger_max": "3600",
                "action_type": "mqtt",
                "action_arg1": "topic",
                "action_arg2": "value",
                "condition_type": "temp",
                "condition_min": "20",
                "condition_max": "",
            })

        self.assertEqual(response.status_code, 400)
        save.assert_not_called()

    def test_save_activity_accepts_rollo_last_move_over_one_day(self):
        submitted = []
        with patch.object(
                routes_actions.db, "save_activity",
                side_effect=lambda *args, **kwargs:
                submitted.append((args, kwargs)) or True):
            response = self.client.post("/save_activity", data={
                "a_name": "Updated rule",
                "trigger_topic": "topic",
                "trigger_min": "",
                "trigger_max": "",
                "action_type": "mqtt",
                "action_arg1": "topic",
                "action_arg2": "value",
                "condition_type": "rollo_last_move",
                "condition_min": "86400",
                "condition_max": "",
            })

        self.assertEqual(response.status_code, 303)
        self.assertEqual(submitted[0][0][6], [
            ("rollo_last_move", "86400", "")
        ])

    def test_save_activity_rejects_multiple_actions(self):
        with patch.object(routes_actions.db, "save_activity") as save:
            response = self.client.post("/save_activity", data={
                "a_name": "Rule",
                "trigger_topic": "topic",
                "trigger_min": "",
                "trigger_max": "",
                "action_type": ["mqtt", "fritz"],
                "action_arg1": ["first", "second"],
                "action_arg2": ["", ""],
                "condition_type": "temp",
                "condition_min": "20",
                "condition_max": "",
            })

        self.assertEqual(response.status_code, 400)
        save.assert_not_called()

    def test_save_activity_rejects_multiple_triggers(self):
        with patch.object(routes_actions.db, "save_activity") as save:
            response = self.client.post("/save_activity", data={
                "a_name": "Rule",
                "trigger_topic": ["topic/one", "topic/two"],
                "trigger_min": ["", ""],
                "trigger_max": ["", ""],
                "action_type": "mqtt",
                "action_arg1": "topic",
                "action_arg2": "value",
                "condition_type": "temp",
                "condition_min": "20",
                "condition_max": "",
            })

        self.assertEqual(response.status_code, 400)
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
