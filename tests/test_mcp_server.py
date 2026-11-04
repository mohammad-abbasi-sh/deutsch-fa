#!/usr/bin/env python3
"""End-to-end tests for the deutsch-fa MCP server (stdio JSON-RPC).

Run: python3 tests/test_mcp_server.py  (from the project root)
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

SERVER = (Path(__file__).resolve().parent.parent / "mcp-server"
          / "deutsch_fa_mcp_server.py")


def rpc_calls(messages):
    """Send JSON-RPC messages to the server, return parsed responses."""
    proc = subprocess.run(
        [sys.executable, str(SERVER)],
        input="\n".join(json.dumps(m) for m in messages) + "\n",
        capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return [json.loads(line) for line in proc.stdout.splitlines()
            if line.strip()]


class McpLifecycle(unittest.TestCase):
    def test_initialize_and_tools_list(self):
        resps = rpc_calls([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list",
             "params": {}},
        ])
        self.assertEqual(len(resps), 2)
        self.assertEqual(resps[0]["result"]["serverInfo"]["name"],
                         "deutsch-fa")
        names = {t["name"] for t in resps[1]["result"]["tools"]}
        self.assertEqual(names, {"decline", "check_sentence",
                                 "gender_hint", "anki_export"})

    def test_decline_tool(self):
        resps = rpc_calls([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "decline",
                        "arguments": {"noun": "Mann"}}},
        ])
        text = resps[0]["result"]["content"][0]["text"]
        self.assertIn("den Mann", text)
        self.assertIn("dem Mann", text)

    def test_decline_json_format(self):
        resps = rpc_calls([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "decline",
                        "arguments": {"noun": "Frau", "format": "json"}}},
        ])
        text = resps[0]["result"]["content"][0]["text"]
        payload = text.split("\n", 1)[1]
        data = json.loads(payload)
        self.assertEqual(data["cases"]["sg"]["dat"], "der Frau")

    def test_check_sentence_tool(self):
        resps = rpc_calls([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "check_sentence",
                        "arguments": {"sentence": "Ich sehe der Mann"}}},
        ])
        text = resps[0]["result"]["content"][0]["text"]
        self.assertIn("den Mann", text)
        self.assertIn("exit code: 1", text)

    def test_gender_hint_tool(self):
        resps = rpc_calls([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "gender_hint",
                        "arguments": {"word": "Wohnung"}}},
        ])
        text = resps[0]["result"]["content"][0]["text"]
        self.assertIn("مؤنث", text)

    def test_anki_export_tool(self):
        resps = rpc_calls([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "anki_export", "arguments": {}}},
        ])
        text = resps[0]["result"]["content"][0]["text"]
        self.assertIn("cards (TSV", text)
        self.assertIn("der Mann", text)

    def test_unknown_tool(self):
        resps = rpc_calls([
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "nope", "arguments": {}}},
        ])
        self.assertIn("error", resps[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
