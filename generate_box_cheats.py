#!/usr/bin/env python3
"""
Generate a single Action Replay cheat code that fills ALL 24 PC boxes
with ALL 649 species in National Dex order (#001-#649).

Pokemon get proper moves via: predefined sets → evolution propagation → type-based.

Usage:
  python generate_box_cheats.py
"""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inject_legendaries import (
    encrypt_stored, create_pokemon, POKEMON_NAMES,
    SLOW_SPECIES, MEDIUM_SLOW_SPECIES,
    LEGENDARIES, PSEUDO_LEGENDARIES, STARTERS,
    EEVEELUTIONS, PIKACHU_FAMILY, SIGILYPH
)

CHEATS_DIR = f"{os.environ['HOME']}/.var/app/com.hydra.noods/config/noods/cheats"
ROM_NAME = "Pokemon - Black Version (USA, Europe) (NDSi Enhanced)"
CHEAT_FILE = f"{CHEATS_DIR}/{ROM_NAME}.cht"

BOX_BASE   = 0x0CBC
BOX_SIZE   = 0x1000
SLOT_SIZE  = 0x88
SLOTS_BOX  = 30

# ── Evolution: species_id → pre-evolution species_id ──
PREV_EVOLUTION = {
    2:1,3:2,5:4,6:5,8:7,9:8,11:10,12:11,14:13,15:14,17:16,18:17,20:19,
    22:21,24:23,25:172,26:25,28:27,30:29,31:30,33:32,34:33,35:173,36:35,
    38:37,39:174,40:39,42:41,44:43,45:44,47:46,49:48,51:50,53:52,55:54,
    57:56,59:58,61:60,62:61,64:63,65:64,67:66,68:67,70:69,71:70,73:72,
    75:74,76:75,78:77,80:79,82:81,85:84,87:86,89:88,91:90,93:92,94:93,
    97:96,99:98,101:100,103:102,105:104,106:236,107:236,110:109,112:111,
    113:440,117:116,119:118,121:120,122:439,124:238,125:239,126:240,
    130:129,134:133,135:133,136:133,139:138,141:140,143:446,148:147,
    149:148,153:152,154:153,156:155,157:156,159:158,160:159,162:161,
    164:163,166:165,168:167,169:42,171:170,176:175,178:177,180:179,
    181:180,182:44,183:298,184:183,185:438,186:61,188:187,189:188,
    192:191,195:194,196:133,197:133,199:79,202:360,205:204,208:95,
    210:209,212:123,217:216,219:218,221:220,224:223,226:458,229:228,
    230:117,232:231,233:137,237:236,242:113,247:246,248:247,253:252,
    254:253,256:255,257:256,259:258,260:259,262:261,264:263,266:265,
    267:266,268:265,269:268,271:270,272:271,274:273,275:274,277:276,
    279:278,281:280,282:281,284:283,286:285,288:287,289:288,291:290,
    292:290,294:293,295:294,297:296,301:300,305:304,306:305,308:307,
    310:309,315:406,317:316,319:318,321:320,323:322,326:325,329:328,
    330:329,332:331,334:333,340:339,342:341,344:343,346:345,348:347,
    350:349,354:353,356:355,358:433,362:361,364:363,365:364,367:366,
    368:366,372:371,373:372,375:374,376:375,388:387,389:388,391:390,
    392:391,394:393,395:394,397:396,398:397,400:399,402:401,404:403,
    405:404,407:315,409:408,411:410,413:412,414:412,416:415,419:418,
    421:420,423:422,424:190,426:425,428:427,429:200,430:198,432:431,
    435:434,437:436,444:443,445:444,448:447,450:449,452:451,454:453,
    457:456,460:459,461:215,462:82,463:108,464:112,465:114,466:125,
    467:126,468:176,469:193,470:133,471:133,472:207,473:221,474:233,
    475:281,476:299,477:356,478:361,490:489,496:495,497:496,499:498,
    500:499,502:501,503:502,505:504,507:506,508:507,510:509,512:511,
    514:513,516:515,518:517,520:519,521:520,523:522,525:524,526:525,
    528:527,530:529,533:532,534:533,536:535,537:536,541:540,542:541,
    544:543,545:544,547:546,549:548,552:551,553:552,555:554,558:557,
    560:559,563:562,565:564,567:566,569:568,571:570,573:572,575:574,
    576:575,578:577,579:578,581:580,583:582,584:583,586:585,589:588,
    591:590,593:592,596:595,598:597,600:599,601:600,603:602,604:603,
    606:605,608:607,609:608,611:610,612:611,614:613,617:616,620:619,
    623:622,625:624,628:627,630:629,634:633,635:634,637:636,
}

