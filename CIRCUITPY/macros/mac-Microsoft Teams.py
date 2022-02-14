# MACROPAD Hotkeys example: Firefox web browser for Mac

from adafruit_hid.keycode import Keycode  # REQUIRED if using Keycode.* values

app = {
    # REQUIRED dict, must be named "app"
    "name": "MS Teams",  # Application name
    "appName": "Microsoft Teams",
    "platform": "mac",
    "macros": [
        # List of button macros...
        # Macros set to "None" will be pulled from the default macro list
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
        (0xFF0000, "Mute", [
                Keycode.COMMAND,
                Keycode.SHIFT,
                Keycode.M
            ]
        ),
        (0xFFFF00, "Video", [
                Keycode.COMMAND,
                Keycode.SHIFT,
                Keycode.O
            ]
        ),
        None,
    ],
}
