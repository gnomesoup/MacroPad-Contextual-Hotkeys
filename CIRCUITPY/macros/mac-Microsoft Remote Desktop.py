# MACROPAD Hotkeys example: Firefox web browser for Mac

from adafruit_hid.keycode import Keycode  # REQUIRED if using Keycode.* values

app = {
    # REQUIRED dict, must be named "app"
    "name": "MS Remote Desktop",  # Application name
    "appName": "Microsoft Remote Desktop",
    "platform": "mac",
    "macros": [           # List of button macros...
        # COLOR    LABEL    KEY SEQUENCE
        # 1st row ----------
        None,
        (0x003B1C, "2019", [
            Keycode.CONTROL,
            Keycode.ALT, "9"
        ]),
        (0, "", []),
        # 2nd row ----------
        None,
        (0x003B1C, "2020", [
            Keycode.CONTROL, Keycode.ALT, "0"
        ]),
        (0, "", []),
        # 3rd row ----------
        (0x10DD00, "Start", [Keycode.WINDOWS]),
        (0x00353E, "2021", [
            Keycode.CONTROL, Keycode.ALT, "1"
        ]),
        None,
        # 4th row ----------
        None,
        (0x002A80, "2022", [
            Keycode.CONTROL, Keycode.ALT, "2"
        ]),
        None
    ]
}
