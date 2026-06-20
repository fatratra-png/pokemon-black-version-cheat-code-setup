#!/usr/bin/env python3
"""
Pokemon Black Save Injector
Injects legendary Pokemon directly into PC boxes of a Gen 5 save file.
The save file is modified in-place.
"""

import struct
import random
import os
import sys

# Gen 4/5 PKM encryption constants
BLOCK_SIZE = 32

# Shuffle inverse tables: for each sv (0-23), maps encrypted block position -> decrypted block position
INVERSE_TABLE = {
    0:  [0, 1, 2, 3], 1:  [0, 1, 3, 2], 2:  [0, 2, 1, 3],
    3:  [0, 3, 1, 2], 4:  [0, 2, 3, 1], 5:  [0, 3, 2, 1],
    6:  [1, 0, 2, 3], 7:  [1, 0, 3, 2], 8:  [2, 0, 1, 3],
    9:  [3, 0, 1, 2], 10: [2, 0, 3, 1], 11: [3, 0, 2, 1],
    12: [1, 2, 0, 3], 13: [1, 3, 0, 2], 14: [2, 1, 0, 3],
    15: [3, 1, 0, 2], 16: [2, 3, 0, 1], 17: [3, 2, 0, 1],
    18: [1, 2, 3, 0], 19: [1, 3, 2, 0], 20: [2, 1, 3, 0],
    21: [3, 1, 2, 0], 22: [2, 3, 1, 0], 23: [3, 2, 1, 0],
}

ORDER_TABLE = {}
for sv, inv in INVERSE_TABLE.items():
    ORDER_TABLE[sv] = [inv.index(i) for i in range(4)]

LCRNG_MULT = 0x41C64E6D
LCRNG_ADD = 0x6073

def decrypt_stored(raw_136):
    pid = struct.unpack_from('<I', raw_136, 0)[0]
    cksum = struct.unpack_from('<H', raw_136, 6)[0]
    sv = ((pid >> 13) & 0x1F) % 24
    dec = bytearray(raw_136)
    seed = cksum
    for i in range(8, 136, 2):
        seed = (seed * LCRNG_MULT + LCRNG_ADD) & 0xFFFFFFFF
        prng = (seed >> 16) & 0xFFFF
        word = struct.unpack_from('<H', dec, i)[0]
        struct.pack_into('<H', dec, i, word ^ prng)
    blocks = [dec[8+b*BLOCK_SIZE:8+(b+1)*BLOCK_SIZE] for b in range(4)]
    inv = INVERSE_TABLE[sv]
    unshuffled = bytearray()
    for b in range(4):
        unshuffled.extend(blocks[inv[b]])
    for i in range(128):
        dec[8+i] = unshuffled[i]
    return bytes(dec)

def encrypt_stored(plain_136):
    pid = struct.unpack_from('<I', plain_136, 0)[0]
    cksum = struct.unpack_from('<H', plain_136, 6)[0]
    sv = ((pid >> 13) & 0x1F) % 24
    enc = bytearray(plain_136)
    blocks = [enc[8+b*BLOCK_SIZE:8+(b+1)*BLOCK_SIZE] for b in range(4)]
    order = ORDER_TABLE[sv]
    shuffled = bytearray()
    for b in range(4):
        shuffled.extend(blocks[order[b]])
    for i in range(128):
        enc[8+i] = shuffled[i]
    seed = cksum
    for i in range(8, 136, 2):
        seed = (seed * LCRNG_MULT + LCRNG_ADD) & 0xFFFFFFFF
        prng = (seed >> 16) & 0xFFFF
        word = struct.unpack_from('<H', enc, i)[0]
        struct.pack_into('<H', enc, i, word ^ prng)
    return bytes(enc)

def calc_checksum(plain_136):
    total = 0
    for i in range(8, 136, 2):
        total += struct.unpack_from('<H', plain_136, i)[0]
    return total & 0xFFFF

# Nature table
NATURES = [
    "Hardy", "Lonely", "Brave", "Adamant", "Naughty",
    "Bold", "Docile", "Relaxed", "Impish", "Lax",
    "Timid", "Hasty", "Serious", "Jolly", "Naive",
    "Modest", "Mild", "Quiet", "Bashful", "Rash",
    "Calm", "Gentle", "Sassy", "Careful", "Quirky"
]

