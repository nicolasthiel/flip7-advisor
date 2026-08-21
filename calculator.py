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
    'x2': 1,
    'fz': 3,
    'f3': 3,
    'sc': 3
}


class Flip7Calculator:

    def __init__(self):
        self.my_line = []
        self.table_line = []
        self.discard_pile = []


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


    def _calculate_score(self, line):
        number_line = [c for c in line if isinstance(c, int)]
        
        number_sum = sum(number_line)

        if 'x2' in line:
            number_sum *= 2 # apply x2 multiplier if present

        bonus_sum = sum([int(c[1:]) for c in line if isinstance(c, str) and c.startswith('+')]) # add all the bonus cards if present
        score = number_sum + bonus_sum

        # apply Flip7 bonus if there are 7 number cards
        if len(number_line) >= 7:
            score += 15

        return score
        

    def calculate_stats(self):

        # identify visible cards and remaining deck
        visible_cards = self.my_line + self.table_line + self.discard_pile
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
        p_bust = 0.0 if 'sc' in self.my_line else bust_cards_left / n_total
        p_safe = 1.0 - p_bust

        # calculate Expected Value (EV)
        expected_new_score = 0.0
        for card, count in remaining_deck.items():
            if count == 0:
                continue
                
            p_draw = count / n_total
            
            if isinstance(card, int) and card in number_cards and 'sc' not in self.my_line:
                expected_new_score += (p_draw * 0) 
            else:
                simulated_line = self.my_line + [card]
                simulated_score = self._calculate_score(simulated_line)
                expected_new_score += (p_draw * simulated_score)

        # calculate current score
        current_score = self._calculate_score(self.my_line)   

        return {
            "deck_empty": False,
            "current_score": current_score,
            "p_bust": p_bust,
            "p_safe": p_safe,
            "ev": expected_new_score
        }
