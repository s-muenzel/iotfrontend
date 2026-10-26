import unittest

from action_form import build_type_schemas, validate_typed_arguments


class ActionFormTests(unittest.TestCase):
    def test_builds_special_and_default_input_schemas(self):
        schemas = build_type_schemas(["custom"])

        self.assertEqual(schemas["zeit"]["arg1"]["input"], "time")
        self.assertEqual(schemas["temp"]["arg2"]["step"], 0.1)
        self.assertEqual(schemas["custom"]["arg1"], {"input": "text"})

    def test_accepts_valid_numeric_values(self):
        validate_typed_arguments("temp", ("-10.5", "50"))
        validate_typed_arguments("zeit", ("3600", "86340"))

    def test_rejects_values_outside_type_constraints(self):
        with self.assertRaises(ValueError):
            validate_typed_arguments("temp", ("51", ""))
        with self.assertRaises(ValueError):
            validate_typed_arguments("hell", ("1.5", ""))
        with self.assertRaises(ValueError):
            validate_typed_arguments("zeit", ("3601", ""))

    def test_allows_generic_text_arguments(self):
        validate_typed_arguments("custom", ("arbitrary", "text"))


if __name__ == "__main__":
    unittest.main()
