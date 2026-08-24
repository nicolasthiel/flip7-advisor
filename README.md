# Flip7 Advisor

A probability and Expected Value ($EV$) calculator for **[Flip7](https://boardgamegeek.com/boardgame/420087/flip-7)**, the card game designed by Eric Olsen.

---

## Overview

In Flip7, card frequencies match their face value (twelve 12s, eleven 11s, ... down to one 1, plus one 0). Players take turns and decide whether to draw a card (hit) and potentially increase their score or stay and receive their current score. The player's score is determined by the sum of their card line. Drawing a duplicate number card causes a bust and results in zero points.
The game is played across multiple rounds where players accumulate and carry over points from round to round, with each round ending when all players have either stopped or busted (or when someone achieves a Flip7, i.e. has seven number cards), until the first player reaches 200 or more points and is declared winner.

For a detailed overview on how to play Flip7 and how scores are calculated, please refer to the [official rulebook](https://www.scribd.com/document/821389083/Flip-7-Rules).

_Flip7 Advisor_ tracks visible table cards to deduce the remaining deck composition, outputting the probability to bust ($P_{\text{bust}}$) and the Expected Value ($EV$) of drawing a card to inform your decision to hit or stay.

---

## Quickstart

### Prerequisites
* Python 3.8+ (Standard Library only)

### Run
```bash
git clone https://github.com/nicolasthiel/flip7-advisor.git
cd flip7-advisor
python main.py
```

Running `python main.py` starts the game and automatically loads the default deck config from `deck_configs/base.json`.

### Run With A Custom Deck Config
```bash
python main.py --deck-config path/to/your-config.json
```

The config file must contain all supported card keys with integer counts.

### Commands
`m <cards>` adds one or more cards to your line \
`md <cards>` moves one or more cards from your line to the discard pile \
`td <cards>` moves one or more cards from the table's line to the discard pile \
`t <cards>` adds one or more cards to the table's line \
`c` calculates $P_{\text{bust}}$​, $P_{\text{safe}}$​, and $EV$ given the current lines \
`d` displays your line, the table line and the discard pile \
`r` resets table for a new round \
`q` exits

### Example
```console
Flip7> t 12 12 8 4
Table Cards: [12, 12, 8, 4]
Flip7> m 12
My Line: [12]
Flip7> c

==============================
Current Score:      12
Risk of Busting:    10.1%
Chance of Safe Hit: 89.9%
Expected Score EV:  16.8
==============================

Flip7> t 0 1 6
Table Cards: [12, 12, 8, 4, 0, 1, 6]
Flip7> m 4
My Line: [12, 4]
Flip7> c

==============================
Current Score:      16
Risk of Busting:    12.9%
Chance of Safe Hit: 87.1%
Expected Score EV:  20.1
==============================
```