# Move PP values (for moves we commonly use)
MOVE_PP = {
    0: 0,  # empty
    # Fighting
    1: 35,   # Pound
    2: 25,   # Karate Chop
    # Normal
    33: 35,  # Tackle
    34: 20,  # Body Slam
    35: 15,  # Wrap
    36: 20,  # Take Down
    38: 30,  # Double-Edge
    39: 40,  # Tail Whip
    40: 40,  # Leer
    41: 35,  # Bite
    42: 35,  # Growl
    43: 30,  # Roar
    44: 20,  # Sing
    45: 30,  # Supersonic
    46: 15,  # Sonic Boom
    47: 15,  # Disable
    48: 20,  # Acid
    49: 15,  # Ember
    53: 25,  # Flamethrower
    57: 5,   # Surf
    58: 5,   # Ice Beam
    59: 5,   # Blizzard
    61: 10,  # Bubble Beam
    62: 5,   # Aurora Beam
    63: 20,  # Hyper Beam
    64: 35,  # Peck
    65: 35,  # Drill Peck
    66: 20,  # Submission
    67: 25,  # Low Kick
    68: 20,  # Counter
    69: 15,  # Seismic Toss
    70: 20,  # Strength
    71: 15,  # Absorb
    72: 25,  # Mega Drain
    73: 10,  # Leech Seed
    74: 20,  # Growth
    75: 35,  # Razor Leaf
    76: 10,  # Solar Beam
    77: 10,  # Poisonpowder
    78: 15,  # Stun Spore
    79: 15,  # Sleep Powder
    80: 40,  # Petal Dance
    81: 10,  # String Shot
    82: 20,  # Dragon Rage
    83: 20,  # Fire Spin
    84: 15,  # Thunder Shock
    85: 15,  # Thunderbolt
    86: 10,  # Thunder Wave
    87: 10,  # Thunder
    88: 15,  # Rock Throw
    89: 10,  # Earthquake
    90: 15,  # Fissure
    91: 10,  # Dig
    92: 15,  # Toxic
    93: 25,  # Confusion
    94: 20,  # Psychic
    95: 20,  # Hypnosis
    96: 30,  # Meditate
    97: 30,  # Agility
    98: 20,  # Quick Attack
    99: 20,  # Rage
    100: 5,  # Teleport
    102: 15, # Mimic
    103: 10, # Screech
    104: 30, # Double Team
    105: 15, # Recover
    106: 5,  # Harden
    107: 30, # Minimize
    108: 10, # Smokescreen
    109: 5,  # Confuse Ray
    110: 5,  # Withdraw
    111: 40, # Defense Curl
    112: 10, # Barrier
    113: 10, # Light Screen
    114: 30, # Haze
    115: 40, # Reflect
    116: 20, # Focus Energy
    117: 20, # Bide
    118: 20, # Metronome
    119: 10, # Mirror Move
    120: 10, # Self-Destruct
    121: 15, # Egg Bomb
    122: 20, # Lick
    123: 20, # Smog
    124: 15, # Sludge
    125: 10, # Bone Club
    126: 20, # Fire Blast
    127: 10, # Waterfall
    129: 15, # Swift
    130: 20, # Sky Attack
    132: 15, # Constrict
    133: 25, # Amnesia
    134: 20, # Kinesis
    135: 15, # Soft-Boiled
    137: 5,  # Glare
    138: 10, # Dream Eater
    139: 10, # Poison Gas
    140: 30, # Barrage
    141: 20, # Leech Life
    142: 30, # Lovely Kiss
    143: 10, # Sky Attack
    144: 30, # Transform
    145: 10, # Bubble
    146: 20, # Dizzy Punch
    147: 10, # Spore
    148: 30, # Flash
    149: 40, # Psybeam
    150: 20, # Jump Kick
    151: 20, # Hi Jump Kick
    152: 20, # Rollout
    153: 20, # Swords Dance
    154: 5,  # Cut
    155: 30, # Gust
    156: 15, # Wing Attack
    157: 5,  # Whirlwind
    158: 35, # Fly
    159: 5,  # Bind
    160: 20, # Slam
    161: 30, # Vine Whip
    162: 10, # Stomp
    163: 30, # Double Kick
    164: 25, # Mega Kick
    165: 20, # Jump Kick
    166: 10, # Rolling Kick
    168: 20, # Headbutt
    169: 15, # Horn Attack
    170: 10, # Fury Attack
    171: 5,  # Horn Drill
    172: 35, # Tackle (again)
    173: 35, # Poison Sting
    174: 20, # Twineedle
    175: 15, # Pin Missile
    176: 30, # Leer
    177: 30, # Bite
    178: 35, # Growl
    179: 30, # Roar
    180: 20, # Sing
    181: 20, # Peck
    182: 35, # Drill Peck
    183: 20, # Fury Strike
    184: 10, # Submission
    185: 15, # Low Kick
    187: 30, # Absorb
    188: 20, # Mega Drain
    189: 10, # Leech Seed
    190: 25, # Razor Leaf
    200: 35, # Fury Cutter
    207: 30, # Slash
    208: 15, # X-Scissor
    # special moves we'll use
    237: 30, # Hidden Power
    240: 30, # Protect
    241: 10, # Mach Punch
    242: 30, # Scary Face
    244: 30, # Feint Attack
    249: 10, # Outrage
    250: 5,  # Sandstorm
    262: 10, # Superpower
    263: 15, # Endeavor
    272: 10, # Close Combat
    275: 5,  # Thunder Fang
    276: 10, # Ice Fang
    277: 15, # Fire Fang
    278: 15, # Shadow Ball
    288: 15, # Hyper Voice
    290: 30, # DragonBreath
    291: 5,  # Dragon Claw
    292: 10, # Dragon Dance
    293: 10, # Dragon Pulse
    296: 5,  # Aura Sphere
    297: 5,  # Dark Pulse
    298: 20, # Air Slash
    299: 5,  # Brave Bird
    300: 20, # Bug Buzz
    302: 15, # Energy Ball
    303: 20, # Earth Power
    304: 20, # Giga Impact
    311: 10, # Nasty Plot
    313: 15, # Seed Bomb
    329: 5,  # Spacial Rend
    330: 5,  # Roar of Time
    331: 10, # Shadow Force
    332: 10, # Draco Meteor
    333: 5,  # Bullet Seed
    334: 10, # Stone Edge
    338: 5,  # Magma Storm
    340: 5,  # Dark Void
    342: 5,  # Seed Flare
    343: 10, # Ominous Wind
    344: 5,  # Shadow Sneak
    348: 20, # Water Pulse
    349: 10, # Doom Desire
    350: 5,  # Psycho Boost
    352: 10, # Power Gem
    354: 10, # Night Slash
    355: 10, # Air Cutter
    357: 10, # Aqua Tail
    358: 15, # Seed Bomb (again)
    359: 20, # Air Slash (again)
    360: 20, # X-Scissor (again)
    363: 10, # Attack Order
    364: 10, # Defend Order
    365: 10, # Heal Order
    366: 10, # Head Smash
    367: 5,  # Double Hit
    368: 10, # Roar of Time (again)
    369: 5,  # Spacial Rend (again)
    370: 5,  # Lunar Dance
    371: 5,  # Crush Grip
    372: 10, # Magma Storm (again)
    373: 5,  # Dark Void (again)
    374: 5,  # Seed Flare (again)
    375: 5,  # Ominous Wind (again)
    376: 10, # Shadow Force (again)
    377: 5,  # Trick Room
    378: 5,  # Draco Meteor
    379: 20, # Discharge
    380: 30, # Lava Plume
    381: 10, # Leaf Storm
    382: 20, # Power Whip
    383: 20, # Rock Wrecker
    384: 5,  # Cross Poison
    385: 15, # Gunk Shot
    386: 10, # Iron Head
    387: 10, # Magnet Bomb
    388: 15, # Stone Edge (again)
    389: 5,  # Captivate
    390: 15, # Stealth Rock
    391: 20, # Grass Knot
    392: 15, # Chatter
    393: 10, # Judgment
    394: 5,  # Bug Bite
    395: 15, # Charge Beam
    396: 20, # Wood Hammer
    397: 15, # Aqua Jet
    398: 15, # Attack Order (again)
    399: 15, # Defend Order (again)
    400: 10, # Heal Order (again)
    401: 10, # Head Smash (again)
    402: 5,  # Double Hit (again)
    403: 5,  # Roar of Time
    404: 5,  # Spacial Rend
    405: 5,  # Lunar Dance
    406: 5,  # Crush Grip
    407: 10, # Magma Storm
    408: 10, # Dark Void
    409: 5,  # Seed Flare
    410: 10, # Ominous Wind
    411: 10, # Shadow Force
    412: 5,  # Hone Claws
    413: 20, # Wide Guard
    414: 10, # Guard Split
    415: 10, # Power Split
    416: 10, # Wonder Room
    417: 10, # Psyshock
    418: 20, # Venoshock
    419: 10, # Autotomize
    420: 10, # Rage Powder
    421: 10, # Telekinesis
    422: 10, # Magic Room
    423: 15, # Smack Down
    424: 15, # Storm Throw
    425: 15, # Flame Burst
    426: 15, # Sludge Wave
    427: 20, # Quiver Dance
    428: 20, # Heavy Slam
    429: 20, # Synchronoise
    430: 15, # Electro Ball
    431: 15, # Soak
    432: 20, # Flame Charge
    433: 15, # Low Sweep
    434: 15, # Acid Spray
    435: 20, # Foul Play
    436: 10, # Simple Beam
    437: 15, # Round
    438: 15, # Echoed Voice
    439: 10, # Chip Away
    440: 15, # Clear Smog
    441: 10, # Stored Power
    442: 20, # Quick Guard
    443: 10, # Ally Switch
    444: 15, # Scald
    445: 15, # Shell Smash
    446: 20, # Heal Pulse
    447: 10, # Hex
    448: 15, # Sky Drop
    449: 20, # Shift Gear
    450: 10, # Circle Throw
    451: 20, # Incinerate
    452: 15, # Quash
    453: 10, # Acrobatics
    454: 20, # Reflect Type
    455: 10, # Retaliate
    456: 15, # Final Gambit
    457: 15, # Bestow
    458: 20, # Inferno
    459: 10, # Water Pledge
    460: 10, # Fire Pledge
    461: 10, # Grass Pledge
    462: 5,  # Volt Switch
    463: 15, # Bulldoze
    464: 10, # Frost Breath
    465: 15, # Dragon Tail
    466: 5,  # Work Up
    467: 10, # Electroweb
    468: 30, # Wild Charge
    469: 5,  # Drill Run
    470: 10, # Dual Chop
    471: 20, # Heart Stamp
    472: 15, # Horn Leech
    473: 10, # Sacred Sword
    474: 15, # Razor Shell
    475: 10, # Heat Crash
    476: 15, # Leaf Tornado
    477: 25, # Steamroller
    478: 20, # Cotton Guard
    479: 10, # Night Daze
    480: 15, # Psyshock (duplicate)
    481: 10, # Tail Slap
    482: 10, # Hurricane
    483: 20, # Head Charge
    484: 15, # Gear Grind
    485: 5,  # Searing Shot
    486: 5,  # Techno Blast
    487: 5,  # Relic Song
    488: 5,  # Secret Sword
    489: 5,  # Glaciate
    490: 5,  # Bolt Strike
    491: 5,  # Blue Flare
    492: 5,  # Fiery Dance
    493: 5,  # Freeze Shock
    494: 5,  # Ice Burn
    495: 5,  # Snarl
    496: 15, # Icicle Crash
    497: 5,  # V-create
    498: 10, # Fusion Flare
    499: 10, # Fusion Bolt
    500: 20, # Flying Press
}

