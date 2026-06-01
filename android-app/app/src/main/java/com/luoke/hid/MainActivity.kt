package com.luoke.hid

import android.bluetooth.BluetoothAdapter
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private var running = false
    private var cmdCount = 0
    private var bluetoothStatus = "初始化中..."

    private val tvBluetooth: TextView get() = findViewById(R.id.tvBluetooth)
    private val tvTcp: TextView get() = findViewById(R.id.tvTcp)
    private val tvCommands: TextView get() = findViewById(R.id.tvCommands)
    private val tvHelp: TextView get() = findViewById(R.id.tvHelp)
    private val btnService: Button get() = findViewById(R.id.btnService)

    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(ctx: Context, intent: Intent) {
            when (intent.action) {
                HidBridgeService.STATUS_UPDATE -> {
                    bluetoothStatus = intent.getStringExtra("text") ?: bluetoothStatus
                    updateUI()
                }
                HidBridgeService.CMD_UPDATE -> {
                    cmdCount = intent.getIntExtra("count", 0)
                    tvCommands.text = "命令数: $cmdCount"
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (checkSelfPermission(android.Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.BLUETOOTH_CONNECT), 100)
            }
            if (checkSelfPermission(android.Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.BLUETOOTH_SCAN), 102)
            }
            if (checkSelfPermission(android.Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.BLUETOOTH_ADVERTISE), 103)
            }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 101)
            }
        }

        val filter = IntentFilter().apply {
            addAction(HidBridgeService.STATUS_UPDATE)
            addAction(HidBridgeService.CMD_UPDATE)
        }
        registerReceiver(receiver, filter, RECEIVER_NOT_EXPORTED)

        btnService.setOnClickListener {
            if (running) stopService() else startService()
        }

        tvHelp.setOnClickListener { showInstructions() }
    }

    override fun onDestroy() {
        unregisterReceiver(receiver)
        super.onDestroy()
    }

    override fun onResume() {
        super.onResume()
        updateUI()
    }

    private fun startService() {
        val adapter = BluetoothAdapter.getDefaultAdapter()
        if (adapter == null || !adapter.isEnabled) {
            AlertDialog.Builder(this)
                .setTitle("需要蓝牙")
                .setMessage("请开启蓝牙以使用 HID 桥接。")
                .setPositiveButton("开启") { _, _ ->
                    startActivity(Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE))
                }
                .setNegativeButton("取消", null)
                .show()
            return
        }
        val intent = Intent(this, HidBridgeService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
        running = true
        bluetoothStatus = "启动中..."
        updateUI()
    }

    private fun stopService() {
        stopService(Intent(this, HidBridgeService::class.java))
        running = false
        bluetoothStatus = "已停止"
        updateUI()
    }

    private fun updateUI() {
        btnService.text = if (running) "停止" else "启动"
        tvBluetooth.text = "蓝牙: $bluetoothStatus"
        tvTcp.text = if (running) "TCP: 监听 :8023" else "TCP: 已停止"
    }

    private fun showInstructions() {
        AlertDialog.Builder(this)
            .setTitle("如何配对")
            .setMessage(
                "此 App 让手机充当蓝牙键盘+鼠标。\n\n" +
                "1. 点「启动」（手机变成可被发现 5 分钟）\n" +
                "2. 在电脑端：蓝牙设置 → 添加设备\n" +
                "3. 找到本手机（显示为 OnePlus 9RT 或 LUOKE HID）\n" +
                "4. 选择它 → 配对\n" +
                "5. App 显示「已连接: 电脑名」\n\n" +
                "注意：必须从电脑侧发起配对，而不是从手机侧！"
            )
            .setPositiveButton("知道了", null)
            .show()
    }
}
