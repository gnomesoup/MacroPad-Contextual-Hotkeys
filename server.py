from adafruit_board_toolkit.circuitpython_serial import data_comports
import json
import logging
import paho.mqtt.client as mqtt
import serial
import sys
import time

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

SUBSCRIBE_TOPIC = "macropad/focus/#"

## Serial connection functions
def detect_port() -> str:
    comports = data_comports()
    ports = [
        comport.device for comport in comports
        if comport.description.startswith("Macropad")
    ]
    if len(ports) > 0:
        return ports[0]
    else:
        raise RuntimeError("Unable to find MacroPad")

def sendMessage(message:str):
    port = detect_port()
    with serial.Serial(port=port) as s:
        bytesToWrite = bytes(message, "utf-8")
        s.write(bytesToWrite)
    return

## MQTT functions
def on_connect(client:mqtt.Client, userdata, flags:dict, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(SUBSCRIBE_TOPIC)
    return

def on_publish(client:mqtt.Client, userdata, mid):
    print(f"Publish to topic {mid}")
    return

def on_message(client:mqtt.Client, userdata, msg):
    global publishedWindow
    print(f"{msg.topic} {str(msg.payload)}")
    publishedWindow = json.loads(msg.payload)
    return

def on_disconnect(client:mqtt.Client, userdata, rc):
    print(f"Disconnected with result code {rc}")
    return

## Get active window functions
def getActiveWindow() -> dict:
    """
    Get the currently active window.
    Returns
    -------
    dict:
        Name of the currently active window.
    """
    import sys
    active_window_name = None
    if sys.platform in ['linux', 'linux2']:
        sysPlatform = 'linux'
        # Alternatives: http://unix.stackexchange.com/q/38867/4784
        try:
            import wnck
        except ImportError:
            logging.info("wnck not installed")
            wnck = None
        if wnck is not None:
            screen = wnck.screen_get_default()
            screen.force_update()
            window = screen.get_active_window()
            if window is not None:
                pid = window.get_pid()
                with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                    active_window_name = f.read()
        else:
            try:
                from gi.repository import Gtk, Wnck
                gi = "Installed"
            except ImportError:
                logging.info("gi.repository not installed")
                gi = None
            if gi is not None:
                Gtk.init([])  # necessary if not using a Gtk.main() loop
                screen = Wnck.Screen.get_default()
                screen.force_update()  # recommended per Wnck documentation
                active_window = screen.get_active_window()
                pid = active_window.get_pid()
                with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                    active_window_name = f.read()
    elif sys.platform in ['Windows', 'win32', 'cygwin']:
        sysPlatform = "windows"
        # http://stackoverflow.com/a/608814/562769
        import win32gui
        import win32process
        from wmi import WMI
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
    elif sys.platform in ['Mac', 'darwin', 'os2', 'os2emx']:
        sysPlatform = "mac"
        # http://stackoverflow.com/a/373310/562769
        from AppKit import NSWorkspace
        active_window_name = (NSWorkspace.sharedWorkspace()
                              .activeApplication()['NSApplicationName'])
    else:
        sysPlatform = None
        print("sys.platform={platform} is unknown. Please report."
              .format(platform=sys.platform))
        print(sys.version)
    return {"name": active_window_name, "platform": sysPlatform} 

if __name__ == '__main__':
    try:
        activeWindow = {}
        sendMessage("Connected\n")
        while True:
            currentWindow = getActiveWindow()
            if activeWindow != currentWindow:
                activeWindow = currentWindow
                print(activeWindow)

    except KeyboardInterrupt:
        print("")
        print("Caught interrupt, exiting...")