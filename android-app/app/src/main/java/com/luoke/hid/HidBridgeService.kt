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
        val chan = NotificationChannel(CHANNEL_ID, "HID 桥接", NotificationManager.IMPORTANCE_LOW)
        getSystemService(NotificationManager::class.java).createNotificationChannel(chan)
        val ntf = Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("洛克 HID 桥")
            .setContentText("运行中")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .build()
        startForeground(1, ntf)

        bt.onStatus = { s -> sendBroadcast(Intent(STATUS_UPDATE).putExtra("text", s).setPackage(packageName)) }
        bt.onConnected = { _, d ->
            updateNtf("已连接: ${d.name ?: d.address}")
            sendBroadcast(Intent(STATUS_UPDATE).putExtra("text", "已连接: ${d.name ?: d.address}").setPackage(packageName))
        }
        bt.onDisconnected = {
            updateNtf("已断开")
            sendBroadcast(Intent(STATUS_UPDATE).putExtra("text", "已断开").setPackage(packageName))
        }
        bt.init()

        tcp = TcpServer(8023, executor) { cmdCount++; android.util.Log.d("HidBridge", "cmdCount=$cmdCount"); sendBroadcast(Intent(CMD_UPDATE).apply { putExtra("count", cmdCount); setPackage(packageName) }) }
        tcp?.start()
        updateNtf("TCP:8023 监听中")
        sendBroadcast(Intent(STATUS_UPDATE).putExtra("text", "TCP:8023 监听中").setPackage(packageName))
    }

    private fun updateNtf(text: String) {
        val ntf = Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("洛克 HID 桥")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
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
        const val STATUS_UPDATE = "com.luoke.hid.STATUS_UPDATE"
    }
}
