#!/usr/bin/env python3
"""
Pokemon Black Save Injector
Injects Pokemon directly into PC boxes and fills Pokedex.
Supports:
  - Legendary Pokemon (original behavior)
  - ALL 649 species (--all flag)
  - Shiny Pokemon (--shiny flag)
  - Pokedex completion (--pokedex flag)

Usage:
  python inject_legendaries.py                    # inject legendaries only
  python inject_legendaries.py --all              # inject all 649 species
  python inject_legendaries.py --all --shiny      # all 649, shiny
  python inject_legendaries.py --all --pokedex    # all 649 + fill pokedex
  python inject_legendaries.py --pokedex          # just fill pokedex, no pokemon
  python inject_legendaries.py /path/to/save.sav  # custom save path
"""

import struct
import random
import os
import sys
import argparse

# Gen 4/5 PKM encryption constants
BLOCK_SIZE = 32
LCRNG_MULT = 0x41C64E6D
LCRNG_ADD = 0x6073

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

NATURES = [
    "Hardy", "Lonely", "Brave", "Adamant", "Naughty",
    "Bold", "Docile", "Relaxed", "Impish", "Lax",
    "Timid", "Hasty", "Serious", "Jolly", "Naive",
    "Modest", "Mild", "Quiet", "Bashful", "Rash",
    "Calm", "Gentle", "Sassy", "Careful", "Quirky"
]

MOVE_PP = {
    0: 0, 1: 35, 2: 25, 33: 35, 34: 20, 35: 15, 36: 20,
    38: 30, 39: 40, 40: 40, 41: 35, 42: 35, 43: 30, 44: 20,
    45: 30, 46: 15, 47: 15, 48: 20, 49: 15, 53: 25, 57: 5,
    58: 5, 59: 5, 61: 10, 62: 5, 63: 20, 64: 35, 65: 35,
    66: 20, 67: 25, 68: 20, 69: 15, 70: 20, 71: 15, 72: 25,
    73: 10, 74: 20, 75: 35, 76: 10, 77: 10, 78: 15, 79: 15,
    80: 40, 81: 10, 82: 20, 83: 20, 84: 15, 85: 15, 86: 10,
    87: 10, 88: 15, 89: 10, 90: 15, 91: 10, 92: 15, 93: 25,
    94: 20, 95: 20, 96: 30, 97: 30, 98: 20, 99: 20, 100: 5,
    102: 15, 103: 10, 104: 30, 105: 15, 106: 5, 107: 30, 108: 10,
    109: 5, 110: 5, 111: 40, 112: 10, 113: 10, 114: 30, 115: 40,
    116: 20, 117: 20, 118: 20, 119: 10, 120: 10, 121: 15, 122: 20,
    123: 20, 124: 15, 125: 10, 126: 20, 127: 10, 129: 15, 130: 20,
    132: 15, 133: 25, 134: 20, 135: 15, 137: 5, 138: 10, 139: 10,
    140: 30, 141: 20, 142: 30, 143: 10, 144: 30, 145: 10, 146: 20,
    147: 10, 148: 30, 149: 40, 150: 20, 151: 20, 152: 20, 153: 20,
    154: 5, 155: 30, 156: 15, 157: 5, 158: 35, 159: 5, 160: 20,
    161: 30, 162: 10, 163: 30, 164: 25, 165: 20, 166: 10, 168: 20,
    169: 15, 170: 10, 171: 5, 172: 35, 173: 35, 174: 20, 175: 15,
    176: 30, 177: 30, 178: 35, 179: 30, 180: 20, 181: 20, 182: 35,
    183: 20, 184: 10, 185: 15, 187: 30, 188: 20, 189: 10, 190: 25,
    200: 35, 207: 30, 208: 15, 237: 30, 240: 30, 241: 10, 242: 30,
    244: 30, 249: 10, 250: 5, 262: 10, 263: 15, 272: 10, 275: 5,
    276: 10, 277: 15, 278: 15, 288: 15, 290: 30, 291: 5, 292: 10,
    293: 10, 296: 5, 297: 5, 298: 20, 299: 5, 300: 20, 302: 15,
    303: 20, 304: 20, 311: 10, 313: 15, 329: 5, 330: 5, 331: 10,
    332: 10, 333: 5, 334: 10, 338: 5, 340: 5, 342: 5, 343: 10,
    344: 5, 348: 20, 349: 10, 350: 5, 352: 10, 354: 10, 355: 10,
    357: 10, 358: 15, 359: 20, 360: 20, 363: 10, 364: 10, 365: 10,
    366: 10, 367: 5, 368: 10, 369: 5, 370: 5, 371: 5, 372: 10,
    373: 5, 374: 5, 375: 5, 376: 10, 377: 5, 378: 5, 379: 20,
    380: 30, 381: 10, 382: 20, 383: 20, 384: 5, 385: 15, 386: 10,
    387: 10, 388: 15, 389: 5, 390: 15, 391: 20, 392: 15, 393: 10,
    394: 5, 395: 15, 396: 20, 397: 15, 398: 15, 399: 15, 400: 10,
    401: 10, 402: 5, 403: 5, 404: 5, 405: 5, 406: 5, 407: 10,
    408: 10, 409: 5, 410: 10, 411: 10, 412: 5, 413: 20, 414: 10,
    415: 10, 416: 10, 417: 10, 418: 20, 419: 10, 420: 10, 421: 10,
    422: 10, 423: 15, 424: 15, 425: 15, 426: 15, 427: 20, 428: 20,
    429: 20, 430: 15, 431: 15, 432: 20, 433: 15, 434: 15, 435: 20,
    436: 10, 437: 15, 438: 15, 439: 10, 440: 15, 441: 10, 442: 20,
    443: 10, 444: 15, 445: 15, 446: 20, 447: 10, 448: 15, 449: 20,
    450: 10, 451: 20, 452: 15, 453: 10, 454: 20, 455: 10, 456: 15,
    457: 15, 458: 20, 459: 10, 460: 10, 461: 10, 462: 5, 463: 15,
    464: 10, 465: 15, 466: 5, 467: 10, 468: 30, 469: 5, 470: 10,
    471: 20, 472: 15, 473: 10, 474: 15, 475: 10, 476: 15, 477: 25,
    478: 20, 479: 10, 480: 15, 481: 10, 482: 10, 483: 20, 484: 15,
    485: 5, 486: 5, 487: 5, 488: 5, 489: 5, 490: 5, 491: 5,
    492: 5, 493: 5, 494: 5, 495: 5, 496: 15, 497: 5, 498: 10,
    499: 10, 500: 20,
}

