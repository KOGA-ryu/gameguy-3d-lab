"""CP437-oriented palette constants."""

from __future__ import annotations


# Light-to-dark ramps. They are Unicode renderings of classic DOS/CP437 glyphs.
CP437_SHADE_RAMP = " .░▒▓█"
CP437_BLOCK_RAMP = " ░▒▓█"
CP437_DENSE_RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$█"
CLASSIC_ASCII_RAMP = " .:-=+*#%@"
BINARY_RAMP = " █"


CP437_ENCODABLE_FALLBACKS = {
    "─": "-",
    "│": "|",
    "░": "\xb0",
    "▒": "\xb1",
    "▓": "\xb2",
    "█": "\xdb",
}
