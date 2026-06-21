# Pokemon Black (USA/Europe) — NooDS Action Replay Cheats

**91 cheats** for **Pokemon Black Version (USA, Europe)** (Game ID: `IRBO-106820A5`)
on the **NooDS** emulator. Covers all legendaries, mythicals, pseudo-legendaries,
starters, Eeveelutions, and utility codes.

---

## Auto-Enabled (`+`)

| Cheat | Effect |
|-------|--------|
| **Infinite HP** | Your Pokemon never faint |
| **EXP x64** | 64x XP after each battle (Lv.100 in 1-2 fights) |
| **100% Catch Rate** | Any ball catches any wild Pokemon |
| **Catch Trainer Pokemon** | Adds "Catch" option during trainer battles |

---

## Utility (`-`, activate in menu)

| Cheat | Use | Effect |
|-------|-----|--------|
| **Walk Through Walls** | `L+A` on / `L+B` off | Pass through any obstacle |
| **Max Money** | Hold `SELECT` | 9,999,999 Pokedollars |
| **900 Master Balls** | `L+R` | 900 Master Balls in item slot 1 |
| **900 Rare Candies** | `L+R` | 900 Rare Candies in recovery pouch |
| **Complete Pokedex** | Hold `SELECT` | All 649 Pokemon seen & caught |
| **Shiny Wild Encounters** | Hold `L` on / release `L` off | All wild encounters are shiny |

---

## Save Injector (`inject_legendaries.py`)

> Populates PC boxes with real Pokemon or sorts existing ones.

| Flag | Effect |
|------|--------|
| *(no flags)* | Injects ~60 legendaries/pseudos/starters |
| `--all` | Injects **all 649 species** into PC boxes |
| `--shiny` | All injected Pokemon are **shiny** (star sparkle) |
| `--pokedex` | Also fills all Pokedex seen/caught flags |
| `--organize` | **Sorts existing Pokemon** by National Dex #001-#649 across all boxes |

**To fill your PC with all 649 shiny Pokemon and complete the Pokedex:**

```bash
python inject_legendaries.py --all --shiny --pokedex
```

**To sort already-caught Pokemon by dex number:**

```bash
python inject_legendaries.py --organize
```

The script auto-detects your save file at `~/Emulator/Pokemon - Black Version.../`. You can also pass a custom path:

```bash
python inject_legendaries.py /path/to/your/save.sav --all --shiny --pokedex
python inject_legendaries.py /path/to/your/save.sav --organize
```

---

## AR Box Generator (`generate_box_cheats.py`)

> Generates a single Action Replay cheat that fills **all 24 PC boxes** with every Pokemon from #001 Bulbasaur to #649 Genesect in National Dex order.

| Property | Value |
|----------|-------|
| **Cheat name** | `[Organize Boxes #001-#649 (L+R)]-` |
| **Activation** | `L+R` at any PC in-game |
| **Species** | 649 unique, no duplicates |
| **Moves** | Predefined (78) + evolution-propagated (24) + type-based STAB (547) — **0 Struggle-only** |

**Usage:**

```bash
python generate_box_cheats.py
```

This appends the cheat to your NooDS cheat file at `~/.var/app/com.hydra.noods/config/noods/cheats/`. The remaining 71 slots (boxes 23–24) are cleared to zero. Each Pokemon is level 100 and shiny.

## Encounter Codes (hold `SELECT` in grass)

### Kanto Legendaries (5)

| Pokemon | National Dex | Hex ID |
|---------|-------------|--------|
| Articuno | #144 | `00000090` |
| Zapdos | #145 | `00000091` |
| Moltres | #146 | `00000092` |
| Mewtwo | #150 | `00000096` |
| Mew | #151 | `00000097` |

### Johto Legendaries (6)

| Pokemon | National Dex | Hex ID |
|---------|-------------|--------|
| Raikou | #243 | `000000F3` |
| Entei | #244 | `000000F4` |
| Suicune | #245 | `000000F5` |
| Lugia | #249 | `000000F9` |
| Ho-Oh | #250 | `000000FA` |
| Celebi | #251 | `000000FB` |

### Hoenn Legendaries (10)

| Pokemon | National Dex | Hex ID |
|---------|-------------|--------|
| Regirock | #377 | `00000179` |
| Regice | #378 | `0000017A` |
| Registeel | #379 | `0000017B` |
| Latias | #380 | `0000017C` |
| Latios | #381 | `0000017D` |
| Kyogre | #382 | `0000017E` |
| Groudon | #383 | `0000017F` |
| Rayquaza | #384 | `00000180` |
| Jirachi | #385 | `00000181` |
| Deoxys | #386 | `00000182` |

### Sinnoh Legendaries (14)

