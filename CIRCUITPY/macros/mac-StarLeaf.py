# MACROPAD Hotkeys example: Firefox web browser for Mac

from adafruit_hid.keycode import Keycode  # REQUIRED if using Keycode.* values

app = {
    # REQUIRED dict, must be named 'app'
    'name': 'StarLeaf',  # Application name
    'appName': 'StarLeaf',
    'platform': 'mac',
    'macros': [           # List of button macros...
        # COLOR    LABEL    KEY SEQUENCE
        # 1st row ----------
        None,
        None,
        None,
        # 2nd row ----------
        None,
        None,
        None,
        # 3rd row ----------
        None,
        None,
        None,
        # 4th row ----------
        (0xFF0000, 'Mute', [
                Keycode.COMMAND,
                Keycode.SHIFT,
                Keycode.A
            ]
        ),
        (0xFFFF00, 'Video', [
                Keycode.COMMAND,
                Keycode.SHIFT,
                Keycode.V
            ]
        ),
        (0x000000, '', ''),
    ],
}
