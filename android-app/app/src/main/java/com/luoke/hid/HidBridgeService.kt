package com.luoke.hid

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder

class HidBridgeService : Service() {

    private val bt = BluetoothController(this)
    private val executor = HIDExecutor(bt)
    private var tcp: TcpServer? = null
    private var cmdCount = 0

    override fun onCreate() {
        super.onCreate()
        val chan = NotificationChannel(CHANNEL_ID, "HID Bridge", NotificationManager.IMPORTANCE_LOW)
        getSystemService(NotificationManager::class.java).createNotificationChannel(chan)
        val ntf = Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("LUOKE HID Bridge")
            .setContentText("Running")
            .setSmallIcon(android.R.drawable.ic_menu_device)
            .build()
        startForeground(1, ntf)

        bt.init()
        bt.onConnected = { _, _ -> updateNtf("Bluetooth connected") }
        bt.onDisconnected = { updateNtf("Bluetooth disconnected") }

        tcp = TcpServer(8023, executor) { cmdCount++; sendBroadcast(Intent(CMD_UPDATE).apply { putExtra("count", cmdCount) }) }
        tcp?.start()
        updateNtf("Listening TCP:8023")
    }

    private fun updateNtf(text: String) {
        val ntf = Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("LUOKE HID Bridge")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_device)
            .setOngoing(true)
            .build()
        startForeground(1, ntf)
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        tcp?.stop()
        bt.disconnect()
        super.onDestroy()
    }

    companion object {
        const val CHANNEL_ID = "hid_bridge"
        const val CMD_UPDATE = "com.luoke.hid.CMD_UPDATE"
    }
}
