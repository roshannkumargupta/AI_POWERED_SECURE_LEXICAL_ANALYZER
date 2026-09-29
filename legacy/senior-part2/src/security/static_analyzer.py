import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml.feature_extractor import FeatureExtractor

class StaticAnalyzer:
    """Performs security analysis of code based on static rules"""
    
    def __init__(self):
        self.extractor = FeatureExtractor()
        
    def static_analyze(self, code):
        """Tells if a code is insecure or not based on its features.
           Returns (vulne_dict, line_info_dict)."""
        features = self.extractor.extract_features(code)
        
        vulne = {
            'Safe': 1,
            'SQL Injection': 0,
            'Command Injection': 0,
            'XSS': 0
        }
        
        line_info = {}

        # SQL Injection
        if features.get('sqli_lines'):
            vulne['SQL Injection'] = 1
            vulne['Safe'] = 0
            line_info['SQL Injection'] = features['sqli_lines']

        # Command Injection
        if features.get('cmd_injection_lines'):
            vulne['Command Injection'] = 1
            vulne['Safe'] = 0
            line_info['Command Injection'] = features['cmd_injection_lines']

        # XSS
        if features.get('xss_lines'):
            vulne['XSS'] = 1
            vulne['Safe'] = 0
            line_info['XSS'] = features['xss_lines']
            
        return vulne, line_info
    
if __name__ == "__main__":
    analyzer = StaticAnalyzer()
    
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            code = f.read()
    else:
        code = """String userInput = getParameter("id");
String query = "SELECT * FROM users WHERE id='" + userInput + "'";
System.out.println(query);
Runtime.getRuntime().exec("cmd /c " + userInput);
document.write("<script>" + userInput + "</script>");"""
        
    vulne, line_info = analyzer.static_analyze(code)
    if vulne['Safe'] == 1:
        print("There were no vulnerabilities detected")
    else:
        for vuln_name, lines in line_info.items():
            if lines:
                line_list = ', '.join(str(l) for l in lines)
                print(f"Possible {vuln_name} at line {line_list}")