# Some move PP values that we need
MOVE_PP.update({
    1: 35,    # Pound
    2: 25,    # Karate Chop
    3: 10,    # Double Slap
    4: 15,    # Comet Punch
    5: 25,    # Mega Punch
    6: 20,    # Pay Day
    7: 15,    # Fire Punch
    8: 15,    # Ice Punch
    9: 15,    # Thunder Punch
    10: 35,   # Scratch
    11: 30,   # Vice Grip
    12: 5,    # Guillotine
    13: 25,   # Razor Wind
    14: 10,   # Swords Dance
    15: 20,   # Cut
    16: 35,   # Gust
    17: 25,   # Wing Attack
    18: 20,   # Whirlwind
    19: 15,   # Fly
    20: 20,   # Bind
    21: 20,   # Slam
    22: 10,   # Vine Whip
    23: 20,   # Stomp
    24: 30,   # Double Kick
    25: 15,   # Mega Kick
    26: 20,   # Jump Kick
    27: 25,   # Rolling Kick
    28: 15,   # Sand Attack
    29: 35,   # Headbutt
    30: 25,   # Horn Attack
    31: 20,   # Fury Attack
    32: 5,    # Horn Drill
    33: 35,   # Tackle
    34: 20,   # Body Slam
    35: 20,   # Wrap
    36: 20,   # Take Down
    37: 10,   # Thrash
    38: 15,   # Double-Edge
    39: 30,   # Tail Whip
    40: 30,   # Poison Sting
    41: 35,   # Twineedle
    42: 15,   # Pin Missile
    43: 30,   # Leer
    44: 25,   # Bite
    45: 40,   # Growl
    46: 20,   # Roar
    47: 15,   # Sing
    48: 20,   # Supersonic
    49: 20,   # Sonic Boom
    50: 15,   # Disable
    51: 30,   # Acid
    52: 25,   # Ember
    53: 15,   # Flamethrower
    54: 15,   # Mist
    55: 25,   # Water Gun
    56: 20,   # Hydro Pump
    57: 15,   # Surf
    58: 10,   # Ice Beam
    59: 5,    # Blizzard
    60: 20,   # Psybeam
    61: 20,   # Bubble Beam
    62: 20,   # Aurora Beam
    63: 5,    # Hyper Beam
    64: 35,   # Peck
    65: 20,   # Drill Peck
    66: 25,   # Submission
    67: 20,   # Low Kick
    68: 20,   # Counter
    69: 20,   # Seismic Toss
    70: 15,   # Strength
    71: 25,   # Absorb
    72: 15,   # Mega Drain
    73: 10,   # Leech Seed
    74: 40,   # Growth
    75: 25,   # Razor Leaf
    76: 10,   # Solar Beam
    77: 35,   # Poisonpowder
    78: 30,   # Stun Spore
    79: 15,   # Sleep Powder
    80: 20,   # Petal Dance
    81: 40,   # String Shot
    82: 10,   # Dragon Rage
    83: 15,   # Fire Spin
    84: 20,   # Thunder Shock
    85: 15,   # Thunderbolt
    86: 20,   # Thunder Wave
    87: 10,   # Thunder
    88: 15,   # Rock Throw
    89: 10,   # Earthquake
    90: 5,    # Fissure
    91: 10,   # Dig
    92: 10,   # Toxic
    93: 25,   # Confusion
    94: 10,   # Psychic
    95: 20,   # Hypnosis
    96: 40,   # Meditate
    97: 30,   # Agility
    98: 30,   # Quick Attack
    99: 20,   # Rage
    100: 20,  # Teleport
    101: 20,  # Night Shade
    102: 10,  # Mimic
    103: 40,  # Screech
    104: 15,  # Double Team
    105: 10,  # Recover
    106: 30,  # Harden
    107: 20,  # Minimize
    108: 20,  # Smokescreen
    109: 10,  # Confuse Ray
    110: 30,  # Withdraw
    111: 40,  # Defense Curl
    112: 20,  # Barrier
    113: 30,  # Light Screen
    114: 30,  # Haze
    115: 20,  # Reflect
    116: 30,  # Focus Energy
    117: 10,  # Bide
    118: 10,  # Metronome
    119: 20,  # Mirror Move
    120: 5,   # Self-Destruct
    121: 10,  # Egg Bomb
    122: 30,  # Lick
    123: 20,  # Smog
    124: 20,  # Sludge
    125: 20,  # Bone Club
    126: 5,   # Fire Blast
    127: 15,  # Waterfall
    128: 5,   # Clamp
    129: 20,  # Swift
    130: 5,   # Sky Attack
    131: 15,  # Fire Spin (again)
    132: 20,  # Constrict
    133: 20,  # Amnesia
    134: 15,  # Kinesis
    135: 10,  # Soft-Boiled
    136: 25,  # Hi Jump Kick
    137: 30,  # Glare
    138: 15,  # Dream Eater
    139: 40,  # Poison Gas
    140: 20,  # Barrage
    141: 10,  # Leech Life
    142: 10,  # Lovely Kiss
    143: 5,   # Sky Attack (again)
    144: 10,  # Transform
    145: 30,  # Bubble
    146: 10,  # Dizzy Punch
    147: 15,  # Spore
    148: 20,  # Flash
    149: 30,  # Psybeam
    150: 10,  # Jump Kick
    151: 10,  # Hi Jump Kick (again)
})