# Map each species to its evolved form (reverse of PREV_EVOLUTION)
EVOLVES_TO = {}
for child, parent in PREV_EVOLUTION.items():
    EVOLVES_TO[parent] = child

# ── Types for all 649 species (Gen 5 era, no Fairy reclass) ──
POKEMON_TYPES = {
    1: ("Grass","Poison"),2: ("Grass","Poison"),3: ("Grass","Poison"),
    4: ("Fire",None),5: ("Fire",None),6: ("Fire","Flying"),
    7: ("Water",None),8: ("Water",None),9: ("Water",None),
    10: ("Bug",None),11: ("Bug",None),12: ("Bug","Flying"),
    13: ("Bug","Poison"),14: ("Bug","Poison"),15: ("Bug","Poison"),
    16: ("Normal","Flying"),17: ("Normal","Flying"),18: ("Normal","Flying"),
    19: ("Normal",None),20: ("Normal",None),21: ("Normal","Flying"),
    22: ("Normal","Flying"),23: ("Poison",None),24: ("Poison",None),
    25: ("Electric",None),26: ("Electric",None),27: ("Ground",None),
    28: ("Ground",None),29: ("Poison",None),30: ("Poison",None),
    31: ("Poison","Ground"),32: ("Poison",None),33: ("Poison",None),
    34: ("Poison","Ground"),35: ("Normal",None),36: ("Normal",None),
    37: ("Fire",None),38: ("Fire",None),39: ("Normal",None),
    40: ("Normal",None),41: ("Poison","Flying"),42: ("Poison","Flying"),
    43: ("Grass","Poison"),44: ("Grass","Poison"),45: ("Grass","Poison"),
    46: ("Bug","Grass"),47: ("Bug","Grass"),48: ("Bug","Poison"),
    49: ("Bug","Poison"),50: ("Ground",None),51: ("Ground",None),
    52: ("Normal",None),53: ("Normal",None),54: ("Water",None),
    55: ("Water",None),56: ("Fighting",None),57: ("Fighting",None),
    58: ("Fire",None),59: ("Fire",None),60: ("Water",None),
    61: ("Water",None),62: ("Water","Fighting"),63: ("Psychic",None),
    64: ("Psychic",None),65: ("Psychic",None),66: ("Fighting",None),
    67: ("Fighting",None),68: ("Fighting",None),69: ("Grass","Poison"),
    70: ("Grass","Poison"),71: ("Grass","Poison"),72: ("Water","Poison"),
    73: ("Water","Poison"),74: ("Rock","Ground"),75: ("Rock","Ground"),
    76: ("Rock","Ground"),77: ("Fire",None),78: ("Fire",None),
    79: ("Water","Psychic"),80: ("Water","Psychic"),81: ("Electric","Steel"),
    82: ("Electric","Steel"),83: ("Normal","Flying"),84: ("Normal","Flying"),
    85: ("Normal","Flying"),86: ("Water",None),87: ("Water","Ice"),
    88: ("Poison",None),89: ("Poison",None),90: ("Water",None),
    91: ("Water","Ice"),92: ("Ghost","Poison"),93: ("Ghost","Poison"),
    94: ("Ghost","Poison"),95: ("Rock","Ground"),96: ("Psychic",None),
    97: ("Psychic",None),98: ("Water",None),99: ("Water",None),
    100: ("Electric",None),101: ("Electric",None),102: ("Grass","Psychic"),
    103: ("Grass","Psychic"),104: ("Ground",None),105: ("Ground",None),
    106: ("Fighting",None),107: ("Fighting",None),108: ("Normal",None),
    109: ("Poison",None),110: ("Poison",None),111: ("Ground","Rock"),
    112: ("Ground","Rock"),113: ("Normal",None),114: ("Grass",None),
    115: ("Normal",None),116: ("Water",None),117: ("Water",None),
    118: ("Water",None),119: ("Water",None),120: ("Water",None),
    121: ("Water","Psychic"),122: ("Psychic",None),123: ("Bug","Flying"),
    124: ("Ice","Psychic"),125: ("Electric",None),126: ("Fire",None),
    127: ("Bug",None),128: ("Normal",None),129: ("Water",None),
    130: ("Water","Flying"),131: ("Water","Ice"),132: ("Normal",None),
    133: ("Normal",None),134: ("Water",None),135: ("Electric",None),
    136: ("Fire",None),137: ("Normal",None),138: ("Rock","Water"),
    139: ("Rock","Water"),140: ("Rock","Water"),141: ("Rock","Water"),
    142: ("Rock","Flying"),143: ("Normal",None),144: ("Ice","Flying"),
    145: ("Electric","Flying"),146: ("Fire","Flying"),147: ("Dragon",None),
    148: ("Dragon",None),149: ("Dragon","Flying"),150: ("Psychic",None),
    151: ("Psychic",None),152: ("Grass",None),153: ("Grass",None),
    154: ("Grass",None),155: ("Fire",None),156: ("Fire",None),
    157: ("Fire",None),158: ("Water",None),159: ("Water",None),
    160: ("Water",None),161: ("Normal",None),162: ("Normal",None),
    163: ("Normal","Flying"),164: ("Normal","Flying"),165: ("Bug","Flying"),
    166: ("Bug","Flying"),167: ("Bug","Poison"),168: ("Bug","Poison"),
    169: ("Poison","Flying"),170: ("Water","Electric"),171: ("Water","Electric"),
    172: ("Electric",None),173: ("Normal",None),174: ("Normal",None),
    175: ("Normal",None),176: ("Normal","Flying"),177: ("Psychic","Flying"),
    178: ("Psychic","Flying"),179: ("Electric",None),180: ("Electric",None),
    181: ("Electric",None),182: ("Grass",None),183: ("Water",None),
    184: ("Water",None),185: ("Rock",None),186: ("Water",None),
    187: ("Grass","Flying"),188: ("Grass","Flying"),189: ("Grass","Flying"),
    190: ("Normal",None),191: ("Grass",None),192: ("Grass",None),
    193: ("Bug","Flying"),194: ("Water","Ground"),195: ("Water","Ground"),
    196: ("Psychic",None),197: ("Dark",None),198: ("Dark","Flying"),
    199: ("Water","Psychic"),200: ("Ghost",None),201: ("Psychic",None),
    202: ("Psychic",None),203: ("Normal","Psychic"),204: ("Bug",None),
    205: ("Bug","Steel"),206: ("Normal",None),207: ("Ground","Flying"),
    208: ("Steel","Ground"),209: ("Normal",None),210: ("Normal",None),
    211: ("Water","Poison"),212: ("Bug","Steel"),213: ("Bug","Rock"),
    214: ("Bug","Fighting"),215: ("Dark","Ice"),216: ("Normal",None),
    217: ("Normal",None),218: ("Fire",None),219: ("Fire","Rock"),
    220: ("Ice","Ground"),221: ("Ice","Ground"),222: ("Water","Rock"),
    223: ("Water",None),224: ("Water",None),225: ("Ice","Flying"),
    226: ("Water","Flying"),227: ("Steel","Flying"),228: ("Dark","Fire"),
    229: ("Dark","Fire"),230: ("Water","Dragon"),231: ("Ground",None),
    232: ("Ground",None),233: ("Normal",None),234: ("Normal",None),
    235: ("Normal",None),236: ("Fighting",None),237: ("Fighting",None),
    238: ("Ice","Psychic"),239: ("Electric",None),240: ("Fire",None),
    241: ("Normal",None),242: ("Normal",None),243: ("Electric",None),
    244: ("Fire",None),245: ("Water",None),246: ("Rock","Ground"),
    247: ("Rock","Ground"),248: ("Rock","Dark"),249: ("Psychic","Flying"),
    250: ("Fire","Flying"),251: ("Psychic","Grass"),252: ("Grass",None),
    253: ("Grass",None),254: ("Grass",None),255: ("Fire",None),
    256: ("Fire","Fighting"),257: ("Fire","Fighting"),258: ("Water",None),
    259: ("Water","Ground"),260: ("Water","Ground"),261: ("Dark",None),
    262: ("Dark",None),263: ("Normal",None),264: ("Normal",None),
    265: ("Bug",None),266: ("Bug",None),267: ("Bug","Flying"),
    268: ("Bug",None),269: ("Bug","Poison"),270: ("Water","Grass"),
    271: ("Water","Grass"),272: ("Water","Grass"),273: ("Grass",None),
    274: ("Grass","Dark"),275: ("Grass","Dark"),276: ("Normal","Flying"),
    277: ("Normal","Flying"),278: ("Water","Flying"),279: ("Water","Flying"),
    280: ("Psychic",None),281: ("Psychic",None),282: ("Psychic",None),
    283: ("Bug","Water"),284: ("Bug","Flying"),285: ("Grass",None),
    286: ("Grass","Fighting"),287: ("Normal",None),288: ("Normal",None),
    289: ("Normal",None),290: ("Bug","Ground"),291: ("Bug","Flying"),
    292: ("Bug","Ghost"),293: ("Normal",None),294: ("Normal",None),
    295: ("Normal",None),296: ("Fighting",None),297: ("Fighting",None),
    298: ("Normal",None),299: ("Rock",None),300: ("Normal",None),
    301: ("Normal",None),302: ("Dark","Ghost"),303: ("Steel",None),
    304: ("Steel","Rock"),305: ("Steel","Rock"),306: ("Steel","Rock"),
    307: ("Fighting","Psychic"),308: ("Fighting","Psychic"),
    309: ("Electric",None),310: ("Electric",None),311: ("Electric",None),
    312: ("Electric",None),313: ("Bug",None),314: ("Bug",None),
    315: ("Grass","Poison"),316: ("Poison",None),317: ("Poison",None),
    318: ("Water","Dark"),319: ("Water","Dark"),320: ("Water",None),
    321: ("Water",None),322: ("Fire","Ground"),323: ("Fire","Ground"),
    324: ("Fire",None),325: ("Psychic",None),326: ("Psychic",None),
    327: ("Normal",None),328: ("Ground",None),329: ("Ground","Dragon"),
    330: ("Ground","Dragon"),331: ("Grass",None),332: ("Grass","Dark"),
    333: ("Normal","Flying"),334: ("Dragon","Flying"),335: ("Normal",None),
    336: ("Poison",None),337: ("Rock","Psychic"),338: ("Rock","Psychic"),
    339: ("Water","Ground"),340: ("Water","Ground"),341: ("Water",None),
    342: ("Water","Dark"),343: ("Ground","Psychic"),344: ("Ground","Psychic"),
    345: ("Rock","Grass"),346: ("Rock","Grass"),347: ("Rock","Bug"),
    348: ("Rock","Bug"),349: ("Water",None),350: ("Water",None),
    351: ("Normal",None),352: ("Normal",None),353: ("Ghost",None),
    354: ("Ghost",None),355: ("Ghost",None),356: ("Ghost",None),
    357: ("Grass","Flying"),358: ("Psychic",None),359: ("Dark",None),
    360: ("Psychic",None),361: ("Ice",None),362: ("Ice",None),
    363: ("Ice","Water"),364: ("Ice","Water"),365: ("Ice","Water"),
    366: ("Water",None),367: ("Water",None),368: ("Water",None),
    369: ("Water","Rock"),370: ("Water",None),371: ("Dragon",None),
    372: ("Dragon",None),373: ("Dragon","Flying"),374: ("Steel","Psychic"),
    375: ("Steel","Psychic"),376: ("Steel","Psychic"),377: ("Rock",None),
    378: ("Ice",None),379: ("Steel",None),380: ("Dragon","Psychic"),
    381: ("Dragon","Psychic"),382: ("Water",None),383: ("Ground",None),
    384: ("Dragon","Flying"),385: ("Steel","Psychic"),386: ("Psychic",None),
    387: ("Grass",None),388: ("Grass",None),389: ("Grass","Ground"),
    390: ("Fire",None),391: ("Fire","Fighting"),392: ("Fire","Fighting"),
    393: ("Water",None),394: ("Water",None),395: ("Water","Steel"),
    396: ("Normal","Flying"),397: ("Normal","Flying"),398: ("Normal","Flying"),
    399: ("Normal",None),400: ("Normal","Water"),401: ("Bug",None),
    402: ("Bug",None),403: ("Electric",None),404: ("Electric",None),
    405: ("Electric",None),406: ("Grass","Poison"),407: ("Grass","Poison"),
    408: ("Rock",None),409: ("Rock",None),410: ("Rock","Steel"),
    411: ("Rock","Steel"),412: ("Bug",None),413: ("Bug","Grass"),
    414: ("Bug","Flying"),415: ("Bug","Flying"),416: ("Bug","Flying"),
    417: ("Electric",None),418: ("Water",None),419: ("Water",None),
    420: ("Grass",None),421: ("Grass",None),422: ("Water",None),
    423: ("Water","Ground"),424: ("Normal",None),425: ("Ghost","Flying"),
    426: ("Ghost","Flying"),427: ("Normal",None),428: ("Normal",None),
    429: ("Ghost",None),430: ("Dark","Flying"),431: ("Normal",None),
    432: ("Normal",None),433: ("Psychic",None),434: ("Poison","Dark"),
    435: ("Poison","Dark"),436: ("Steel","Psychic"),437: ("Steel","Psychic"),
    438: ("Rock",None),439: ("Psychic",None),440: ("Normal",None),
    441: ("Normal","Flying"),442: ("Ghost","Dark"),443: ("Dragon","Ground"),
    444: ("Dragon","Ground"),445: ("Dragon","Ground"),446: ("Normal",None),
    447: ("Fighting",None),448: ("Fighting","Steel"),449: ("Ground",None),
    450: ("Ground",None),451: ("Poison","Bug"),452: ("Poison","Dark"),
    453: ("Poison","Fighting"),454: ("Poison","Fighting"),
    455: ("Grass",None),456: ("Water",None),457: ("Water",None),
    458: ("Water","Flying"),459: ("Grass","Ice"),460: ("Grass","Ice"),
    461: ("Dark","Ice"),462: ("Electric","Steel"),463: ("Normal",None),
    464: ("Ground","Rock"),465: ("Grass",None),466: ("Electric",None),
    467: ("Fire",None),468: ("Normal","Flying"),469: ("Bug","Flying"),
    470: ("Grass",None),471: ("Ice",None),472: ("Ground","Flying"),
    473: ("Ice","Ground"),474: ("Normal",None),475: ("Psychic","Fighting"),
    476: ("Rock","Steel"),477: ("Ghost",None),478: ("Ice","Ghost"),
    479: ("Electric","Ghost"),480: ("Psychic",None),481: ("Psychic",None),
    482: ("Psychic",None),483: ("Steel","Dragon"),484: ("Water","Dragon"),
    485: ("Fire","Steel"),486: ("Normal",None),487: ("Ghost","Dragon"),
    488: ("Psychic",None),489: ("Water",None),490: ("Water",None),
    491: ("Dark",None),492: ("Grass",None),493: ("Normal",None),
    494: ("Psychic","Fire"),495: ("Grass",None),496: ("Grass",None),
    497: ("Grass",None),498: ("Fire",None),499: ("Fire","Fighting"),
    500: ("Fire","Fighting"),501: ("Water",None),502: ("Water",None),
    503: ("Water",None),504: ("Normal",None),505: ("Normal",None),
    506: ("Normal",None),507: ("Normal",None),508: ("Normal",None),
    509: ("Dark",None),510: ("Dark",None),511: ("Grass",None),
    512: ("Grass",None),513: ("Fire",None),514: ("Fire",None),
    515: ("Water",None),516: ("Water",None),517: ("Psychic",None),
    518: ("Psychic",None),519: ("Normal","Flying"),520: ("Normal","Flying"),
    521: ("Normal","Flying"),522: ("Electric",None),523: ("Electric",None),
    524: ("Rock",None),525: ("Rock",None),526: ("Rock",None),
    527: ("Psychic","Flying"),528: ("Psychic","Flying"),529: ("Ground",None),
    530: ("Ground","Steel"),531: ("Normal",None),532: ("Fighting",None),
    533: ("Fighting",None),534: ("Fighting",None),535: ("Water",None),
    536: ("Water","Ground"),537: ("Water","Ground"),538: ("Fighting",None),
    539: ("Fighting",None),540: ("Bug","Grass"),541: ("Bug","Grass"),
    542: ("Bug","Grass"),543: ("Bug","Poison"),544: ("Bug","Poison"),
    545: ("Bug","Poison"),546: ("Grass",None),547: ("Grass",None),
    548: ("Grass",None),549: ("Grass",None),550: ("Water",None),
    551: ("Ground","Dark"),552: ("Ground","Dark"),553: ("Ground","Dark"),
    554: ("Fire",None),555: ("Fire",None),556: ("Grass",None),
    557: ("Bug","Rock"),558: ("Bug","Rock"),559: ("Dark","Fighting"),
    560: ("Dark","Fighting"),561: ("Psychic","Flying"),
    562: ("Ghost",None),563: ("Ghost",None),564: ("Water","Rock"),
    565: ("Water","Rock"),566: ("Rock","Flying"),567: ("Rock","Flying"),
    568: ("Poison",None),569: ("Poison",None),570: ("Dark",None),
    571: ("Dark",None),572: ("Normal",None),573: ("Normal",None),
    574: ("Psychic",None),575: ("Psychic",None),576: ("Psychic",None),
    577: ("Psychic",None),578: ("Psychic",None),579: ("Psychic",None),
    580: ("Water","Flying"),581: ("Water","Flying"),582: ("Ice",None),
    583: ("Ice",None),584: ("Ice",None),585: ("Normal","Grass"),
    586: ("Normal","Grass"),587: ("Electric","Flying"),
    588: ("Bug",None),589: ("Bug","Steel"),590: ("Grass","Poison"),
    591: ("Grass","Poison"),592: ("Water","Ghost"),593: ("Water","Ghost"),
    594: ("Water",None),595: ("Bug","Electric"),596: ("Bug","Electric"),
    597: ("Grass","Steel"),598: ("Grass","Steel"),599: ("Steel",None),
    600: ("Steel",None),601: ("Steel",None),602: ("Electric",None),
    603: ("Electric",None),604: ("Electric",None),605: ("Psychic",None),
    606: ("Psychic",None),607: ("Ghost","Fire"),608: ("Ghost","Fire"),
    609: ("Ghost","Fire"),610: ("Dragon",None),611: ("Dragon",None),
    612: ("Dragon",None),613: ("Ice",None),614: ("Ice",None),
    615: ("Ice",None),616: ("Bug",None),617: ("Bug",None),
    618: ("Ground","Electric"),619: ("Fighting",None),620: ("Fighting",None),
    621: ("Dragon",None),622: ("Ground","Ghost"),623: ("Ground","Ghost"),
    624: ("Dark","Steel"),625: ("Dark","Steel"),626: ("Normal",None),
    627: ("Normal","Flying"),628: ("Normal","Flying"),629: ("Dark","Flying"),
    630: ("Dark","Flying"),631: ("Fire",None),632: ("Bug","Steel"),
    633: ("Dark","Dragon"),634: ("Dark","Dragon"),635: ("Dark","Dragon"),
    636: ("Bug","Fire"),637: ("Bug","Fire"),638: ("Steel","Fighting"),
    639: ("Rock","Fighting"),640: ("Grass","Fighting"),
    641: ("Flying",None),642: ("Electric","Flying"),
    643: ("Dragon","Fire"),644: ("Dragon","Electric"),
    645: ("Ground","Flying"),646: ("Dragon","Ice"),
    647: ("Water","Fighting"),648: ("Normal","Psychic"),
    649: ("Bug","Steel"),
}

