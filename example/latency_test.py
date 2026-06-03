"""延迟测试示例"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PC.hid_device import HIDInput

# 开启延迟显示
dev = HIDInput(show_latency=True)
print(f"Transport: {dev.transport_name}")

# 连续 ping 10 次
for i in range(10):
    dev.cmd("ping")

# 输出统计
print()
print(dev.latency_str())
# → avg=4.5ms min=3.8ms max=5.2ms p50=4.5ms p99=5.2ms n=10

# 获取结构化数据
stats = dev.latency_stats()
print(f"平均延迟: {stats['avg']:.1f}ms")
print(f"P99 延迟: {stats['p99']:.1f}ms")