def get_pp(move_id):
    return MOVE_PP.get(move_id, 40)

EXP_AT_100 = {
    "medium_fast": 1000000,
    "slow": 1250000,
    "medium_slow": 1059860,
    "fast": 800000,
    "erratic": 600000,
    "fluctuating": 1640000,
}

def exp_for_level(level, growth_rate):
    n = level
    if growth_rate == "fast":
        return int(0.8 * n**3)
    elif growth_rate == "medium_fast":
        return n**3
    elif growth_rate == "medium_slow":
        return int(1.2 * n**3 - 15 * n**2 + 100 * n - 140)
    elif growth_rate == "slow":
        return int(1.25 * n**3)
    elif growth_rate == "erratic":
        if n <= 50:
            return int(n**3 * (100 - n) / 50)
        elif n <= 68:
            return int(n**3 * (150 - n) / 100)
        elif n <= 98:
            return int(n**3 * ((1911 - 10 * n) / 3) / 500)
        else:
            return int(n**3 * (160 - n) / 100)
    elif growth_rate == "fluctuating":
        if n <= 15:
            return int(n**3 * ((n + 1) / 3 + 24) / 50)
        elif n <= 36:
            return int(n**3 * (n + 14) / 50)
        else:
            return int(n**3 * ((n / 2) + 32) / 50)
    return 1000000

