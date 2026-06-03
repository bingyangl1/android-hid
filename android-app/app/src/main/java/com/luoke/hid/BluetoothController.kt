package com.luoke.hid

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothHidDevice
import android.bluetooth.BluetoothHidDeviceAppQosSettings
import android.bluetooth.BluetoothHidDeviceAppSdpSettings
import android.bluetooth.BluetoothProfile
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import com.luoke.hid.reports.DescriptorCollection
import com.luoke.hid.reports.MouseReport
import com.luoke.hid.reports.KeyboardReport

class BluetoothController(private val ctx: Context) {

    private val adapter by lazy { BluetoothAdapter.getDefaultAdapter()!! }
    var hidDevice: BluetoothHidDevice? = null
    var hostDevice: BluetoothDevice? = null
    var onConnected: ((BluetoothHidDevice, BluetoothDevice) -> Unit)? = null
    var onDisconnected: (() -> Unit)? = null
    var onStatus: ((String) -> Unit)? = null

    fun init() {
        if (hidDevice != null) return
        if (!adapter.isEnabled) {
            onStatus?.invoke("蓝牙未开启")
            return
        }
        ctx.registerReceiver(bondReceiver, IntentFilter(BluetoothDevice.ACTION_BOND_STATE_CHANGED))
        onStatus?.invoke("正在请求 HID 代理...")
        adapter.getProfileProxy(ctx, serviceListener, BluetoothProfile.HID_DEVICE)
    }

    private val serviceListener = object : BluetoothProfile.ServiceListener {
        override fun onServiceConnected(profile: Int, proxy: BluetoothProfile) {
            if (profile != BluetoothProfile.HID_DEVICE) return
            val hid = proxy as? BluetoothHidDevice ?: return
            hidDevice = hid

            val ok = hid.registerApp(
                BluetoothHidDeviceAppSdpSettings(
                    "LUOKE HID",
                    "蓝牙 HID 键盘鼠标",
                    "luoke-hid-bt",
                    BluetoothHidDevice.SUBCLASS1_COMBO,
                    DescriptorCollection.MOUSE_KEYBOARD_COMBO
                ),
                null,
                BluetoothHidDeviceAppQosSettings(
                    BluetoothHidDeviceAppQosSettings.SERVICE_BEST_EFFORT,
                    800, 9, 0, 11250,
                    BluetoothHidDeviceAppQosSettings.MAX
                ),
                java.util.concurrent.Executors.newSingleThreadExecutor(),
                hidCallback
            )

            if (ok) {
                onStatus?.invoke("HID 已注册，正在开启可被发现...")
                try {
                    Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE).also {
                        it.putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION, 300)
                        it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        ctx.startActivity(it)
                    }
                } catch (_: Exception) {
                    onStatus?.invoke("HID 已注册（请手动开启蓝牙可被发现）")
                }
            } else {
                onStatus?.invoke("HID 注册失败")
            }
        }

        override fun onServiceDisconnected(profile: Int) {
            if (profile == BluetoothProfile.HID_DEVICE) {
                hidDevice = null
                onStatus?.invoke("HID 代理已断开")
            }
        }
    }

    private val hidCallback = object : BluetoothHidDevice.Callback() {
        override fun onConnectionStateChanged(device: BluetoothDevice?, state: Int) {
            when (state) {
                BluetoothProfile.STATE_CONNECTED -> {
                    if (device != null) {
                        hostDevice = device
                        onStatus?.invoke("已连接: ${device.name ?: device.address}")
                        hidDevice?.let { onConnected?.invoke(it, device) }
                    }
                }
                BluetoothProfile.STATE_DISCONNECTED -> {
                    hostDevice = null
                    onStatus?.invoke("已断开，等待重连...")
                    onDisconnected?.invoke()
                    reDiscoverable()
                }
            }
        }
        override fun onGetReport(device: BluetoothDevice?, type: Byte, id: Byte, bufferSize: Int) {}
        override fun onSetReport(device: BluetoothDevice?, type: Byte, id: Byte, data: ByteArray?) {}
    }

    fun sendMouseReport(report: MouseReport): Boolean {
        val hid = hidDevice ?: return false
        val host = hostDevice ?: return false
        return hid.sendReport(host, MouseReport.ID, report.bytes)
    }

    fun sendKeyboardReport(report: KeyboardReport): Boolean {
        val hid = hidDevice ?: return false
        val host = hostDevice ?: return false
        return hid.sendReport(host, KeyboardReport.ID, report.bytes)
    }

    fun disconnect() {
        ctx.unregisterReceiver(bondReceiver)
        hostDevice?.let { hidDevice?.disconnect(it) }
        hidDevice?.let {
            try { it.unregisterApp() } catch (_: Exception) {}
        }
        hidDevice?.let { adapter.closeProfileProxy(BluetoothProfile.HID_DEVICE, it) }
        hidDevice = null
        hostDevice = null
    }

    private fun reDiscoverable() {
        try {
            Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE).also {
                it.putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION, 300)
                it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                ctx.startActivity(it)
            }
            onStatus?.invoke("等待电脑重连...")
        } catch (_: Exception) {
            onStatus?.invoke("已断开（请手动开启可被发现）")
        }
    }

    private val bondReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (intent.action == BluetoothDevice.ACTION_BOND_STATE_CHANGED) {
                val device = intent.getParcelableExtra<BluetoothDevice>(BluetoothDevice.EXTRA_DEVICE)
                val bondState = intent.getIntExtra(BluetoothDevice.EXTRA_BOND_STATE, BluetoothDevice.BOND_NONE)
                if (bondState == BluetoothDevice.BOND_BONDED && device != null) {
                    onStatus?.invoke("已配对: ${device.name ?: device.address}，等待 HID 连接...")
                }
            }
        }
    }
}
