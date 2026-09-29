import json
from collections import defaultdict

class ReportGenerator:
    """Generates grouped security reports with remediation advice"""
    
    def __init__(self):
        # Professional remediation database
        self.solutions = {
            'SQL Injection': {
                'title': 'Use Parameterized Queries (PreparedStatements)',
                'description': 'Never concatenate user input directly into SQL strings.',
                'fix': 'Use the PreparedStatement API to safely bind variables.',
                'example': [
                    '// SECURE (Fix)',
                    'String query = "SELECT * FROM users WHERE id = ?";',
                    'PreparedStatement pstmt = connection.prepareStatement(query);',
                    'pstmt.setString(1, input);'
                ]
            },
            'Cross-Site Scripting (XSS)': {
                'title': 'Implement Output Encoding',
                'description': 'User-provided data must be encoded before being rendered in the browser.',
                'fix': 'Use a trusted library like OWASP Java Encoder for context-aware encoding.',
                'example': [
                    '// SECURE (Fix)',
                    'import org.owasp.encoder.Encode;',
                    'writer.println("<div>" + Encode.forHtml(userInput) + "</div>");'
                ]
            },
            'Command Injection': {
                'title': 'Use Parameterized Process Execution',
                'description': 'Executing shell commands with concatenated strings allows shell injection.',
                'fix': 'Use ProcessBuilder and pass arguments as a separate list.',
                'example': [
                    '// SECURE (Fix)',
                    'ProcessBuilder pb = new ProcessBuilder("git", "checkout", branchName);',
                    'pb.start();'
                ]
            }
        }

        # Normalization mapping (XSS -> Cross-Site Scripting (XSS))
        self.type_mapping = {
            'XSS': 'Cross-Site Scripting (XSS)',
            'SQLI': 'SQL Injection',
            'SQL INJECTION': 'SQL Injection',
            'COMMAND INJECTION': 'Command Injection'
        }

    def _get_solution(self, vuln_type):
        """Helper to find a solution even if the name varies slightly"""
        # Try direct match
        if vuln_type in self.solutions:
            return self.solutions[vuln_type]
        
        # Try normalization mapping
        norm_type = self.type_mapping.get(vuln_type.upper())
        if norm_type:
            return self.solutions.get(norm_type)
            
        return None

    def generate_console_report(self, results):
        """Prints a grouped remediation report to the console"""
        if not results:
            print("No vulnerabilities detected.")
            return

        print("=" * 80)
        print("SECURITY ANALYSIS REPORT (Grouped by Type)")
        print("=" * 80)

        grouped_results = defaultdict(list)
        for r in results:
            grouped_results[r['type']].append(r)

        for vuln_type, occurrences in grouped_results.items():
            solution = self._get_solution(vuln_type)
            # Use the descriptive name from the solution if possible
            display_name = solution['title'].split('(')[0] if solution else vuln_type
            
            print(f"\n>>> VULNERABILITY: {vuln_type} ({len(occurrences)} occurrences)")
            print("-" * 80)
            
            for i, occ in enumerate(occurrences, 1):
                status_str = f"[{occ['status']}]"
                print(f"   {i}. Line {occ['line']:<4} | {status_str:<25} | Confidence: {occ['confidence']:.2%}")
                print(f"      Code: {occ['snippet']}")
            
            if solution:
                print(f"\n   --- REMEDIATION ---")
                print(f"   Title:       {solution['title']}")
                print(f"   Description: {solution['description']}")
                print(f"   Recommended: {solution['fix']}")
                print("\n   Code Example:")
                for line in solution['example']:
                    print(f"      {line}")
            else:
                print(f"\n   No remediation template found for '{vuln_type}'.")
            
            print("-" * 80)

    def generate_json_report(self, results, output_file):
        """Exports the analysis and remediation data to a JSON file"""
        report_data = {
            'summary': {
                'total_vulnerabilities': len(results),
                'high_confidence': sum(1 for r in results if r['status'] == 'Vulnerable')
            },
            'findings': results,
            'remediation_database': self.solutions
        }

        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=4)