def get_pp(move_id):
    """Return PP for a move ID (or 40 if unknown)"""
    return MOVE_PP.get(move_id, 40)

# EXP for level 100 for each growth rate
# These are the total EXP needed to reach level 100
GROWTH_RATES = {
    "erratic": 600000,
    "fast": 800000,
    "medium_fast": 1000000,
    "medium_slow": 1059860,
    "slow": 1250000,
    "fluctuating": 1640000,
}

# EXP for level 100 in Standard (Medium Fast) = 1,000,000
# Most legendaries use Medium Fast or Slow growth
# Let's map species to growth rate
EXP_AT_100 = {
    "medium_fast": 1000000,
    "slow": 1250000,
    "medium_slow": 1059860,
    "fast": 800000,
    "erratic": 600000,
    "fluctuating": 1640000,
}

# Legendary Pokemon species data
# Format: (species_id, name, type1, type2, growth_rate, move_ids)
LEGENDARIES = [
    # Kanto
    (144, "Articuno", "Ice", "Flying", "slow", [58, 155, 130, 47]),  # Ice Beam, Gust, Sky Attack, Sing
    (145, "Zapdos", "Electric", "Flying", "slow", [85, 155, 130, 84]),  # Thunderbolt, Gust, Sky Attack, Thunder Shock
    (146, "Moltres", "Fire", "Flying", "slow", [53, 155, 130, 52]),  # Flamethrower, Gust, Sky Attack, Ember
    (150, "Mewtwo", "Psychic", None, "slow", [94, 60, 65, 149]),  # Psychic, Psybeam, Drill Peck(?), Recover
    (151, "Mew", "Psychic", None, "medium_slow", [94, 60, 65, 149]),  # Psychic, Psybeam, Recover, Transform
    
    # Johto
    (243, "Raikou", "Electric", None, "slow", [85, 97, 84, 86]),  # Thunderbolt, Agility, Thunder Shock, Thunder Wave
    (244, "Entei", "Fire", None, "slow", [53, 126, 97, 52]),  # Flamethrower, Fire Blast, Agility, Ember
    (245, "Suicune", "Water", None, "slow", [57, 58, 48, 55]),  # Surf, Ice Beam, Supersonic, Water Gun
    (249, "Lugia", "Psychic", "Flying", "slow", [94, 58, 97, 155]),  # Psychic, Ice Beam, Agility, Gust
    (250, "Ho-Oh", "Fire", "Flying", "slow", [126, 53, 130, 155]),  # Fire Blast, Flamethrower, Sky Attack, Gust
    
    # Hoenn
    (377, "Regirock", "Rock", None, "slow", [88, 89, 106, 110]),  # Rock Throw, Earthquake, Harden, Withdraw
    (378, "Regice", "Ice", None, "slow", [58, 59, 106, 54]),  # Ice Beam, Blizzard, Harden, Mist
    (379, "Registeel", "Steel", None, "slow", [169, 89, 106, 110]),  # Iron Head-ish... use Headbutt, Earthquake, Harden, Withdraw
    (380, "Latias", "Dragon", "Psychic", "slow", [94, 297, 155, 97]),  # Psychic, Dragon Pulse, Gust, Agility
    (381, "Latios", "Dragon", "Psychic", "slow", [94, 297, 155, 97]),  # Psychic, Dragon Pulse, Gust, Agility
    (382, "Kyogre", "Water", None, "slow", [57, 127, 58, 55]),  # Surf, Waterfall, Ice Beam, Water Gun
    (383, "Groudon", "Ground", None, "slow", [89, 126, 88, 33]),  # Earthquake, Fire Blast, Rock Throw, Tackle
    (384, "Rayquaza", "Dragon", "Flying", "slow", [293, 89, 126, 155]),  # Dragon Pulse, Earthquake, Fire Blast, Gust
    (385, "Jirachi", "Steel", "Psychic", "slow", [94, 94, 65, 149]),  # Psychic, Dream Eater(Drain), Recover, Wish(??)
    
    # Sinnoh
    (480, "Uxie", "Psychic", None, "slow", [94, 93, 97, 149]),  # Psychic, Confusion, Agility, Amnesia
    (481, "Mesprit", "Psychic", None, "slow", [94, 93, 97, 149]),
    (482, "Azelf", "Psychic", None, "slow", [94, 93, 97, 149]),
    (483, "Dialga", "Steel", "Dragon", "slow", [293, 89, 126, 97]),  # Dragon Pulse, Earthquake, Fire Blast, Roar of Time
    (484, "Palkia", "Water", "Dragon", "slow", [293, 57, 58, 97]),  # Dragon Pulse, Surf, Ice Beam, Spacial Rend
    (485, "Heatran", "Fire", "Steel", "slow", [126, 53, 89, 93]),  # Fire Blast, Flamethrower, Earthquake, Lava Plume
    (486, "Regigigas", "Normal", None, "slow", [36, 89, 169, 106]),  # Take Down, Earthquake, Headbutt, Harden
    (487, "Giratina", "Ghost", "Dragon", "slow", [293, 94, 89, 93]),  # Dragon Pulse, Shadow Ball, Earthquake, Shadow Force
    (488, "Cresselia", "Psychic", None, "slow", [94, 135, 93, 60]),  # Psychic, Moonlight (Recover = 105), Confusion, Psybeam
    (489, "Phione", "Water", None, "slow", [57, 55, 97, 127]),
    (490, "Manaphy", "Water", None, "slow", [57, 94, 58, 97]),
    (491, "Darkrai", "Dark", None, "slow", [297, 94, 95, 101]),  # Dark Pulse, Psychic, Hypnosis, Night Shade
    (492, "Shaymin", "Grass", None, "medium_slow", [75, 76, 79, 93]),  # Razor Leaf, Solar Beam, Growth... I mean Seed Flare
    (493, "Arceus", "Normal", None, "slow", [94, 293, 89, 126]),  # Judgment, Dragon Pulse, Earthquake, Fire Blast
    
    # Unova
    (494, "Victini", "Psychic", "Fire", "slow", [94, 126, 53, 60]),  # Psychic, Fire Blast, Flamethrower, Searing Shot
    (638, "Cobalion", "Steel", "Fighting", "slow", [169, 117, 106, 110]),  # Sacred Sword, Close Combat... use Iron Head
    (639, "Terrakion", "Rock", "Fighting", "slow", [89, 88, 117, 97]),
    (640, "Virizion", "Grass", "Fighting", "slow", [75, 117, 97, 79]),
    (641, "Tornadus", "Flying", None, "slow", [155, 97, 155, 298]),  # Gust, Agility, Hurricane, Air Slash
    (642, "Thundurus", "Electric", "Flying", "slow", [85, 97, 155, 84]),
    (643, "Reshiram", "Dragon", "Fire", "slow", [126, 293, 53, 298]),  # Blue Flare, Dragon Pulse, Flamethrower, Fusion Flare
    (644, "Zekrom", "Dragon", "Electric", "slow", [85, 293, 89, 298]),  # Bolt Strike, Dragon Pulse, Earthquake, Fusion Bolt
    (645, "Landorus", "Ground", "Flying", "slow", [89, 155, 97, 303]),  # Earthquake, Gust, Agility, Earth Power
    (646, "Kyurem", "Dragon", "Ice", "slow", [58, 293, 59, 155]),  # Ice Beam, Dragon Pulse, Blizzard, Glaciate
    (647, "Keldeo", "Water", "Fighting", "slow", [57, 117, 127, 97]),
    (648, "Meloetta", "Normal", "Psychic", "slow", [94, 93, 297, 97]),
    (649, "Genesect", "Bug", "Steel", "slow", [387, 53, 85, 293]),  # Techno Blast, Flamethrower, Thunderbolt, Flash Cannon
]

