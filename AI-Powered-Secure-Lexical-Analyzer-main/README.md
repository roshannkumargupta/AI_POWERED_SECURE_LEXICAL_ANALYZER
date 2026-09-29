# AI Powered Secure Lexical Analyzer

An advanced analysis tool that combines Deterministic Rule-Based Detection with Machine Learning Verification (Random Forest) to identify SQL Injection, XSS, and Command Injection vulnerabilities in Java source codes.

## Key Features

*   **Hybrid Analysis Pipeline:** Uses a high-speed Lexical Analyzer to find "hotspots" and a Random Forest model to verify them.
*   **Surgical Precision:** AI only analyzes the specific context around suspicious lines, reducing false positives.
*   **Sanitization Suggestions:** Automatically generates security advice and "Secure Code" examples for every finding.
*   **Self-Healing:** Has the ability to fix simple SQLi and Command Injection vulnerabilities.
*   **Modern Web Dashboard:** A sleek, dark-mode interface for real-time code auditing.
*   **Performance Benchmarked:** Proven to be 5.4x faster than traditional sliding-window AI scanners.
*   **Low Carbon Footprint:** Very energy efficient compared to professional industry tools

## Tech Stack

### Backend & AI
*   **Python 3.12:** Core logic and analysis engine.
*   **Scikit-Learn:** Random Forest implementation and TF-IDF vectorization.
*   **Flask:** Web server and REST API for the dashboard.
*   **Joblib:** Model serialization and loading.
*   **NumPy & SciPy:** Numerical operations and sparse matrix handling.
*   **CodeCarbon:** Calculate carbon footprint of trained AI.
*   **Matplotlib:** Generation of performance benchmarking graphs.

### Frontend
*   **HTML5 / CSS3:** Custom UI (Dark and Light) without external CSS frameworks.
*   **Vanilla JavaScript:** Real-time communication with the Flask API.

### Security Domain
*   **Custom Lexer:** Built with regular expressions for high-speed pattern matching.
*   **Hybrid Pipeline:** Combines static signatures with semantic AI analysis.

## Architecture

The system operates in a three-stage pipeline:
1.  **Static Layer:** Scans code for dangerous patterns using Regex and Keyword matching.
2.  **ML Layer:** A Random Forest model (trained on 23k+ synthetic samples) analyzes the "semantics" of suspicious code blocks using TF-IDF features.
3.  **Reporting Layer:** Groups findings and maps them to industry-standard remediation strategies (OWASP/SANS).
4.  **Self Healing Layer:** Attemps to self heal some simple vulnerabilities of SQL Injection and Command Injection.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Himanshu-Sharma418/AI-Powered-Secure-Lexical-Analyzer.git
   ```

2. Set up Virtual Environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## First-time Setup
In order to run the analyzers, the following steps have to followed:

1. **Download a dataset:** A dataset containing vulnerable code (SQL Injections, Command Injecions, and Cross-Site Scripting) as well as Safe code has to be downloaded and saved into the `datasets/` folder. The dataset must be in CSV format.

2. **Modify code if required:** Modify the `preprocess.py` and `train.py` to be compatible with your dataset. Make changes to the training file name and the column names according to what is in your dataset.

3. **Train the Model:** Run the following script to preprocess the data and train the model
   ```bash
   python3 src/ml/preprocess.py
   python3 src/ml/train.py
   ```


## Usage

Before using, you need to make sure you have a trained model and other required processed features in the `data/models/` and `data/processed/` directories respectively.

For testing purposes, I trained the model on [Vulnerbility Fix Dataset](https://www.kaggle.com/datasets/jiscecseaiml/vulnerability-fix-dataset) from Kaggle. Therefore, the code written in `src/ml/preprocess.py` works only for CSV files with similar structure. You may modify the code to preprocess different kinds of datasets as required.

Please note that despite having more than 23k samples of code, it is still a synthetic, AI generated dataset with lot of redundant code. Use it with caution as it will almost certainly lead to overfitting.

### 1. Command Line Auditor
To scan a single Java file and get a detailed terminal report:
```bash
python3 src/utils/auditor.py test_files/UserManager.java
```

### 2. Web Dashboard
To launch the interactive web interface:
```bash
python3 web/app.py
```
Then navigate to http://127.0.0.1:5000 in your browser.

## Benchmarking Results

Our tests show the efficiency of the Surgical Hybrid approach compared to pure AI scanning:

| Method              | Avg Speed (ms / 10 lines) |
| :------------------ | :------------------------ |
| Static (Rules)      | 0.90 ms                   |
| AI (Sliding Window) | 94.20 ms                  |
| Hybrid (Surgical)   | 17.37 ms                  |

*Graphs can be found in `docs/benchmarks/`*

## Project Structure

*   **`src/security/`:** Core detection logic (Static, AI, and Hybrid Analyzers).
*   **`src/ml/`:** Machine Learning pipeline (Preprocessing and Training).
*   **`src/utils/`:** Reporting and Benchmarking tools.
*   **`web/`:** Flask-based dashboard files.
*   **`test_files/`:** Sample Java files for testing.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
