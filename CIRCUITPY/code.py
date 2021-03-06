from adafruit_macropad import MacroPad
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
import asyncio
import displayio
import json
import os
from rainbowio import colorwheel
import terminalio
import time
import usb_cdc

MACRO_FOLDER = "/macros"
DEFAULT_APP = "mac-Default"
CLIENT_VERSION = "2022-02.0"
MESSAGING_VERSION = "1"

class ServerData:
    """Class to store incoming serial data from the host device"""
    def __init__(self):
        self.name = ""
        self.platform = ""
        self.buffer = b""
        self.connected = False
        self.readTime = None
        self.updated = False

class MacropadMode:
    """Defines modes of the macropad"""
    def __init__(self) -> None:
        """Enum like class to define modes of the macropad"""

    SWITCH = 1
    """Mode to manually select between available apps"""
    HOTKEY = 2
    """Standard mode for hotkeys"""
    IDLE = 3
    """Mode for idle state. Computer is asleep or screensave is on"""
    MEETING = 4
    """Mode for active online meeting"""

class MacroPadState:
    """
    Class to store the current state of the macropad to share across async
    functions
    """
    def __init__(self):
        self.pressed = set()
        self.values = [0x000000] * 12
        self.colorIndex = 0
        self.colorInterval = 0.5
        self.position = 0
        self.labelText = "App"
        self.currentMode = MacropadMode.HOTKEY
        self.targetMode = MacropadMode.HOTKEY
        self.appAutoSwitch = True
        self.apps = {
            "idle": {
                "name": "Adafruit MacroPad",
                "appName": 'Idle',
                "platform": 'none',
                "macros": [(0x000000, "", "")] * 12
            }
        }
        self.defaultApp = DEFAULT_APP
        self.targetApp = self.defaultApp
        self.currentApp = None
        self.appList = ["auto"]
        self.targetSwitchIndex = None
        self.switchIndex = None
        self.switchTime = None

async def GetServerData(serial:usb_cdc.data, data: ServerData):
    """Get data from server and store in server data class"""
    while True:
        if data.readTime is not None and time.monotonic() - data.readTime > 0.5:
            data.buffer = b""
        data.buffer += ReadSerial(serial, data)
        if data.buffer:
            try:
                serialData = json.loads(data.buffer)
                data.name = serialData['name']
                data.platform = serialData['platform']
                data.updated = True
                data.buffer = b""
                print(f"Focused app: {data.name}")
            except ValueError:
                pass
        await asyncio.sleep(0)

def ReadSerial(serial:usb_cdc.data, data: ServerData) -> str:
    """Read incoming serial data"""
    available = serial.in_waiting
    text = ""
    while available:
        data.readTime = time.monotonic()
        raw = serial.read(available)
        text = raw.decode("utf-8")
        available = serial.in_waiting
    return text

async def RequestUpdateFromServer(
    macropadState: MacroPadState, serial:usb_cdc.data
):
    autoSwitch = None
    while True:
        if macropadState.appAutoSwitch != autoSwitch:
            autoSwitch = macropadState.appAutoSwitch
            message = json.dumps(
                {
                    "updateRequested": True,
                    "version": MESSAGING_VERSION,
                }
            )
            print(f"Requesting update: {message}")
            serial.write(bytes(f"{message}\n", "utf-8"))
        await asyncio.sleep(0.2)

