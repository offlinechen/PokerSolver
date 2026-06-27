"""Pre-built villain hand ranges per position and mode."""

STANDARD_9MAX_RANGES = {
    # (rank1, rank2, suited_flag): suited=True → suited only; False → offsuit only; None → both
    "UTG": [
        ((12, 12), None),  # AA
        ((11, 11), None),  # KK
        ((10, 10), None),  # QQ
        ((9, 9), None),    # JJ
        ((8, 8), None),    # TT
        ((7, 7), None),    # 99
        ((12, 11), True),  # AKs
        ((12, 11), False), # AKo
        ((12, 10), True),  # AQs
        ((11, 10), True),  # KQs
    ],
    "UTG1": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((11, 10), True), ((11, 9), True),
        ((12, 10), False),
    ],
    "UTG2": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((11, 10), True),
        ((11, 9), True), ((10, 9), True),
        ((12, 10), False), ((12, 9), False),
    ],
    "MP": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((11, 10), True),
        ((11, 9), True), ((10, 9), True), ((10, 8), True),
        ((9, 8), True), ((12, 10), False),
    ],
    "HJ": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
        ((5, 5), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((11, 10), True), ((11, 9), True), ((10, 9), True),
        ((10, 8), True), ((9, 8), True), ((8, 7), True),
        ((12, 10), False), ((11, 10), False),
    ],
    "CO": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
        ((5, 5), None), ((4, 4), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((12, 6), True), ((12, 5), True),
        ((11, 10), True), ((11, 9), True), ((10, 9), True),
        ((10, 8), True), ((9, 8), True), ((8, 7), True), ((7, 6), True),
        ((12, 10), False), ((11, 10), False),
        ((12, 4), True), ((12, 3), True),
    ],
    "BTN": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
        ((5, 5), None), ((4, 4), None), ((3, 3), None), ((2, 2), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((12, 6), True), ((12, 5), True), ((12, 4), True),
        ((12, 3), True), ((12, 2), True),
        ((11, 10), True), ((11, 9), True), ((10, 9), True),
        ((10, 8), True), ((9, 8), True), ((8, 7), True), ((7, 6), True),
        ((6, 5), True), ((5, 4), True),
        ((12, 10), False), ((11, 10), False), ((10, 9), False),
        ((12, 9), False), ((11, 9), False),
    ],
    "SB": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
        ((5, 5), None), ((4, 4), None), ((3, 3), None), ((2, 2), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((12, 6), True), ((12, 5), True), ((12, 4), True),
        ((12, 3), True), ((12, 2), True),
        ((11, 10), True), ((11, 9), True), ((10, 9), True),
        ((10, 8), True), ((9, 8), True), ((8, 7), True), ((7, 6), True),
        ((6, 5), True), ((5, 4), True),
        ((12, 10), False), ((11, 10), False), ((10, 9), False),
        ((12, 9), False), ((11, 9), False), ((9, 8), False),
    ],
    "BB": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
        ((5, 5), None), ((4, 4), None), ((3, 3), None), ((2, 2), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((12, 6), True), ((12, 5), True), ((12, 4), True),
        ((12, 3), True), ((12, 2), True),
        ((11, 10), True), ((11, 9), True), ((10, 9), True),
        ((10, 8), True), ((9, 8), True), ((8, 7), True), ((7, 6), True),
        ((6, 5), True), ((5, 4), True),
        ((12, 10), False), ((11, 10), False), ((10, 9), False),
        ((12, 9), False), ((11, 9), False), ((9, 8), False),
        ((12, 3), False), ((10, 8), False), ((12, 2), False),
    ],
}

# Alias for backward compatibility — the 7-position table used by original TexasSolver
STANDARD_RANGES = STANDARD_9MAX_RANGES
