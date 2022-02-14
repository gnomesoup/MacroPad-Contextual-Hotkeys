from adafruit_board_toolkit.circuitpython_serial import data_comports
import asyncio
import json
from pygetwindow import getActiveWindow
import Quartz
from serial_asyncio import open_serial_connection
from serial import SerialException
import sys

PLATFORM = sys.platform
WINDOW_LIBRARY = None
SERVER_VERSION = "2022-02.0"
MESSAGE_VERSION = "1"

def getActiveWindowMac():
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )
    for i in range(len(windows)):
    # for win in windows:
        win = windows[i]
        if win['kCGWindowLayer'] == 0:
            return '%s' % (
                win[Quartz.kCGWindowOwnerName]
            ) # Temporary. For now, we'll just return the title of the active window.

class ActiveWindowData:
    """Handle Active Window information across async calls"""
    def __init__(self) -> None:
        self.WindowName = ""
        self.Platform = "linux" if PLATFORM in ['linux', 'linux2'] else \
            "windows" if PLATFORM in ['Windows', 'win32', 'cygwin'] else \
            "mac" if PLATFORM in ["Mac", "darwin", "os2", "os2emx"] else \
            PLATFORM

class MacropadData:
    """Handle MacroPad serial data across async calls"""
    def __init__(self) -> None:
        self.Connected = False
        self.Port = ""
        self.Buffer = ""
        self.Incoming = ""
        self.ReadStart = None
        self.reader = None
        self.writer = None

    def data_received(self, data: bytes) -> None:
        print("data received", repr(data))
        try:
            jsonData = json.loads(data)
            print(jsonData)
        except:
            pass
    def connection_lost(self, exc: Exception) -> None:
        print("connection lost")
        self.transport.loop.stop()

def DetectPort():
    comports = data_comports()
    ports = [
        comport.device for comport in comports
        if comport.description.startswith("Macropad")
    ]
    if len(ports) > 0:
        return ports[0]
    else:
        return ""

async def OpenSerialConnection(data:MacropadData):
    port = ""
    while True:
        if not data.Connected:
            port = DetectPort()
            if port:
                try:
                    data.reader, data.writer = await open_serial_connection(
                        url=port,
                        baudrate=9600
                    )
                    data.Connected = True
                    print("Connected to MacroPad")
                except SerialException:
                    data.Connected = False
        elif not data.Connected:
            data.reader = None
            data.writer = None
        await asyncio.sleep(2)

async def GetActiveWindowData(
    windowData: ActiveWindowData, macropadData:MacropadData
):
    """Poll the computer for it's active window"""
    while True:
        if windowData.Platform == "mac":
            currentWindow = getActiveWindowMac().strip()
        else:
            currentWindow = getActiveWindow().strip()
        if currentWindow != windowData.WindowName:
            print(currentWindow)
            windowData.WindowName = currentWindow
            message = json.dumps(
                {
                    "name": currentWindow,
                    "platform": windowData.Platform,
                    "version": MESSAGE_VERSION
                }
            )
            SerialWrite(macropadData.writer, message)
        await asyncio.sleep(0.3)

def SerialWrite(
    writer, message
):
    """Get/Send Messages to the Macropad"""
    if writer and message:
        writer.write(message.encode("utf-8"))

async def SerialRead(
    macropadData: MacropadData,
):
    while True:
        if macropadData.Connected:
            try:
                data = await macropadData.reader.readline()
                macropadData.Incoming = json.loads(data)
            except SerialException:
                macropadData.Connected = False
                print("Disconnected from Macropad")
            except ValueError:
                pass
        else:
            await asyncio.sleep(0)

async def IncomingHandler(
    macropadData: MacropadData, windowData: ActiveWindowData
):
    while True:
        if macropadData.Incoming:
            data = macropadData.Incoming
            try:
                if data['updateRequested']:
                    windowData.WindowName = ""
            except ValueError:
                pass
            macropadData.Incoming = ""
        await asyncio.sleep(0.3)

async def main():
    macropadData = MacropadData()
    macropadData.Port = DetectPort()
    activeWindowData = ActiveWindowData()
    await asyncio.gather(
        IncomingHandler(macropadData, activeWindowData),
        OpenSerialConnection(macropadData),
        SerialRead(macropadData),
        GetActiveWindowData(activeWindowData, macropadData),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("")
        print("Keyboard Interrupt")
