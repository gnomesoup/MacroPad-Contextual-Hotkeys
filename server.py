from curses import baudrate
from adafruit_board_toolkit.circuitpython_serial import data_comports
import asyncio
import json
import serial_asyncio
import sys
import time

PLATFORM = sys.platform
WINDOW_LIBRARY = None
SERVER_VERSION = "2022-01.0"
MESSAGE_VERSION = "1"

class ActiveWindowData:
    """Handle Active Window information across async calls"""
    def __init__(self) -> None:
        self.WindowName = ""

class MacropadData:
    """Handle MacroPad serial data across async calls"""
    def __init__(self) -> None:
        self.Connected = False
        self.Port = ""
        self.Buffer = ""
        self.Message = b""
        self.Incoming = ""
        self.ReadStart = None

class SerialProtocol(asyncio.Protocol):
    def connection_made(self, transport: serial_asyncio.SerialTransport) -> None:
        self.transport = transport
        print("port opened", transport)
        transport.serial.rts = False
        transport.write(
            bytes(
                json.dumps({"name": "Test", "platform": "mac"})
                , "utf-8"
            )
        )
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

if PLATFORM in ['linux', 'linux2']:
    print("Loading setting for linux")
    PLATFORM = "linux"
    if WINDOW_LIBRARY is None:
        try:
            import wnck
            WINDOW_LIBRARY = "wnck"
            def GetActiveWindowName() -> str:
                active_window_name = ""
                screen = wnck.screen_get_default()
                screen.force_update()
                window = screen.get_active_window()
                if window is not None:
                    pid = window.get_pid()
                    with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                        active_window_name = f.read()
                return active_window_name
        except ImportError:
            WINDOW_LIBRARY = None
    if WINDOW_LIBRARY is None:
        try:
            from gi.repository import Gtk, Wnck
            WINDOW_LIBRARY = "gi"
            def GetActiveWindowName() -> str:
                active_window_name = ""
                Gtk.init([])  # necessary if not using a Gtk.main() loop
                screen = Wnck.Screen.get_default()
                screen.force_update()  # recommended per Wnck documentation
                active_window = screen.get_active_window()
                pid = active_window.get_pid()
                with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                    active_window_name = f.read()
                return active_window_name
        except ImportError:
            WINDOW_LIBRARY = None
elif PLATFORM in ["Windows", "win32", "cygwin"]:
    PLATFORM = "windows"
    print("Loading setting for windows")
    import win32gui
    import win32process
    from wmi import WMI
    def GetActiveWindowName() -> str:
        active_window_name = ""
        wmi = WMI()
        window = win32gui.GetForegroundWindow()
        try: 
            _, pid = win32process.GetWindowThreadProcessId(window)
            for process in wmi.query(
                f"SELECT Description from Win32_Process "
                f"WHERE processId = {str(pid)}"
            ):
                exe = (process.Description).replace(".exe", "")
            active_window_name = exe
        except:
            active_window_name = win32gui.GetWindowText(window)
        return active_window_name
elif PLATFORM in ["Mac", "darwin", "os2", "os2emx"]:
    PLATFORM = "mac"
    print("Loading setting for mac")
    from AppKit import NSWorkspace
    def GetActiveWindowName() -> str:
        activeApplication = NSWorkspace.sharedWorkspace().activeApplication()
        if activeApplication is None:
            return None
        return activeApplication['NSApplicationName']
else:
    print(f"sys.platform={PLATFORM} is unknown. Please report.")
    print(sys.version)
    exit()

async def DetectPort(macropadData:MacropadData) -> str:
    """Check to see if a Macropad is connected"""
    while True:
        comports = data_comports()
        ports = [
            comport.device for comport in comports
            if comport.description.startswith("Macropad")
        ]
        if len(ports) > 0:
            if macropadData.Port != ports[0]:
                print(f"macropad port: {ports[0]}")
                macropadData.Port = ports[0]
        else:
            if macropadData.Port is not None:
                print("Macropad not found")
                macropadData.Port = None
        await asyncio.sleep(1)


async def GetActiveWindowData(
    windowData: ActiveWindowData, macropadData:MacropadData
):
    """Poll the computer for it's active window"""
    while True:
        currentWindow = GetActiveWindowName()
        if currentWindow != windowData.WindowName:
            print(currentWindow)
            windowData.WindowName = currentWindow
            macropadData.Message = json.dumps(
                {
                    "name": currentWindow,
                    "platform": PLATFORM,
                    "version": SERVER_VERSION
                }
            )
        await asyncio.sleep(0.1)

async def SerialWrite(
    macropadData: MacropadData,
    writer: asyncio.StreamWriter
):
    """Get/Send Messages to the Macropad"""
    while True:
        if macropadData.Port:
            if macropadData.Message:
                print(f"Serial Write {macropadData.Message.encode('utf-8')}")
                writer.write(macropadData.Message.encode("utf-8"))
                macropadData.Message = b""
        await asyncio.sleep(0.1)

async def SerialRead(
    macropadData: MacropadData,
    reader: asyncio.StreamReader
):
    while True:
        data = await reader.readline()
        try:
            macropadData.Incoming = json.loads(data)
        except ValueError:
            pass

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
    activeWindowData = ActiveWindowData()
    reader, writer = await serial_asyncio.open_serial_connection(
        url="/dev/cu.usbmodem103",
        baudrate=9600
    )
    await asyncio.gather(
        GetActiveWindowData(activeWindowData, macropadData),
        DetectPort(macropadData),
        IncomingHandler(macropadData, activeWindowData),
        SerialWrite(macropadData, writer),
        SerialRead(macropadData, reader),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("")
        print("Keyboard Interrupt")
