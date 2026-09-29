import re
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

class CodeHealer:
    """Simple code healer for SQLi and Command Injection"""
    
    def __init__(self):
        self.type_mapping = {
            'SQLI': 'SQL Injection',
            'SQL INJECTION': 'SQL Injection',
            'COMMAND INJECTION': 'Command Injection'
        }

    def _get_indentation(self, line):
        """Extracts leading whitespace from a line"""
        match = re.match(r'^(\s*)', line)
        return match.group(1) if match else ""

    def _fix_sqli(self, line, indent):
        """Standard SQLi multi-parameter fix"""
        # Match the assignment structure
        match = re.search(r'String\s+([a-zA-Z0-9_]+)\s*=\s*(.*);', line.strip())
        if not match: 
            return None
        
        # Extract string literals and identifiers in order
        # This regex matches either a double-quoted string (handling escapes) or an identifier
        var_name, expr = match.groups()
        params = re.findall(r'\+\s*([a-zA-Z0-9_]+)', expr)
        if not params: 
            return None
        
        parts = re.findall(r'("(?:\\.|[^"\\])*?")', expr)
        cleaned_parts = []
        for i, p in enumerate(parts):
            p = p[1:-1]
            if i < len(params): p = p.rstrip().rstrip("'").rstrip()
            if i > 0: p = p.lstrip().lstrip("'").lstrip()
            cleaned_parts.append(p)
        
        # Reconstruct the query string with '?' placeholders
        # Joining with " ? " and then collapsing multiple spaces ensures clean formatting
        query_str = " ? ".join(cleaned_parts)
        query_str = re.sub(r'\s+', ' ', query_str).strip()
        fix_lines = [
            f'String {var_name} = "{query_str}";',
            f'PreparedStatement pstmt = connection.prepareStatement({var_name});'
        ]
        
        for i, p in enumerate(params, 1):
            fix_lines.append(f'pstmt.setString({i}, {p});')

        return "\n".join([indent + l for l in fix_lines])

    def _fix_command(self, full_code, line_num, indent):
        """Heals command injection using ProcessBuilder"""
        lines = full_code.split('\n')
        current_line = lines[line_num - 1].strip()

        # Try to find the variable name being executed: exec(commandName)
        exec_match = re.search(r'\.exec\s*\(\s*([a-zA-Z0-9_]+)\s*\)', current_line)
        
        target_line = current_line
        if exec_match:
            var_name = exec_match.group(1)
            # Look back for the assignment of this variable
            for i in range(line_num - 2, max(-1, line_num - 12), -1):
                if f'String {var_name}' in lines[i]:
                    target_line = lines[i].strip()
                    indent = self._get_indentation(lines[i])
                    break

        # Parse the command string more accurately
        # Pattern: "ping -c 4 " + host
        match = re.search(r'"(.*?)"\s*\+\s*([a-zA-Z0-9_]+)', target_line)
        if match:
            full_cmd_str, input_var = match.groups()
            
            # Split the command string into parts (e.g., ["ping", "-c", "4"])
            cmd_parts = full_cmd_str.strip().split()
            
            # Reconstruct the ProcessBuilder arguments
            # We want: "cmd", "arg1", "arg2", inputVar
            pb_args = ", ".join([f'"{p}"' for p in cmd_parts]) + f', {input_var.strip()}'
            
            fix_lines = [
                f'ProcessBuilder pb = new ProcessBuilder({pb_args});',
                f'Process p = pb.start();'
            ]
            return "\n".join([indent + l for l in fix_lines])
        
        return None

    def suggest_fix(self, vuln_type, full_code, line_num):
        """Context-aware entry point"""
        v_type = str(vuln_type).upper()
        
        # Skip XSS
        if 'XSS' in v_type or 'CROSS-SITE' in v_type:
            return None
        
        lines = full_code.split('\n')
        if not (0 < line_num <= len(lines)):
            return None
            
        current_line = lines[line_num - 1]
        indent = self._get_indentation(current_line)

        if 'SQL' in v_type:
            return self._fix_sqli(current_line, indent)
        if 'COMMAND' in v_type:
            return self._fix_command(full_code, line_num, indent)
            
        return None
