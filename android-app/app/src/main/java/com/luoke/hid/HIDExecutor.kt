package com.luoke.hid

import com.luoke.hid.reports.KeyboardReport
import com.luoke.hid.reports.MouseReport
import kotlinx.coroutines.delay

class HIDExecutor(private val bt: BluetoothController) {

    private var mouseState = 0
    private val mouseReport = MouseReport()
    private val keyboardReport = KeyboardReport()

    private fun sendMouse(buttons: Int? = null) {
        if (buttons != null) mouseState = buttons
        mouseReport.let { r ->
            r.leftButton = mouseState and 1 != 0
            r.rightButton = mouseState and 2 != 0
            r.middleButton = mouseState and 4 != 0
            r.x1Button = mouseState and 8 != 0
            r.x2Button = mouseState and 16 != 0
            bt.sendMouseReport(r)
        }
    }

    private fun sendKeyboard(mod: Int, key: Int) {
        keyboardReport.reset()
        keyboardReport.leftControl = mod and 0x01 != 0
        keyboardReport.leftShift = mod and 0x02 != 0
        keyboardReport.leftAlt = mod and 0x04 != 0
        keyboardReport.leftGui = mod and 0x08 != 0
        keyboardReport.rightControl = mod and 0x10 != 0
        keyboardReport.rightShift = mod and 0x20 != 0
        keyboardReport.rightAlt = mod and 0x40 != 0
        keyboardReport.rightGui = mod and 0x80 != 0
        if (key > 0) keyboardReport.key1 = key.toByte()
        bt.sendKeyboardReport(keyboardReport)
    }

    suspend fun exec(cmd: CommandParser.Command): String {
        return try {
            when (cmd.type) {
                "ping" -> "pong"

                "mclick" -> {
                    val btn = CommandParser.parseMouseButton(cmd.args.getOrElse(0) { "left" })
                    val hold = cmd.args.getOrNull(1)?.toIntOrNull() ?: 40
                    sendMouse(btn); delay(hold.toLong())
                    sendMouse(0)
                    if (mouseState != 0) sendMouse()
                    "ok"
                }

                "mpress" -> {
                    val btn = CommandParser.parseMouseButton(cmd.args.getOrElse(0) { "left" })
                    mouseState = mouseState or btn; sendMouse(); "ok"
                }

                "mrelease" -> {
                    if (cmd.args.isNotEmpty()) {
                        val btn = CommandParser.parseMouseButton(cmd.args[0])
                        mouseState = mouseState and btn.inv()
                    } else {
                        mouseState = 0
                    }
                    sendMouse(); "ok"
                }

                "mmove" -> {
                    val dx = cmd.args.getOrNull(0)?.toIntOrNull() ?: 0
                    val dy = cmd.args.getOrNull(1)?.toIntOrNull() ?: 0
                    val wheel = cmd.args.getOrNull(2)?.toIntOrNull() ?: 0
                    mouseReport.dx = dx
                    mouseReport.dy = dy
                    mouseReport.vScroll = wheel.toByte()
                    mouseReport.hScroll = 0
                    bt.sendMouseReport(mouseReport)
                    mouseReport.dx = 0; mouseReport.dy = 0
                    mouseReport.vScroll = 0
                    "ok"
                }

                "ktap" -> {
                    val (mod, usage) = CommandParser.parseKey(cmd.args.getOrElse(0) { "" })
                    val hold = cmd.args.getOrNull(1)?.toIntOrNull() ?: 40
                    sendKeyboard(mod, usage); delay(hold.toLong()); sendKeyboard(0, 0)
                    "ok"
                }

                "kpress" -> {
                    val (mod, usage) = CommandParser.parseKey(cmd.args.getOrElse(0) { "" })
                    sendKeyboard(mod, usage); "ok"
                }

                "krelease" -> {
                    sendKeyboard(0, 0); "ok"
                }

                "throw" -> {
                    val t1 = (cmd.args.getOrNull(0)?.toIntOrNull() ?: 175).toLong()
                    val gap = (cmd.args.getOrNull(1)?.toIntOrNull() ?: 20).toLong()
                    val t2 = (cmd.args.getOrNull(2)?.toIntOrNull() ?: 35).toLong()
                    sendMouse(1); delay(t1); sendMouse(0); delay(gap)
                    sendKeyboard(0x02, 0); delay(t2); sendKeyboard(0, 0)
                    "ok"
                }

                "bthrow" -> {
                    val n = cmd.args.getOrNull(0)?.toIntOrNull() ?: 10
                    val t1 = (cmd.args.getOrNull(1)?.toIntOrNull() ?: 175).toLong()
                    val gap = (cmd.args.getOrNull(2)?.toIntOrNull() ?: 20).toLong()
                    val t2 = (cmd.args.getOrNull(3)?.toIntOrNull() ?: 35).toLong()
                    val iv = (cmd.args.getOrNull(4)?.toIntOrNull() ?: 500).toLong()
                    repeat(n) {
                        sendMouse(1); delay(t1); sendMouse(0); delay(gap)
                        sendKeyboard(0x02, 0); delay(t2); sendKeyboard(0, 0)
                        if (it < n - 1) delay(iv)
                    }
                    "ok"
                }

                else -> "err:unknown command ${cmd.type}"
            }
        } catch (e: Exception) {
            "err:${e.message}"
        }
    }
}
