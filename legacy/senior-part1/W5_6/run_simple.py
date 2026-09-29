import sys
from pathlib import Path
from W5_6.lexer import SecureIngestionPipeline, SimpleLexerOutput


def main():
    """Main entry point."""
    
    # Check if input file provided as command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        with open(input_file, 'r', encoding='utf-8') as f:
            sample_code = f.read()
        filename = str(input_file)
    else:
     filename = Path(__file__).parent / "sample_input.txt"
    if filename.exists():
        with open(filename, 'r', encoding='utf-8') as f:
            sample_code = f.read()
            filename=str(filename)  #convert path-->string
    else:
        sample_code = '''validVar = 123;
normal = "hello";
bad = "abc\x01";
wrongID = 9abc;
'''
    
    filename="sample_input.txt"
    
    print(f"\n{'='*70}")
    print(f"WEEK 5&6 LEXER - SIMPLE OUTPUT FORMAT")
    print(f"{'='*70}")
    print(f"Processing: {filename}")
    print(f"{'='*70}\n")
    
    # Initialize pipeline with comprehensive Week 5&6 features
    pipeline = SecureIngestionPipeline(output_dir="results", log_file=None)
    
    # Process the code using full Week 5&6 analysis
    print("Running comprehensive lexical analysis...")
    result = pipeline.process_string(sample_code, filename)
    
    # Generate simple output
    simple = SimpleLexerOutput(result)
    
    # Print summary
    simple.print_summary()
    
    # Print simple output format
    print("INVALID TOKENS:\n")
    output = simple.to_simple_format(show_all=False)
    
    if output == "(No errors detected)":
        print("✅ No errors detected! All tokens are valid.\n")
    else:
        print(output + "\n")
    
    # Save to logs.txt
    print("Saving output to logs.txt...")
    simple.save_simple_format("logs.txt", show_all=False)
    
    # Also save comprehensive JSON output
    print("Saving comprehensive JSON output...")
    result.save("results/comprehensive_output.json")
    
    print(f"\n{'='*70}")
    print("DONE!")
    print(f"{'='*70}")
    print("Files created:")
    print("  - logs.txt (simple format)")
    print("  - results/comprehensive_output.json (full analysis)")
    print(f"{'='*70}\n")


def run_on_file(filepath: str):
    """
    Run lexer on a specific file.
    
    Args:
        filepath: Path to Python source file
    """
    if not Path(filepath).exists():
        print(f"Error: File '{filepath}' not found!")
        return
    
    print(f"\n{'='*70}")
    print(f"Processing file: {filepath}")
    print(f"{'='*70}\n")
    
    # Initialize pipeline
    pipeline = SecureIngestionPipeline(output_dir="results", log_file=None)
    
    # Process file
    result = pipeline.process_file(filepath)
    
    # Generate simple output
    simple = SimpleLexerOutput(result)
    simple.print_summary()
    
    print("INVALID TOKENS:\n")
    print(simple.to_simple_format(show_all=False))
    print()
    
    # Save outputs
    output_name = Path(filepath).stem + "_simple.txt"
    simple.save_simple_format(output_name, show_all=False)
    print(f"\nOutput saved to {output_name}")


if __name__ == "__main__":
    main()