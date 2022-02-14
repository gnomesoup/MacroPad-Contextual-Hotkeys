# MACROPAD Hotkeys example: Firefox web browser for Mac

from adafruit_hid.keycode import Keycode  # REQUIRED if using Keycode.* values

app = {
    # REQUIRED dict, must be named "app"
    "name": "VSCode",  # Application name
    "appName": "Code", # Name as reported by OS
    "platform": "mac", # OS name. choose from ["mac", "linux", "windows"]
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
        None,
        (0x1E87EC, "Tasks", [
            Keycode.CONTROL,
            Keycode.SHIFT,
            Keycode.T,
            -Keycode.CONTROL,
            -Keycode.SHIFT,
            -Keycode.T,
            0.1,
            Keycode.ENTER,
            -Keycode.ENTER,
        ]),
        None,
    ],
}
