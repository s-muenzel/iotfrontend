"""Shared input metadata and validation for action and condition forms."""
from decimal import Decimal, InvalidOperation
from check_types import CHECK_TYPE_RANGES, TAG_BITS, TAG_MASK


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


_ARGUMENT_INPUTS = {
    "zeit": {"input": "time", "step": 60},
    "hell": {"input": "number", "step": 1},
    "temp": {"input": "number", "step": 0.1},
    "heizung_ist": {"input": "number", "step": 0.1},
    "heizung_soll": {"input": "number", "step": 0.1},
    "rollo_pos": {"input": "number", "step": 1},
    "rollo_mode": {"input": "number", "step": 1},
    "rollo_last_move": {"input": "number", "step": 1},
}

_TAG_INCOMPATIBLE_COMBINATIONS = (
    ("Werktag", "Wochenende"),
    ("Werktag", "Feiertag"),
)


def build_type_schemas(types):
    """Build the form schema for known types, including special input types."""
    type_names = set(types) | set(CHECK_TYPE_RANGES)
    schemas = {}

    for type_name in type_names:
        if type_name == "tag":
            schemas[type_name] = {
                "arg1": {
                    "input": "tag",
                    "options": dict(TAG_BITS),
                    "incompatible": _TAG_INCOMPATIBLE_COMBINATIONS,
                },
                "arg2": {"input": "none"},
            }
            continue

        argument_schema = _ARGUMENT_INPUTS.get(
            type_name, {"input": "text"}
        )
        ranges = CHECK_TYPE_RANGES.get(type_name)
        if ranges:
            argument_schema = dict(argument_schema)
            argument_schema["min"] = min(bounds[0] for bounds in ranges)
            argument_schema["max"] = max(bounds[1] for bounds in ranges)
            argument_schema["ranges"] = ranges
        schemas[type_name] = {
            "arg1": dict(argument_schema),
            "arg2": dict(argument_schema),
        }

    return schemas


def validate_typed_arguments(type_name, values):
    """Reject values that do not satisfy a type's numeric input constraints."""
    if type_name == "tag":
        _validate_tag_arguments(values)
        return

    schema = _ARGUMENT_INPUTS.get(type_name, {"input": "text"})
    ranges = CHECK_TYPE_RANGES.get(type_name)

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

        if not ranges:
            continue

        allowed_ranges = tuple(
            (Decimal(str(minimum)), Decimal(str(maximum)))
            for minimum, maximum in ranges
        )
        if not any(minimum <= number <= maximum
                   for minimum, maximum in allowed_ranges):
            range_description = " or ".join(
                "{} to {}".format(minimum, maximum)
                for minimum, maximum in allowed_ranges
            )
            raise ValueError(
                "Argument {} must be in range {}".format(
                    index, range_description
                )
            )

        step = Decimal(str(schema["step"]))
        if (number - allowed_ranges[0][0]) % step:
            raise ValueError(
                "Argument {} must use increments of {}".format(index, step)
            )


def _validate_tag_arguments(values):
    """Validate a tag bitfield supplied in Min, with Max left empty."""
    minimum, maximum = values
    if maximum not in ("", 0, "0"):
        raise ValueError("Tag conditions use Min only; Max must be 0")
    try:
        number = Decimal(minimum)
    except (InvalidOperation, TypeError):
        raise ValueError("Min must contain at least one tag value") from None

    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError("Min must contain a valid tag selection")

    mask = int(number)
    if mask <= 0 or mask & ~TAG_MASK:
        raise ValueError("Min must contain a valid tag selection")

    selected = {
        name for name, bit in TAG_BITS.items()
        if mask & bit
    }
    if any(set(combination).issubset(selected)
           for combination in _TAG_INCOMPATIBLE_COMBINATIONS):
        raise ValueError(
            "Werktag cannot be combined with Wochenende or Feiertag"
        )


def validate_condition_type(type_name):
    """Reject condition types that are not supported by the controller."""
    if type_name not in CONDITION_TYPES:
        raise ValueError("Select a valid condition type")


def validate_action_type(type_name):
    """Reject action types that are not supported by the controller."""
    if type_name not in ACTION_TYPES:
        raise ValueError("Select a valid action type")