async def IdleState(
    macropad:MacroPad, macroPadState:MacroPadState
):
    """Handle key colors in idle states"""
    while True:
        colorInterval = 0
        if macroPadState.currentMode in (MacropadMode.IDLE, MacropadMode.SWITCH):
            for pin in range(12):
                if pin not in macroPadState.pressed:
                    cIndex = macroPadState.colorIndex
                    oPin = pin - 3
                    cIndex = (cIndex - ((pin // 4 + oPin % 3) * 6)) % 256
                    macropad.pixels[pin] = colorwheel(cIndex)
                macroPadState.values[pin] = colorwheel(cIndex)
            macroPadState.colorIndex = (macroPadState.colorIndex + int(1)) % 256
        await asyncio.sleep(colorInterval)

async def KeyHandler(
    macropad:MacroPad,
    macroPadState:MacroPadState,
):
    """Poll keys for state changes"""
    while True:
        keyEvent = macropad.keys.events.get()
        if keyEvent:
            keyNumber = keyEvent.key_number
            print(f"keyEvent: {keyEvent}")
            macro = GetAppMacro(keyNumber, macroPadState)
            if keyEvent.pressed:
                macropad.pixels[keyNumber] = 0xAAAAAA
                macroPadState.pressed.add(keyNumber)
                if macroPadState.currentMode == MacropadMode.HOTKEY:
                    KeyPressedAction(macro, macropad)
            if keyEvent.released:
                macropad.pixels[keyNumber] = macroPadState.values[keyNumber]
                if macroPadState.currentMode == MacropadMode.HOTKEY:
                    KeyReleaseAction(macro, macropad)
                macroPadState.pressed.remove(keyNumber)
        await asyncio.sleep(0)

def KeyPressedAction(
    macro: tuple, macropad: MacroPad
):
    print(macro)
    sequence = macro[2]
    if sequence:
        try:
            for item in sequence:
                if isinstance(item, int):
                    if item >= 0:
                        macropad.keyboard.press(item)
                    else:
                        macropad.keyboard.release(-item)
                elif isinstance(item, float):
                    time.sleep(item)
                else:
                    macropad.keyboard_layout.write(item)
        except TypeError as e:
            print(f"TypeError: {e}")
            print("Are the macro keys in a list?")
    return

def KeyReleaseAction(
    macro: tuple, macropad: MacroPad
):
    sequence = macro[2]
    if sequence:
        for item in sequence:
            if isinstance(item, int):
                if item >= 0:
                    macropad.keyboard.release(item)
    return

def GetAppMacro(keyNumber: int, mpState: MacroPadState):
    appData = mpState.apps[mpState.currentApp]
    if appData is None:
        print("No app data found")
        return None
    else:
        macro = appData['macros'][keyNumber]
        if macro is None:
            macro = mpState.apps[mpState.defaultApp]['macros'][keyNumber]
    return macro

async def EncoderHandler(macropad:MacroPad, macroPadState:MacroPadState):
    """Poll encoder position for changes"""
    while True:
        macropad.encoder_switch_debounced.update()
        encoderSwitch = macropad.encoder_switch_debounced.pressed
        if encoderSwitch:
            print("encoder pressed")
            if macroPadState.currentMode != MacropadMode.SWITCH:
                macroPadState.targetMode = MacropadMode.SWITCH 
            else:
                macroPadState.targetMode = MacropadMode.HOTKEY
        encoderDifference = macropad.encoder - macroPadState.position
        if encoderDifference != 0:
            if macroPadState.currentMode != MacropadMode.SWITCH:
                if encoderDifference > 0:
                    macropad.consumer_control.send(
                        macropad.ConsumerControlCode.VOLUME_INCREMENT
                    )
                else:
                    macropad.consumer_control.send(
                        macropad.ConsumerControlCode.VOLUME_DECREMENT
                    )
            else:
                i = macroPadState.switchIndex + encoderDifference
                macroPadState.targetSwitchIndex = i % len(macroPadState.appList)
                macroPadState.switchTime = time.monotonic()
            macroPadState.position = macropad.encoder
        await asyncio.sleep(0)

async def SwitchModeHandler(
    macroPadState:MacroPadState,
):
    while True:
        if macroPadState.currentMode == MacropadMode.SWITCH:
            targetIndex = macroPadState.targetSwitchIndex
            switchIndex = macroPadState.switchIndex
            if targetIndex != switchIndex:
                appList = macroPadState.appList
                macroPadState.switchIndex = targetIndex
                if appList[targetIndex] == "auto":
                    appLabel = "Auto Switch Apps"
                else:
                    appKey = appList[targetIndex]
                    app = macroPadState.apps[appKey]
                    appLabel = f"{app['name']} ({app['platform']})"
                macroPadState.displayGroup[1].text = appLabel
        await asyncio.sleep(0)

async def ModeChangeHandler(
    macroPadState:MacroPadState
):
    """Change modes of the macropad"""
    while True:
        if (
            macroPadState.currentMode == MacropadMode.SWITCH and
            time.monotonic() - macroPadState.switchTime > 60
        ):
            print("Switch Time Up")
            macroPadState.targetMode = MacropadMode.HOTKEY
        if macroPadState.targetMode != macroPadState.currentMode:
            print("Mode Switch")
            if macroPadState.currentMode == MacropadMode.SWITCH:
                # Close out switch mode
                i = macroPadState.switchIndex
                if i != 0:
                    macroPadState.targetApp = macroPadState.appList[i]
                else:
                    macroPadState.appAutoSwitch = True
                macroPadState.targetSwitchIndex = None
                macroPadState.switchIndex = None
                macroPadState.switchTime = None
            if macroPadState.targetMode == MacropadMode.SWITCH:
                macroPadState.displayGroup[13].text = "Switch Mode"
                for i in range(12):
                    if i == 0:
                        macroPadState.displayGroup[0].text = "<"
                    elif i == 2:
                        macroPadState.displayGroup[2].text = ">"
                    else:
                        macroPadState.displayGroup[i].text = ""
                if macroPadState.appAutoSwitch:
                    targetIndex = 0
                else:
                    targetIndex = macroPadState.appList.index(
                        macroPadState.currentApp
                    )
                macroPadState.targetSwitchIndex = targetIndex
                macroPadState.appAutoSwitch = False
                macroPadState.switchTime = time.monotonic()
                print("Switching mode activated")
            elif macroPadState.targetMode == MacropadMode.IDLE:
                macroPadState.displayGroup[13].text = "Sleeping..."
                print("Idle mode activated")
            elif macroPadState.targetMode == MacropadMode.HOTKEY:
                macroPadState.currentApp = None
                print("App mode activated")
            macroPadState.currentMode = macroPadState.targetMode
            print(f"macroPadState.currentMode = {macroPadState.currentMode}")
            
        await asyncio.sleep(0)

async def SetAppAuto(
    macroPadState:MacroPadState,
    serverData:ServerData
):
    while True:
        if macroPadState.appAutoSwitch == True and serverData.updated == True:
            print("Auto Switching App")
            serverData.updated = False
            platform = serverData.platform
            appName = serverData.name
            macroPadState.targetApp = f"{platform}-{appName}"
        await asyncio.sleep(0)

async def LoadApp(
    macropad:MacroPad,
    macroPadState:MacroPadState
):
    """Poll for app changes and load up required info"""
    while True:
        currentApp = macroPadState.currentApp
        targetApp = macroPadState.targetApp
        apps = macroPadState.apps
        if currentApp != targetApp:
            defaultAppKey = macroPadState.defaultApp
            if targetApp not in apps:
                displayName = f"{targetApp.split('-', 1)[1]}*"
                currentApp = defaultAppKey
                macroPadState.targetApp = currentApp
            else:
                currentApp = targetApp
                displayName = None
            macroPadState.currentApp = currentApp
            appData = apps[currentApp]
            defaultAppData = apps[defaultAppKey]
            print(
                f"Load App: {appData['name']}"
            )
            macroPadState.displayGroup[13].text = appData['name'] if \
                displayName is None else displayName
            for i, macro in enumerate(appData['macros']):
                if i > 11:
                    continue
                if macro is None:
                    macro = defaultAppData['macros'][i]
                macropad.pixels[i] = macro[0]
                macroPadState.values[i] = macro[0]
                macroPadState.displayGroup[i].text = macro[1]
        await asyncio.sleep(0)

async def main():
    serial = usb_cdc.data
    serverData = ServerData()
    macropad = MacroPad()
    macroPadState = MacroPadState()
    macroPadState.displayGroup = displayio.Group()
    
    files = os.listdir(MACRO_FOLDER)
    files.sort()
    for filename in files:
        if filename.endswith('.py'):
            try:
                # module = __import__(f"{MACRO_FOLDER}/{filename[:-3]}")
                module = __import__("{}/{}".format(MACRO_FOLDER, filename[:-3]))
                appKey = f"{module.app['platform']}-{module.app['appName']}"
                macroPadState.apps[appKey] = module.app
                macroPadState.appList.append(appKey)
            except (
                AttributeError,
                ImportError,
                IndexError,
                KeyError,
                NameError,
                SyntaxError,
                TypeError,
            ) as e:
                print(f"Error Loading Macros: {filename}\n{e}")
    for keyIndex in range(12):
        x = keyIndex % 3
        y = keyIndex // 3
        macroPadState.displayGroup.append(
            label.Label(
                terminalio.FONT,
                text="",
                color=0xFFFFFF,
                anchored_position=(
                    (macropad.display.width - 1) * x / 2,
                    (macropad.display.height - 1) - ((3 - y) * 12)
                ),
                anchor_point=(x / 2, 1.0)
            )
        )
    macroPadState.displayGroup.append(
        Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF)
    )
    macroPadState.displayGroup.append(
        label.Label(
            terminalio.FONT,
            text=macroPadState.labelText,
            color=0x000000,
            anchored_position=(macropad.display.width // 2, -2),
            anchor_point=(0.5, 0)
        )
    )
    macropad.display.show(macroPadState.displayGroup)
    await asyncio.gather(
        RequestUpdateFromServer(macroPadState, serial),
        IdleState(macropad, macroPadState),
        GetServerData(serial, serverData),
        KeyHandler(macropad, macroPadState),
        EncoderHandler(macropad, macroPadState),
        ModeChangeHandler(macroPadState),
        LoadApp(macropad, macroPadState),
        SetAppAuto(macroPadState, serverData),
        SwitchModeHandler(macroPadState),
    )

asyncio.run(main())


