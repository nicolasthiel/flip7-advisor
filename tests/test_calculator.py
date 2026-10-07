import unittest

from calculator import Flip7Calculator
from schema import DeckConfigJSON


def get_base_deck_counts() -> DeckConfigJSON:
    return {
        12: 12,
        11: 11,
        10: 10,
        9: 9,
        8: 8,
        7: 7,
        6: 6,
        5: 5,
        4: 4,
        3: 3,
        2: 2,
        1: 1,
        0: 1,
        "+2": 1,
        "+4": 1,
        "+6": 1,
        "+8": 1,
        "+10": 1,
        "x2": 1,
        "fz": 3,
        "f3": 3,
        "sc": 3,
    }


class TestScoreCalculation(unittest.TestCase):

    def setUp(self):
        self.calc = Flip7Calculator(get_base_deck_counts())

    def test_numbers_only(self):
        line = [12, 4, 3]
        self.assertEqual(self.calc._calculate_score(line), 19)

    def test_multiplier_applies_to_numbers_only(self):
        line = [10, 5, "x2"]
        # (10 + 5) * 2 = 30
        self.assertEqual(self.calc._calculate_score(line), 30)

    def test_bonus_cards_added_after_multiplier(self):
        line = [10, "x2", "+4", "+2"]
        # (10 * 2) + 4 + 2 = 26
        self.assertEqual(self.calc._calculate_score(line), 26)

    def test_flip7_bonus_with_seven_number_cards(self):
        line = [0, 1, 2, 3, 4, 5, 6]
        # Sum = 21, plus 15 Flip7 bonus = 36
        self.assertEqual(self.calc._calculate_score(line), 36)

    def test_no_flip7_bonus_with_six_number_cards(self):
        line = [1, 2, 3, 4, 5, 6]
        # Sum = 21, no bonus
        self.assertEqual(self.calc._calculate_score(line), 21)

    def test_flip7_bonus_with_multiplier_and_bonus_cards(self):
        line = [0, 1, 2, 3, 4, 5, 6, "x2", "+10"]
        # (21 * 2) + 10 + 15 = 42 + 10 + 15 = 67
        self.assertEqual(self.calc._calculate_score(line), 67)

    def test_action_cards_do_not_add_points(self):
        line = [7, "sc", "fz", "f3"]
        self.assertEqual(self.calc._calculate_score(line), 7)

    def test_empty_line_scores_zero(self):
        self.assertEqual(self.calc._calculate_score([]), 0)


class TestDeckTracking(unittest.TestCase):

    def setUp(self):
        self.calc = Flip7Calculator(get_base_deck_counts())

    def test_visible_cards_reduce_remaining_deck(self):
        self.calc.add_to_my_line(12)
        self.calc.add_to_table_line(12)
        self.calc.add_to_discard_pile(12)

        rem = self.calc._get_remaining_deck()
        self.assertEqual(rem[12], 9)  # 12 - 3 = 9

    def test_remove_cards_restores_remaining_deck(self):
        self.calc.add_to_my_line(8)
        self.assertEqual(self.calc._get_remaining_deck()[8], 7)
        self.calc.remove_from_my_line(8)
        self.assertEqual(self.calc._get_remaining_deck()[8], 8)

    def test_remove_missing_card_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.calc.remove_from_my_line(99)

        with self.assertRaises(ValueError):
            self.calc.remove_from_table_line(99)

    def test_reset_round_clears_all_visible_cards(self):
        self.calc.add_to_my_line(12)
        self.calc.add_to_table_line(10)
        self.calc.add_to_discard_pile("sc")

        self.calc.reset_round()
        self.assertEqual(self.calc.my_line, [])
        self.assertEqual(self.calc.table_line, [])
        self.assertEqual(self.calc.discard_pile, [])

        rem = self.calc._get_remaining_deck()
        self.assertEqual(rem[12], 12)
        self.assertEqual(rem[10], 10)
        self.assertEqual(rem["sc"], 3)

    def test_get_state_returns_deep_copies(self):
        state = self.calc.get_state()
        state["my_line"].append(12)
        self.assertEqual(self.calc.my_line, [])


