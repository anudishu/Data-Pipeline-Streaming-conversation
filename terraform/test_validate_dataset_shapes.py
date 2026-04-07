#!/usr/bin/env python3
import json
import os
import tempfile
import unittest

from chat_stream_pipeline.validate import classify_record, validate_file


class TestClassifyRecord(unittest.TestCase):
    def test_order_city_row(self) -> None:
        obj = {"orderId": 12, "cityCode": "NYC"}
        self.assertEqual(classify_record(obj), "order_city")

    def test_conversation_row(self) -> None:
        obj = {
            "senderAppType": "Courier Android",
            "fromId": 1,
            "toId": 2,
            "chatStartedByMessage": True,
            "orderId": 9,
            "orderStage": "ACCEPTED",
            "customerId": 2,
            "messageSentTime": "2024-02-01T10:00:00Z",
            "courierId": 1,
        }
        self.assertEqual(classify_record(obj), "conversation")

    def test_unknown_when_keys_missing(self) -> None:
        obj = {"orderId": 9}
        self.assertEqual(classify_record(obj), "unknown")


class TestValidateFile(unittest.TestCase):
    def _write(self, lines: list[str]) -> str:
        handle = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        try:
            for line in lines:
                handle.write(line + "\n")
            return handle.name
        finally:
            handle.close()

    def test_happy_path_counts(self) -> None:
        path = self._write(
            [
                json.dumps(
                    {
                        "senderAppType": "Courier Android",
                        "fromId": 1,
                        "toId": 2,
                        "chatStartedByMessage": True,
                        "orderId": 9,
                        "orderStage": "ACCEPTED",
                        "customerId": 2,
                        "messageSentTime": "2024-02-01T10:00:00Z",
                        "courierId": 1,
                    },
                    separators=(",", ":"),
                ),
                json.dumps({"orderId": 9, "cityCode": "NYC"}, separators=(",", ":")),
            ]
        )
        try:
            summary = validate_file(path, fail_on_unknown=True, max_unknown=0)
            self.assertEqual(summary.json_errors, 0)
            self.assertEqual(summary.conversation_rows, 1)
            self.assertEqual(summary.order_city_rows, 1)
            self.assertEqual(summary.unknown_rows, 0)
        finally:
            os.unlink(path)

    def test_json_error_increments_counter(self) -> None:
        path = self._write(["not-json"])
        try:
            summary = validate_file(path, fail_on_unknown=False, max_unknown=0)
            self.assertEqual(summary.json_errors, 1)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
