# MACROPAD Hotkeys example: Firefox web browser for Mac

from adafruit_hid.keycode import Keycode  # REQUIRED if using Keycode.* values

app = {
    # REQUIRED dict, must be named 'app'
    'name': 'Windows',  # Application name
    'appName': 'Default',
    'platform': 'windows',
    'macros': [           # List of button macros...
        # COLOR    LABEL    KEY SEQUENCE
        # 1st row ----------
        (0x003B1C, '2019', [
            Keycode.CONTROL, Keycode.ALT, '9'
        ]),
        (0x000080, '1Pass', [
            Keycode.COMMAND,
            Keycode.SPACE,
            -Keycode.COMMAND,
            -Keycode.SPACE,
            0.1,
            '1password 7',
            Keycode.ENTER,
            -Keycode.ENTER
        ]),
        (0x000000, '', ''),
        # 2nd row ----------
        (0x003B1C, '2020', [
            Keycode.CONTROL, Keycode.ALT, '0'
        ]),
        (0x464eb8, 'Teams', [
            Keycode.COMMAND,
            Keycode.SPACE,
            -Keycode.SPACE,
            0.1,
            -Keycode.COMMAND,
            'microsoft teams',
            Keycode.ENTER,
            -Keycode.ENTER
        ]),
        (0x000000, '', ''),
        # 3rd row ----------
        (0x00353E, '2021', [
            Keycode.CONTROL, Keycode.ALT, '1'
        ]),
        (0x000000, '', ''),
        (0x000000, '', ''),
        # 4th row ----------
        (0x002A80, '2022', [
            Keycode.CONTROL, Keycode.ALT, '2'
        ]),
        (0x000000, '', ''),
        (0x000000, '', ''),
        # Encoder button ---
        (0x000000, '', '')  # Close window/tab
    ]
}