class TestProbabilitiesAndExpectedValue(unittest.TestCase):

    def setUp(self):
        self.calc = Flip7Calculator(get_base_deck_counts())

    def test_probabilities_standard_line(self):
        self.calc.add_to_my_line(12)
        stats = self.calc.calculate_stats()

        self.assertFalse(stats["deck_empty"])
        self.assertEqual(stats["current_score"], 12)
        # 11 twelves left in deck out of 93 remaining cards
        expected_p_bust = 11 / 93
        self.assertAlmostEqual(stats["p_bust"], expected_p_bust, places=5)
        self.assertAlmostEqual(stats["p_safe"], 1.0 - expected_p_bust, places=5)
        self.assertGreater(stats["ev"], 0.0)

    def test_second_chance_eliminates_bust_probability(self):
        self.calc.add_to_my_line(12)
        self.calc.add_to_my_line("sc")
        stats = self.calc.calculate_stats()

        self.assertEqual(stats["p_bust"], 0.0)
        self.assertEqual(stats["p_safe"], 1.0)

    def test_second_chance_ev_with_duplicate(self):
        # Construct a simple deck where only card 12 is in the deck
        tiny_deck = {
            12: 2,
            11: 0,
            10: 0,
            9: 0,
            8: 0,
            7: 0,
            6: 0,
            5: 0,
            4: 0,
            3: 0,
            2: 0,
            1: 0,
            0: 0,
            "+2": 0,
            "+4": 0,
            "+6": 0,
            "+8": 0,
            "+10": 0,
            "x2": 0,
            "fz": 0,
            "f3": 0,
            "sc": 0,
        }
        calc = Flip7Calculator(tiny_deck)
        calc.add_to_my_line(12)
        calc.add_to_my_line("sc")

        # In deck, only one 12 remains (since one 12 is in my_line)
        stats = calc.calculate_stats()
        # Holding 'sc' protects against bust; cards are not removed automatically
        # Simulated line becomes [12, 'sc', 12] with score 24.0
        self.assertAlmostEqual(stats["ev"], 24.0)

    def test_freeze_locks_in_current_score(self):
        tiny_deck = {
            12: 0,
            11: 0,
            10: 0,
            9: 0,
            8: 0,
            7: 0,
            6: 0,
            5: 0,
            4: 0,
            3: 0,
            2: 0,
            1: 0,
            0: 0,
            "+2": 0,
            "+4": 0,
            "+6": 0,
            "+8": 0,
            "+10": 0,
            "x2": 0,
            "fz": 1,
            "f3": 0,
            "sc": 0,
        }
        calc = Flip7Calculator(tiny_deck)
        calc.add_to_my_line(10)

        stats = calc.calculate_stats()
        # Drawing fz locks in current score 10
        self.assertAlmostEqual(stats["ev"], 10.0)

    def test_flip_three_simulates_three_draws(self):
        # A deck with 3 safe bonus cards: +2, +4, +6 and 1 f3
        tiny_deck = {
            12: 0,
            11: 0,
            10: 0,
            9: 0,
            8: 0,
            7: 0,
            6: 0,
            5: 0,
            4: 0,
            3: 0,
            2: 0,
            1: 0,
            0: 0,
            "+2": 1,
            "+4": 1,
            "+6": 1,
            "+8": 0,
            "+10": 0,
            "x2": 0,
            "fz": 0,
            "f3": 1,
            "sc": 0,
        }
        calc = Flip7Calculator(tiny_deck)
        calc.add_to_my_line(10)

        # Directly testing _simulate_f3_draws:
        # After drawing f3, the remaining deck has +2, +4, +6.
        # Resolving 3 draws yields exactly 10 + 2 + 4 + 6 = 22.0.
        deck_after_f3 = {"+2": 1, "+4": 1, "+6": 1}
        direct_f3_score = calc._simulate_f3_draws([10], deck_after_f3, draws_left=3)
        self.assertAlmostEqual(direct_f3_score, 22.0)

        # Testing composite EV from the 4-card deck:
        # Draws:
        # P(+2) = 0.25 -> score 12
        # P(+4) = 0.25 -> score 14
        # P(+6) = 0.25 -> score 16
        # P(f3) = 0.25 -> score 22
        # Expected EV = 0.25 * (12 + 14 + 16 + 22) = 16.0
        stats = calc.calculate_stats()
        self.assertAlmostEqual(stats["ev"], 16.0)

    def test_empty_deck_stats(self):
        empty_deck = {k: 0 for k in get_base_deck_counts()}
        calc = Flip7Calculator(empty_deck)
        stats = calc.calculate_stats()
        self.assertTrue(stats.get("deck_empty"))


if __name__ == "__main__":
    unittest.main()
