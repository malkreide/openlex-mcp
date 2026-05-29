#!/usr/bin/env python3
"""Generate tool-definition hashes for SEC-022 rug-pull protection.

Run at release time (from the repo root):
    PYTHONPATH=src python scripts/gen_tool_hashes.py > docs/tool-hashes.json

The output file is committed to the repository. If CI detects a diff in
docs/tool-hashes.json that is not accompanied by a CHANGELOG entry, the
reviewer should request a re-approval of the changed tool definitions.

Hash covers: tool name + description + parameter JSON schema (sorted keys).
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openlex_mcp import server as srv  # noqa: E402


def _tool_signature(tool) -> str:
    return json.dumps(
        {
            "name": tool.name,
            "description": (tool.description or "").strip(),
            "parameters": tool.parameters,
            "output_schema": getattr(tool, "output_schema", None),
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def main() -> None:
    tools = srv.mcp._tool_manager._tools
    hashes = {
        name: hashlib.sha256(_tool_signature(tool).encode()).hexdigest()
        for name, tool in sorted(tools.items())
    }
    output = {
        "mcp_protocol_version": srv.MCP_PROTOCOL_VERSION,
        "tool_count": len(hashes),
        "tools": hashes,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
