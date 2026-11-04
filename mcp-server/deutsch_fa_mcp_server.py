#!/usr/bin/env python3
"""MCP server for deutsch-fa — expose the German declension engine
as tools for any MCP client.

Zero-dependency (Python standard library only). Speaks JSON-RPC 2.0
over stdio, newline-delimited, following the MCP lifecycle:

    initialize -> notifications/initialized -> tools/list -> tools/call

Tools:
    decline
        noun    German noun, with or without article (required)
        format  "text" (default) or "json"
    check_sentence
        sentence  German sentence to check (required)
        format    "text" (default) or "json"
    gender_hint
        word    German noun to look up or predict (required)
    anki_export
        (no arguments) returns the full noun list as Anki TSV

The server runs skills/deutsch-fa/scripts/deutsch_fa.py as a subprocess;
exit-code semantics are preserved in the returned text (check: 0 = no
findings, 1 = findings; decline: 1 = noun not in the curated list).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE.parent / "skills" / "deutsch-fa" / "scripts" / "deutsch_fa.py"

SERVER_INFO = {"name": "deutsch-fa", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"


def run_cli(*args):
    proc = subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True, timeout=120)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def tool_decline(args):
    noun = args.get("noun")
    if not noun:
        raise ValueError("decline requires 'noun'")
    cmd = ["decline", noun]
    if args.get("format") == "json":
        cmd.append("--json")
    code, out, err = run_cli(*cmd)
    lines = [f"decline exit code: {code}"]
    if out:
        lines.append(out)
    if err:
        lines.append("stderr: " + err)
    return "\n".join(lines)


def tool_check_sentence(args):
    sentence = args.get("sentence")
    if not sentence:
        raise ValueError("check_sentence requires 'sentence'")
    cmd = ["check", sentence]
    if args.get("format") == "json":
        cmd.append("--json")
    code, out, err = run_cli(*cmd)
    lines = [f"check exit code: {code}"]
    if out:
        lines.append(out)
    if err:
        lines.append("stderr: " + err)
    return "\n".join(lines)


def tool_gender_hint(args):
    word = args.get("word")
    if not word:
        raise ValueError("gender_hint requires 'word'")
    code, out, err = run_cli("rules", word)
    lines = [f"rules exit code: {code}"]
    if out:
        lines.append(out)
    if err:
        lines.append("stderr: " + err)
    return "\n".join(lines)


def tool_anki_export(args):
    code, out, err = run_cli("anki")
    lines = [f"anki exit code: {code}",
             f"{len(out.splitlines())} cards (TSV: front<TAB>back)"]
    if out:
        lines.append(out)
    if err:
        lines.append("stderr: " + err)
    return "\n".join(lines)


TOOLS = [
    {
        "name": "decline",
        "description": (
            "Decline a German noun: full der/die/das article paradigm across "
            "the four cases (singular + plural), indefinite and negative "
            "articles, possessive forms, weak adjective endings, and the "
            "Persian gloss. Use instead of guessing a noun's gender or case "
            "forms. Answers in German with Persian explanations."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "noun": {"type": "string",
                         "description": "German noun, with or without article"},
                "format": {"type": "string", "enum": ["text", "json"],
                           "description": "output format (default text)"},
            },
            "required": ["noun"],
        },
    },
    {
        "name": "check_sentence",
        "description": (
            "Check a learner's German sentence for article/case errors, "
            "N-declension mistakes and wrong adjective endings — only where "
            "deterministically decidable from verb frames and case "
            "prepositions. Conservative: no finding does not mean the "
            "sentence is perfect. Explanations in Persian."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sentence": {"type": "string",
                             "description": "German sentence to check"},
                "format": {"type": "string", "enum": ["text", "json"],
                           "description": "output format (default text)"},
            },
            "required": ["sentence"],
        },
    },
    {
        "name": "gender_hint",
        "description": (
            "Look up a German noun's gender in the curated list, or predict "
            "it from ending rules (with reliability and exceptions) when the "
            "noun is not listed. Persian explanations."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "word": {"type": "string",
                         "description": "German noun to look up or predict"},
            },
            "required": ["word"],
        },
    },
    {
        "name": "anki_export",
        "description": (
            "Export the curated A1 noun list (German + article + plural + "
            "Persian gloss) as Anki-importable TSV."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
]

HANDLERS = {
    "decline": tool_decline,
    "check_sentence": tool_check_sentence,
    "gender_hint": tool_gender_hint,
    "anki_export": tool_anki_export,
}


def handle(request):
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"tools": TOOLS},
        }
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if handler is None:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32602,
                          "message": f"unknown tool: {name}"},
            }
        try:
            text = handler(arguments)
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        except Exception as exc:  # noqa: BLE001 - surface as tool error
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text",
                                        "text": f"error: {exc}"}],
                           "isError": True},
            }
    return {
        "jsonrpc": "2.0", "id": req_id,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
