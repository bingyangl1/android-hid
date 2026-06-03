package com.hid.btbridge.reports

import kotlin.experimental.and
import kotlin.experimental.or

class MouseReport(val bytes: ByteArray = ByteArray(7) { 0 }) {

    var leftButton: Boolean
        get() = bytes[0] and 0b1 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b1 else bytes[0] and 0b11111110.toByte() }
    var rightButton: Boolean
        get() = bytes[0] and 0b10 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b10 else bytes[0] and 0b11111101.toByte() }
    var middleButton: Boolean
        get() = bytes[0] and 0b100 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b100 else bytes[0] and 0b11111011.toByte() }
    var x1Button: Boolean
        get() = bytes[0] and 0b1000 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b1000 else bytes[0] and 0b11110111.toByte() }
    var x2Button: Boolean
        get() = bytes[0] and 0b10000 != 0.toByte()
        set(v) { bytes[0] = if (v) bytes[0] or 0b10000 else bytes[0] and 0b11101111.toByte() }

    var dx: Int
        get() = (bytes[1].toInt() and 0xFF) or ((bytes[2].toInt() and 0xFF) shl 8)
        set(v) { bytes[1] = (v and 0xFF).toByte(); bytes[2] = ((v shr 8) and 0xFF).toByte() }

    var dy: Int
        get() = (bytes[3].toInt() and 0xFF) or ((bytes[4].toInt() and 0xFF) shl 8)
        set(v) { bytes[3] = (v and 0xFF).toByte(); bytes[4] = ((v shr 8) and 0xFF).toByte() }

    var vScroll: Byte
        get() = bytes[5]
        set(v) { bytes[5] = v }
    var hScroll: Byte
        get() = bytes[6]
        set(v) { bytes[6] = v }

    fun reset() = bytes.fill(0)

    companion object {
        const val ID = 4
    }
}