# ── Type-based move pool (Gen 5 move IDs) ──
TYPE_MOVES = {
    "Normal":   [102, 332, 425, 269],  # Return, Body Slam, Double-Edge, Facade
    "Fire":     [53, 126, 52, 59],     # Flamethrower, Fire Blast, Ember, Fire Spin
    "Water":    [57, 56, 55, 127],     # Surf, Hydro Pump, Waterfall, Scald
    "Electric": [85, 86, 84, 97],      # Thunderbolt, Thunder, Thunder Shock, Agility
    "Grass":    [76, 75, 79, 77],      # Solar Beam, Petal Dance, Energy Ball, Grass Knot
    "Ice":      [58, 59, 54, 55],      # Ice Beam, Blizzard, Aurora Beam, Icy Wind
    "Fighting": [90, 91, 92, 93],      # Aura Sphere, Focus Blast, Brick Break, Low Kick
    "Poison":   [93, 92, 94, 398],     # Sludge Bomb, Poison Jab, Gunk Shot, Cross Poison
    "Ground":   [89, 88, 90, 33],      # Earthquake, Dig, Bone Rush, Struggle
    "Flying":   [156, 158, 159, 155],  # Aerial Ace, Fly, Brave Bird, Air Slash
    "Psychic":  [94, 95, 96, 97],      # Psychic, Psyshock, Confusion, Agility
    "Bug":      [169, 168, 170, 171],  # X-Scissor, Megahorn, U-turn, Bug Buzz
    "Rock":     [88, 89, 222, 106],    # Stone Edge, Rock Slide, Rock Blast, Stealth Rock
    "Ghost":    [101, 104, 105, 109],  # Shadow Ball, Shadow Claw, Shadow Force, Night Shade
    "Dragon":   [295, 296, 297, 293],  # Outrage, Dragon Claw, Draco Meteor, Dragon Pulse
    "Dark":     [297, 298, 299, 300],  # Dark Pulse, Night Slash, Crunch, Nasty Plot
    "Steel":    [169, 170, 210, 211],  # Iron Head, Flash Cannon, Metal Claw, Bullet Punch
}

