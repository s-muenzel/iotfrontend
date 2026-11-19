import unittest
from unittest.mock import MagicMock, patch

from flask import Flask
import mqtt_handler
import routes_actions


class MqttHandlerTests(unittest.TestCase):
    def test_publish_requires_a_connected_client(self):
        client = MagicMock()
        client.is_connected.return_value = False

        with patch.object(mqtt_handler, "mqtt_client_instance", client):
            with self.assertRaisesRegex(RuntimeError, "not connected"):
                mqtt_handler.publish_message("topic", "payload")

        client.publish.assert_not_called()

    def test_publish_checks_result_and_waits_for_broker_ack(self):
        client = MagicMock()
        client.is_connected.return_value = True
        result = MagicMock()
        result.rc = mqtt_handler.mqtt_client.MQTT_ERR_SUCCESS
        result.mid = 42
        result.is_published.return_value = True
        client.publish.return_value = result

        with patch.object(mqtt_handler, "mqtt_client_instance", client):
            returned = mqtt_handler.publish_message("topic", "payload")

        self.assertIs(returned, result)
        client.publish.assert_called_once_with(
            topic="topic", payload="payload", qos=1
        )
        result.wait_for_publish.assert_called_once_with(
            timeout=mqtt_handler.MQTT_PUBLISH_TIMEOUT
        )

    def test_publish_rejects_non_success_return_code(self):
        client = MagicMock()
        client.is_connected.return_value = True
        result = MagicMock()
        result.rc = mqtt_handler.mqtt_client.MQTT_ERR_NO_CONN
        client.publish.return_value = result

        with patch.object(mqtt_handler, "mqtt_client_instance", client):
            with self.assertRaisesRegex(RuntimeError, "failed with code"):
                mqtt_handler.publish_message("topic", "payload")

        result.wait_for_publish.assert_not_called()

    def test_publish_times_out_without_broker_acknowledgment(self):
        client = MagicMock()
        client.is_connected.return_value = True
        result = MagicMock()
        result.rc = mqtt_handler.mqtt_client.MQTT_ERR_SUCCESS
        result.is_published.return_value = False
        client.publish.return_value = result

        with patch.object(mqtt_handler, "mqtt_client_instance", client):
            with self.assertRaisesRegex(TimeoutError, "not acknowledged"):
                mqtt_handler.publish_message("topic", "payload")

        result.wait_for_publish.assert_called_once_with(
            timeout=mqtt_handler.MQTT_PUBLISH_TIMEOUT
        )

    def test_initialization_stores_client_only_after_connection(self):
        client = MagicMock()
        client.connect.return_value = mqtt_handler.mqtt_client.MQTT_ERR_SUCCESS
        client.is_connected.return_value = True
        client.subscribe.return_value = (
            mqtt_handler.mqtt_client.MQTT_ERR_SUCCESS, 1
        )
        config = {"mqtt": {"mqttserver": "broker", "mqttport": 1883}}

        with patch.object(mqtt_handler, "mqtt_client_instance", None), \
                patch.object(
                    mqtt_handler.mqtt_client, "Client", return_value=client
                ), \
                patch.object(mqtt_handler.yaml, "safe_load", return_value=config), \
                patch("builtins.open"):
            initialized = mqtt_handler.init_mqtt()
            self.assertIs(mqtt_handler.mqtt_client_instance, client)
            client.loop_start.assert_called_once()
            client.subscribe.assert_called_once_with("Sensor/Solar/////+")

        self.assertIs(initialized, client)

    def test_failed_initialization_clears_global_client(self):
        client = MagicMock()
        client.connect.side_effect = OSError("broker unavailable")
        config = {"mqtt": {"mqttserver": "broker", "mqttport": 1883}}

        with patch.object(mqtt_handler, "mqtt_client_instance", None), \
                patch.object(
                    mqtt_handler.mqtt_client, "Client", return_value=client
                ), \
                patch.object(mqtt_handler.yaml, "safe_load", return_value=config), \
                patch("builtins.open"):
            initialized = mqtt_handler.init_mqtt()

        self.assertIsNone(initialized)
        self.assertIsNone(mqtt_handler.mqtt_client_instance)
        client.disconnect.assert_called_once()
        client.loop_stop.assert_not_called()

    def test_action_reload_reports_publish_failure(self):
        app = Flask(__name__)
        app.register_blueprint(routes_actions.actions_bp)

        with patch.object(
            routes_actions.mqtt_handler,
            "reload_actions",
            side_effect=RuntimeError("MQTT unavailable")
        ):
            response = app.test_client().get("/reloadaktions")

        self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()
