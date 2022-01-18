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

class KeyStates:
    def __init__(self):
        self.pressed = set()
        self.values = [0x000000] * 12
        self.colorIndex = 0
        self.colorInterval = 0.5

async def GetServerData(serial:usb_cdc.data, data: ServerData):
    while True:
        if data.readTime is not None and time.monotonic() - data.readTime > 0.5:
            data.buffer = b""
        data.buffer += ReadSerial(serial, data)
        if data.buffer:
            print(data.buffer)
        try:
            serialData = json.loads(data.buffer)
            data.name = serialData['name']
            data.platform = serialData['platform']
            data.buffer = b""
            print(data.name)
        except ValueError:
            pass
        await asyncio.sleep(0.1)
    return

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
    macropad:MacroPad, pin, keyStates:KeyStates
):
    while True:
        if pin not in keyStates.pressed:
            macropad.pixels[pin] = colorwheel(keyStates.colorIndex)
        keyStates.colorIndex = (keyStates.colorIndex + int(1)) % 256
        keyStates.values[pin] = colorwheel(keyStates.colorIndex)
        await asyncio.sleep(keyStates.colorInterval)

async def GetPressedKey(macropad, keyStates:KeyStates):
    while True:
        keyEvent = macropad.keys.events.get()
        if keyEvent:
            if keyEvent.pressed:
                macropad.pixels[keyEvent.key_number] = 0xAAAAAA
                keyStates.pressed.add(keyEvent.key_number)
            if keyEvent.released:
                macropad.pixels[keyEvent.key_number] = keyStates.values[ 
                    keyEvent.key_number
                 ]
                keyStates.pressed.remove(keyEvent.key_number)
        await asyncio.sleep(0)

async def main():
    serial = usb_cdc.data
    serverData = ServerData()
    macropad = MacroPad()
    keyStates = KeyStates()
    colorTask = asyncio.create_task(
        colorChange(macropad, 0, keyStates)
    )
    getServerData = asyncio.create_task(
        GetServerData(serial, serverData)
    )
    getPressedKey = asyncio.create_task(
        GetPressedKey(macropad, keyStates)
    )
    await asyncio.gather(getServerData, colorTask, getPressedKey)

asyncio.run(main())


