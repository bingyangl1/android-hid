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
    private var bluetoothOk = false
    private var hostName = "none"

    private val tvBluetooth: TextView get() = findViewById(R.id.tvBluetooth)
    private val tvTcp: TextView get() = findViewById(R.id.tvTcp)
    private val tvDevice: TextView get() = findViewById(R.id.tvDevice)
    private val tvCommands: TextView get() = findViewById(R.id.tvCommands)
    private val btnService: Button get() = findViewById(R.id.btnService)

    private val cmdReceiver = object : BroadcastReceiver() {
        override fun onReceive(ctx: Context, intent: Intent) {
            cmdCount = intent.getIntExtra("count", 0)
            tvCommands.text = "Commands: $cmdCount"
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (checkSelfPermission(android.Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.BLUETOOTH_CONNECT), 100)
            }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 101)
            }
        }

        registerReceiver(cmdReceiver, IntentFilter(HidBridgeService.CMD_UPDATE), RECEIVER_NOT_EXPORTED)

        btnService.setOnClickListener {
            if (running) stopService() else startService()
        }
    }

    override fun onDestroy() {
        unregisterReceiver(cmdReceiver)
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
                .setTitle("Bluetooth Required")
                .setMessage("Please enable Bluetooth to use HID Bridge.")
                .setPositiveButton("Enable") { _, _ ->
                    startActivityForResult(Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE), 200)
                }
                .setNegativeButton("Cancel", null)
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
        updateUI()
    }

    private fun stopService() {
        stopService(Intent(this, HidBridgeService::class.java))
        running = false
        hostName = "none"
        updateUI()
    }

    private fun updateUI() {
        btnService.text = if (running) "STOP" else "START"
        tvBluetooth.text = "Bluetooth: initializing..."
        tvTcp.text = if (running) "TCP: listening on :8023" else "TCP: stopped"
        tvDevice.text = "Device: $hostName"
    }
}
