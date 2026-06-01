package com.luoke.hid

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothHidDevice
import android.bluetooth.BluetoothHidDeviceAppQosSettings
import android.bluetooth.BluetoothHidDeviceAppSdpSettings
import android.bluetooth.BluetoothProfile
import android.content.Context
import com.luoke.hid.reports.DescriptorCollection
import com.luoke.hid.reports.MouseReport
import com.luoke.hid.reports.KeyboardReport

class BluetoothController(private val ctx: Context) {

    private val adapter by lazy { BluetoothAdapter.getDefaultAdapter()!! }
    var hidDevice: BluetoothHidDevice? = null
    var hostDevice: BluetoothDevice? = null
    var onConnected: ((BluetoothHidDevice, BluetoothDevice) -> Unit)? = null
    var onDisconnected: (() -> Unit)? = null

    fun init() {
        if (hidDevice != null) return
        adapter.getProfileProxy(ctx, serviceListener, BluetoothProfile.HID_DEVICE)
    }

    private val serviceListener = object : BluetoothProfile.ServiceListener {
        override fun onServiceConnected(profile: Int, proxy: BluetoothProfile) {
            if (profile != BluetoothProfile.HID_DEVICE) return
            val hid = proxy as? BluetoothHidDevice ?: return
            hidDevice = hid
            hid.registerApp(
                BluetoothHidDeviceAppSdpSettings(
                    "LUOKE HID",
                    "LUOKE Bluetooth HID Bridge",
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
                { },
                hidCallback
            )
            adapter.setScanMode(BluetoothAdapter.SCAN_MODE_CONNECTABLE_DISCOVERABLE, 300000)
        }

        override fun onServiceDisconnected(profile: Int) {
            if (profile == BluetoothProfile.HID_DEVICE) hidDevice = null
        }
    }

    private val hidCallback = object : BluetoothHidDevice.Callback() {
        override fun onConnectionStateChanged(device: BluetoothDevice?, state: Int) {
            when (state) {
                BluetoothProfile.STATE_CONNECTED -> {
                    if (device != null) {
                        hostDevice = device
                        hidDevice?.let { onConnected?.invoke(it, device) }
                    }
                }
                BluetoothProfile.STATE_DISCONNECTED -> {
                    hostDevice = null
                    onDisconnected?.invoke()
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
        hostDevice?.let { hidDevice?.disconnect(it) }
        hidDevice?.let {
            try { it.unregisterApp() } catch (_: Exception) {}
        }
        hidDevice?.let { adapter.closeProfileProxy(BluetoothProfile.HID_DEVICE, it) }
        hidDevice = null
        hostDevice = null
    }
}
