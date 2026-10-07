import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, get_type_hints

from calculator import Flip7Calculator
from logger import Flip7Logger, get_default_log_path
from schema import DeckConfigJSON


class CLIController:

    def __init__(
        self,
        deck_counts: DeckConfigJSON,
        log_file: Optional[str] = None,
    ):
        self.calculator = Flip7Calculator(deck_counts=deck_counts)
        self.valid_cards = set(self.calculator.deck_counts.keys())
        self.log_file = log_file or get_default_log_path()
        self.logger = Flip7Logger(self.log_file)

    def _parse_card(self, token: str) -> Optional[Any]:
        if token.isdigit():
            val = int(token)
            return val if val in self.valid_cards else None
        elif token in self.valid_cards:
            return token
        else:
            return None

    def _display_stats(self, stats: Dict[str, Any]) -> None:
        if stats.get("deck_empty"):
            print("\n[!] The deck is empty.")
            return

        print("\n" + "=" * 30)
        print(f"Current Score:      {stats['current_score']}")
        print(f"Risk of Busting:    {stats['p_bust'] * 100:.1f}%")
        print(f"Chance of Safe Hit: {stats['p_safe'] * 100:.1f}%")
        print(f"Expected Score EV:  {stats['ev']:.1f}")
        print("=" * 30 + "\n")

    def execute_command(
        self, raw_input: Optional[str], silent: bool = False
    ) -> Dict[str, Any]:
        """Parse and execute a single command line, update state, and log event."""
        normalized_input = (
            raw_input.strip().lower() if raw_input is not None else ""
        )
        cmd = None
        args: List[str] = []
        outcome = "error"
        error = None
        stats = None

        try:
            if not normalized_input:
                outcome = "blank"
                return {
                    "raw_input": raw_input,
                    "normalized_input": normalized_input,
                    "command": None,
                    "arguments": [],
                    "outcome": outcome,
                    "state": self.calculator.get_state(),
                    "stats": None,
                    "error": None,
                }

            parts = normalized_input.split()
            cmd = parts[0]
            args = parts[1:]

            if cmd in ("q", "quit"):
                outcome = "quit"
                if not silent:
                    print("Exiting...")

            elif cmd in ("r", "reset"):
                self.calculator.reset_round()
                outcome = "reset"
                if not silent:
                    print("[✓] Round reset. All cards cleared.")

            elif cmd == "m":
                for arg in args:
                    card = self._parse_card(arg)
                    if card is not None and card in self.valid_cards:
                        if card in ["fz", "f3"]:
                            self.calculator.add_to_discard_pile(card)
                        else:
                            self.calculator.add_to_my_line(card)
                    else:
                        if not silent:
                            print(f"[!] Invalid card ignored: {arg}")
                outcome = "dispatched"
                if not silent:
                    print(f"My Line: {self.calculator.my_line}")

            elif cmd == "md":
                for arg in args:
                    card = self._parse_card(arg)
                    if card is not None:
                        try:
                            self.calculator.remove_from_my_line(card)
                            self.calculator.add_to_discard_pile(card)
                        except ValueError as exc:
                            error = str(exc)
                            if not silent:
                                print(f"[!] {exc}")
                    else:
                        if not silent:
                            print(f"[!] Invalid card ignored: {arg}")
                outcome = "dispatched"
                if not silent:
                    print(f"My Line: {self.calculator.my_line}")

            elif cmd == "t":
                for arg in args:
                    card = self._parse_card(arg)
                    if card is not None and card in self.valid_cards:
                        self.calculator.add_to_table_line(card)
                    else:
                        if not silent:
                            print(f"[!] Invalid card ignored: {arg}")
                outcome = "dispatched"
                if not silent:
                    print(f"Table Cards: {self.calculator.table_line}")

            elif cmd == "td":
                for arg in args:
                    card = self._parse_card(arg)
                    if card is not None:
                        try:
                            self.calculator.remove_from_table_line(card)
                            self.calculator.add_to_discard_pile(card)
                        except ValueError as exc:
                            error = str(exc)
                            if not silent:
                                print(f"[!] {exc}")
                    else:
                        if not silent:
                            print(f"[!] Invalid card ignored: {arg}")
                outcome = "dispatched"
                if not silent:
                    print(f"Table Cards: {self.calculator.table_line}")

            elif cmd in ("c", "calc"):
                stats = self.calculator.calculate_stats()
                outcome = "calculated"
                if not silent:
                    self._display_stats(stats)

            elif cmd in ("d", "display"):
                outcome = "dispatched"
                if not silent:
                    print(f"My Line: {self.calculator.my_line}")
                    print(f"Table Cards: {self.calculator.table_line}")
                    print(f"Discard Pile: {self.calculator.discard_pile}")

            else:
                outcome = "unknown"
                if not silent:
                    print(
                        "[!] Unknown command. Use m, md, t, td, c, d, r, or q."
                    )

        except KeyboardInterrupt:
            outcome = "interrupted"
            if not silent:
                print("\nExiting...")
        except Exception as exc:
            outcome = "error"
            error = str(exc)
            if not silent:
                print(f"[!] Error: {exc}")
        finally:
            result_payload = {
                "raw_input": raw_input,
                "normalized_input": normalized_input,
                "command": cmd,
                "arguments": args,
                "outcome": outcome,
                "state": self.calculator.get_state(),
                "stats": stats,
                "error": error,
            }
            self.logger.log_command(
                raw_input=raw_input,
                normalized_input=normalized_input,
                command=cmd,
                arguments=args,
                outcome=outcome,
                state=result_payload["state"],
                stats=stats,
                error=error,
            )
            if outcome in {"quit", "interrupted"}:
                self.logger.close()

        return result_payload

    def run(self) -> None:
        print("Commands:")
        print("  m <cards>   -> Add to YOUR line (e.g., 'm 12 5 +2 x2')")
        print(
            "  md <card>   -> Remove a card from YOUR line to the discard pile"
            " (e.g., 'md sc')"
        )
        print("  t <cards>   -> Add to TABLE line (e.g., 't 11 11 0 +4 x2')")
        print(
            "  td <cards>  -> Remove a card from TABLE to the discard pile"
            " (e.g., 'td sc')"
        )
        print("  c           -> Calculate Expected Value & Probabilities")
        print("  d           -> Display current state")
        print("  r           -> Reset for a new round")
        print("  q           -> Quit\n")

        while True:
            try:
                raw_input = input("Flip7> ")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                self.logger.log_command(
                    raw_input=None,
                    normalized_input="",
                    command=None,
                    arguments=[],
                    outcome="interrupted",
                    state=self.calculator.get_state(),
                )
                self.logger.close()
                sys.exit(0)

            result = self.execute_command(raw_input, silent=False)
            if result["outcome"] == "quit":
                sys.exit(0)


