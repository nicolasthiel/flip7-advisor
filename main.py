import argparse
import json
import os
import sys

from calculator import Flip7Calculator, DeckConfigJSON


class CLIController:

    def __init__(self, deck_counts: DeckConfigJSON):
        self.calculator = Flip7Calculator(deck_counts=deck_counts)
        self.valid_cards = set(self.calculator.deck_counts.keys())


    def _parse_card(self, token):
        if token.isdigit():
            return int(token)
        elif token in self.valid_cards:
            return token
        else:
            return None

        
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
                        if card is not None and card in self.valid_cards:
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
                        if card is not None and card in self.valid_cards:
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
                    print("[!] Unknown command. Use m, t, c, r, or q.") # TODO replace with valid command list

            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(0)
            except Exception as e:
                print(f"[!] Error: {e}")


def _deck_key_to_json_key(card):
    return str(card) if isinstance(card, int) else card


def _json_key_to_deck_key(card_key):
    return int(card_key) if card_key.isdigit() else card_key


def _normalize_and_validate_deck_config(raw_config):
    if not isinstance(raw_config, dict):
        raise ValueError("Deck config must be a JSON object mapping card keys to counts.")

    expected_keys = set(DeckConfigJSON.__required_keys__)
    provided_lookup = {str(key): value for key, value in raw_config.items()}
    provided_keys = set(provided_lookup.keys())

    missing_keys = sorted(expected_keys - provided_keys)
    extra_keys = sorted(provided_keys - expected_keys)

    if missing_keys or extra_keys:
        error_parts = []
        if missing_keys:
            error_parts.append(f"missing keys: {', '.join(missing_keys)}")
        if extra_keys:
            error_parts.append(f"unknown keys: {', '.join(extra_keys)}")
        raise ValueError("Invalid deck keys; " + "; ".join(error_parts) + ".")

    normalized_config = {}
    for key in sorted(expected_keys, key=lambda value: (not value.isdigit(), int(value) if value.isdigit() else value)):
        count = provided_lookup[key]
        if isinstance(count, bool) or not isinstance(count, int):
            raise ValueError(f"Count for '{key}' must be an integer.")
        if count < 0:
            raise ValueError(f"Count for '{key}' must be >= 0.")
        normalized_config[_json_key_to_deck_key(key)] = count

    if sum(normalized_config.values()) == 0:
        raise ValueError("Deck config cannot have all counts set to 0.")

    return normalized_config


def load_deck_config(config_path):
    expanded_path = os.path.abspath(os.path.expanduser(config_path))
    try:
        with open(expanded_path, "r", encoding="utf-8") as file_handle:
            raw_config = json.load(file_handle)
    except FileNotFoundError as exc:
        raise ValueError(f"Deck config file not found: {expanded_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Deck config is not valid JSON: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Could not read deck config file: {exc}") from exc

    return _normalize_and_validate_deck_config(raw_config)


def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores its path in sys._MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # If sys._MEIPASS doesn't exist, we are running as a normal Python script
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


DEFAULT_DECK_CONFIG_PATH = get_resource_path("deck_configs/base.json")

def parse_args():
    parser = argparse.ArgumentParser(description="Flip7 Advisor CLI")
    parser.add_argument(
        "--deck-config",
        dest="deck_config",
        default=DEFAULT_DECK_CONFIG_PATH,
        help="Path to a JSON file that defines initial deck counts.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        custom_deck_counts = load_deck_config(args.deck_config)
        print(f"[✓] Loaded deck config from {os.path.abspath(os.path.expanduser(args.deck_config))}")
    except ValueError as error:
        print(f"[!] Failed to load deck config: {error}")
        sys.exit(1)
    print(type(custom_deck_counts))
    cli = CLIController(deck_counts=custom_deck_counts)
    cli.run()