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

async def GetServerData(serial:usb_cdc.data, data: ServerData):
    while True:
        data.buffer += ReadSerial(serial, data)
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
        raw = serial.read(available)
        text = raw.decode("utf-8")
        available = serial.in_waiting
    return text

async def blink(macropad, pin, interval, count):
    for _ in range(count):
        macropad.pixels[pin] = (128, 128, 0)
        await asyncio.sleep(interval)
        macropad.pixels[pin] = 0
        await asyncio.sleep(interval)

async def colorChange(macropad, pin, index, interval):
    while True:
        macropad.pixels[pin] = colorwheel(index.value)
        index.value = (index.value + int(1)) % 256
        await asyncio.sleep(interval)


async def main():
    serial = usb_cdc.data
    serverData = ServerData()
    macropad = MacroPad()
    colorIndex = ColorIndex()
    # blinkTask2 = asyncio.create_task(blink(macropad, 5, 0.1, 20))
    colorTask = asyncio.create_task(colorChange(macropad, 0, colorIndex, .5))
    getServerData = GetServerData(serial, serverData)
    await asyncio.gather(getServerData, colorTask)
    print("done")

asyncio.run(main())


