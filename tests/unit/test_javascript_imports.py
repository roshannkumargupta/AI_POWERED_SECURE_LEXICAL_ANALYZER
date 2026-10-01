"""Unit tests for JavaScript import insertion utility."""

from apsla.fixes.edits import apply_edits
from apsla.fixes.imports import ensure_import_javascript


def test_insert_commonjs_require():
    source = "const fs = require('fs');\n\nfunction main() {}\n"
    edits = ensure_import_javascript(
        source,
        import_name="crypto",
        esm_stmt="import crypto from 'crypto';",
        cjs_stmt="const crypto = require('crypto');",
    )
    res = apply_edits(source, edits) if edits else source
    expected = "const fs = require('fs');\nconst crypto = require('crypto');\n\nfunction main() {}\n"
    assert res == expected


def test_insert_esm_import():
    source = "import React from 'react';\n\nexport default function App() {}\n"
    edits = ensure_import_javascript(
        source,
        import_name="DOMPurify",
        esm_stmt="import DOMPurify from 'dompurify';",
        cjs_stmt="const DOMPurify = require('dompurify');",
    )
    res = apply_edits(source, edits) if edits else source
    expected = "import React from 'react';\nimport DOMPurify from 'dompurify';\n\nexport default function App() {}\n"
    assert res == expected


def test_insert_after_use_strict():
    source = "'use strict';\n\nfunction calculate() {}\n"
    edits = ensure_import_javascript(
        source,
        import_name="crypto",
        esm_stmt="import crypto from 'crypto';",
        cjs_stmt="const crypto = require('crypto');",
    )
    res = apply_edits(source, edits) if edits else source
    assert "'use strict';\nconst crypto = require('crypto');\n\nfunction calculate() {}" in res


def test_insert_after_shebang():
    source = "#!/usr/bin/env node\n'use strict';\n\nconsole.log('hi');\n"
    edits = ensure_import_javascript(
        source,
        import_name="crypto",
        esm_stmt="import crypto from 'crypto';",
        cjs_stmt="const crypto = require('crypto');",
    )
    res = apply_edits(source, edits) if edits else source
    assert res.startswith("#!/usr/bin/env node\n'use strict';\nconst crypto = require('crypto');")


def test_duplicate_import_no_op():
    source = "const crypto = require('crypto');\n\nconsole.log(crypto.randomUUID());\n"
    edits = ensure_import_javascript(
        source,
        import_name="crypto",
        esm_stmt="import crypto from 'crypto';",
        cjs_stmt="const crypto = require('crypto');",
    )
    res = apply_edits(source, edits) if edits else source
    assert res == source


def test_duplicate_esm_import_no_op():
    source = "import DOMPurify from 'dompurify';\n\nconst clean = DOMPurify.sanitize(x);\n"
    edits = ensure_import_javascript(
        source,
        import_name="DOMPurify",
        esm_stmt="import DOMPurify from 'dompurify';",
        cjs_stmt="const DOMPurify = require('dompurify');",
    )
    res = apply_edits(source, edits) if edits else source
    assert res == source