# ── Pokemon names for all 649 species ──
POKEMON_NAMES = [
    "Bulbasaur","Ivysaur","Venusaur","Charmander","Charmeleon","Charizard",
    "Squirtle","Wartortle","Blastoise","Caterpie","Metapod","Butterfree",
    "Weedle","Kakuna","Beedrill","Pidgey","Pidgeotto","Pidgeot",
    "Rattata","Raticate","Spearow","Fearow","Ekans","Arbok",
    "Pikachu","Raichu","Sandshrew","Sandslash","NidoranF","Nidorina",
    "Nidoqueen","NidoranM","Nidorino","Nidoking","Clefairy","Clefable",
    "Vulpix","Ninetales","Jigglypuff","Wigglytuff","Zubat","Golbat",
    "Oddish","Gloom","Vileplume","Paras","Parasect","Venonat",
    "Venomoth","Diglett","Dugtrio","Meowth","Persian","Psyduck",
    "Golduck","Mankey","Primeape","Growlithe","Arcanine","Poliwag",
    "Poliwhirl","Poliwrath","Abra","Kadabra","Alakazam","Machop",
    "Machoke","Machamp","Bellsprout","Weepinbell","Victreebel","Tentacool",
    "Tentacruel","Geodude","Graveler","Golem","Ponyta","Rapidash",
    "Slowpoke","Slowbro","Magnemite","Magneton","Farfetchd","Doduo",
    "Dodrio","Seel","Dewgong","Grimer","Muk","Shellder",
    "Cloyster","Gastly","Haunter","Gengar","Onix","Drowzee",
    "Hypno","Krabby","Kingler","Voltorb","Electrode","Exeggcute",
    "Exeggutor","Cubone","Marowak","Hitmonlee","Hitmonchan","Lickitung",
    "Koffing","Weezing","Rhyhorn","Rhydon","Chansey","Tangela",
    "Kangaskhan","Horsea","Seadra","Goldeen","Seaking","Staryu",
    "Starmie","Mr. Mime","Scyther","Jynx","Electabuzz","Magmar",
    "Pinsir","Tauros","Magikarp","Gyarados","Lapras","Ditto",
    "Eevee","Vaporeon","Jolteon","Flareon","Porygon","Omanyte",
    "Omastar","Kabuto","Kabutops","Aerodactyl","Snorlax","Articuno",
    "Zapdos","Moltres","Dratini","Dragonair","Dragonite","Mewtwo",
    "Mew","Chikorita","Bayleef","Meganium","Cyndaquil","Quilava",
    "Typhlosion","Totodile","Croconaw","Feraligatr","Sentret","Furret",
    "Hoothoot","Noctowl","Ledyba","Ledian","Spinarak","Ariados",
    "Crobat","Chinchou","Lanturn","Pichu","Cleffa","Igglybuff",
    "Togepi","Togetic","Natu","Xatu","Mareep","Flaaffy",
    "Ampharos","Bellossom","Marill","Azumarill","Sudowoodo","Politoed",
    "Hoppip","Skiploom","Jumpluff","Aipom","Sunkern","Sunflora",
    "Yanma","Wooper","Quagsire","Espeon","Umbreon","Murkrow",
    "Slowking","Misdreavus","Unown","Wobbuffet","Girafarig","Pineco",
    "Forretress","Dunsparce","Gligar","Steelix","Snubbull","Granbull",
    "Qwilfish","Scizor","Shuckle","Heracross","Sneasel","Teddiursa",
    "Ursaring","Slugma","Magcargo","Swinub","Piloswine","Corsola",
    "Remoraid","Octillery","Delibird","Mantine","Skarmory","Houndour",
    "Houndoom","Kingdra","Phanpy","Donphan","Porygon2","Stantler",
    "Smeargle","Tyrogue","Hitmontop","Smoochum","Elekid","Magby",
    "Miltank","Blissey","Raikou","Entei","Suicune","Larvitar",
    "Pupitar","Tyranitar","Lugia","Ho-Oh","Celebi","Treecko",
    "Grovyle","Sceptile","Torchic","Combusken","Blaziken","Mudkip",
    "Marshtomp","Swampert","Poochyena","Mightyena","Zigzagoon","Linoone",
    "Wurmple","Silcoon","Beautifly","Cascoon","Dustox","Lotad",
    "Lombre","Ludicolo","Seedot","Nuzleaf","Shiftry","Taillow",
    "Swellow","Wingull","Pelipper","Ralts","Kirlia","Gardevoir",
    "Surskit","Masquerain","Shroomish","Breloom","Slakoth","Vigoroth",
    "Slaking","Nincada","Ninjask","Shedinja","Whismur","Loudred",
    "Exploud","Makuhita","Hariyama","Azurill","Nosepass","Skitty",
    "Delcatty","Sableye","Mawile","Aron","Lairon","Aggron",
    "Meditite","Medicham","Electrike","Manectric","Plusle","Minun",
    "Volbeat","Illumise","Roselia","Gulpin","Swalot","Carvanha",
    "Sharpedo","Wailmer","Wailord","Numel","Camerupt","Torkoal",
    "Spoink","Grumpig","Spinda","Trapinch","Vibrava","Flygon",
    "Cacnea","Cacturne","Swablu","Altaria","Zangoose","Seviper",
    "Lunatone","Solrock","Barboach","Whiscash","Corphish","Crawdaunt",
    "Baltoy","Claydol","Lileep","Cradily","Anorith","Armaldo",
    "Feebas","Milotic","Castform","Kecleon","Shuppet","Banette",
    "Duskull","Dusclops","Tropius","Chimecho","Absol","Wynaut",
    "Snorunt","Glalie","Spheal","Sealeo","Walrein","Clamperl",
    "Huntail","Gorebyss","Relicanth","Luvdisc","Bagon","Shelgon",
    "Salamence","Beldum","Metang","Metagross","Regirock","Regice",
    "Registeel","Latias","Latios","Kyogre","Groudon","Rayquaza",
    "Jirachi","Deoxys","Turtwig","Grotle","Torterra","Chimchar",
    "Monferno","Infernape","Piplup","Prinplup","Empoleon","Starly",
    "Staravia","Staraptor","Bidoof","Bibarel","Kricketot","Kricketune",
    "Shinx","Luxio","Luxray","Budew","Roserade","Cranidos",
    "Rampardos","Shieldon","Bastiodon","Burmy","Wormadam","Mothim",
    "Combee","Vespiquen","Pachirisu","Buizel","Floatzel","Cherubi",
    "Cherrim","Shellos","Gastrodon","Ambipom","Drifloon","Drifblim",
    "Buneary","Lopunny","Mismagius","Honchkrow","Glameow","Purugly",
    "Chingling","Stunky","Skuntank","Bronzor","Bronzong","Bonsly","Mime Jr.",
    "Happiny","Chatot","Spiritomb","Gible","Gabite","Garchomp",
    "Munchlax","Riolu","Lucario","Hippopotas","Hippowdon","Skorupi",
    "Drapion","Croagunk","Toxicroak","Carnivine","Finneon","Lumineon",
    "Mantyke","Snover","Abomasnow","Weavile","Magnezone","Lickilicky",
    "Rhyperior","Tangrowth","Electivire","Magmortar","Togekiss","Yanmega",
    "Leafeon","Glaceon","Gliscor","Mamoswine","Porygon-Z","Gallade",
    "Probopass","Dusknoir","Froslass","Rotom","Uxie","Mesprit",
    "Azelf","Dialga","Palkia","Heatran","Regigigas","Giratina",
    "Cresselia","Phione","Manaphy","Darkrai","Shaymin","Arceus",
    "Victini","Snivy","Servine","Serperior","Tepig","Pignite",
    "Emboar","Oshawott","Dewott","Samurott","Patrat","Watchog",
    "Lillipup","Herdier","Stoutland","Purrloin","Liepard","Pansage",
    "Simisage","Pansear","Simisear","Panpour","Simipour","Munna",
    "Musharna","Pidove","Tranquill","Unfezant","Blitzle","Zebstrika",
    "Roggenrola","Boldore","Gigalith","Woobat","Swoobat","Drilbur",
    "Excadrill","Audino","Timburr","Gurdurr","Conkeldurr","Tympole",
    "Palpitoad","Seismitoad","Throh","Sawk","Sewaddle","Swadloon",
    "Leavanny","Venipede","Whirlipede","Scolipede","Cottonee","Whimsicott",
    "Petilil","Lilligant","Basculin","Sandile","Krokorok","Krookodile",
    "Darumaka","Darmanitan","Maractus","Dwebble","Crustle","Scraggy",
    "Scrafty","Sigilyph","Yamask","Cofagrigus","Tirtouga","Carracosta",
    "Archen","Archeops","Trubbish","Garbodor","Zorua","Zoroark",
    "Minccino","Cinccino","Gothita","Gothorita","Gothitelle","Solosis",
    "Duosion","Reuniclus","Ducklett","Swanna","Vanillite","Vanillish",
    "Vanilluxe","Deerling","Sawsbuck","Emolga","Karrablast","Escavalier",
    "Foongus","Amoonguss","Frillish","Jellicent","Alomomola","Joltik",
    "Galvantula","Ferroseed","Ferrothorn","Klink","Klang","Klinklang",
    "Tynamo","Eelektrik","Eelektross","Elgyem","Beheeyem","Litwick",
    "Lampent","Chandelure","Axew","Fraxure","Haxorus","Cubchoo",
    "Beartic","Cryogonal","Shelmet","Accelgor","Stunfisk","Mienfoo",
    "Mienshao","Druddigon","Golett","Golurk","Pawniard","Bisharp",
    "Bouffalant","Rufflet","Braviary","Vullaby","Mandibuzz","Heatmor",
    "Durant","Deino","Zweilous","Hydreigon","Larvesta","Volcarona",
    "Cobalion","Terrakion","Virizion","Tornadus","Thundurus","Reshiram",
    "Zekrom","Landorus","Kyurem","Keldeo","Meloetta","Genesect",
]

