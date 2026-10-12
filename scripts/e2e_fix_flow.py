"""Exercise the public fix lifecycle against a running SecureLex API server."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request

SAMPLES = {
    "python": ("demo.py", "import os\nuser_input = input()\nos.system(user_input)\n"),
    "java": (
        "Demo.java",
        "class Demo { void run(String input) throws Exception { Runtime.getRuntime().exec(input); } }\n",
    ),
    "javascript": (
        "demo.js",
        "const cp = require('child_process'); const input = process.argv[2]; cp.exec(input);\n",
    ),
    "cpp": (
        "demo.cpp",
        "#include <cstdlib>\nint main(int argc, char** argv) { return std::system(argv[1]); }\n",
    ),
}


def request(base: str, path: str, payload: dict[str, object] | None = None) -> tuple[int, object]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            body = response.read(2 * 1024 * 1024).decode("utf-8", "replace")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read(2 * 1024 * 1024).decode("utf-8", "replace")
        try:
            decoded: object = json.loads(body)
        except json.JSONDecodeError:
            decoded = body
        return exc.code, decoded
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, {"error": f"server unavailable: {type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8010/api")
    args = parser.parse_args()
    for index, (language, (filename, source)) in enumerate(SAMPLES.items()):
        print(f"\n=== {language} ===")
        status, analyzed = request(
            args.base_url,
            "/analyze",
            {
                "source": source,
                "language": language,
                "filename": filename,
                "api_version": 2,
                "source_version": 0,
            },
        )
        print(f"analyze HTTP {status}")
        if status != 200 or not isinstance(analyzed, dict):
            print(json.dumps(analyzed, indent=2))
            continue
        findings = analyzed.get("security_findings", analyzed.get("findings", []))
        if not findings:
            print(
                "No finding returned by the running analyzer; proposal stage cannot be exercised for this sample."
            )
            continue
        target_id = str(findings[0].get("id", ""))
        status, proposed = request(
            args.base_url,
            "/fixes/propose",
            {
                "source": source,
                "source_version": 0,
                "language": language,
                "filename": filename,
                "target_finding_id": target_id,
                "session_id": f"sl2-6-e2e-{index}",
                "origin": "rule",
            },
        )
        print(f"propose HTTP {status}: {json.dumps(proposed, indent=2)}")
        if status != 200 or not isinstance(proposed, dict) or "proposal" not in proposed:
            continue
        proposal = proposed["proposal"]
        base = {
            "source": source,
            "source_version": 0,
            "language": language,
            "filename": filename,
            "session_id": f"sl2-6-e2e-{index}",
            "proposal": proposal,
        }
        status, verified = request(args.base_url, "/fixes/verify", base)
        print(f"verify HTTP {status}: {json.dumps(verified, indent=2)}")
        if status != 200 or not isinstance(verified, dict):
            continue
        outcome = verified.get("report", {}).get("outcome")
        if outcome not in {"Verified for specified checks", "Partially verified"}:
            print("apply skipped because independent verification did not permit it")
            continue
        status, applied = request(args.base_url, "/fixes/apply", {**base, "approved": True})
        print(f"apply HTTP {status}: {json.dumps(applied, indent=2)}")
        if status != 200 or not isinstance(applied, dict) or not applied.get("applied"):
            continue
        status, after = request(
            args.base_url,
            "/analyze",
            {
                "source": applied["source"],
                "language": language,
                "filename": filename,
                "api_version": 2,
                "source_version": applied["source_version"],
            },
        )
        print(f"re-analyze HTTP {status}: {json.dumps(after, indent=2)}")
        status, undone = request(args.base_url, "/fixes/undo", {"session_id": base["session_id"]})
        print(f"undo HTTP {status}: {json.dumps(undone, indent=2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
