"""
Simple Output Generator for Week 5&6 Lexer

This module provides a simplified interface to the comprehensive
Week 5&6 lexer, outputting results in a simple text format:

    ERROR at {position}: {type}: {value} (Entropy={entropy}, Valid={valid})

Usage:
    from simple_output import generate_simple_output
    
    output = generate_simple_output("x = 5", "demo.py")
    print(output)
"""

from lexer import SecureIngestionPipeline, SimpleLexerOutput


def generate_simple_output(source_code: str, filename: str = "<string>") -> str:
    """
    Process source code and generate simple text output.
    
    This function uses the full Week 5&6 lexer pipeline for comprehensive
    analysis, then formats the output in a simple text format.
    
    Args:
        source_code: Python source code to analyze
        filename: Optional filename for the source
    
    Returns:
        Simple text output with one line per invalid token
    
    Example:
        >>> code = 'validVar = 123;'
        >>> output = generate_simple_output(code)
        >>> print(output)
        ERROR at 0: IDENTIFIER: validVar (Entropy=2.750, Valid=False)
    """
    # Use full pipeline for comprehensive analysis
    pipeline = SecureIngestionPipeline(output_dir="results", log_file=None)
    result = pipeline.process_string(source_code, filename)
    
    # Generate simple output
    simple = SimpleLexerOutput(result)
    return simple.to_simple_format(show_all=False)


def generate_simple_output_from_file(filepath: str) -> str:
    """
    Process a Python file and generate simple text output.
    
    Args:
        filepath: Path to Python source file
    
    Returns:
        Simple text output with one line per invalid token
    
    Example:
        >>> output = generate_simple_output_from_file("sample.py")
        >>> print(output)
    """
    pipeline = SecureIngestionPipeline(output_dir="results", log_file=None)
    result = pipeline.process_file(filepath)
    
    simple = SimpleLexerOutput(result)
    return simple.to_simple_format(show_all=False)


def save_simple_output(source_code: str, output_path: str, filename: str = "<string>"):
    """
    Process source code and save simple output to a file.
    
    Args:
        source_code: Python source code to analyze
        output_path: Path to save output file
        filename: Optional filename for the source
    
    Example:
        >>> code = 'x = 5'
        >>> save_simple_output(code, "logs.txt")
    """
    output = generate_simple_output(source_code, filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"Output saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    sample_code = '''validVar = 123;
normal = "hello";
bad = "abc\x01";
wrongID = 9abc;
veryRandom = asd9f8as9df8as9df8as9df;
'''
    
    print("=== SIMPLE OUTPUT FORMAT ===\n")
    output = generate_simple_output(sample_code, "sample_input.txt")
    print(output)
    
    print("\n=== SAVING TO FILE ===")
    save_simple_output(sample_code, "logs.txt", "sample_input.txt")