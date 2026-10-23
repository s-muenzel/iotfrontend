import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import call, patch

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
        rooms = {"Kitchen": "kitchen-unit", "Office": "office-unit"}
        devices = [
            {
                "name": room,
                "units": [{
                    "unitType": "avmThermostat",
                    "isConnected": True,
                    "interfaces": {
                        "temperatureInterface": {"celsius": 19.5},
                        "thermostatInterface": {
                            "setPointTemperature": {
                                "mode": "temperature",
                                "celsius": 21.0
                            }
                        }
                    }
                }]
            }
            for room in rooms
        ]

        status = fritz_handler._temperatures_from_devices(
            devices, rooms=rooms
        )

        self.assertEqual(set(status), set(rooms))
        self.assertTrue(all(
            values == {"actual": 19.5, "target": 21.0}
            for values in status.values()
        ))

    def test_reads_each_cached_room_for_all_room_status(self):
        rooms = {"Kitchen": "kitchen-unit", "Office": "office-unit"}
        units = {
            "kitchen-unit": {
                "unitType": "avmThermostat",
                "isConnected": True,
                "interfaces": {
                    "temperatureInterface": {"celsius": 19.5},
                    "thermostatInterface": {
                        "setPointTemperature": {
                            "mode": "temperature",
                            "celsius": 21.0
                        }
                    }
                }
            },
            "office-unit": {
                "unitType": "avmThermostat",
                "isConnected": True,
                "interfaces": {
                    "temperatureInterface": {"celsius": 20.0},
                    "thermostatInterface": {
                        "setPointTemperature": {
                            "mode": "temperature",
                            "celsius": 22.0
                        }
                    }
                }
            }
        }

        def get_room_unit(_url, _sid, path):
            room_uid = path.rsplit("/", 1)[-1]
            return json.dumps(units[room_uid]).encode("utf-8")

        with (
            patch.object(fritz_handler, "ROOMS", rooms),
            patch.object(fritz_handler, "get_sid", return_value="test-sid"),
            patch.object(
                fritz_handler,
                "_smart_home_rest_request",
                side_effect=get_room_unit
            ) as request
        ):
            status = fritz_handler.hole_Temperatur_Daten()

        self.assertEqual(status, {
            "Kitchen": {"actual": 19.5, "target": 21.0},
            "Office": {"actual": 20.0, "target": 22.0}
        })
        self.assertEqual(request.call_args_list, [
            call(
                fritz_handler._CONFIG["url"],
                "test-sid",
                "/overview/units/kitchen-unit"
            ),
            call(
                fritz_handler._CONFIG["url"],
                "test-sid",
                "/overview/units/office-unit"
            )
        ])

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
    #         fritz_handler.setze_Soll_Temperatur("Eva", "22.5")

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
                    fritz_handler.setze_Soll_Temperatur("Tim", target)


if __name__ == "__main__":
    unittest.main()