| Pokemon | National Dex | Hex ID |
|---------|-------------|--------|
| Uxie | #480 | `000001E0` |
| Mesprit | #481 | `000001E1` |
| Azelf | #482 | `000001E2` |
| Dialga | #483 | `000001E3` |
| Palkia | #484 | `000001E4` |
| Heatran | #485 | `000001E5` |
| Regigigas | #486 | `000001E6` |
| Giratina | #487 | `000001E7` |
| Cresselia | #488 | `000001E8` |
| Phione | #489 | `000001E9` |
| Manaphy | #490 | `000001EA` |
| Darkrai | #491 | `000001EB` |
| Shaymin | #492 | `000001EC` |
| Arceus | #493 | `000001ED` |

### Unova Legendaries & Mythicals (13)

| Pokemon | National Dex | Hex ID |
|---------|-------------|--------|
| Victini | #494 | `000001EE` |
| Cobalion | #638 | `0000027E` |
| Terrakion | #639 | `0000027F` |
| Virizion | #640 | `00000280` |
| Tornadus | #641 | `00000281` |
| Thundurus | #642 | `00000282` |
| Reshiram | #643 | `00000283` |
| Zekrom | #644 | `00000284` |
| Landorus | #645 | `00000285` |
| Kyurem | #646 | `00000286` |
| Keldeo | #647 | `00000287` |
| Meloetta | #648 | `00000288` |
| Genesect | #649 | `00000289` |

### Pseudo-Legendaries & Giants (13)

| Pokemon | National Dex | Hex ID |
|---------|-------------|--------|
| Dragonite | #149 | `00000095` |
| Snorlax | #143 | `0000008F` |
| Gyarados | #130 | `00000082` |
| Tyranitar | #248 | `000000F8` |
| Salamence | #373 | `00000175` |
| Metagross | #376 | `00000178` |
| Garchomp | #445 | `000001BD` |
| Lucario | #448 | `000001C0` |
| Milotic | #350 | `0000015E` |
| Steelix | #208 | `000000D0` |
| Wailord | #321 | `00000141` |
| Hydreigon | #635 | `0000027B` |
| Volcarona | #637 | `0000027D` |

### Requested Regular Pokemon (3)

| Pokemon | National Dex | Hex ID |
|---------|-------------|--------|
| Pikachu | #25 | `00000019` |
| Raichu | #26 | `0000001A` |
| Sigilyph | #561 | `00000231` |

### Eevee & Eeveelutions (8)

| Pokemon | National Dex | Hex ID |
|---------|-------------|--------|
| Eevee | #133 | `00000085` |
| Vaporeon | #134 | `00000086` |
| Jolteon | #135 | `00000087` |
| Flareon | #136 | `00000088` |
| Espeon | #196 | `000000C4` |
| Umbreon | #197 | `000000C5` |
| Leafeon | #470 | `000001D6` |
| Glaceon | #471 | `000001D7` |

### All Starters (15)

| Pokemon | National Dex | Hex ID |
|---------|-------------|--------|
| Bulbasaur | #1 | `00000001` |
| Charmander | #4 | `00000004` |
| Squirtle | #7 | `00000007` |
| Chikorita | #152 | `00000098` |
| Cyndaquil | #155 | `0000009B` |
| Totodile | #158 | `0000009E` |
| Treecko | #252 | `000000FC` |
| Torchic | #255 | `000000FF` |
| Mudkip | #258 | `00000102` |
| Turtwig | #387 | `00000183` |
| Chimchar | #390 | `00000186` |
| Piplup | #393 | `00000189` |
| Snivy | #495 | `000001EF` |
| Tepig | #498 | `000001F2` |
| Oshawott | #501 | `000001F5` |

---

## How to Get Everything

1. Enable **Complete Pokedex** (hold SELECT) — marks all 649 as seen & caught
2. Enable **900 Master Balls** (L+R) — infinite supply
3. Enable the desired **Encounter** code — hold SELECT in grass, walk into wild encounter
4. Catch with any ball (100% Catch Rate)
5. Use **EXP x64** or **Rare Candies** to hit Lv.100 instantly

---

## Installation

```bash
chmod +x install_pokemon_black_cheats.sh
./install_pokemon_black_cheats.sh
```

Or copy to `~/.var/app/com.hydra.noods/config/noods/cheats/`.

---

## Usage in NooDS

1. Launch **NooDS** and load Pokemon Black
2. **Tools → Action Replay**
3. Toggle cheats on/off
4. Resume game

---

## Encounter Code Template

To add any of the 649 Pokemon as an encounter:

```
94000130 FFFB0000
C0000000 0000002F
12250010 00000XXX
DC000000 00000004
D2000000 00000000
```

Replace `XXX` with the National Dex number in hex (e.g. `283` for Reshiram).

---

## NooDS Cheat File Format

```
[Cheat Name]+          ← '+' = enabled, '-' = disabled
XXXXXXXX XXXXXXXX      ← AR code (8 hex, space, 8 hex)
                       ← blank line separates entries
```
