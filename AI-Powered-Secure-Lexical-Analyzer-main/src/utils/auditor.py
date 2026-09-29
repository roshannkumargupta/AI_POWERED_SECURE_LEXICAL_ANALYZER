import os
import sys

# Ensure project root is in the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.security.hybrid_analyzer import HybridAnalyzer
from src.utils.report_generator import ReportGenerator

class SecurityAuditor:
    """Main Auditor class that orchestrates analysis and reporting"""
    
    def __init__(self):
        self.analyzer = HybridAnalyzer()
        self.generator = ReportGenerator()

    def run(self, code):
        # Run Hybrid Analysis
        results = self.analyzer.analyze(code)

        # Generate Detailed Remediation Report
        self.generator.generate_console_report(results)
        
        return results

if __name__ == "__main__":
    auditor = SecurityAuditor()
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        else:
            print(f"Error: File '{file_path}' not found.")
            sys.exit(1)
    else:
        code = """
        public class TestApp {
            public void process(String data) {
                // Some safe code here
                int x = 10;
                System.out.println("Processing...");
                
                // A SQL Injection hotspot
                String query = "SELECT * FROM users WHERE name = '" + data + "'";
                db.execute(query);
                
                // More safe code
                log.info("Finished database op");
                
                // A Command Injection hotspot
                Runtime.getRuntime().exec("ping " + data);
            }
        }
        """

    auditor.run(code)
