"""
手机端重复丢球序列 v2 - 文件句柄保持在循环外，降低每次丢球开销

参数:
  1. n:      丢球次数 (默认 10)
  2. t1_ms:  左键按住时间 (默认 175)
  3. gap_ms: 左键到 Shift 间隔 (默认 50)
  4. t2_ms:  Shift 按住时间 (默认 35)
  5. iv_ms:  每次丢球间隔 (默认 500)
"""
import os, time, sys

m = "/dev/hidg1"
k = "/dev/hidg0"

n    = int(sys.argv[1])  if len(sys.argv) > 1 else 10
t1   = int(sys.argv[2])  / 1000 if len(sys.argv) > 2 else 0.175
gap  = int(sys.argv[3])  / 1000 if len(sys.argv) > 3 else 0.05
t2   = int(sys.argv[4])  / 1000 if len(sys.argv) > 4 else 0.035
iv   = int(sys.argv[5])  / 1000 if len(sys.argv) > 5 else 0.5

fm = os.open(m, os.O_WRONLY)
fk = os.open(k, os.O_WRONLY)

for i in range(n):
    os.write(fm, bytes([1, 0, 0, 0]))
    time.sleep(t1)
    os.write(fm, bytes([0, 0, 0, 0]))
    time.sleep(gap)
    os.write(fk, bytes([0x02, 0, 0, 0, 0, 0, 0, 0]))
    time.sleep(t2)
    os.write(fk, bytes([0, 0, 0, 0, 0, 0, 0, 0]))
    if i < n - 1:
        time.sleep(iv)

os.close(fm)
os.close(fk)
