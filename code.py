from adafruit_macropad import MacroPad
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from adafruit_hid.consumer_control_code import ConsumerControlCode
import asyncio
import displayio
import json
import os
from rainbowio import colorwheel
import terminalio
import time
import usb_cdc

MACRO_FOLDER = "/macros"

class ServerData:
    """Class to store incoming serial data from the host device"""
    def __init__(self):
        self.name = ""
        self.platform = ""
        self.buffer = b""
        self.connected = False
        self.readTime = None
        self.updated = False

class SwitchMode:
    """Defines modes of the macropad"""
    def __init__(self) -> None:
        """Enum like class to define modes of the macropad"""

    SWITCH = 1
    """Mode to manually select between available apps"""
    APP = 2
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
        self.currentMode = SwitchMode.APP
        self.targetMode = SwitchMode.APP
        self.appAutoSwitch = True
        self.apps = {
            "idle": {
                "name": "Adafruit MacroPad",
                "appName": 'Idle',
                "platform": 'none',
                "macros": [(0x000000, "", "")] * 12
            }
        }
        self.targetApp = "mac-Default"
        self.currentApp = None
        self.appList = ["auto"]
        self.targetSwitchIndex = None
        self.switchIndex = None

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

async def IdleState(
    macropad:MacroPad, macroPadState:MacroPadState
):
    """Handle key colors in idle states"""
    while True:
        colorInterval = 0.5
        if macroPadState.currentMode in (SwitchMode.IDLE, SwitchMode.SWITCH):
            for pin in range(12):
                if pin not in macroPadState.pressed:
                    macropad.pixels[pin] = colorwheel(macroPadState.colorIndex)
                macroPadState.values[pin] = colorwheel(macroPadState.colorIndex)
            macroPadState.colorIndex = (macroPadState.colorIndex + int(1)) % 256
        await asyncio.sleep(colorInterval)

async def KeyHandler(macropad:MacroPad, macroPadState:MacroPadState):
    """Poll keys for state changes"""
    while True:
        keyEvent = macropad.keys.events.get()
        if keyEvent:
            appData = macroPadState.apps[macroPadState.currentApp]
            sequence = appData['macros'][keyEvent.key_number][2]
            print(f"keyEvent: {keyEvent}")
            if keyEvent.pressed:
                macropad.pixels[keyEvent.key_number] = 0xAAAAAA
                macroPadState.pressed.add(keyEvent.key_number)
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
            else:
                for item in sequence:
                    if isinstance(item, int):
                        if item >= 0:
                            macropad.keyboard.release(item)
            if keyEvent.released:
                macropad.pixels[keyEvent.key_number] = appData['macros'][
                    keyEvent.key_number
                ][0]
                macroPadState.pressed.remove(keyEvent.key_number)
        await asyncio.sleep(0)

async def EncoderHandler(macropad:MacroPad, macroPadState:MacroPadState):
    """Poll encoder position for changes"""
    while True:
        macropad.encoder_switch_debounced.update()
        encoderSwitch = macropad.encoder_switch_debounced.pressed
        if encoderSwitch:
            print("encoder pressed")
            macroPadState.targetMode = SwitchMode.SWITCH if \
                macroPadState.currentMode != SwitchMode.SWITCH \
                else SwitchMode.APP
        encoderDifference = macropad.encoder - macroPadState.position
        if encoderDifference != 0:
            if macroPadState.currentMode != SwitchMode.SWITCH:
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
            macroPadState.position = macropad.encoder
        await asyncio.sleep(0)

async def SwitchModeHandler(
    macropad:MacroPad,
    macroPadState:MacroPadState,
):
    while True:
        if macroPadState.currentMode == SwitchMode.SWITCH:
            targetIndex = macroPadState.targetSwitchIndex
            switchIndex = macroPadState.switchIndex
            if targetIndex != switchIndex:
                appList = macroPadState.appList
                macroPadState.switchIndex = targetIndex
                if appList[targetIndex] == "auto":
                    appLabel = "Auto Switch Apps"
                    macroPadState.appAutoSwitch = True
                else:
                    appKey = appList[targetIndex]
                    app = macroPadState.apps[appKey]
                    appLabel = f"{app['name']} ({app['platform']})"
                    macroPadState.appAutoSwitch = False
                macroPadState.displayGroup[1].text = appLabel
        await asyncio.sleep(0)

async def ModeChangeHandler(
    macropad:MacroPad,
    macroPadState:MacroPadState,
):
    """Change modes of the macropad"""
    while True:
        if macroPadState.targetMode != macroPadState.currentMode:
            print("Mode Switch")
            if macroPadState.targetMode == SwitchMode.SWITCH:
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
                print("Switching mode activated")
            elif macroPadState.targetMode == SwitchMode.IDLE:
                print("Idle mode activated")
                macroPadState.displayGroup[13].text = "Sleeping..."
            elif macroPadState.targetMode == SwitchMode.APP:
                macroPadState.currentApp = None
                macroPadState.targetSwitchIndex = None
                macroPadState.switchIndex = None
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
            print("Loading new app")
            defaultAppKey = f"{targetApp.split('-')[0]}-Default"
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
            ):
                print(f"Error Loading Macros: {filename}")

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
    idleState = asyncio.create_task(
        IdleState(macropad, macroPadState)
    )
    getServerData = asyncio.create_task(
        GetServerData(serial, serverData)
    )
    keyHandler = asyncio.create_task(
        KeyHandler(macropad, macroPadState)
    )
    encoderHandler = asyncio.create_task(
        EncoderHandler(macropad, macroPadState)
    )
    modeChangeHandler = asyncio.create_task(
        ModeChangeHandler(macropad, macroPadState)
    )
    loadApp = asyncio.create_task(
        LoadApp(macropad, macroPadState)
    )
    setAppAuto = asyncio.create_task(
        SetAppAuto(macroPadState, serverData)
    )
    switchModeHandler = asyncio.create_task(
        SwitchModeHandler(macropad, macroPadState)
    )
    await asyncio.gather(
        getServerData,
        idleState,
        keyHandler,
        encoderHandler,
        modeChangeHandler,
        loadApp,
        setAppAuto,
        switchModeHandler
    )

asyncio.run(main())


