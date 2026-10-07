import copy
from typing import Any, Dict, List

from schema import DeckConfigJSON


class Flip7Calculator:

    def __init__(self, deck_counts: DeckConfigJSON):
        self.my_line: List[Any] = []
        self.table_line: List[Any] = []
        self.discard_pile: List[Any] = []
        self.deck_counts = copy.deepcopy(deck_counts)

    def reset_round(self):
        self.my_line = []
        self.table_line = []
        self.discard_pile = []

    def add_to_my_line(self, card):
        self.my_line.append(card)

    def remove_from_my_line(self, card):
        if card in self.my_line:
            self.my_line.remove(card)
        else:
            raise ValueError(f"Card {card} not found in your line.")

    def remove_from_table_line(self, card):
        if card in self.table_line:
            self.table_line.remove(card)
        else:
            raise ValueError(f"Card {card} not found in table line.")

    def add_to_table_line(self, card):
        self.table_line.append(card)

    def add_to_discard_pile(self, card):
        self.discard_pile.append(card)

    def _get_remaining_deck(self) -> Dict[Any, int]:
        visible_cards = self.my_line + self.table_line + self.discard_pile
        remaining_deck = copy.deepcopy(self.deck_counts)
        for card in visible_cards:
            if card in remaining_deck and remaining_deck[card] > 0:
                remaining_deck[card] -= 1
        return remaining_deck

    def get_state(self) -> Dict[str, Any]:
        return {
            "deck_counts": copy.deepcopy(self.deck_counts),
            "remaining_deck": self._get_remaining_deck(),
            "my_line": list(self.my_line),
            "table_line": list(self.table_line),
            "discard_pile": list(self.discard_pile),
        }

    def _calculate_score(self, line: List[Any]) -> int:
        number_line = [c for c in line if isinstance(c, int)]
        number_sum = sum(number_line)

        if "x2" in line:
            number_sum *= 2  # apply x2 multiplier if present

        bonus_sum = sum(
            int(c[1:]) for c in line if isinstance(c, str) and c.startswith("+")
        )
        score = number_sum + bonus_sum

        # apply Flip7 bonus if there are 7 or more number cards
        if len(number_line) >= 7:
            score += 15

        # if duplicate number cards are present and "sc" is not, the score is 0
        if len(number_line) != len(set(number_line)) and "sc" not in line:
            score = 0

        return score

    def _simulate_f3_draws(
        self, line: List[Any], remaining_deck: Dict[Any, int], draws_left: int = 3
    ) -> float:
        """Simulate sequential draws caused by the Flip Three (f3) card."""
        if draws_left <= 0:
            return float(self._calculate_score(line))

        n_total = sum(remaining_deck.values())
        if n_total == 0:
            return float(self._calculate_score(line))

        expected = 0.0
        line_numbers = {c for c in line if isinstance(c, int)}

        for card, count in remaining_deck.items():
            if count == 0:
                continue

            p_draw = count / n_total
            next_deck = dict(remaining_deck)
            next_deck[card] -= 1

            if isinstance(card, int) and card in line_numbers and "sc" not in line:
                sub_score = 0.0
            elif card == "fz":
                sub_score = float(self._calculate_score(line))
            elif card == "f3":
                sub_score = self._simulate_f3_draws(
                    line, next_deck, draws_left - 1
                )
            else:
                next_line = list(line)
                next_line.append(card)
                sub_score = self._simulate_f3_draws(
                    next_line, next_deck, draws_left - 1
                )

            expected += p_draw * sub_score

        return expected

    def calculate_stats(self) -> Dict[str, Any]:
        remaining_deck = self._get_remaining_deck()

        # calculate probabilities
        n_total = sum(remaining_deck.values())
        if n_total == 0:
            return {"deck_empty": True}

        number_cards = {card for card in self.my_line if isinstance(card, int)}
        bust_cards_left = sum(remaining_deck.get(num, 0) for num in number_cards)
        p_bust = 0.0 if "sc" in self.my_line else bust_cards_left / n_total
        p_safe = 1.0 - p_bust

        # calculate current score
        current_score = self._calculate_score(self.my_line)

        # calculate Expected Value (EV)
        expected_new_score = 0.0
        for card, count in remaining_deck.items():
            if count == 0:
                continue

            p_draw = count / n_total

            if isinstance(card, int) and card in number_cards and "sc" not in self.my_line:
                # Bust results in 0 score
                expected_new_score += p_draw * 0
            elif card == "fz":
                # Freeze safely locks in current score
                expected_new_score += p_draw * current_score
            elif card == "f3":
                # Flip Three requires resolving 3 sequential draws
                deck_after_draw = dict(remaining_deck)
                deck_after_draw["f3"] -= 1
                f3_score = self._simulate_f3_draws(
                    self.my_line, deck_after_draw, draws_left=3
                )
                expected_new_score += p_draw * f3_score
            else:
                simulated_line = self.my_line + [card]
                simulated_score = self._calculate_score(simulated_line)
                expected_new_score += p_draw * simulated_score

        return {
            "deck_empty": False,
            "current_score": current_score,
            "p_bust": p_bust,
            "p_safe": p_safe,
            "ev": expected_new_score,
        }