# ── Species that use Slow growth rate (legendaries & mythicals) ──
SLOW_SPECIES = {
    144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 251,
    377, 378, 379, 380, 381, 382, 383, 384, 385, 386,
    480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493,
    494, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649,
}

# ── Species that use Medium Slow growth rate (starters & their families) ──
MEDIUM_SLOW_SPECIES = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 152, 153, 154, 155, 156, 157,
    158, 159, 160, 252, 253, 254, 255, 256, 257, 258, 259, 260,
    387, 388, 389, 390, 391, 392, 393, 394, 395,
    495, 496, 497, 498, 499, 500, 501, 502, 503,
}

# ── Cool/famous non-legendary species for priority sorting (lvl 40) ──
PRIORITY_SPECIES = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 25, 26,
    31, 34, 36, 38, 40, 51, 55, 59, 62, 65, 68, 71, 76, 78, 80,
    82, 85, 91, 94, 95, 99, 101, 103, 105, 106, 107, 108, 110, 112,
    117, 119, 122, 123, 128, 130, 131, 132, 133, 134, 135, 136, 137, 142, 143,
    147, 148, 149, 152, 153, 154, 155, 156, 157, 158, 159, 160,
    175, 176, 183, 184, 185, 196, 197, 202, 208, 212, 214, 215,
    225, 227, 229, 230, 233, 237, 241, 242, 246, 247, 248,
    252, 253, 254, 255, 256, 257, 258, 259, 260,
    264, 282, 284, 286, 289, 297, 302, 303, 306, 310, 330, 334, 335, 336,
    350, 359, 371, 372, 373, 374, 375, 376,
    387, 388, 389, 390, 391, 392, 393, 394, 395,
    398, 405, 407, 411, 419, 424, 429, 430, 443, 444, 445, 448, 461, 462,
    463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473,
    474, 475, 477, 478, 479,
    495, 496, 497, 498, 499, 500, 501, 502, 503,
    505, 508, 530, 531, 534, 537, 553, 555, 571,
    576, 579, 581, 584, 586, 589, 591, 593, 596, 598,
    601, 604, 609, 612, 614, 617, 620, 628, 630,
    633, 634, 635, 637,
}

def make_shiny_pid(tid=25077, sid=62212, desired_nature=None):
    """Generate a PID that results in a shiny Pokemon.
    Shiny condition: (PID_high ^ PID_low ^ TID ^ SID) < 8
    """
    tsn = tid ^ sid
    base_xor = tsn & 0xFFF8
    for _ in range(200000):
        pid_high = random.randint(0, 0xFFFF)
        for lb in range(8):
            xor_val = base_xor | lb
            pid_low = pid_high ^ xor_val
            pid = (pid_high << 16) | pid_low
            if desired_nature is None or pid % 25 == desired_nature:
                return pid
    return None