# Pokemon with multiple forms we only want one of
EXTRAS = [
    (144, "Articuno"),  # Already in list
    (150, "Mewtwo"),
    (151, "Mew"),
    (249, "Lugia"),
    (250, "Ho-Oh"),
    (382, "Kyogre"),
    (383, "Groudon"),
    (384, "Rayquaza"),
    (483, "Dialga"),
    (484, "Palkia"),
    (487, "Giratina"),
    (643, "Reshiram"),
    (644, "Zekrom"),
    (646, "Kyurem"),
]

# Pseudo-legendaries
PSEUDO_LEGENDARIES = [
    (149, "Dragonite", "Dragon", "Flying", "slow", [293, 89, 130, 36]),
    (248, "Tyranitar", "Rock", "Dark", "slow", [89, 88, 297, 36]),
    (373, "Salamence", "Dragon", "Flying", "slow", [293, 53, 89, 156]),
    (376, "Metagross", "Steel", "Psychic", "slow", [169, 94, 89, 93]),
    (445, "Garchomp", "Dragon", "Ground", "slow", [293, 89, 291, 97]),
    (474, "Porygon-Z", "Normal", None, "medium_fast", [94, 58, 85, 93]),
    (635, "Hydreigon", "Dark", "Dragon", "slow", [297, 293, 126, 89]),
]

