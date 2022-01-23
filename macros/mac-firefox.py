# MACROPAD Hotkeys example: Firefox web browser for Mac

from adafruit_hid.keycode import Keycode  # REQUIRED if using Keycode.* values

app = {
    # REQUIRED dict, must be named "app"
    "name": "Firefox",  # Application name
    "appName": "Firefox",
    "platform": "mac",
    "macros": [
        # List of button macros...
        # Macros set to "None" will be pulled from the default macro list
        # COLOR    LABEL    KEY SEQUENCE
        # 1st row ----------
        (0x000080, '1Pass', [
               Keycode.COMMAND,
               Keycode.PERIOD 
            ]
        ),
        None,
        None,
        # 2nd row ----------
        None,
        None,
        None,
        # 3rd row ----------
        (0xa000a0, "Priv", [
            Keycode.COMMAND,
            Keycode.SHIFT,
            Keycode.P
        ]),
        None,
        None,
        # 4th row ----------
        None,
        None,
        None,
    ],
}