def make_pid_for_nature(desired_nature):
    for _ in range(200000):
        pid = random.randint(0, 0xFFFFFFFF)
        if pid % 25 == desired_nature:
            return pid
    return random.randint(0, 0xFFFFFFFF)

def encode_utf16_le(text, max_len):
    encoded = text.encode('utf-16-le')
    if len(encoded) > max_len * 2:
        encoded = encoded[:max_len * 2]
    return encoded + b'\xFF\xFF'

def create_pokemon(species_id, species_name, moves, growth_rate="slow",
                   level=100, tid=25077, sid=62212, nature=0, ot_name="FAH",
                   language=2, game_version=19, ball=4, met_level=50,
                   met_location=0, encounter_type=0, shiny=False):
    pid = make_shiny_pid(tid, sid, nature) if shiny else make_pid_for_nature(nature)
    if pid is None:
        pid = make_pid_for_nature(nature)

    exp = exp_for_level(level, growth_rate)

    pp1 = get_pp(moves[0]) if len(moves) > 0 else 0
    pp2 = get_pp(moves[1]) if len(moves) > 1 else 0
    pp3 = get_pp(moves[2]) if len(moves) > 2 else 0
    pp4 = get_pp(moves[3]) if len(moves) > 3 else 0

    buf = bytearray(136)
    struct.pack_into('<I', buf, 0, pid)

    struct.pack_into('<H', buf, 0x08, species_id)
    struct.pack_into('<H', buf, 0x0A, 0)
    struct.pack_into('<H', buf, 0x0C, tid)
    struct.pack_into('<H', buf, 0x0E, sid)
    struct.pack_into('<I', buf, 0x10, exp)
    buf[0x14] = 255
    buf[0x15] = 0
    buf[0x16] = 0
    buf[0x17] = language

    buf[0x18] = 0
    buf[0x19] = 0
    buf[0x1A] = 0
    buf[0x1B] = 0
    buf[0x1C] = 0
    buf[0x1D] = 0

    buf[0x1E] = 0
    buf[0x1F] = 0
    buf[0x20] = 0
    buf[0x21] = 0
    buf[0x22] = 0
    buf[0x23] = 0

    struct.pack_into('<H', buf, 0x24, 0)
    struct.pack_into('<H', buf, 0x26, 0)

    for i in range(4):
        move_id = moves[i] if i < len(moves) else 0
        struct.pack_into('<H', buf, 0x28 + i * 2, move_id)

    buf[0x30] = pp1
    buf[0x31] = pp2
    buf[0x32] = pp3
    buf[0x33] = pp4

    struct.pack_into('<I', buf, 0x34, 0)
    struct.pack_into('<I', buf, 0x38, 0)
    struct.pack_into('<H', buf, 0x3C, 0)
    struct.pack_into('<H', buf, 0x3E, 0)

    buf[0x40] = 0
    buf[0x41] = nature if not shiny else pid % 25
    buf[0x42] = 0
    buf[0x43] = 0

    struct.pack_into('<I', buf, 0x44, 0)

    nickname = encode_utf16_le(species_name, 11)
    buf[0x48:0x48+len(nickname)] = nickname

    buf[0x5E] = 0
    buf[0x5F] = game_version

    struct.pack_into('<H', buf, 0x60, 0)
    struct.pack_into('<H', buf, 0x62, 0)
    struct.pack_into('<I', buf, 0x64, 0)

    ot_encoded = encode_utf16_le(ot_name[:7], 7)
    buf[0x68:0x68+len(ot_encoded)] = ot_encoded

    buf[0x78] = 0
    buf[0x79] = 0
    buf[0x7A] = 0
    buf[0x7B] = 0
    buf[0x7C] = 0
    buf[0x7D] = 0

    struct.pack_into('<H', buf, 0x7E, 0)
    struct.pack_into('<H', buf, 0x80, met_location)

    buf[0x82] = 0
    buf[0x83] = ball
    buf[0x84] = met_level & 0x7F
    buf[0x85] = encounter_type
    buf[0x86] = 0
    buf[0x87] = 0

    cksum = calc_checksum(bytes(buf))
    struct.pack_into('<H', buf, 6, cksum)

    return bytes(buf)