def get_moves_for_type(t1, t2):
    """Get 4 moves based on Pokemon's types."""
    pool = []
    for t in [t1, t2]:
        if t and t in TYPE_MOVES:
            pool.extend(TYPE_MOVES[t])
    pool = list(dict.fromkeys(pool))  # deduplicate preserving order
    if len(pool) >= 4:
        return pool[:4]
    # Fallback: normal moves
    normal_moves = [m for m in TYPE_MOVES["Normal"] if m not in pool]
    pool.extend(normal_moves)
    return pool[:4]

# Build predefined move sets
PREDEFINED_MOVES = {}
for entry in LEGENDARIES + PSEUDO_LEGENDARIES + STARTERS + EEVEELUTIONS + PIKACHU_FAMILY + SIGILYPH:
    PREDEFINED_MOVES[entry[0]] = entry[2]

def get_moves(species_id, moves_cache):
    """Get moves for a species. Uses predefined → evolution propagation → type-based."""
    if species_id in moves_cache:
        return moves_cache[species_id]
    if species_id in PREDEFINED_MOVES:
        moves_cache[species_id] = PREDEFINED_MOVES[species_id]
        return moves_cache[species_id]
    # Check if evolved form has predefined moves → propagate backwards
    if species_id in EVOLVES_TO:
        evo_id = EVOLVES_TO[species_id]
        evo_moves = get_moves(evo_id, moves_cache)
        if evo_moves != [33, 33, 33, 33]:
            moves_cache[species_id] = evo_moves
            return evo_moves
    # Check if any child in evolution chain has moves → propagate upwards
    # (covers baby Pokemon like Pichu getting Pikachu's moves)
    for child_id, parent_id in PREV_EVOLUTION.items():
        if parent_id == species_id:
            child_moves = get_moves(child_id, moves_cache)
            if child_moves != [33, 33, 33, 33]:
                moves_cache[species_id] = child_moves
                return child_moves
    # Type-based assignment
    t1, t2 = POKEMON_TYPES.get(species_id, ("Normal", None))
    moves = get_moves_for_type(t1, t2)
    moves_cache[species_id] = moves
    return moves

