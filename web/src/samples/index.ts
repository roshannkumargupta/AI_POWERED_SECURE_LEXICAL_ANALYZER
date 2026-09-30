import { SampleItem } from '../api/client';

export const BUNDLED_SAMPLES: SampleItem[] = [
  {
    id: 'python-vuln-cmd-injection',
    title: 'Command Injection (Flask / os.system)',
    category: 'vulnerable',
    language: 'python',
    filename: 'vulnerable_ping.py',
    code: `from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/ping')
def ping():
    # Untrusted user parameter flows directly into system shell
    target = request.args.get('ip')
    os.system('ping -c 1 ' + target)
    return 'Ping dispatched'
`,
    description:
      'Vulnerable endpoint where an HTTP request parameter enters via request.args.get and reaches the os.system() sink via dynamic string concatenation.',
  },
  {
    id: 'python-adv-trojan-source',
    title: 'Trojan Source Bidi Override Attack',
    category: 'adversarial',
    language: 'python',
    filename: 'trojan_auth.py',
    code: `# Trojan Source Bidirectional Override Attack (CVE-2021-42574)
access_level = 'user'

# Visual display appears benign, but bidi control reverses execution logic
if access_level != 'user\u202e \u2066# check admin\u2069 \u2066':
    print('Administrative privileges granted!')
else:
    print('Standard access only.')
`,
    description:
      'Adversarial sample exploiting Right-to-Left Override (U+202E) control characters to reverse visual token order while preserving malicious execution semantics.',
  },
  {
    id: 'python-adv-cyrillic-homoglyph',
    title: 'Cyrillic Homoglyph Execution',
    category: 'adversarial',
    language: 'python',
    filename: 'homoglyph_exec.py',
    code: `# Confusable homoglyph: Latin 'e' replaced with Cyrillic 'е' (U+0435)
payload = input('Enter expression: ')
\u0435xec(payload)
`,
    description:
      'Adversarial obfuscation substituting Latin characters with visually identical Cyrillic counterparts to evade simple keyword-based detection filters.',
  },
  {
    id: 'python-safe-subprocess',
    title: 'Safe Parameterized Subprocess Execution',
    category: 'safe',
    language: 'python',
    filename: 'safe_ping.py',
    code: `import subprocess
import shlex

def safe_ping(target_ip: str) -> None:
    # Verified remediation: array argument vector without shell=True
    clean_ip = shlex.quote(target_ip)
    cmd = ['ping', '-c', '1', clean_ip]
    subprocess.run(cmd, check=True)
`,
    description:
      'Remediated safe implementation using subprocess.run with argument vector and shlex sanitization, immune to shell command injection.',
  },
];
