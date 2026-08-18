# Flip7 Advisor

A probability and Expected Value ($EV$) calculator for **[Flip 7](https://boardgamegeek.com/boardgame/420087/flip-7)**, the card game designed by Eric Olsen.

---

## Overview

In Flip 7, card frequencies match their face value (twelve 12s, eleven 11s, ... down to one 1, plus one 0). The player's score is determined by the sum of their card line. Drawing a duplicate number card causes a bust and results in zero points.
The game is played across multiple rounds where players accumulate and carry over points from round to round, with each round ending when all players have either stopped or busted (or when someone achieves a Flip 7, i.e. has seven number cards), until the first player reaches 200 or more points and is declared winner.

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
python CLI.py
```

### Commands
`m <cards>` adds one or more cards to your line \
`t <cards>` adds one or more cards to the table's line \
`c` calculates $P_{\text{bust}}$​, $P_{\text{safe}}$​, and $EV$ given the current lines \
`r` resets table for a new round \
`q` exits