# ── Original legendary sets ──
LEGENDARIES = [
    (144, "Articuno", [58, 155, 130, 47]),
    (145, "Zapdos", [85, 155, 130, 84]),
    (146, "Moltres", [53, 155, 130, 52]),
    (150, "Mewtwo", [94, 60, 65, 149]),
    (151, "Mew", [94, 60, 65, 149]),
    (243, "Raikou", [85, 97, 84, 86]),
    (244, "Entei", [53, 126, 97, 52]),
    (245, "Suicune", [57, 58, 48, 55]),
    (249, "Lugia", [94, 58, 97, 155]),
    (250, "Ho-Oh", [126, 53, 130, 155]),
    (377, "Regirock", [88, 89, 106, 110]),
    (378, "Regice", [58, 59, 106, 54]),
    (379, "Registeel", [169, 89, 106, 110]),
    (380, "Latias", [94, 297, 155, 97]),
    (381, "Latios", [94, 297, 155, 97]),
    (382, "Kyogre", [57, 127, 58, 55]),
    (383, "Groudon", [89, 126, 88, 33]),
    (384, "Rayquaza", [293, 89, 126, 155]),
    (385, "Jirachi", [94, 94, 65, 149]),
    (480, "Uxie", [94, 93, 97, 149]),
    (481, "Mesprit", [94, 93, 97, 149]),
    (482, "Azelf", [94, 93, 97, 149]),
    (483, "Dialga", [293, 89, 126, 97]),
    (484, "Palkia", [293, 57, 58, 97]),
    (485, "Heatran", [126, 53, 89, 93]),
    (486, "Regigigas", [36, 89, 169, 106]),
    (487, "Giratina", [293, 94, 89, 93]),
    (488, "Cresselia", [94, 135, 93, 60]),
    (489, "Phione", [57, 55, 97, 127]),
    (490, "Manaphy", [57, 94, 58, 97]),
    (491, "Darkrai", [297, 94, 95, 101]),
    (492, "Shaymin", [75, 76, 79, 93]),
    (493, "Arceus", [94, 293, 89, 126]),
    (494, "Victini", [94, 126, 53, 60]),
    (638, "Cobalion", [169, 117, 106, 110]),
    (639, "Terrakion", [89, 88, 117, 97]),
    (640, "Virizion", [75, 117, 97, 79]),
    (641, "Tornadus", [155, 97, 155, 298]),
    (642, "Thundurus", [85, 97, 155, 84]),
    (643, "Reshiram", [126, 293, 53, 298]),
    (644, "Zekrom", [85, 293, 89, 298]),
    (645, "Landorus", [89, 155, 97, 303]),
    (646, "Kyurem", [58, 293, 59, 155]),
    (647, "Keldeo", [57, 117, 127, 97]),
    (648, "Meloetta", [94, 93, 297, 97]),
    (649, "Genesect", [387, 53, 85, 293]),
]

PSEUDO_LEGENDARIES = [
    (149, "Dragonite", [293, 89, 130, 36]),
    (248, "Tyranitar", [89, 88, 297, 36]),
    (373, "Salamence", [293, 53, 89, 156]),
    (376, "Metagross", [169, 94, 89, 93]),
    (445, "Garchomp", [293, 89, 291, 97]),
    (474, "Porygon-Z", [94, 58, 85, 93]),
    (635, "Hydreigon", [297, 293, 126, 89]),
]

STARTERS = [
    (6, "Charizard", [53, 126, 156, 89]),
    (9, "Blastoise", [57, 58, 127, 110]),
    (3, "Venusaur", [76, 77, 75, 89]),
    (154, "Meganium", [76, 75, 79, 89]),
    (157, "Typhlosion", [53, 126, 97, 89]),
    (160, "Feraligatr", [57, 58, 127, 89]),
    (254, "Sceptile", [75, 76, 291, 89]),
    (257, "Blaziken", [126, 117, 89, 53]),
    (260, "Swampert", [57, 89, 58, 127]),
    (389, "Torterra", [89, 75, 76, 36]),
    (392, "Infernape", [126, 117, 89, 53]),
    (395, "Empoleon", [57, 58, 127, 169]),
    (497, "Serperior", [75, 76, 97, 89]),
    (500, "Emboar", [126, 117, 53, 89]),
    (503, "Samurott", [57, 127, 58, 169]),
]

EEVEELUTIONS = [
    (134, "Vaporeon", [57, 58, 127, 97]),
    (135, "Jolteon", [85, 86, 97, 84]),
    (136, "Flareon", [126, 53, 36, 97]),
    (196, "Espeon", [94, 60, 97, 149]),
    (197, "Umbreon", [297, 109, 103, 97]),
    (470, "Leafeon", [75, 76, 97, 149]),
    (471, "Glaceon", [58, 59, 97, 55]),
]

PIKACHU_FAMILY = [
    (25, "Pikachu", [85, 86, 97, 84]),
    (26, "Raichu", [85, 86, 97, 84]),
]

SIGILYPH = [(561, "Sigilyph", [94, 298, 58, 155])]

# ── Original legendary-only list (for default mode) ──
def get_legendary_list():
    seen = set()
    result = []
    for entry in LEGENDARIES + PSEUDO_LEGENDARIES + STARTERS + EEVEELUTIONS + PIKACHU_FAMILY + SIGILYPH:
        sid, name, *rest = entry
        if sid not in seen:
            seen.add(sid)
            moves = rest[0] if rest else [33]
            result.append((sid, name, moves))
    return result

def get_all_species_list():
    """Generate data for all 649 species sorted by priority with levels.
    
    Priority order: legendaries (lvl 40) > cool/famous (lvl 40) > rest (lvl 20)
    """
    legendaries = []
    priority = []
    others = []
    for sid in range(1, 650):
        name = POKEMON_NAMES[sid - 1]
        moves = [33, 33, 33, 33]
        if sid in SLOW_SPECIES:
            legendaries.append((sid, name, moves, 40))
        elif sid in PRIORITY_SPECIES:
            priority.append((sid, name, moves, 40))
        else:
            others.append((sid, name, moves, 20))
    return legendaries + priority + others


def crc16_ccitt_false(data):
    crc = 0xFFFF
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
        crc &= 0xFFFF
    return crc

