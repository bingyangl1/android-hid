package com.luoke.hid

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket

class TcpServer(
    private val port: Int,
    private val executor: HIDExecutor,
    private val onCommand: () -> Unit
) {
    private var serverSocket: ServerSocket? = null
    private val scope = CoroutineScope(Dispatchers.IO)
    @Volatile var running = true

    fun start() {
        running = true
        scope.launch {
            try {
                    val ss = ServerSocket(port, 50, InetAddress.getByName("0.0.0.0"))
                serverSocket = ss
                while (running) {
                    try {
                        val sock = ss.accept()
                        scope.launch { handle(sock) }
                    } catch (_: Exception) {
                        if (!running) break
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun stop() {
        running = false
        try { serverSocket?.close() } catch (_: Exception) {}
        serverSocket = null
    }

    private suspend fun handle(sock: Socket) {
        try {
            sock.soTimeout = 0
            val reader = BufferedReader(InputStreamReader(sock.getInputStream()))
            val writer = OutputStreamWriter(sock.getOutputStream())
            android.util.Log.d("TcpServer", "client connected: ${sock.remoteSocketAddress}")
            while (running) {
                val line = reader.readLine() ?: break
                android.util.Log.d("TcpServer", "recv: $line")
                val cmd = CommandParser.parse(line) ?: continue
                onCommand()
                val resp = executor.exec(cmd) + "\n"
                writer.write(resp); writer.flush()
            }
        } catch (e: Exception) {
            android.util.Log.e("TcpServer", "handle error", e)
        } finally {
            try { sock.close() } catch (_: Exception) {}
        }
    }
}
