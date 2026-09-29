import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.security.static_analyzer import StaticAnalyzer
from src.security.ai_analyzer import AIAnalyzer

class HybridAnalyzer:
    """Surgical Hybrid Analyzer: Static Rules find hotspots, AI verifies them"""
    
    def __init__(self):
        self.static = StaticAnalyzer()
        self.ai = AIAnalyzer()

    def analyze(self, code):
        """
        Runs the surgical hybrid pipeline.
        Only sends suspicious lines to the AI.
        """
        lines = code.split('\n')
        
        # Run Static Analysis first
        static_vulns, static_line_info = self.static.static_analyze(code)
        
        final_results = []

        # Iterate through Static hits
        for vuln_type, detected_lines in static_line_info.items():
            for line_num in detected_lines:
                # Context Window Extraction (The local view)
                # (Extract 5 lines above and 5 lines below the hit)
                start_idx = max(0, line_num - 5)
                end_idx = min(len(lines), line_num + 5)
                context_snippet = '\n'.join(lines[start_idx:end_idx])
                
                # AI Verification
                # Only analyze the snippet that static analyzer flagged
                ai_type, ai_conf = self.ai.predict_snippet(context_snippet)
                
                # Determine status
                # (Agreement must happen on BOTH existence and type)
                is_vulnerable = (ai_type == vuln_type) and (ai_conf > 0.5)
                
                status = "Vulnerable" if is_vulnerable else "Potentially Vulnerable"
                
                snippet = lines[line_num-1].strip() if line_num <= len(lines) else ""
                
                final_results.append({
                    'type': vuln_type,
                    'line': line_num,
                    'status': status,
                    'confidence': ai_conf if is_vulnerable else 0.5,
                    'snippet': snippet,
                    'ai_suggestion': ai_type # What the AI thinks it is
                })

        return final_results

    def print_report(self, results):
        """Helper to print a professional report"""
        if not results:
            print("No vulnerabilities detected.")
            return

        print("=" * 80)
        print(f"{'TYPE':<20} | {'LINE':<5} | {'STATUS':<25} | {'CONFIDENCE'}")
        print("-" * 80)
        
        # Sort by status (Vulnerable first) then line
        results.sort(key=lambda x: (x['status'] != 'Vulnerable', x['line']))
        
        for r in results:
            status_str = f"[{r['status']}]"
            print(f"{r['type']:<20} | {r['line']:<5} | {status_str:<25} | {r['confidence']:.2%}")
            print(f"   Snippet: {r['snippet']}")
            if r['status'] == "Potentially Vulnerable":
                 print(f"   AI Note: AI classified this context as '{r['ai_suggestion']}'")
            print("-" * 80)

if __name__ == "__main__":
    analyzer = HybridAnalyzer()
    
    test_code = """
    public class HybridTest {
        public void test(String input) {
            // Hotspot 1: Real SQLi
            String query = "SELECT * FROM users WHERE id='" + input + "'";
            db.execute(query);
            
            // Hotspot 2: Safe String concat
            String logMsg = "User " + input + " logged in.";
            System.out.println(logMsg);
        }
    }
    """
    
    results = analyzer.analyze(test_code)
    analyzer.print_report(results)
