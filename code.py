from adafruit_macropad import MacroPad
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from adafruit_hid.consumer_control_code import ConsumerControlCode
import asyncio
import displayio
import json
from rainbowio import colorwheel
import terminalio
import time
import usb_cdc

class ColorIndex:
    def __init__(self):
        self.value = 0

class ServerData:
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

async def GetServerData(serial:usb_cdc.data, data: ServerData):
    while True:
        if data.readTime is not None and time.monotonic() - data.readTime > 0.5:
            data.buffer = b""
        data.buffer += ReadSerial(serial, data)
        try:
            serialData = json.loads(data.buffer)
            data.name = serialData['name']
            data.platform = serialData['platform']
            data.updated = True
            data.buffer = b""
            print(data.name)
        except ValueError:
            pass
        await asyncio.sleep(0.1)

def ReadSerial(serial:usb_cdc.data, data: ServerData) -> str:
    available = serial.in_waiting
    text = ""
    while available:
        data.readTime = time.monotonic()
        raw = serial.read(available)
        text = raw.decode("utf-8")
        available = serial.in_waiting
    return text

async def colorChange(
    macropad:MacroPad, macroPadState:MacroPadState
):
    while True:
        colorInterval = max(0, macroPadState.position / 64)
        for pin in range(12):
            if pin not in macroPadState.pressed:
                macropad.pixels[pin] = colorwheel(macroPadState.colorIndex)
            macroPadState.values[pin] = colorwheel(macroPadState.colorIndex)
        macroPadState.colorIndex = (macroPadState.colorIndex + int(1)) % 256
        await asyncio.sleep(colorInterval)

async def GetPressedKey(macropad:MacroPad, macroPadState:MacroPadState):
    while True:
        macropad.encoder_switch_debounced.update()
        encoderSwitch = macropad.encoder_switch_debounced.pressed
        if encoderSwitch:
            macroPadState.targetMode = SwitchMode.SWITCH if \
                macroPadState.currentMode != SwitchMode.SWITCH \
                else SwitchMode.APP

        keyEvent = macropad.keys.events.get()
        if keyEvent:
            if keyEvent.pressed:
                macropad.pixels[keyEvent.key_number] = 0xAAAAAA
                macroPadState.pressed.add(keyEvent.key_number)
            if keyEvent.released:
                macropad.pixels[keyEvent.key_number] = macroPadState.values[
                    keyEvent.key_number
                ]
                macroPadState.pressed.remove(keyEvent.key_number)
        await asyncio.sleep(0)

async def GetEncoderState(macropad:MacroPad, macroPadState:MacroPadState):
    while True:
        if macropad.encoder != macroPadState.position:
            macroPadState.position = macropad.encoder
            print(max(0, macroPadState.position / 64))
        await asyncio.sleep(0)

async def SwitchStates(
    macropad:MacroPad,
    macroPadState:MacroPadState,
    data:ServerData
):
    while True:
        if macroPadState.targetMode != macroPadState.currentMode:
            print("Mode Switch")
            print(f"targetMode = {macroPadState.targetMode}")
            print(f"currentMode = {macroPadState.currentMode}")
            if macroPadState.targetMode == SwitchMode.SWITCH:
                macroPadState.displayGroup[13].text = "Switch Mode"
                macroPadState.displayGroup[0].text = "<"
                macroPadState.displayGroup[1].text = "Test"
                macroPadState.displayGroup[2].text = ">"
            elif macroPadState.targetMode == SwitchMode.IDLE:
                macroPadState.displayGroup[13].text = "Sleeping..."
            elif macroPadState.targetMode == SwitchMode.APP:
                data.updated = True
            macroPadState.currentMode = macroPadState.targetMode
        if data.updated and macroPadState.currentMode == SwitchMode.APP:
            macroPadState.displayGroup[13].text = data.name
            data.updated = False
            macropad.display.refresh()
        await asyncio.sleep(0)

async def main():
    serial = usb_cdc.data
    serverData = ServerData()
    macropad = MacroPad()
    macroPadState = MacroPadState()
    macroPadState.displayGroup = displayio.Group()
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
    colorTask = asyncio.create_task(
        colorChange(macropad, macroPadState)
    )
    getServerData = asyncio.create_task(
        GetServerData(serial, serverData)
    )
    getPressedKey = asyncio.create_task(
        GetPressedKey(macropad, macroPadState)
    )
    getEncoderState = asyncio.create_task(
        GetEncoderState(macropad, macroPadState)
    )
    switchStates = asyncio.create_task(
        SwitchStates(macropad, macroPadState, serverData)
    )
    await asyncio.gather(
        getServerData,
        colorTask,
        getPressedKey,
        getEncoderState,
        switchStates
    )

asyncio.run(main())


