import json
import os
import shutil
import tempfile
import unittest

from logger import Flip7Logger, Flip7FileLogger, get_default_log_path


class TestFlip7Logger(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.test_dir, "nested", "sub", "test.jsonl")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_file_and_directory_creation(self):
        logger = Flip7Logger(self.log_path)
        logger.log_command(
            raw_input="m 12",
            normalized_input="m 12",
            command="m",
            arguments=["12"],
            outcome="dispatched",
            state={"my_line": [12]},
        )
        logger.close()

        self.assertTrue(os.path.exists(self.log_path))
        self.assertEqual(logger.records_written, 1)

    def test_structured_jsonl_record_format(self):
        logger = Flip7Logger(self.log_path)
        logger.log_command(
            raw_input="c",
            normalized_input="c",
            command="c",
            arguments=[],
            outcome="calculated",
            state={"my_line": [12, 4]},
            stats={"current_score": 16, "p_bust": 0.1, "p_safe": 0.9, "ev": 20.0},
            error=None,
        )
        logger.close()

        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])

        self.assertEqual(record["event"], "command")
        self.assertEqual(record["command"], "c")
        self.assertEqual(record["outcome"], "calculated")
        self.assertIn("timestamp", record)
        self.assertEqual(record["state"]["my_line"], [12, 4])
        self.assertEqual(record["stats"]["current_score"], 16)
        self.assertNotIn("error", record)  # None error omitted or check presence

    def test_closed_logger_does_not_write(self):
        logger = Flip7Logger(self.log_path)
        logger.close()
        self.assertTrue(logger.is_closed)

        logger.log_command(
            raw_input="m 1",
            normalized_input="m 1",
            command="m",
            arguments=["1"],
            outcome="dispatched",
            state={},
        )
        self.assertEqual(logger.records_written, 0)
        self.assertFalse(os.path.exists(self.log_path))

    def test_context_manager(self):
        with Flip7Logger(self.log_path) as logger:
            logger.log_command(
                raw_input="d",
                normalized_input="d",
                command="d",
                arguments=[],
                outcome="dispatched",
                state={},
            )
            self.assertFalse(logger.is_closed)

        self.assertTrue(logger.is_closed)
        self.assertEqual(logger.records_written, 1)

    def test_silent_failure_on_unwritable_path(self):
        # Using an impossible path on Windows/Unix should not raise any exception
        invalid_path = "\0invalid_path/file.jsonl"
        logger = Flip7Logger(invalid_path)
        # Must not raise an error
        logger.log_command(
            raw_input="test",
            normalized_input="test",
            command="test",
            arguments=[],
            outcome="error",
            state={},
        )
        logger.close()

    def test_non_serializable_objects_handled_silently(self):
        logger = Flip7Logger(self.log_path)
        # Sets are not natively JSON serializable
        logger.log_command(
            raw_input="test",
            normalized_input="test",
            command="test",
            arguments=[],
            outcome="dispatched",
            state={"numbers": {1, 2, 3}},
        )
        logger.close()

        self.assertEqual(logger.records_written, 1)
        with open(self.log_path, "r", encoding="utf-8") as f:
            data = json.loads(f.readline())
        self.assertIn("numbers", data["state"])

    def test_legacy_compatibility(self):
        self.assertIs(Flip7FileLogger, Flip7Logger)
        logger = Flip7FileLogger(self.log_path)
        logger.record("test_event", custom_key="value")
        logger.close()

        with open(self.log_path, "r", encoding="utf-8") as f:
            data = json.loads(f.readline())
        self.assertEqual(data["event"], "test_event")
        self.assertEqual(data["custom_key"], "value")

    def test_get_default_log_path_format(self):
        path = get_default_log_path(self.test_dir)
        self.assertTrue(path.endswith(".jsonl"))
        basename = os.path.basename(path)
        # Should be formatted as YYYYMMDD_HHMMSS.jsonl
        name_part = basename.replace(".jsonl", "")
        self.assertIn("_", name_part)
        parts = name_part.split("_")
        self.assertTrue(parts[0].isdigit())
        self.assertTrue(parts[1].isdigit())

    def test_get_default_log_path_collision_avoidance(self):
        path1 = get_default_log_path(self.test_dir)
        # Create file at path1
        with open(path1, "w", encoding="utf-8") as f:
            f.write("{}")
        path2 = get_default_log_path(self.test_dir)
        self.assertNotEqual(path1, path2)
        self.assertTrue(path2.endswith("_1.jsonl"))

    def test_logger_default_file_path(self):
        logger = Flip7Logger()
        self.assertTrue(logger.file_path.endswith(".jsonl"))
        self.assertIn("logs", logger.file_path)
        logger.close()


if __name__ == "__main__":
    unittest.main()

