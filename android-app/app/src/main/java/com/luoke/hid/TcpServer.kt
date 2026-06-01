package com.luoke.hid

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
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
                val ss = ServerSocket(port)
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
            while (running) {
                val line = reader.readLine() ?: break
                val cmd = CommandParser.parse(line) ?: continue
                onCommand()
                val resp = executor.exec(cmd) + "\n"
                writer.write(resp); writer.flush()
            }
        } catch (_: Exception) {
        } finally {
            try { sock.close() } catch (_: Exception) {}
        }
    }
}
