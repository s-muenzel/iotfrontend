"""Argument ranges for the supported check types.

Bounds are inclusive. Entries with multiple pairs allow disjoint ranges.
For ``rollo_mode``, the range applies to each of its two switch arguments.
"""

TAG_BITS = {
    "Montag": 1 << 0,
    "Dienstag": 1 << 1,
    "Mittwoch": 1 << 2,
    "Donnerstag": 1 << 3,
    "Freitag": 1 << 4,
    "Samstag": 1 << 5,
    "Sonntag": 1 << 6,
    "Werktag": 1 << 7,
    "Wochenende": 1 << 8,
    "Feiertag": 1 << 9,
}

TAG_MASK = sum(TAG_BITS.values())

CHECK_TYPE_RANGES = {
    "tag": ((0, TAG_MASK),),
    "zeit": ((0, 86399),),
    "hell": ((0, 65535),),
    "temp": ((-35, 50),),
    "heizung_ist": ((-10, 45),),
    "heizung_soll": ((0, 0), (8, 28)),
    "rollo_pos": ((0, 100),),
    "rollo_mode": ((0, 1),),
    "rollo_last_move": ((0, 86399),),
}