# Starters (final forms)
STARTERS = [
    (6, "Charizard", "Fire", "Flying", "medium_slow", [53, 126, 156, 89]),
    (9, "Blastoise", "Water", None, "medium_slow", [57, 58, 127, 110]),
    (3, "Venusaur", "Grass", "Poison", "medium_slow", [76, 77, 75, 89]),
    (154, "Meganium", "Grass", None, "medium_slow", [76, 75, 79, 89]),
    (157, "Typhlosion", "Fire", None, "medium_slow", [53, 126, 97, 89]),
    (160, "Feraligatr", "Water", None, "medium_slow", [57, 58, 127, 89]),
    (254, "Sceptile", "Grass", None, "medium_slow", [75, 76, 291, 89]),
    (257, "Blaziken", "Fire", "Fighting", "medium_slow", [126, 117, 89, 53]),
    (260, "Swampert", "Water", "Ground", "medium_slow", [57, 89, 58, 127]),
    (389, "Torterra", "Grass", "Ground", "medium_slow", [89, 75, 76, 36]),
    (392, "Infernape", "Fire", "Fighting", "medium_slow", [126, 117, 89, 53]),
    (395, "Empoleon", "Water", "Steel", "medium_slow", [57, 58, 127, 169]),
    (497, "Serperior", "Grass", None, "medium_slow", [75, 76, 97, 89]),
    (500, "Emboar", "Fire", "Fighting", "medium_slow", [126, 117, 53, 89]),
    (503, "Samurott", "Water", None, "medium_slow", [57, 127, 58, 169]),
]

# Eeveelutions
EEVEELUTIONS = [
    (134, "Vaporeon", "Water", None, "medium_fast", [57, 58, 127, 97]),
    (135, "Jolteon", "Electric", None, "medium_fast", [85, 86, 97, 84]),
    (136, "Flareon", "Fire", None, "medium_fast", [126, 53, 36, 97]),
    (196, "Espeon", "Psychic", None, "medium_fast", [94, 60, 97, 149]),
    (197, "Umbreon", "Dark", None, "medium_fast", [297, 109, 103, 97]),
    (470, "Leafeon", "Grass", None, "medium_fast", [75, 76, 97, 149]),
    (471, "Glaceon", "Ice", None, "medium_fast", [58, 59, 97, 55]),
]

# All Pokemon to inject (filtered to unique species)
ALL_TO_INJECT = []

# Get unique species from legendaries (one per species)
seen_species = set()
for entry in LEGENDARIES:
    sid = entry[0]
    if sid not in seen_species:
        seen_species.add(sid)
        ALL_TO_INJECT.append(entry)

for entry in PSEUDO_LEGENDARIES:
    sid = entry[0]
    if sid not in seen_species:
        seen_species.add(sid)
        ALL_TO_INJECT.append(entry)

for entry in STARTERS:
    sid = entry[0]
    if sid not in seen_species:
        seen_species.add(sid)
        ALL_TO_INJECT.append(entry)

for entry in EEVEELUTIONS:
    sid = entry[0]
    if sid not in seen_species:
        seen_species.add(sid)
        ALL_TO_INJECT.append(entry)

# Also add Pikachu and Raichu (they're cute)
PIKACHU_FAMILY = [
    (25, "Pikachu", "Electric", None, "medium_fast", [85, 86, 97, 84]),
    (26, "Raichu", "Electric", None, "medium_fast", [85, 86, 97, 84]),
]
for entry in PIKACHU_FAMILY:
    sid = entry[0]
    if sid not in seen_species:
        seen_species.add(sid)
        ALL_TO_INJECT.append(entry)

