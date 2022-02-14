import board
import digitalio
import storage
import usb_cdc
print("boot")

usb_cdc.enable(console=True, data=True)
button = digitalio.DigitalInOut(board.KEY12)
button.pull = digitalio.Pull.UP

if button.value:
    storage.disable_usb_drive()
