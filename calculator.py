import copy


INITIAL_DECK_COUNTS = {
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
    '+2': 1,
    '+4': 1,
    '+6': 1,
    '+8': 1,
    '+10': 1,
    'x2': 1
}


class Flip7Calculator:

    def __init__(self):
        self.my_line = []
        self.table_line = []


    def reset_round(self):
        self.my_line = []
        self.table_line = []


    def add_to_my_line(self, card):
        self.my_line.append(card)


    def add_to_table_line(self, card):
        self.table_line.append(card)


    def _calculate_score(self, line):
        number_line = [c for c in line if isinstance(c, int)]
        if len(set(number_line)) == len(number_line):
            number_sum = sum(number_line)

            if 'x2' in line:
                number_sum *= 2 # apply x2 multiplier if present

            bonus_sum = sum([int(c[1:]) for c in line if isinstance(c, str) and c.startswith('+')]) # add all the bonus cards if present

            return number_sum + bonus_sum
        return 0
    
    
    def calculate_stats(self):

        # identify visible cards and remaining deck
        visible_cards = self.my_line + self.table_line
        remaining_deck = copy.deepcopy(INITIAL_DECK_COUNTS)
        for card in visible_cards:
            if card in remaining_deck and remaining_deck[card] > 0:
                remaining_deck[card] -= 1

        # calculate probabilities
        n_total = sum(remaining_deck.values())
        if n_total == 0:
            return {
                "deck_empty": True
            }
        number_cards = set([card for card in self.my_line if isinstance(card, int)])
        bust_cards_left = sum(remaining_deck.get(num, 0) for num in number_cards)
        p_bust = bust_cards_left / n_total
        p_safe = 1.0 - p_bust

        # calculate Expected Value (EV)
        expected_new_score = 0.0
        for card, count in remaining_deck.items():
            if count == 0:
                continue
                
            p_draw = count / n_total
            
            if isinstance(card, int) and card in number_cards:
                expected_new_score += (p_draw * 0) 
            else:
                simulated_line = self.my_line + [card]
                simulated_score = self._calculate_score(simulated_line)
                
                sim_unique = set([card for card in simulated_line if isinstance(card, int)])
                if len(sim_unique) == 7:
                    simulated_score += 15
                    
                expected_new_score += (p_draw * simulated_score)

        # calculate current score
        current_score = self._calculate_score(self.my_line)
        if len(number_cards) >= 7:
            current_score += 15

        return {
            "deck_empty": False,
            "current_score": current_score,
            "p_bust": p_bust,
            "p_safe": p_safe,
            "ev": expected_new_score
        }
