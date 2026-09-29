import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from codecarbon import EmissionsTracker

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.security.hybrid_analyzer import HybridAnalyzer

def generate_real_code(lines_count):
    """Generates a real multi-line Java string for testing"""
    base_code = [
        "public class BenchmarkTest {",
        "    public void method() {",
        "        String data = \"test\";",
        "        // Vulnerability Hotspot",
        "        String sql = \"SELECT * FROM users WHERE id = '\" + data + \"'\";",
        "        System.out.println(sql);"
    ]
    # Fill the rest with realistic-looking boilerplate lines
    for i in range(lines_count - 8):
        base_code.append(f"        int var{i} = {i}; // Boilerplate line to simulate file size")
    
    base_code.append("    }")
    base_code.append("}")
    return "\n".join(base_code)

def generate_emission_graph(data_points, output_dir):
    plt.figure(figsize=(10, 6))
    data_points.sort(key=lambda x: x[0])
    locs = [d[0] for d in data_points]
    emissions = [d[1] for d in data_points]
    
    plt.scatter(locs, emissions, color='#2ecc71', label='Secure Lexical Analyzer', s=80, edgecolors='black', zorder=5)
    
    if len(locs) > 1:
        z = np.polyfit(locs, emissions, 1)
        p = np.poly1d(z)
        plt.plot(locs, p(locs), color='#27ae60', linestyle='--', linewidth=2, label='Energy Scaling Trend')

    plt.title('Carbon Footprint Analysis: Secure Lexical Analyzer', fontsize=14, fontweight='bold')
    plt.xlabel('Lines of Code (LOC)', fontsize=12)
    plt.ylabel('CO2 Emissions (grams)', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    
    output_path = os.path.join(output_dir, 'carbon_impact_vs_loc.png')
    plt.savefig(output_path)
    print(f"\nVisual graph saved to: {output_path}")

def run_emission_benchmark():
    output_dir = os.path.join(PROJECT_ROOT, 'docs/benchmarks')
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    analyzer = HybridAnalyzer()
    
    # Define sizes to test
    line_sizes = [10, 50, 100, 250, 500]
    data_points = []
    
    tracker = EmissionsTracker(
        project_name="visual_benchmark",
        output_dir=output_dir,
        measure_power_secs=1,
        save_to_file=False
    )

    for loc in line_sizes:
        print(f"  Generating and testing {loc} actual lines of code...")
        code = generate_real_code(loc)
        
        tracker.start()
        # 100 iterations to get a stable energy delta
        for _ in range(100):
            analyzer.analyze(code)
        
        emissions_kg = tracker.stop()
        emissions_g = emissions_kg * 1000
        data_points.append((loc, emissions_g))
        print(f"    Emissions: {emissions_g:.6f} grams")

    generate_emission_graph(data_points, output_dir)

if __name__ == "__main__":
    run_emission_benchmark()
