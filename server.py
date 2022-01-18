from adafruit_board_toolkit.circuitpython_serial import data_comports
import json
import logging
import paho.mqtt.client as mqtt
from secrets import secret
import serial
import sys
import time

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

SUBSCRIBE_TOPIC = "macropad/focus/#"

## Serial connection functions
def DetectPort() -> str:
    comports = data_comports()
    ports = [
        comport.device for comport in comports
        if comport.description.startswith("Macropad")
    ]
    if len(ports) > 0:
        print(ports[0])
        return ports[0]
    else:
        raise RuntimeError("Unable to find MacroPad")

def SendMessage(message:str):
    port = DetectPort()
    with serial.Serial(port=port) as s:
        print(f"s.out_waiting = {s.out_waiting}")
        s.reset_output_buffer()
        s.write(message)
    return

## MQTT functions
def on_connect(client:mqtt.Client, userdata, flags:dict, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(SUBSCRIBE_TOPIC)
    return

def on_publish(client:mqtt.Client, userdata, mid):
    # print(f"Publish to topic {mid}")
    return

def on_message(client:mqtt.Client, userdata, msg):
    global publishedWindow
    # print(f"{msg.topic} {str(msg.payload)}")
    SendMessage(msg.payload)
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
        activeApplication = NSWorkspace.sharedWorkspace().activeApplication()
        if activeApplication is None:
            return None
        active_window_name = activeApplication['NSApplicationName']
    else:
        sysPlatform = None
        print("sys.platform={platform} is unknown. Please report."
              .format(platform=sys.platform))
        print(sys.version)
    return {"name": active_window_name, "platform": sysPlatform} 

if __name__ == '__main__':
    client = mqtt.Client(
        client_id=secret['computerName'],
        transport="websockets",
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.tls_set()
    client.username_pw_set(secret['mqttUsername'], secret['mqttPassword'])
    client.connect(secret['mqttURL'], port=secret['mqttPort'])
    client.loop_start()
    activeWindow = {}
    try:
        while True:
            currentWindow = getActiveWindow()
            if activeWindow != currentWindow and currentWindow is not None:
                activeWindow = currentWindow
                client.publish(
                    topic=f"macropad/focus/{secret['computerName']}",
                    payload=json.dumps(activeWindow)
                )

    except KeyboardInterrupt:
        print("")
        print("Caught interrupt, exiting...")