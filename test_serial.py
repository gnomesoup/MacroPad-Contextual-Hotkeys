import time
import serial
from adafruit_board_toolkit.circuitpython_serial import data_comports

def detect_port() -> str:
    comports = data_comports()
    ports = [
        comport.device for comport in comports
        if comport.description.startswith("Macropad")
    ]
    if len(ports) > 0:
        print(f"port = {ports[0]}")
        return ports[0]
    else:
        raise RuntimeError("Unable to find MacroPad")
if __name__ == '__main__':
    try:
        # while True:
        port = detect_port()
        with serial.Serial( port=port,) as macroPadSerial:
            print(f"macroPadSerial.isOpen() = {macroPadSerial.isOpen()}")
            print(f"macroPadSerial.in_waiting = {macroPadSerial.in_waiting}")
            time.sleep(1)
            bytesToWrite = bytes("\n", "utf-8")
            print(bytesToWrite)
            writeReturn = macroPadSerial.write(bytesToWrite)
            print(f"writeReturn = {writeReturn}")

    except KeyboardInterrupt:
        print("")
        print("Caught interrupt, exiting...")