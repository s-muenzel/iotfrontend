import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import fritz_handler


class FritzHandlerTests(unittest.TestCase):
    # def test_reads_credentials_from_separate_config_file(self):
    #     with TemporaryDirectory() as directory:
    #         config_path = Path(directory) / "fritz.cnf"
    #         config_path.write_text(
    #             "fritz:\n"
    #             "  url: http://fritz.box\n"
    #             "  username: test-user\n"
    #             "  password: test-password\n",
    #             encoding="utf-8"
    #         )
    #         with patch.object(fritz_handler, "CONFIG_PATH", config_path):
    #             config = fritz_handler._load_config()

    #     self.assertEqual(config, {
    #         "url": "http://fritz.box",
    #         "username": "test-user",
    #         "password": "test-password"
    #     })

    def test_reads_temperatures_for_configured_rooms(self):
        devices = [
            {
                "name": room,
                "units": [{
                    "unitType": "avmThermostat",
                    "isConnected": True,
                    "interfaces": {
                        "temperatureInterface": {"celsius": 19.5},
                        "thermostatInterface": {
                            "setPointTemperature": {"celsius": 21.0}
                        }
                    }
                }]
            }
            for room in fritz_handler.ROOMS
        ]

        status = fritz_handler._temperatures_from_devices(devices)

        self.assertEqual(set(status), set(fritz_handler.ROOMS))
        self.assertTrue(all(
            values == {"actual": 19.5, "target": 21.0}
            for values in status.values()
        ))

    # def test_sets_only_the_selected_room_target(self):
    #     devices = [{
    #         "name": "Eva",
    #         "units": [{
    #             "UID": "eva-unit",
    #             "unitType": "avmThermostat",
    #             "isConnected": True
    #         }]
    #     }]
    #     with (
    #         patch.object(
    #             fritz_handler, "_with_session",
    #             side_effect=lambda operation: operation("http://box", "sid")
    #         ),
    #         patch.object(fritz_handler, "_get_devices", return_value=devices),
    #         patch.object(fritz_handler, "_smart_home_request") as request
    #     ):
    #         fritz_handler.set_target_temperature("Eva", "22.5")

    #     request.assert_called_once_with(
    #         "http://box",
    #         "sid",
    #         "/overview/units/eva-unit",
    #         method="PUT",
    #         payload={
    #             "interfaces": {
    #                 "thermostatInterface": {
    #                     "setPointTemperature": {
    #                         "mode": "temperature",
    #                         "celsius": 22.5
    #                     }
    #                 }
    #             }
    #         }
    #     )

    def test_rejects_out_of_range_or_non_half_degree_targets(self):
        for target in ("7.5", "28.5", "20.2", "nan"):
            with self.subTest(target=target):
                with self.assertRaises(fritz_handler.InvalidTargetError):
                    fritz_handler.set_target_temperature("Tim", target)


if __name__ == "__main__":
    unittest.main()
