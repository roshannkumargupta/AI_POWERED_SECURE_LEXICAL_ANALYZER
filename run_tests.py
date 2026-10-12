import json
import sys

import pytest

results = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "xfailed": 0, "xpassed": 0}
failures = []

class ResultRecorder:
    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            if report.passed:
                results["passed"] += 1
            elif report.failed:
                results["failed"] += 1
                failures.append(f"{report.nodeid}: {report.longreprtext[:200]}")
            elif report.skipped:
                results["skipped"] += 1
        elif report.when == "setup" and report.failed:
            results["errors"] += 1
            failures.append(f"SETUP {report.nodeid}: {report.longreprtext[:200]}")

    def pytest_sessionfinish(self, session, exitstatus):
        results["exitstatus"] = int(exitstatus)
        with open(r"reports\pytest_results.json", "w") as f:
            json.dump({"results": results, "failures": failures[:50]}, f, indent=2)

ec = pytest.main(["-q", "--tb=no", "--no-header", "-p", "no:cacheprovider"], plugins=[ResultRecorder()])
sys.exit(ec)
