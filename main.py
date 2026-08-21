import sys
import copy

from calculator import Flip7Calculator, INITIAL_DECK_COUNTS


class CLIController:

    def __init__(self):
        self.calculator = Flip7Calculator()


    def _parse_card(self, token):
        if token.isdigit():
            return int(token)
        elif token in ['+2', '+4', '+6', '+8', '+10', 'x2', 'fz', 'f3', 'sc']:
            return token
        else:
            raise ValueError(f"Invalid card: {token}")

        
    def _display_stats(self, stats):
        if stats.get("deck_empty"):
            print("\n[!] The deck is empty.")
            return

        print("\n" + "="*30)
        print(f"Current Score:      {stats["current_score"]}")
        print(f"Risk of Busting:    {stats['p_bust'] * 100:.1f}%")
        print(f"Chance of Safe Hit: {stats['p_safe'] * 100:.1f}%")
        print(f"Expected Score EV:  {stats["ev"]:.1f}")
        print("="*30 + "\n")


    def run(self):
        print("Commands:")
        print("  m <cards>   -> Add to YOUR line (e.g., 'm 12 5 +2 x2')")
        print("  md <card>   -> Remove a card from YOUR line to the discard pile (e.g., 'md sc')")
        print("  t <cards>   -> Add to TABLE line (e.g., 't 11 11 0 +4 x2')")
        print("  mt <cards>  -> Remove a card from TABLE to the discard pile (e.g., 'mt sc')")
        print("  c           -> Calculate Expected Value & Probabilities")
        print("  d           -> Display current state")
        print("  r           -> Reset for a new round")
        print("  q           -> Quit\n")

        while True:
            try:
                user_input = input("Flip7> ").strip().lower()
                if not user_input:
                    continue

                parts = user_input.split()
                cmd = parts[0]
                args = parts[1:]

                if cmd == 'q' or cmd == 'quit':
                    print("Exiting...")
                    sys.exit(0)

                elif cmd == 'r' or cmd == 'reset':
                    self.calculator.reset_round()
                    print("[✓] Round reset. All cards cleared.")

                elif cmd == 'm':
                    for arg in args:
                        card = self._parse_card(arg)
                        if card is not None and card in INITIAL_DECK_COUNTS:
                            if card in ["fz", "f3"]:
                                self.calculator.add_to_discard_pile(card)
                            else:
                                self.calculator.add_to_my_line(card)
                        else:
                            print(f"[!] Invalid card ignored: {arg}")
                    print(f"My Line: {self.calculator.my_line}")

                elif cmd == 'md':
                    for arg in args:
                        card = self._parse_card(arg)
                        if card is not None:
                            try:
                                self.calculator.remove_from_my_line(card)
                                self.calculator.add_to_discard_pile(card)
                            except ValueError as e:
                                print(f"[!] {e}")
                        else:
                            print(f"[!] Invalid card ignored: {arg}")
                    print(f"My Line: {self.calculator.my_line}")

                elif cmd == 't':
                    for arg in args:
                        card = self._parse_card(arg)
                        if card is not None and card in INITIAL_DECK_COUNTS:
                            self.calculator.add_to_table_line(card)
                        else:
                            print(f"[!] Invalid card ignored: {arg}")
                    print(f"Table Cards: {self.calculator.table_line}")

                elif cmd == 'td':
                    for arg in args:
                        card = self._parse_card(arg)
                        if card is not None:
                            try:
                                self.calculator.remove_from_table_line(card)
                                self.calculator.add_to_discard_pile(card)
                            except ValueError as e:
                                print(f"[!] {e}")
                        else:
                            print(f"[!] Invalid card ignored: {arg}")
                    print(f"Table Cards: {self.calculator.table_line}")

                elif cmd == 'c' or cmd == 'calc':
                    stats = self.calculator.calculate_stats()
                    self._display_stats(stats)

                elif cmd == 'd' or cmd == 'display':
                    print(f"My Line: {self.calculator.my_line}")
                    print(f"Table Cards: {self.calculator.table_line}")
                    print(f"Discard Pile: {self.calculator.discard_pile}")

                else:
                    print("[!] Unknown command. Use m, t, c, r, or q.")

            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(0)
            except Exception as e:
                print(f"[!] Error: {e}")


if __name__ == "__main__":
    cli = CLIController()
    cli.run()