def slot_offset(box, slot):
    return BOX_BASE + (box - 1) * BOX_SIZE + (slot - 1) * SLOT_SIZE

def pkm_bytes_to_ar_lines(data_136):
    lines = []
    for i in range(0, 136, 8):
        chunk = data_136[i:i+8]
        hi = struct.unpack_from('<I', chunk, 0)[0]
        lo = struct.unpack_from('<I', chunk, 4)[0]
        lines.append(f"{hi:08X} {lo:08X}")
    return lines

def generate_single_cheat(species_entries, cheat_name):
    """Generate one cheat entry writing all species to boxes in order,
    clearing remaining slots (650-720)."""
    lines = []
    lines.append(f"[{cheat_name}]-")
    lines.append("94000130 FCFF0000")
    lines.append("B2000024 00000000")

    for idx, (species_id, species_name, moves, level) in enumerate(species_entries):
        box = idx // SLOTS_BOX + 1
        slot = idx % SLOTS_BOX + 1
        offset = slot_offset(box, slot)

        if species_id in SLOW_SPECIES:
            growth_rate = "slow"
        elif species_id in MEDIUM_SLOW_SPECIES:
            growth_rate = "medium_slow"
        else:
            growth_rate = "medium_fast"

        plain = create_pokemon(
            species_id, species_name, moves,
            growth_rate=growth_rate, shiny=True, level=100,
            met_level=50
        )
        encrypted = encrypt_stored(plain)

        lines.append(f"E{offset:07X} {SLOT_SIZE:08X}")
        lines.extend(pkm_bytes_to_ar_lines(encrypted))

    # Clear remaining slots (650-720)
    for slot_idx in range(649, 720):
        box = slot_idx // SLOTS_BOX + 1
        slot = slot_idx % SLOTS_BOX + 1
        offset = slot_offset(box, slot)
        lines.append(f"E{offset:07X} {SLOT_SIZE:08X}")
        for _ in range(17):
            lines.append("00000000 00000000")

    lines.append("D2000000 00000000")
    lines.append("")
    return lines

