"""Villain hand ranges for Short Deck Hold'em (36-card deck, 6-A).

Key differences from standard:
- No 22-55 pocket pairs (2-5 removed)
- Ranges are ~1.5-2x wider (equity is flatter)
- Suited connectors gain value (Flush > Full House)
"""

SHORTDECK_RANGES = {
    # (rank1, rank2, suited_flag): rank is in standard encoding (0-12)
    # suited=True → suited only; False → offsuit only; None → both
    "UTG": [
        ((12, 12), None),  # AA
        ((11, 11), None),  # KK
        ((10, 10), None),  # QQ
        ((9, 9), None),    # JJ
        ((8, 8), None),    # TT
        ((7, 7), None),    # 99
        ((6, 6), None),    # 88
        ((5, 5), None),    # 77
        ((4, 4), None),    # 66
        ((12, 11), True),  # AKs
        ((12, 11), False), # AKo
        ((12, 10), True),  # AQs
        ((12, 9), True),   # AJs
        ((11, 10), True),  # KQs
        ((11, 9), True),   # KJs
        ((12, 10), False), # AQo
    ],
    "MP": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None),
        ((6, 6), None), ((5, 5), None), ((4, 4), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((11, 10), True), ((11, 9), True), ((11, 8), True),
        ((10, 9), True), ((10, 8), True), ((9, 8), True),
        ((8, 7), True), ((7, 6), True),
        ((12, 10), False), ((12, 9), False), ((11, 10), False),
    ],
    "HJ": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None),
        ((6, 6), None), ((5, 5), None), ((4, 4), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((12, 6), True), ((12, 5), True),
        ((11, 10), True), ((11, 9), True), ((11, 8), True),
        ((10, 9), True), ((10, 8), True), ((9, 8), True),
        ((8, 7), True), ((7, 6), True), ((6, 5), True),
        ((12, 10), False), ((12, 9), False), ((11, 10), False),
        ((10, 9), False),
    ],
    "CO": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None),
        ((6, 6), None), ((5, 5), None), ((4, 4), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((12, 6), True), ((12, 5), True), ((12, 4), True),
        ((11, 10), True), ((11, 9), True), ((11, 8), True),
        ((11, 7), True), ((10, 9), True), ((10, 8), True),
        ((9, 8), True), ((8, 7), True), ((7, 6), True), ((6, 5), True),
        ((12, 10), False), ((12, 9), False), ((11, 10), False),
        ((10, 9), False), ((9, 8), False),
    ],
    "BTN": [
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None),
        ((6, 6), None), ((5, 5), None), ((4, 4), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((12, 6), True), ((12, 5), True), ((12, 4), True),
        ((11, 10), True), ((11, 9), True), ((11, 8), True),
        ((11, 7), True), ((11, 6), True),
        ((10, 9), True), ((10, 8), True), ((10, 7), True),
        ((9, 8), True), ((9, 7), True), ((8, 7), True),
        ((7, 6), True), ((6, 5), True), ((5, 4), True),
        ((12, 10), False), ((12, 9), False), ((11, 10), False),
        ((10, 9), False), ((9, 8), False), ((8, 7), False),
        ((12, 8), False), ((11, 9), False),
    ],
    "SB": [
        # SB is even wider in short deck (similar to BTN but slightly tighter)
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None),
        ((6, 6), None), ((5, 5), None), ((4, 4), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((12, 6), True), ((12, 5), True), ((12, 4), True),
        ((11, 10), True), ((11, 9), True), ((11, 8), True),
        ((11, 7), True), ((10, 9), True), ((10, 8), True),
        ((9, 8), True), ((8, 7), True), ((7, 6), True), ((6, 5), True),
        ((12, 10), False), ((12, 9), False), ((11, 10), False),
        ((10, 9), False), ((9, 8), False), ((8, 7), False),
    ],
    "BB": [
        # BB defends VERY wide in short deck
        ((12, 12), None), ((11, 11), None), ((10, 10), None),
        ((9, 9), None), ((8, 8), None), ((7, 7), None),
        ((6, 6), None), ((5, 5), None), ((4, 4), None),
        ((12, 11), True), ((12, 11), False), ((12, 10), True),
        ((12, 9), True), ((12, 8), True), ((12, 7), True),
        ((12, 6), True), ((12, 5), True), ((12, 4), True),
        ((11, 10), True), ((11, 9), True), ((11, 8), True),
        ((11, 7), True), ((11, 6), True), ((11, 5), True),
        ((10, 9), True), ((10, 8), True), ((10, 7), True),
        ((9, 8), True), ((9, 7), True), ((8, 7), True),
        ((7, 6), True), ((6, 5), True), ((5, 4), True),
        ((12, 10), False), ((12, 9), False), ((11, 10), False),
        ((10, 9), False), ((9, 8), False), ((8, 7), False),
        ((12, 8), False), ((11, 9), False), ((10, 8), False),
        ((12, 7), False), ((12, 4), False),
    ],
}
