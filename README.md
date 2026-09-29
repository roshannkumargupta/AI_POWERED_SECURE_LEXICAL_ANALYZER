# SecureLex IDE (`apsla`)

SecureLex IDE is an intelligent, multi-language secure lexical analyzer and IDE-style static/hybrid code analysis platform supporting Python, Java, JavaScript, and C++.

## Features

- **Hybrid Detection**: Seamless fusion of deterministic rule checking, real taint data-flow analysis, and ML confidence scoring.
- **Unicode Defense**: Detection and mitigation of Trojan Source (bidi overrides), zero-width characters, homoglyphs, and confusables.
- **Fix & Verify Engine**: Generates syntax-aware remediation patches and re-analyzes transformed code to verify that vulnerabilities disappear without introducing regressions.
- **Offline & Cross-Platform**: Self-contained architecture without runtime CDN requirements, compatible with Windows, macOS, and Linux.

## Quickstart

```bash
# Set up environment
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .

# CLI analysis
apsla analyze <path-to-source-file>
```
