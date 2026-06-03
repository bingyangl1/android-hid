package com.hid.btbridge.reports

import kotlin.experimental.and
import kotlin.experimental.or

class KeyboardReport(val bytes: ByteArray = ByteArray(3) { 0 }) {

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

    var key1: Byte
        get() = bytes[2]
        set(v) { bytes[2] = v }

    fun reset() = bytes.fill(0)

    companion object {
        const val ID = 8
    }
}
