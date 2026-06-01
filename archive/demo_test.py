from hid_device import HIDInput
import time

dev = HIDInput()
print(f"Transport: {dev.transport_name}")

print("Left 170ms...")
dev.mouse.click("left", 170)

print("Wait 130ms...")
time.sleep(0.13)

print("Right 25ms...")
dev.mouse.click("right", 25)

print("Done")