def _json_key_to_deck_key(card_key: str) -> Any:
    return int(card_key) if card_key.isdigit() else card_key


def _get_typed_dict_hints(typed_dict_cls: Any) -> Dict[str, Any]:
    try:
        return get_type_hints(typed_dict_cls)
    except Exception:
        return getattr(typed_dict_cls, "__annotations__", {})


def _normalize_and_validate_deck_config(raw_config: Any) -> Dict[Any, int]:
    if not isinstance(raw_config, dict):
        raise ValueError(
            "Deck config must be a JSON object mapping card keys to counts."
        )

    expected_types = _get_typed_dict_hints(DeckConfigJSON)
    expected_keys = set(expected_types.keys())
    if not expected_keys:
        raise ValueError("Deck config schema is unavailable.")

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
    for key in sorted(
        expected_keys,
        key=lambda val: (not val.isdigit(), int(val) if val.isdigit() else val),
    ):
        count = provided_lookup[key]
        expected_type = expected_types.get(key, int)
        if expected_type is int and (
            isinstance(count, bool) or not isinstance(count, int)
        ):
            raise ValueError(f"Count for '{key}' must be an integer.")
        if expected_type is not int and not isinstance(count, expected_type):
            raise ValueError(
                f"Count for '{key}' must be of type {expected_type.__name__}."
            )
        if count < 0:
            raise ValueError(f"Count for '{key}' must be >= 0.")
        normalized_config[_json_key_to_deck_key(key)] = count

    if sum(normalized_config.values()) == 0:
        raise ValueError("Deck config cannot have all counts set to 0.")

    return normalized_config


def load_deck_config(config_path: str) -> Dict[Any, int]:
    expanded_path = os.path.abspath(os.path.expanduser(config_path))
    try:
        with open(expanded_path, "r", encoding="utf-8") as file_handle:
            raw_config = json.load(file_handle)
    except FileNotFoundError as exc:
        raise ValueError(
            f"Deck config file not found: {expanded_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Deck config is not valid JSON: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Could not read deck config file: {exc}") from exc

    return _normalize_and_validate_deck_config(raw_config)


def get_resource_path(relative_path: str) -> str:
    """Get the absolute path to a resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
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
    parser.add_argument(
        "--log-file",
        dest="log_file",
        default=None,
        help=(
            "Path to the JSONL command log file (defaults to a new"
            " datetime-named file in logs/)."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        custom_deck_counts = load_deck_config(args.deck_config)
        print(
            "[✓] Loaded deck config from"
            f" {os.path.abspath(os.path.expanduser(args.deck_config))}"
        )
    except ValueError as error:
        print(f"[!] Failed to load deck config: {error}")
        sys.exit(1)
    cli = CLIController(deck_counts=custom_deck_counts, log_file=args.log_file)
    cli.run()