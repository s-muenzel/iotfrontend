    "tag": Bitfield, possible Values (combination of the following):
        Montag	Bit 0	0000000001	1
        Dienstag	Bit 1	0000000010	2
        Mittwoch	Bit 2	0000000100	4
        Donnerstag	Bit 3	0000001000	8
        Freitag	Bit 4	0000010000	16
        Samstag	Bit 5	0000100000	32
        Sonntag	Bit 6	0001000000	64
        Werktag	Bit 7	0010000000	128
        Wochenende	Bit 8	0100000000	256
        Feiertag	Bit 9	1000000000	512
    "zeit": Sekunden seit Mitternacht (0-86399)
    "hell": Lux (0-65535)
    "temp": °C (-35 - 50)
    "heizung_ist": °C (-10 - 45)
    "heizung_soll": °C (0: off, 8 - 28)
    "rollo_pos": Percentage (0-100),
    "rollo_mode": Schalter Aus (0), Schalter An (1)
    "rollo_last_move": Sekunden seit der letzten Bewegung (0-86399)

The same ranges are available as Python constants in `check_types.py`.

For `"tag"`, selected weekday bits must match today's weekday. Selected
qualifier bits are additional conditions: `Werktag` means Monday-Friday except
public holidays, `Wochenende` means Saturday or Sunday, and `Feiertag` means
the holiday API reports a holiday. If several qualifiers are selected, all
must match.
For "tag" at least one weekday or one qualifier must be present, but multiple selections are allowed.
For qualifiers only `Feiertag` and `Wochenende` can be present at the same time.
 