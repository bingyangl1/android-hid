import os, time, random, sys, signal

FK = os.environ.get("HID_FK", "/dev/hidg0")
FM = os.environ.get("HID_FM", "/dev/hidg1")
BAIL = "/data/local/tmp/hid_bail"

running = True

def stop(_, __):
    global running; running = False

signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)

try:
    fk = os.open(FK, os.O_RDWR)
    fm = os.open(FM, os.O_RDWR)
except OSError as e:
    print(f"无法打开HID设备: {e}", file=sys.stderr)
    sys.exit(1)

count = rate_count = 0
start = rate_start = time.monotonic()
paused = False

try:
    os.unlink(BAIL)
except OSError:
    pass

while running:
    if os.path.exists(BAIL):
        break

    count += 1
    rate_count += 1

    os.write(fm, b"\x01\x00\x00\x00")
    time.sleep(random.randint(165, 185) / 1000)
    os.write(fm, b"\x00\x00\x00\x00")

    time.sleep(random.uniform(0.09, 0.11))

    os.write(fm, b"\x02\x00\x00\x00")
    time.sleep(random.randint(15, 35) / 1000)
    os.write(fm, b"\x00\x00\x00\x00")

    now = time.monotonic()
    if now - rate_start >= 2.0:
        print(f"#{count}  {rate_count/(now-rate_start):.1f}球/秒")
        rate_count = 0
        rate_start = now

elapsed = time.monotonic() - start
avg = count / elapsed if count else 0
print(f"共{count}球  平均{avg:.1f}球/秒" if count else "中断")
os.close(fk)
os.close(fm)
