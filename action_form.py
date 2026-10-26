"""Shared input metadata and validation for action and condition forms."""
from decimal import Decimal, InvalidOperation


# Keep in sync with the keys in iotcontroler/controler.py:CHECK_FUNCTIONS.
CONDITION_TYPES = (
    "tag",
    "zeit",
    "hell",
    "temp",
    "heizung_ist",
    "heizung_soll",
    "rollo_pos",
    "rollo_mode",
    "rollo_last_move",
)

# Keep in sync with the keys in iotcontroler/controler.py:ACTION_FUNCTIONS.
ACTION_TYPES = ("mqtt", "fritz")


_SPECIAL_ARGUMENT_SCHEMAS = {
    "zeit": {"input": "time", "min": 0, "max": 86340, "step": 60},
    "hell": {"input": "number", "min": 0, "max": 4096, "step": 1},
    "temp": {"input": "number", "min": -30, "max": 50, "step": 0.1},
    "rollo_last_move": {
        "input": "number", "min": 0, "max": 86400000, "step": 100
    },
    "rollo_pos": {"input": "number", "min": -1, "max": 100, "step": 1},
    "rollo_mode": {"input": "number", "min": 0, "max": 1, "step": 1},
}


def build_type_schemas(types):
    """Build the form schema for known types, including special input types."""
    type_names = set(types) | set(_SPECIAL_ARGUMENT_SCHEMAS)
    schemas = {}

    for type_name in type_names:
        argument_schema = _SPECIAL_ARGUMENT_SCHEMAS.get(
            type_name, {"input": "text"}
        )
        schemas[type_name] = {
            "arg1": dict(argument_schema),
            "arg2": dict(argument_schema),
        }

    return schemas


def validate_typed_arguments(type_name, values):
    """Reject values that do not satisfy a type's numeric input constraints."""
    schema = _SPECIAL_ARGUMENT_SCHEMAS.get(type_name, {"input": "text"})

    for index, value in enumerate(values, start=1):
        if schema["input"] == "text" or value == "":
            continue

        try:
            number = Decimal(value)
        except (InvalidOperation, TypeError):
            raise ValueError(
                "Argument {} must be a valid number".format(index)
            ) from None

        if not number.is_finite():
            raise ValueError(
                "Argument {} must be a finite number".format(index)
            )

        minimum = Decimal(str(schema["min"]))
        maximum = Decimal(str(schema["max"]))
        step = Decimal(str(schema["step"]))
        if number < minimum or number > maximum:
            raise ValueError(
                "Argument {} must be between {} and {}".format(
                    index, minimum, maximum
                )
            )

        if (number - minimum) % step:
            raise ValueError(
                "Argument {} must use increments of {}".format(index, step)
            )


def validate_condition_type(type_name):
    """Reject condition types that are not supported by the controller."""
    if type_name not in CONDITION_TYPES:
        raise ValueError("Select a valid condition type")


def validate_action_type(type_name):
    """Reject action types that are not supported by the controller."""
    if type_name not in ACTION_TYPES:
        raise ValueError("Select a valid action type")
