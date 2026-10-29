import unittest
from unittest.mock import patch

from flask import Flask
import routes_actions


class ActivityFormRouteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__, template_folder="../templates")
        app.register_blueprint(routes_actions.actions_bp)
        self.client = app.test_client()

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
            "trigger": [["sensor/temp", "", "", 1]],
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
            self.assertEqual(response.data.count(b'data-row="trigger"'), 1)
            self.assertNotIn(b'data-add-row="action"', response.data)
            self.assertIn(b'data-add-row="condition"', response.data)
            self.assertEqual(response.data.count(b'data-row="action"'), 1)
            self.assertIn(b"<fieldset>\n    <legend>Bedingungen</legend>", response.data)
            self.assertIn(b"<div data-row=\"condition\">", response.data)
            self.assertNotIn(b"<fieldset data-row=\"condition\">", response.data)

        self.assertIn(b'value="Rule"', edit_response.data)
        self.assertIn(b'value="sensor/temp"', edit_response.data)

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
        self.assertEqual(args[4], [("topic/one", "", "")])
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
