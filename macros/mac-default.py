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
        (0x104000, 'RayC', [Keycode.COMMAND, Keycode.SPACE]),
        (0x000000, '', ''),
        # 2nd row ----------
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
        (0x404000, 'Char', [
            Keycode.CONTROL, Keycode.COMMAND, Keycode.SPACE
        ]),
        (0x000000, '', ''),
        # 3rd row ----------
        (0xa000a0, 'FFPri', [
            Keycode.COMMAND,
            Keycode.SPACE,
            -Keycode.SPACE,
            0.1,
            -Keycode.COMMAND,
            'firefox',
            Keycode.ENTER,
            -Keycode.ENTER,
            0.1,
            Keycode.COMMAND,
            Keycode.SHIFT,
            Keycode.P
        ]),
        (0x000000, '', ''),
        (0x000000, '', ''),
        # 4th row ----------
        (0x880000, 'Mute', [
                Keycode.COMMAND,
                Keycode.SPACE,
                -Keycode.SPACE,
                0.1,
                -Keycode.COMMAND,
                'microsoft teams',
                Keycode.ENTER,
                -Keycode.ENTER,
                Keycode.COMMAND,
                Keycode.SHIFT,
                Keycode.M
            ]
        ),
        (0x000000, '', ''),
        (0x000000, '', ''),
    ],
}
