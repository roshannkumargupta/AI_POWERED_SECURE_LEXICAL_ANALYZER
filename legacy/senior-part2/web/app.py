import os
import sys
import logging
from flask import Flask, request, jsonify, render_template

# Setup professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Consistent Path Handling: Find project root relative to this file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from src.security.hybrid_analyzer import HybridAnalyzer
from src.utils.report_generator import ReportGenerator
from src.security.healer import CodeHealer

app = Flask(__name__, 
            template_folder=os.path.join(PROJECT_ROOT, 'web/templates'),
            static_folder=os.path.join(PROJECT_ROOT, 'web/static'))

# Initialize components
logger.info("Initializing Hybrid AI Analyzer & Healer...")
try:
    analyzer = HybridAnalyzer()
    generator = ReportGenerator()
    healer = CodeHealer()
    logger.info("System Ready: Models and Healer loaded.")
except Exception as e:
    logger.error(f"Failed to initialize system: {e}")
    sys.exit(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_code():
    data = request.json
    code = data.get('code', '')
    
    if not code:
        logger.warning("Analyze request received with no code.")
        return jsonify({'error': 'No code provided'}), 400
        
    logger.info(f"Analysis Started: Received {len(code.splitlines())} lines of code.")
    
    # Run the Hybrid Analysis
    results = analyzer.analyze(code)
    
    # Split code to get full lines for indentation preservation
    code_lines = code.splitlines()
    
    # Enrich results with remediation and suggested fixes
    enriched_results = []
    for r in results:
        vuln_type = r['type']
        remediation = generator._get_solution(vuln_type) or {}
        
        suggested_fix = healer.suggest_fix(vuln_type, code, r['line'])
        
        logger.info(f"Detection: Found {vuln_type} at line {r['line']} (Confidence: {r['confidence']:.2%})")
        
        enriched_results.append({
            'type': vuln_type,
            'line': r['line'],
            'status': r['status'],
            'confidence': r['confidence'],
            'snippet': r['snippet'],
            'remediation': remediation,
            'suggested_fix': suggested_fix
        })
    
    summary = {
        'total': len(enriched_results),
        'vulnerable': sum(1 for r in enriched_results if r['status'] == 'Vulnerable'),
        'potential': sum(1 for r in enriched_results if r['status'] == 'Potentially Vulnerable')
    }
    
    logger.info(f"Analysis Complete: {summary['total']} issues found.")
    
    return jsonify({
        'summary': summary,
        'results': enriched_results
    })

if __name__ == '__main__':
    logger.info("Starting Web Dashboard on http://127.0.0.1:5000")
    app.run(debug=False, port=5000)
