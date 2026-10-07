import json
import os
import shutil
import tempfile
import unittest

from main import CLIController, load_deck_config
from schema import DeckConfigJSON


def get_base_deck_dict():
    return {
        "12": 12,
        "11": 11,
        "10": 10,
        "9": 9,
        "8": 8,
        "7": 7,
        "6": 6,
        "5": 5,
        "4": 4,
        "3": 3,
        "2": 2,
        "1": 1,
        "0": 1,
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


class TestDeckConfigValidation(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_config(self, data):
        path = os.path.join(self.test_dir, "config.json")
        with open(path, "w", encoding="utf-8") as f:
            if isinstance(data, str):
                f.write(data)
            else:
                json.dump(data, f)
        return path

    def test_load_valid_base_deck(self):
        config = load_deck_config("deck_configs/base.json")
        self.assertIn(12, config)
        self.assertEqual(config[12], 12)
        self.assertIn("x2", config)
        self.assertEqual(config["x2"], 1)

    def test_missing_file_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            load_deck_config(os.path.join(self.test_dir, "nonexistent.json"))
        self.assertIn("not found", str(ctx.exception))

    def test_invalid_json_raises_value_error(self):
        path = self._write_config("{ malformed json }")
        with self.assertRaises(ValueError) as ctx:
            load_deck_config(path)
        self.assertIn("not valid JSON", str(ctx.exception))

    def test_missing_keys_raises_value_error(self):
        data = get_base_deck_dict()
        del data["12"]
        path = self._write_config(data)
        with self.assertRaises(ValueError) as ctx:
            load_deck_config(path)
        self.assertIn("missing keys", str(ctx.exception))

    def test_extra_keys_raises_value_error(self):
        data = get_base_deck_dict()
        data["extra_card"] = 1
        path = self._write_config(data)
        with self.assertRaises(ValueError) as ctx:
            load_deck_config(path)
        self.assertIn("unknown keys", str(ctx.exception))

    def test_non_integer_count_raises_value_error(self):
        data = get_base_deck_dict()
        data["12"] = "twelve"
        path = self._write_config(data)
        with self.assertRaises(ValueError) as ctx:
            load_deck_config(path)
        self.assertIn("must be an integer", str(ctx.exception))

    def test_negative_count_raises_value_error(self):
        data = get_base_deck_dict()
        data["12"] = -1
        path = self._write_config(data)
        with self.assertRaises(ValueError) as ctx:
            load_deck_config(path)
        self.assertIn("must be >= 0", str(ctx.exception))

    def test_all_zero_counts_raises_value_error(self):
        data = {k: 0 for k in get_base_deck_dict()}
        path = self._write_config(data)
        with self.assertRaises(ValueError) as ctx:
            load_deck_config(path)
        self.assertIn("cannot have all counts set to 0", str(ctx.exception))


class TestCLIController(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "test_log.jsonl")
        self.deck = load_deck_config("deck_configs/base.json")
        self.cli = CLIController(deck_counts=self.deck, log_file=self.log_file)

    def tearDown(self):
        self.cli.logger.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_card_parsing(self):
        self.assertEqual(self.cli._parse_card("12"), 12)
        self.assertEqual(self.cli._parse_card("0"), 0)
        self.assertEqual(self.cli._parse_card("+4"), "+4")
        self.assertEqual(self.cli._parse_card("x2"), "x2")
        self.assertEqual(self.cli._parse_card("fz"), "fz")
        self.assertIsNone(self.cli._parse_card("99"))
        self.assertIsNone(self.cli._parse_card("invalid"))

    def test_blank_command(self):
        res = self.cli.execute_command("", silent=True)
        self.assertEqual(res["outcome"], "blank")

    def test_quit_command(self):
        res = self.cli.execute_command("q", silent=True)
        self.assertEqual(res["outcome"], "quit")

    def test_add_to_my_line_and_action_diversion(self):
        # Adding regular cards and action cards
        res = self.cli.execute_command("m 12 4 +2 sc fz f3", silent=True)
        self.assertEqual(res["outcome"], "dispatched")

        # 12, 4, +2, sc stay in my_line
        self.assertIn(12, self.cli.calculator.my_line)
        self.assertIn(4, self.cli.calculator.my_line)
        self.assertIn("+2", self.cli.calculator.my_line)
        self.assertIn("sc", self.cli.calculator.my_line)

        # fz and f3 are automatically diverted to discard pile
        self.assertNotIn("fz", self.cli.calculator.my_line)
        self.assertNotIn("f3", self.cli.calculator.my_line)
        self.assertIn("fz", self.cli.calculator.discard_pile)
        self.assertIn("f3", self.cli.calculator.discard_pile)

    def test_remove_from_my_line(self):
        self.cli.execute_command("m 10 5", silent=True)
        res = self.cli.execute_command("md 10", silent=True)
        self.assertEqual(res["outcome"], "dispatched")
        self.assertEqual(self.cli.calculator.my_line, [5])
        self.assertEqual(self.cli.calculator.discard_pile, [10])

        # Attempt to remove card not in line
        res_missing = self.cli.execute_command("md 99", silent=True)
        self.assertEqual(res_missing["outcome"], "dispatched")

    def test_table_line_and_discard(self):
        self.cli.execute_command("t 11 8", silent=True)
        self.assertEqual(self.cli.calculator.table_line, [11, 8])

        self.cli.execute_command("td 11", silent=True)
        self.assertEqual(self.cli.calculator.table_line, [8])
        self.assertEqual(self.cli.calculator.discard_pile, [11])

    def test_calc_command(self):
        self.cli.execute_command("m 12", silent=True)
        res = self.cli.execute_command("c", silent=True)
        self.assertEqual(res["outcome"], "calculated")
        stats = res["stats"]
        self.assertIsNotNone(stats)
        self.assertEqual(stats["current_score"], 12)
        self.assertGreater(stats["p_bust"], 0.0)

    def test_display_and_reset_commands(self):
        self.cli.execute_command("m 10", silent=True)
        self.cli.execute_command("t 9", silent=True)
        res_d = self.cli.execute_command("d", silent=True)
        self.assertEqual(res_d["outcome"], "dispatched")

        res_r = self.cli.execute_command("r", silent=True)
        self.assertEqual(res_r["outcome"], "reset")
        self.assertEqual(self.cli.calculator.my_line, [])
        self.assertEqual(self.cli.calculator.table_line, [])

    def test_unknown_command(self):
        res = self.cli.execute_command("unknown_cmd 123", silent=True)
        self.assertEqual(res["outcome"], "unknown")

    def test_logging_written_per_command(self):
        self.cli.execute_command("m 12", silent=True)
        self.cli.execute_command("c", silent=True)
        self.assertEqual(self.cli.logger.records_written, 2)

        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)
        record1 = json.loads(lines[0])
        record2 = json.loads(lines[1])
        self.assertEqual(record1["command"], "m")
        self.assertEqual(record2["command"], "c")

    def test_default_log_file_is_datetime_named(self):
        controller = CLIController(deck_counts=self.deck)
        try:
            self.assertTrue(controller.log_file.endswith(".jsonl"))
            self.assertIn("logs", controller.log_file)
            basename = os.path.basename(controller.log_file).replace(".jsonl", "")
            self.assertTrue(basename.split("_")[0].isdigit())
        finally:
            controller.logger.close()
            # Clean up default generated log file if it was created
            if os.path.exists(controller.log_file):
                try:
                    os.remove(controller.log_file)
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()

