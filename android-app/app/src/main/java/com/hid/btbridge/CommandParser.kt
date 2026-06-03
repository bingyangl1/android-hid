package com.hid.btbridge

object CommandParser {

    private val KEY_MAP = mapOf(
        "A" to 4, "B" to 5, "C" to 6, "D" to 7, "E" to 8,
        "F" to 9, "G" to 10, "H" to 11, "I" to 12, "J" to 13,
        "K" to 14, "L" to 15, "M" to 16, "N" to 17, "O" to 18,
        "P" to 19, "Q" to 20, "R" to 21, "S" to 22, "T" to 23,
        "U" to 24, "V" to 25, "W" to 26, "X" to 27, "Y" to 28, "Z" to 29,
        "1" to 30, "2" to 31, "3" to 32, "4" to 33, "5" to 34,
        "6" to 35, "7" to 36, "8" to 37, "9" to 38, "0" to 39,
        "ENTER" to 40, "ESCAPE" to 41, "ESC" to 41, "BACKSPACE" to 42, "BKSP" to 42,
        "TAB" to 43, "SPACE" to 44, "MINUS" to 45, "EQUAL" to 46,
        "LEFTBRACE" to 47, "RIGHTBRACE" to 48, "BACKSLASH" to 49, "BACKSLASH2" to 50,
        "SEMICOLON" to 51, "APOSTROPHE" to 52, "GRAVE" to 53, "COMMA" to 54,
        "DOT" to 55, "SLASH" to 56, "CAPSLOCK" to 57,
        "F1" to 58, "F2" to 59, "F3" to 60, "F4" to 61, "F5" to 62,
        "F6" to 63, "F7" to 64, "F8" to 65, "F9" to 66, "F10" to 67,
        "F11" to 68, "F12" to 69,
        "PRINTSCREEN" to 70, "SCROLLLOCK" to 71, "PAUSE" to 72,
        "INSERT" to 73, "INS" to 73, "HOME" to 74, "PAGEUP" to 75, "PGUP" to 75,
        "DELETE" to 76, "DEL" to 76, "END" to 77, "PAGEDOWN" to 78, "PGDN" to 78,
        "RIGHT" to 79, "LEFT" to 80, "DOWN" to 81, "UP" to 82,
        "NUMLOCK" to 83,
        "NUM_SLASH" to 84, "NUM_ASTERISK" to 85, "NUM_MINUS" to 86,
        "NUM_PLUS" to 87, "NUM_ENTER" to 88, "NUM1" to 89, "NUM2" to 90,
        "NUM3" to 91, "NUM4" to 92, "NUM5" to 93, "NUM6" to 94, "NUM7" to 95,
        "NUM8" to 96, "NUM9" to 97, "NUM0" to 98, "NUM_DOT" to 99,
        "MENU" to 101, "APPS" to 101
    )

    private val MOD_ALIAS = mapOf(
        "LCTRL" to 0x01, "RCTRL" to 0x10,
        "CTRL" to 0x01,
        "LSHIFT" to 0x02, "RSHIFT" to 0x20,
        "SHIFT" to 0x02,
        "LALT" to 0x04, "RALT" to 0x40,
        "ALT" to 0x04,
        "LGUI" to 0x08, "RGUI" to 0x80,
        "GUI" to 0x08, "LWIN" to 0x08, "RWIN" to 0x80, "WIN" to 0x08
    )

    data class Command(
        val type: String,
        val args: List<String>
    )

    fun parse(line: String): Command? {
        val s = line.trim().lowercase()
        if (s.isEmpty() || s.startsWith("#")) return null
        val parts = s.split(":")
        return Command(parts[0], parts.drop(1))
    }

    fun parseKey(name: String): Pair<Int, Int> {
        val upper = name.uppercase()
        MOD_ALIAS[upper]?.let { return it to 0 }
        KEY_MAP[upper]?.let { return 0 to it }
        if (upper.length == 1 && upper[0] in 'A'..'Z') {
            return 0 to (KEY_MAP[upper] ?: 0)
        }
        return 0 to 0
    }

    fun parseMouseButton(name: String): Int {
        return when (name.lowercase()) {
            "left" -> 1; "right" -> 2; "middle" -> 4; "x1" -> 8; "x2" -> 16
            else -> 1
        }
    }
}
