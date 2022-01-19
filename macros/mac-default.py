# MACROPAD Hotkeys example: Firefox web browser for Mac

from adafruit_hid.keycode import Keycode  # REQUIRED if using Keycode.* values

app = {
    # REQUIRED dict, must be named 'app'
    'name': 'Mac',  # Application name
    'appName': 'Default',
    'platform': 'mac',
    'macros': [           # List of button macros...
        # COLOR    LABEL    KEY SEQUENCE
        # 1st row ----------
        (0x104000, 'Spot', [Keycode.COMMAND, Keycode.SPACE]),
        (0x000080, '1Pass', [
            Keycode.COMMAND,
            Keycode.SPACE,
            -Keycode.COMMAND,
            -Keycode.SPACE,
            '1password 7',
            Keycode.ENTER,
        ]),
        (0x000000, '', ''),
        # 2nd row ----------
        (0x404000, 'Char', [
            Keycode.CONTROL, Keycode.COMMAND, Keycode.SPACE
        ]),
        (0x464eb8, 'Teams', [
            Keycode.COMMAND,
            Keycode.SPACE,
            -Keycode.SPACE,
            -Keycode.COMMAND,
            'microsoft teams',
            Keycode.ENTER
        ]),
        (0x000000, '', ''),
        # 3rd row ----------
        (0x000000, '', ''),
        (0x000000, '', ''),
        (0x000000, '', ''),
        # 4th row ----------
        (0x000000, '', ''),
        (0x000000, '', ''),
        (0x000000, '', ''),
        # Encoder dial ---
        (0x000000, '', ''),
    ],
}