def organize_boxes(save_data, box_base):
    """Read all Pokemon from boxes, sort by National Dex ID, write back in order.

    Scans all 24 boxes (720 slots), decrypts each non-empty Pokemon,
    sorts them by species ID, then writes them sequentially from slot 0,
    clearing the remaining slots.
    """
    pokemon_list = []
    for slot_idx in range(720):
        offset = get_slot_offset(box_base, slot_idx)
        if offset + 136 > len(save_data):
            break
        encrypted = bytes(save_data[offset:offset+136])
        pid = struct.unpack_from('<I', encrypted, 0)[0]
        ck = struct.unpack_from('<H', encrypted, 6)[0]
        if pid == 0 or ck == 0 or ck == 0xFFFF:
            continue
        try:
            decrypted = decrypt_stored(encrypted)
            species_id = struct.unpack_from('<H', decrypted, 0x08)[0]
            if species_id == 0 or species_id > 649:
                continue
            pokemon_list.append((species_id, decrypted))
        except Exception:
            continue

    total = len(pokemon_list)
    print(f"  Found {total} non-empty Pokemon in boxes")

    pokemon_list.sort(key=lambda x: x[0])

    for i, (species_id, decrypted) in enumerate(pokemon_list):
        offset = get_slot_offset(box_base, i)
        re_encrypted = encrypt_stored(decrypted)
        save_data[offset:offset+136] = re_encrypted

    for i in range(total, 720):
        offset = get_slot_offset(box_base, i)
        save_data[offset:offset+136] = bytes(136)

    print(f"  Organized {total} Pokemon by National Dex order (#001-#649)")
    return total


def update_box_checksums(save_data, box_base, num_boxes=24):
    for b in range(num_boxes):
        start = box_base + b * 0x1000
        if start + 0x1000 > len(save_data):
            break
        box_data = save_data[start:start + 0xFF0]
        chk = crc16_ccitt_false(bytes(box_data))
        struct.pack_into('<H', save_data, start + 0xFF2, chk)

def get_slot_offset(box_base, slot_idx):
    box = slot_idx // 30
    slot_in_box = slot_idx % 30
    return box_base + box * 0x1000 + slot_in_box * 136

def get_save_slot_offset(save_data):
    slot1_valid = save_data[0:4] == b'\x03\x00\x00\x00' and save_data[4:10] == b'\x42\x00\x4F\x00\x58\x00'
    slot2_valid = save_data[0x20000:0x20004] == b'\x03\x00\x00\x00' and save_data[0x20004:0x2000A] == b'\x42\x00\x4F\x00\x58\x00'
    if slot1_valid:
        return 0
    elif slot2_valid:
        return 0x20000
    else:
        return 0

def fill_pokedex(save_data, slot_offset):
    """Fill all Pokedex seen/caught flags for 649 species.
    
    Pokedex data offset within save slot: 0xD1B0
    Structure: first 4 bytes initial marker, then 0x131 dwords of 0xFFFFFFFF
    """
    dex_start = slot_offset + 0xD1B0
    if dex_start + 0x4C8 > len(save_data):
        print(f"  [WARN] Pokedex offset 0x{dex_start:05X} out of bounds, skipping")
        return False

    save_data[dex_start:dex_start+4] = struct.pack('<I', 0x00001803)
    offset = dex_start + 4
    for i in range(0x131):
        if offset + 4 <= len(save_data):
            save_data[offset:offset+4] = b'\xFF\xFF\xFF\xFF'
            offset += 4

    print(f"  Pokedex filled at save offset 0x{dex_start:05X}")
    return True

def inject_pokemon(save_data, box_base, species_list, shiny=False, slot_range=(0, 720), force=False):
    """Inject Pokemon into PC box slots within the given slot index range.
    
    If force=True, overwrites all slots regardless of existing data.
    If force=False, only fills empty slots (pid==0 or cksum==0/0xFFFF).
    """
    slots = []
    for slot_idx in range(slot_range[0], slot_range[1]):
        offset = get_slot_offset(box_base, slot_idx)
        if offset + 136 > len(save_data):
            break
        if force:
            slots.append((offset, slot_idx))
        else:
            slot_data = save_data[offset:offset+136]
            pid = struct.unpack_from('<I', slot_data, 0)[0]
            ck = struct.unpack_from('<H', slot_data, 6)[0]
            if pid == 0 or ck == 0 or ck == 0xFFFF:
                slots.append((offset, slot_idx))

    mode = "overwrite" if force else "empty"
    print(f"  Found {len(slots)} {mode} slots in range [{slot_range[0]}, {slot_range[1]})")

    to_inject = species_list
    if len(to_inject) > len(slots):
        print(f"  Warning: Only {len(slots)} slots available, need {len(to_inject)}")
        print(f"  Will inject first {len(slots)} species.")
        to_inject = to_inject[:len(slots)]

    injected = 0
    for i, entry in enumerate(to_inject):
        if i >= len(slots):
            break

        if len(entry) == 4:
            species_id, species_name, moves, level = entry
        else:
            species_id, species_name, moves = entry
            level = 100

        offset, slot_idx = slots[i]

        if species_id in SLOW_SPECIES:
            growth_rate = "slow"
        elif species_id in MEDIUM_SLOW_SPECIES:
            growth_rate = "medium_slow"
        else:
            growth_rate = "medium_fast"

        try:
            plain_pkm = create_pokemon(
                species_id, species_name, moves,
                growth_rate=growth_rate, shiny=shiny, level=level,
                met_level=min(level, 50)
            )
            encrypted = encrypt_stored(plain_pkm)
            save_data[offset:offset+136] = encrypted
            injected += 1
            if i % 50 == 0 or i == len(to_inject) - 1:
                print(f"  Injected {i+1}/{len(to_inject)}: {species_name} (ID {species_id}) into slot {slot_idx}")
        except Exception as e:
            print(f"  Failed to inject {species_name}: {e}")

    return injected


