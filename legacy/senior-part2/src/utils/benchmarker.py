import os
import sys
import time
import csv
import random
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# Ensure project root is in the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.security.static_analyzer import StaticAnalyzer
from src.security.ai_analyzer import AIAnalyzer
from src.security.hybrid_analyzer import HybridAnalyzer

class PerformanceBenchmarker:
    """Creates graph on Execution Time vs. Lines of Code (LOC)"""
    
    def __init__(self, dataset_path=None, num_samples=500):
        if dataset_path is None:
            dataset_path = os.path.join(PROJECT_ROOT, 'datasets/cleaned_file1.csv')
            
        self.dataset_path = dataset_path
        self.num_samples = num_samples
        self.static_analyzer = StaticAnalyzer()
        self.ai_analyzer = AIAnalyzer()
        self.hybrid_analyzer = HybridAnalyzer()
        
        # Store results as: {mode: [(loc, time), ...]}
        self.data_points = {
            'static': [],
            'ai': [],
            'hybrid': []
        }

    def _get_samples(self):
        """Get samples with varying lengths (Lines of Code)"""
        print(f"Sampling {self.num_samples} test cases from {self.dataset_path}...")
        samples = []
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                reader = list(csv.DictReader(f))
                selected = random.sample(reader, min(len(reader), self.num_samples))
                for row in selected:
                    samples.append(row['vulnerable_code'])
            return samples
        except Exception as e:
            print(f"Error sampling dataset: {e}")
            return []

    def run_benchmark(self):
        test_code_list = self._get_samples()
        if not test_code_list:
            return

        print("\n--- Measuring Performance vs. LOC ---")
        
        for i, code in enumerate(test_code_list, 1):
            loc = len(code.split('\n'))
            
            # 1. Static
            start = time.time()
            self.static_analyzer.static_analyze(code)
            self.data_points['static'].append((loc, (time.time() - start) * 1000))

            # 2. AI
            start = time.time()
            self.ai_analyzer.analyze(code)
            self.data_points['ai'].append((loc, (time.time() - start) * 1000))

            # 3. Hybrid
            start = time.time()
            self.hybrid_analyzer.analyze(code)
            self.data_points['hybrid'].append((loc, (time.time() - start) * 1000))

            if i % 100 == 0:
                print(f"Processed {i}/{len(test_code_list)} samples...")

    def generate_report(self, output_dir=None):
        if output_dir is None:
            output_dir = os.path.join(PROJECT_ROOT, 'docs/benchmarks')
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        plt.figure(figsize=(12, 8))
        
        colors = {'static': '#3498db', 'ai': '#e74c3c', 'hybrid': '#2ecc71'}
        labels = {'static': 'Static (Rules)', 'ai': 'AI (Sliding Window)', 'hybrid': 'Hybrid (Surgical)'}
        markers = {'static': 'o', 'ai': 's', 'hybrid': '^'}

        for mode in ['static', 'ai', 'hybrid']:
            if not self.data_points[mode]:
                continue
            data = np.array(self.data_points[mode])
            locs = data[:, 0]
            times = data[:, 1]
            
            # Scatter plot of raw data
            plt.scatter(locs, times, color=colors[mode], label=labels[mode], 
                        alpha=0.4, marker=markers[mode], s=20)
            
            # Add a Trend Line (Linear Regression)
            if len(locs) > 1:
                z = np.polyfit(locs, times, 1)
                p = np.poly1d(z)
                plt.plot(locs, p(locs), color=colors[mode], linestyle='--', linewidth=2)

        plt.title('Performance Scaling: Analysis Time vs. Lines of Code', fontsize=14, fontweight='bold')
        plt.xlabel('Lines of Code (LOC)', fontsize=12)
        plt.ylabel('Execution Time (milliseconds)', fontsize=12)
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend()
        
        output_path = os.path.join(output_dir, 'time_vs_loc.png')
        plt.savefig(output_path)
        print(f"\nGraph saved to: {output_path}")

        # Summary Table print
        print("\nAvg Performance (ms per 10 lines):")
        for mode in ['static', 'ai', 'hybrid']:
            if not self.data_points[mode]:
                continue
            data = np.array(self.data_points[mode])
            avg_per_10 = (np.mean(data[:, 1]) / np.mean(data[:, 0])) * 10
            print(f"   {mode.upper():<10}: {avg_per_10:.4f} ms")

if __name__ == "__main__":
    bench = PerformanceBenchmarker(num_samples=400)
    bench.run_benchmark()
    bench.generate_report()