def main():
    # Pre-compute moves for all 649 species with propagation
    moves_cache = {}
    species = []
    type_only = 0
    propagated = 0
    predefined = 0

    for sid in range(1, 650):
        name = POKEMON_NAMES[sid - 1]
        moves = get_moves(sid, moves_cache)
        species.append((sid, name, moves, 100))

    # Count move sources
    for sid in range(1, 650):
        name = POKEMON_NAMES[sid - 1]
        moves = moves_cache[sid]
        if sid in PREDEFINED_MOVES:
            predefined += 1
        elif sid in EVOLVES_TO and EVOLVES_TO[sid] in PREDEFINED_MOVES:
            propagated += 1
        elif any(child == sid for child in PREV_EVOLUTION.values()) and any(
            PREV_EVOLUTION.get(c) == sid and c in PREDEFINED_MOVES
            for c in PREV_EVOLUTION
        ):
            propagated += 1
        else:
            type_only += 1

    assert len(species) == 649

    os.makedirs(CHEATS_DIR, exist_ok=True)

    # Remove old box-related entries from file
    header = ""
    if os.path.exists(CHEAT_FILE):
        with open(CHEAT_FILE, 'r') as f:
            content = f.read()
        lines = content.split('\n')
        filtered = []
        skip = False
        for line in lines:
            if line.startswith('[Box ') or line.startswith('[Fill ALL 649') or line.startswith('[Organize Boxes'):
                skip = True
                continue
            if skip:
                if line.startswith('[') or line == '':
                    skip = False
                    if line.startswith('['):
                        filtered.append(line)
                continue
            filtered.append(line)
        header = '\n'.join(filtered).rstrip('\n') + '\n\n'

    with open(CHEAT_FILE, 'w') as f:
        f.write(header)

    cheat_lines = generate_single_cheat(species, "Organize Boxes #001-#649 (L+R)")
    with open(CHEAT_FILE, 'a') as f:
        f.write('\n'.join(cheat_lines))

    print(f"Written {len(cheat_lines)} lines to {CHEAT_FILE}")
    print(f"Cheat name: [Organize Boxes #001-#649 (L+R)]-")
    print(f"{len(species)} unique species, no duplicates. Remaining 71 slots cleared.")
    print(f"Move sources: {predefined} predefined + {propagated} evolution-propagated + {type_only} type-based")
    print("Activate in NooDS: Tools > Cheats, enable it, then press L+R at a PC.")

if __name__ == "__main__":
    main()