# Sigilyph
SIGILYPH = [(561, "Sigilyph", "Psychic", "Flying", "medium_fast", [94, 298, 58, 155])]
for entry in SIGILYPH:
    sid = entry[0]
    if sid not in seen_species:
        seen_species.add(sid)
        ALL_TO_INJECT.append(entry)

print(f"Total unique Pokemon to inject: {len(ALL_TO_INJECT)}")

def make_pid_for_nature(desired_nature):
    """Generate a PID that results in the given nature"""
    for _ in range(200000):
        pid = random.randint(0, 0xFFFFFFFF)
        if pid % 25 == desired_nature:
            return pid
    return random.randint(0, 0xFFFFFFFF)  # fallback

def encode_utf16_le(text, max_len):
    """Encode text as UTF-16LE with null terminator"""
    encoded = text.encode('utf-16-le')
    if len(encoded) > max_len * 2:
        encoded = encoded[:max_len * 2]
    return encoded + b'\xFF\xFF'

def create_pokemon(species_id, species_name, moves, growth_rate="slow",
                   level=100, tid=25077, sid=62212, nature=0, ot_name="FAH",
                   language=2, game_version=19, ball=4, met_level=50,
                   met_location=0, encounter_type=0):
    """
    Create a Gen 5 PKM structure (decrypted, 136 bytes)
    
    game_version: 19 = Pokemon Black
    ball: 4 = Poke Ball
    met_location: 0 = "Met in a trade" or use a specific location
    """
    pid = make_pid_for_nature(nature)
    
    # Experience for level 100
    exp = EXP_AT_100.get(growth_rate, 1000000)
    
    # PP for moves
    pp1 = get_pp(moves[0]) if len(moves) > 0 else 0
    pp2 = get_pp(moves[1]) if len(moves) > 1 else 0
    pp3 = get_pp(moves[2]) if len(moves) > 2 else 0
    pp4 = get_pp(moves[3]) if len(moves) > 3 else 0
    
    # Create the 136-byte structure
    buf = bytearray(136)
    
    # PID (0x00)
    struct.pack_into('<I', buf, 0, pid)
    
    # Checksum placeholder (0x06), will be calculated later
    # Keep as 0 for now
    
    # Block A (bytes 0x08-0x27)
    struct.pack_into('<H', buf, 0x08, species_id)  # Species
    struct.pack_into('<H', buf, 0x0A, 0)  # Held Item (none)
    struct.pack_into('<H', buf, 0x0C, tid)  # TID
    struct.pack_into('<H', buf, 0x0E, sid)  # SID
    struct.pack_into('<I', buf, 0x10, exp)  # EXP
    buf[0x14] = 255  # Friendship (max)
    buf[0x15] = 0  # Ability (0 = first ability)
    buf[0x16] = 0  # Markings
    buf[0x17] = language  # Language (2 = English)
    
    # EVs (all 0)
    buf[0x18] = 0  # HP EV
    buf[0x19] = 0  # ATK EV
    buf[0x1A] = 0  # DEF EV
    buf[0x1B] = 0  # SPE EV
    buf[0x1C] = 0  # SPA EV
    buf[0x1D] = 0  # SPD EV
    
    # Contest stats (all 0)
    buf[0x1E] = 0  # Cool
    buf[0x1F] = 0  # Beauty
    buf[0x20] = 0  # Cute
    buf[0x21] = 0  # Smart
    buf[0x22] = 0  # Tough
    buf[0x23] = 0  # Sheen
    
    # Ribbons (all 0)
    struct.pack_into('<H', buf, 0x24, 0)  # Sinnoh Ribbon Set 1
    struct.pack_into('<H', buf, 0x26, 0)  # Unova Ribbon Set
    
    # Block B (bytes 0x28-0x47)
    # Moves
    for i in range(4):
        move_id = moves[i] if i < len(moves) else 0
        struct.pack_into('<H', buf, 0x28 + i * 2, move_id)
    
    # PP
    buf[0x30] = pp1
    buf[0x31] = pp2
    buf[0x32] = pp3
    buf[0x33] = pp4
    
    # PP Ups (all 0)
    struct.pack_into('<I', buf, 0x34, 0)
    
    # Unknown at 0x38-0x3B
    struct.pack_into('<I', buf, 0x38, 0)
    
    # Hoenn Ribbons
    struct.pack_into('<H', buf, 0x3C, 0)
    struct.pack_into('<H', buf, 0x3E, 0)
    
    # Flags + Nature
    buf[0x40] = 0  # Form flags
    buf[0x41] = nature  # Nature
    buf[0x42] = 0  # Ability flags
    buf[0x43] = 0  # Unused
    
    # Egg/Unknown at 0x44-0x47
    struct.pack_into('<I', buf, 0x44, 0)
    
    # Block C (bytes 0x48-0x67)
    # Nickname
    nickname = encode_utf16_le(species_name, 11)
    buf[0x48:0x48+len(nickname)] = nickname
    
    buf[0x5E] = 0  # Unknown
    buf[0x5F] = game_version  # Origin game (19 = Black)
    
    # Sinnoh Ribbons 3 and 4
    struct.pack_into('<H', buf, 0x60, 0)
    struct.pack_into('<H', buf, 0x62, 0)
    
    # Unused
    struct.pack_into('<I', buf, 0x64, 0)
    
    # Block D (bytes 0x68-0x87)
    # OT Name
    ot_encoded = encode_utf16_le(ot_name[:7], 7)
    buf[0x68:0x68+len(ot_encoded)] = ot_encoded
    
    # Dates (all 0 - not important)
    buf[0x78] = 0  # Date Egg Received - year
    buf[0x79] = 0  # month
    buf[0x7A] = 0  # day
    buf[0x7B] = 0  # Date Met - year
    buf[0x7C] = 0  # month
    buf[0x7D] = 0  # day
    
    # Egg Location
    struct.pack_into('<H', buf, 0x7E, 0)
    
    # Met Location
    struct.pack_into('<H', buf, 0x80, met_location)
    
    # Pokerus
    buf[0x82] = 0
    
    # Poke Ball
    buf[0x83] = ball
    
    # Met Level (lower 7 bits) + OT Gender (bit 7)
    buf[0x84] = met_level & 0x7F
    
    # Encounter Type
    buf[0x85] = encounter_type
    
    # Unused
    buf[0x86] = 0
    buf[0x87] = 0
    
    # Calculate and set checksum
    cksum = calc_checksum(bytes(buf))
    struct.pack_into('<H', buf, 6, cksum)
    
    return bytes(buf)