def main():
    parser = argparse.ArgumentParser(
        description="Pokemon Black Save Injector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python inject_legendaries.py                    # legendaries only
  python inject_legendaries.py --all              # all 649 species
  python inject_legendaries.py --all --shiny      # all 649, shiny
  python inject_legendaries.py --all --pokedex    # all 649 + fill pokedex
  python inject_legendaries.py --pokedex          # just fill pokedex
  python inject_legendaries.py --organize         # sort boxes by national dex
  python inject_legendaries.py --all --shiny --pokedex  # everything
  python inject_legendaries.py /path/to/save.sav  # custom save path
        """
    )
    parser.add_argument('save_path', nargs='?', default=None,
                        help='Path to save file (optional)')
    parser.add_argument('--all', action='store_true',
                        help='Inject all 649 species instead of just legendaries')
    parser.add_argument('--shiny', action='store_true',
                        help='Generate shiny Pokemon')
    parser.add_argument('--pokedex', action='store_true',
                        help='Fill Pokedex seen/caught flags for all 649 species')
    parser.add_argument('--organize', action='store_true',
                        help='Sort all Pokemon in boxes by National Dex #001-#649')
    parser.add_argument('--no-backup', action='store_true',
                        help='Skip creating backup file')

    args = parser.parse_args()

    save_path = args.save_path or os.path.expanduser(
        "~/Emulator/Pokemon - Black Version (USA Europe) (NDSi Enhanced)"
        "/Pokemon - Black Version (USA, Europe) (NDSi Enhanced).sav"
    )

    if not os.path.exists(save_path):
        print(f"Save file not found: {save_path}")
        return 1

    print(f"Reading save file: {save_path}")
    with open(save_path, 'rb') as f:
        save_data = bytearray(f.read())

    print(f"Save file size: {len(save_data)} bytes")

    slot_offset = get_save_slot_offset(save_data)
    print(f"Active save slot offset: 0x{slot_offset:05X}")

    # Slot 2 (at 0x24000) is the active save slot for box data
    # Slot 1 (slot_offset) is used for Pokedex
    box_slot = 0x24000
    box_base = box_slot + 0x400
    print(f"Box data base offset (Slot 2): 0x{box_base:05X}")
    print(f"Pokedex base offset (Slot 1):   0x{slot_offset + 0xD1B0:05X}")

    any_injected = False

    # Fill Pokedex if requested
    if args.pokedex:
        print("\n[Pokedex]")
        fill_pokedex(save_data, slot_offset)
        any_injected = True

    # Build species list and inject
    if args.all:
        print("\n[All 649 Species mode]")
        all_species = get_all_species_list()
        shiny_label = " SHINY" if args.shiny else ""

        # Someone's PC = boxes 1-8 (240 slots total)
        # Species are already sorted: legendaries (lvl 40) > cool (lvl 40) > rest (lvl 20)
        print(f"\n[Injecting{shiny_label} into Someone's PC (boxes 1-8, 240 slots)]")
        injected = inject_pokemon(save_data, box_base, all_species, shiny=args.shiny, slot_range=(0, 240), force=True)
        print(f"\n  Injected {injected} Pokemon into Someone's PC")
        any_injected = True
    elif not args.pokedex and not args.organize:
        # Default mode: inject legendaries (only when no other flag is specified)
        print("\n[Legendary-only mode]")
        species_list = get_legendary_list()
        shiny_label = " SHINY" if args.shiny else ""
        print(f"Pokemon to inject: {len(species_list)}{shiny_label}")
        print(f"\n[Injecting{shiny_label}]")
        injected = inject_pokemon(save_data, box_base, species_list, shiny=args.shiny)
        print(f"\n  Injected {injected}/{len(species_list)} Pokemon{shiny_label}")
        any_injected = True

    # Organize boxes if requested (sort all Pokemon by National Dex number)
    if args.organize:
        print(f"\n[Organizing Boxes]")
        organized = organize_boxes(save_data, box_base)
        any_injected = True

    if not any_injected:
        print("Nothing to do. Use --all, --pokedex, --organize, or run without flags for legendaries.")
        return 0

    # Update box checksums if any Pokemon were injected
    if any_injected:
        print(f"\n[Updating box checksums]")
        update_box_checksums(save_data, box_base)
        print(f"  Checksums updated for boxes 1-24")

    # Create backup
    if not args.no_backup:
        backup_path = save_path + ".bak"
        if not os.path.exists(backup_path):
            print(f"\nCreating backup at: {backup_path}")
            with open(backup_path, 'wb') as f:
                f.write(save_data)

    # Write save
    print(f"\nWriting save file...")
    with open(save_path, 'wb') as f:
        f.write(save_data)

    print(f"Done! Save file written to: {save_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
