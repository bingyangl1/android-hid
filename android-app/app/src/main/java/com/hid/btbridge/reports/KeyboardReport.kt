package com.hid.btbridge.reports

import kotlin.experimental.and
import kotlin.experimental.or

class KeyboardReport(val bytes: ByteArray = ByteArray(8) { 0 }) {
    // bytes[0] = modifier bits
    // bytes[1] = reserved
    // bytes[2..7] = key1..key6 (HID usage codes)

    var leftControl: Boolean
        get() = bytes[0] and 0b1 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b1 else bytes[0] and 0b11111110.toByte() }
    var leftShift: Boolean
        get() = bytes[0] and 0b10 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b10 else bytes[0] and 0b11111101.toByte() }
    var leftAlt: Boolean
        get() = bytes[0] and 0b100 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b100 else bytes[0] and 0b11111011.toByte() }
    var leftGui: Boolean
        get() = bytes[0] and 0b1000 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b1000 else bytes[0] and 0b11110111.toByte() }
    var rightControl: Boolean
        get() = bytes[0] and 0b10000 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b10000 else bytes[0] and 0b11101111.toByte() }
    var rightShift: Boolean
        get() = bytes[0] and 0b100000 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b100000 else bytes[0] and 0b11011111.toByte() }
    var rightAlt: Boolean
        get() = bytes[0] and 0b1000000 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b1000000 else bytes[0] and 0b10111111.toByte() }
    var rightGui: Boolean
        get() = bytes[0] and 0b10000000.toByte() != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b10000000.toByte() else bytes[0] and 0b01111111 }

    fun addKey(usage: Int): Boolean {
        if (usage <= 0) return false
        val b = usage.toByte()
        // already in report
        for (i in 2..7) if (bytes[i] == b) return true
        // find empty slot
        for (i in 2..7) if (bytes[i] == 0.toByte()) { bytes[i] = b; return true }
        return false // 6 keys already pressed
    }

    fun removeKey(usage: Int): Boolean {
        if (usage <= 0) return false
        val b = usage.toByte()
        for (i in 2..7) {
            if (bytes[i] == b) { bytes[i] = 0; return true }
        }
        return false
    }

    fun hasKey(usage: Int): Boolean {
        val b = usage.toByte()
        for (i in 2..7) if (bytes[i] == b) return true
        return false
    }

    fun setModifiers(mod: Int) {
        bytes[0] = (bytes[0].toInt() and 0xFF00 or (mod and 0xFF)).toByte()
    }

    fun clearModifiers() {
        bytes[0] = (bytes[0].toInt() and 0xFF00).toByte()
    }

    fun reset() = bytes.fill(0)

    companion object {
        const val ID = 8
    }
}