def get_slot_offset(box_base, slot_idx):
    """Get file offset for box slot index (0-719).
    Each box occupies 0x1000 bytes, slots are contiguous within each box.
    """
    box = slot_idx // 30
    slot_in_box = slot_idx % 30
    return box_base + box * 0x1000 + slot_in_box * 136

def get_save_slot_offset(save_data):
    """Determine which save slot is active.
    In Gen 5, the save alternates between two slots.
    We check both and use the one with valid data.
    Box data area starts at 0x400 within the active slot.
    """
    # Check slot 1 (0x00000) and slot 2 (0x20000)
    # A slot is active if it has box names starting at 0x000
    slot1_valid = save_data[0:4] == b'\x03\x00\x00\x00' and save_data[4:10] == b'\x42\x00\x4F\x00\x58\x00'
    
    # Slot 2 might have "BOX 1" at 0x20000
    slot2_valid = save_data[0x20000:0x20004] == b'\x03\x00\x00\x00' and save_data[0x20004:0x2000A] == b'\x42\x00\x4F\x00\x58\x00'
    
    if slot1_valid:
        return 0  # Slot 1 is active
    elif slot2_valid:
        return 0x20000  # Slot 2 is active
    else:
        # Default to slot 1
        return 0

def main():
    save_path = os.path.expanduser("~/Emulator/Pokemon - Black Version (USA Europe) (NDSi Enhanced)/Pokemon - Black Version (USA, Europe) (NDSi Enhanced).sav")
    
    # Check if a custom path was passed
    if len(sys.argv) > 1:
        save_path = sys.argv[1]
    
    if not os.path.exists(save_path):
        print(f"Save file not found: {save_path}")
        return 1
    
    print(f"Reading save file: {save_path}")
    with open(save_path, 'rb') as f:
        save_data = bytearray(f.read())
    
    print(f"Save file size: {len(save_data)} bytes")
    
    # Determine the active save slot offset
    slot_offset = get_save_slot_offset(save_data)
    print(f"Active save slot offset: 0x{slot_offset:05X}")
    
    # Box data starts at 0x400 from the slot base
    box_base = slot_offset + 0x400
    print(f"Box data base offset: 0x{box_base:05X}")
    
    # Find empty slots
    empty_slots = []
    for slot_idx in range(720):  # 24 boxes x 30 slots
        offset = get_slot_offset(box_base, slot_idx)
        if offset + 136 > len(save_data):
            break
        slot_data = save_data[offset:offset+136]
        pid = struct.unpack_from('<I', slot_data, 0)[0]
        ck = struct.unpack_from('<H', slot_data, 6)[0]
        if pid == 0 or ck == 0 or ck == 0xFFFF:
            empty_slots.append(offset)
    
    print(f"Found {len(empty_slots)} empty slots")
    
    # Check how many Pokemon we want to inject
    to_inject = ALL_TO_INJECT
    print(f"Pokemon to inject: {len(to_inject)}")
    
    if len(to_inject) > len(empty_slots):
        print(f"Warning: Not enough empty slots! Need {len(to_inject)}, have {len(empty_slots)}")
        print("Will only fill available empty slots.")
        to_inject = to_inject[:len(empty_slots)]
    
    # Inject Pokemon
    injected = 0
    for i, (species_id, species_name, *_) in enumerate(to_inject):
        if i >= len(empty_slots):
            break
        
        offset = empty_slots[i]
        
        # Get the moves for this Pokemon
        entry = None
        for e in ALL_TO_INJECT:
            if e[0] == species_id:
                entry = e
                break
        
        if entry is None:
            continue
        
        moves = entry[5] if len(entry) > 5 else [33, 0, 0, 0]  # Default: Tackle
        growth_rate = entry[4] if len(entry) > 4 else "slow"
        
        # Create the Pokemon
        try:
            plain_pkm = create_pokemon(species_id, species_name, moves, growth_rate=growth_rate)
            encrypted = encrypt_stored(plain_pkm)
            
            # Write to save
            save_data[offset:offset+136] = encrypted
            injected += 1
            
            print(f"  Injected #{i+1}: {species_name} (ID {species_id}) at offset 0x{offset:06X}")
        except Exception as e:
            print(f"  Failed to inject {species_name}: {e}")
    
    # Create backup
    backup_path = save_path + ".bak"
    if not os.path.exists(backup_path):
        print(f"\nCreating backup at: {backup_path}")
        with open(backup_path, 'wb') as f:
            f.write(save_data)
    
    # Write save
    with open(save_path, 'wb') as f:
        f.write(save_data)
    
    print(f"\nDone! Injected {injected} Pokemon.")
    print(f"Save file written to: {save_path}")
    return 0

if __name__ == "__main__":
    main()
