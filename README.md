# NexaShield App

## 🛡️ Advanced CyberSecurity Defense System

NexaShield is a cutting-edge cybersecurity defense system designed to provide robust protection against a wide array of digital threats, including sophisticated phishing attacks and various forms of malware. Leveraging advanced machine learning models and a modular architecture, NexaShield aims to offer real-time threat detection, analysis, and prevention capabilities. This project is hosted on GitHub: https://github.com/git-atharvb/nexashield-app.git

---

## Table of Contents

1.  [Introduction](#1-introduction)
2.  [Features](#2-features)
3.  [Architecture Overview](#3-architecture-overview)
4.  [Technology Stack](#4-technology-stack)
5.  [Modules and Components](#5-modules-and-components)
    *   [Antivirus Module](#antivirus-module)
    *   [Phishing Detection Module](#phishing-detection-module)
    *   [Network Intrusion Detection (NIDS)](#network-intrusion-detection-nids)
    *   [Process & Memory Management](#process--memory-management)
    *   [SIEM Dashboard](#siem-dashboard)
6.  [Machine Learning Models and Datasets](#6-machine-learning-models-and-datasets)
    *   [Antivirus Model Details](#antivirus-model-details)
    *   [Phishing Detection Model Details](#phishing-detection-model-details)
7.  [Design and Styling](#7-design-and-styling)
8.  [Installation and Setup](#8-installation-and-setup)
9.  [Usage](#9-usage)
10. [Contributing](#10-contributing)
11. [License](#11-license)

---

## 1. 🚀 Introduction

In an increasingly interconnected world, digital security is paramount. NexaShield addresses this critical need by offering an intelligent, adaptive desktop defense system. It integrates multiple threat detection mechanisms—ranging from ML-based phishing and malware detection to real-time network packet sniffing and active OS-level firewall prevention. Our goal is to empower users and organizations with a proactive, unified threat management suite against evolving cyber threats.

## 2. ✨ Features

*   **Real-time Phishing Detection** 🎣: Analyzes URLs and web content to identify and block phishing attempts. This feature helps protect users from fraudulent websites designed to steal credentials or sensitive information by scrutinizing various URL characteristics and page content.
*   **Advanced Antivirus Scanning** 🦠: Detects and neutralizes various types of malware, including viruses, worms, and Trojans. It employs sophisticated machine learning techniques to identify malicious code and behavioral patterns in files and processes.
*   **Machine Learning Powered** 🧠: Utilizes sophisticated ML models for accurate and adaptive threat identification. Our models are continuously trained on vast and diverse datasets to recognize new and emerging threats, reducing reliance on static signatures.
*   **Network Intrusion Detection & Prevention (NIDS/IPS)** 🚨: Live packet capture and Deep Packet Inspection (DPI) powered by Scapy. Includes Snort-style rules to identify network scans, payloads, and automatically block malicious IPs at the OS firewall level.
*   **Real-time Process & Memory Monitoring** ⚡: Track, suspend, or terminate suspicious system processes. Monitor live CPU/RAM utilization, inspect disk partitions, check S.M.A.R.T health status, and easily clean temporary files.
*   **SIEM Dashboard** 📊: A centralized command center summarizing device health, active telemetry (animated histograms), and aggregating recent security events into a single actionable feed.
*   **Modular Design** 🧩: Allows for easy expansion and integration of new security features. This architecture ensures scalability, maintainability, and the ability to rapidly adapt to new threat landscapes and incorporate additional security modules.
*   **User-friendly GUI** 🖥️: Built with PyQt6, providing a highly responsive, modern desktop interface with interactive graphs, customizable tables, and a seamless user experience.
*   **Comprehensive Reporting** 📑: Effortlessly export live process lists, network packet captures (PCAP), and scan histories to PDF or CSV formats for forensic analysis.

## 3. 🏛️ Architecture Overview

NexaShield is designed as a powerful modular Desktop Application, seamlessly integrating a locally hosted Python backend with a rich graphical interface.

*   **Graphical User Interface (GUI)** 🌐: Developed using PyQt6, it handles user interaction, interactive telemetry charting, and configuration panels.
*   **Core Logic Engines** ⚙️: Multi-threaded Python workers utilizing libraries like `psutil` (for system metrics) and `scapy` (for deep packet inspection).
*   **Machine Learning Integration** 🧠: ML models for Antivirus and Phishing detection load locally or communicate with microservices to deliver high-performance inferences.
*   **Local Database** 🗄️: Uses local SQLite (`nexashield.db`) to log real-time events, threat history, and maintain signature databases locally.

# Working Synopsis 

[PyQt6 Desktop GUI] --> B(Python Core Engine)
    B --> C{ML Service: Phishing Detection}
    B --> D{ML Service: Antivirus Engine}
    C --> E["Nexa_Datasets/phishing (Cloud/Local)"]
    D --> F["Nexa_Datasets/antivirus (Cloud/Local)"]
    B --> G[SQLite Database]
    B --> H[Scapy NIDS Engine]
    B --> I[psutil System Monitor]


## 4. Technology Stack

*   **Desktop Framework**: PyQt6 (Python GUI).
*   **Networking & Sniffing**: Scapy.
*   **System Telemetry**: psutil, OS-level WMI/bash calls.
*   **Machine Learning**: Scikit-learn, Pandas, NumPy, TensorFlow/PyTorch.
*   **Data Serialization**: `pickle` (`.pkl` files), JSON.
*   **Database**: SQLite (`nexashield.db`).
*   **PDF Generation**: PyQt6 `QtPrintSupport`.

## 5. Modules and Components

NexaShield is structured into distinct modules to manage different aspects of cybersecurity.

### Antivirus Module
This module is responsible for detecting and identifying malicious software. It integrates with the core system to scan files, processes, and system behavior for known and emerging threats.

### Phishing Detection Module
Focused on web-based threats, this module analyzes URLs, website content, and network traffic patterns to identify and warn users about phishing attempts, protecting them from credential theft and other social engineering attacks.

### Network Intrusion Detection (NIDS)
Sniffs network traffic across all interfaces to intercept malicious packets. Features deep packet inspection, rule-based signature matching (similar to Snort), and active blocking of dangerous IP addresses using the OS's native firewall.

### Process & Memory Management
Provides detailed insight into system performance, allowing users to track down high CPU/RAM consumers, terminate suspicious activities, evaluate storage health (S.M.A.R.T), and reclaim memory by safely clearing temp files.

### SIEM Dashboard
A global overview aggregating device telemetry (histograms and donut charts for CPU/RAM/Disk), system health checks, and a consolidated feed of security alerts coming from all other active modules.

## 6. Machine Learning Models and Datasets

The core intelligence of NexaShield lies in its machine learning models, trained on extensive and diverse datasets.

### Antivirus Model Details

The Antivirus module employs a supervised machine learning approach to classify files or system activities as benign or malicious.

*   **Datasets Used (`Nexa_Datasets/antivirus/`)**:
    *   `data.csv`: The primary dataset containing features extracted from various files (e.g., API calls, file structure, entropy, permissions) and their corresponding labels (benign/malicious).
    *   `labels.txt`: A file listing the distinct class labels used in the `data.csv` for classification.
    *   `df_file_extensions.csv`: Likely used for feature engineering, mapping file extensions to specific risk scores or categories, or for filtering/grouping data.
    *   `REWEMA.csv`: Potentially a dataset containing features specific to the REWEMA malware family or a broader set of behavioral indicators, used to enrich the feature set or for specific detection rules.
    *   `sample_analysis_data.txt`: Raw or pre-processed data from sample analyses, used for further feature extraction or as a testbed.
    *   `vectorizer.pkl`: A serialized vectorizer object (e.g., `TfidfVectorizer`, `CountVectorizer`, or a custom feature vectorizer). This component is crucial for transforming raw, often textual or categorical, features (like API call sequences, file paths, or string patterns) into numerical vectors that the ML model can process.
    *   `classification_report.csv`: Contains performance metrics (precision, recall, F1-score, support) for the trained antivirus model, indicating its effectiveness.
    *   `cross_validation_result.csv`: Shows the results of cross-validation, demonstrating the model's robustness and generalization capabilities across different data subsets.

*   **Working of the ML Model**:
    1.  **Data Collection & Preprocessing**: Raw file samples are analyzed to extract relevant features. `data.csv` is compiled from these features. `df_file_extensions.csv` and `REWEMA.csv` might contribute to feature engineering, adding context or specific indicators.
    2.  **Feature Vectorization**: The `vectorizer.pkl` is loaded and applied to transform the extracted features (e.g., sequences of API calls, strings from `REWEMA.csv`) into a numerical format suitable for machine learning algorithms.
    3.  **Model Training**: A classification algorithm (e.g., Support Vector Machine, Random Forest, Gradient Boosting, or a Neural Network) is trained on the vectorized features from `data.csv` and their corresponding labels from `labels.txt`.
    4.  **Evaluation**: The model's performance is rigorously evaluated using metrics stored in `classification_report.csv` and `cross_validation_result.csv` to ensure high accuracy and low false positive rates.
    5.  **Deployment**: The trained model (or its logic) is integrated into the Antivirus module to perform real-time detection on new files or processes. When a new file is scanned, its features are extracted, vectorized using the same `vectorizer.pkl`, and fed to the trained model for classification.

### Phishing Detection Model Details

The Phishing Detection module utilizes machine learning to identify and block malicious URLs and web content.

*   **Datasets Used (`Nexa_Datasets/phishing/`)**:
    *   `merged_url_datasets.csv`, `phishind_dataset.csv`, `phishing_site_urls.csv`, `synthetic_phsihing_dataset.csv`: These are the primary datasets containing a large collection of URLs, labeled as either legitimate or phishing. `synthetic_phsihing_dataset.csv` indicates the use of generated data to augment training and improve model robustness.
    *   `malicious_code_links_finidngs_v1.json`: Contains detailed findings or features extracted from known malicious links, potentially including JavaScript snippets, HTML structure anomalies, or specific obfuscation techniques. This data enriches the feature set for URL analysis.
    *   `Trojan_detection.csv`: While primarily for Trojans, this dataset might be used to identify URLs that host or distribute Trojan malware, integrating a broader threat context into phishing detection.
    *   `phishing_model.pkl`: A serialized, pre-trained machine learning model specifically for phishing detection.

*   **Working of the ML Model**:
    1.  **Data Collection & Aggregation**: URLs from various sources (`merged_url_datasets.csv`, `phishind_dataset.csv`, `phishing_site_urls.csv`, `synthetic_phsihing_dataset.csv`) are collected and combined.
    2.  **Feature Engineering**: For each URL, a rich set of features is extracted. These typically include:
        *   **URL-based features**: Length of URL, presence of IP address, number of subdomains, special characters, domain age, WHOIS information, use of HTTPS, redirection count.
        *   **Content-based features**: (If applicable, using `malicious_code_links_finidngs_v1.json` for insights) HTML structure, presence of suspicious JavaScript, embedded forms, brand impersonation indicators.
        *   **Lexical features**: Bag-of-words or TF-IDF on URL components.
    3.  **Model Training**: A classification algorithm (e.g., Logistic Regression, Gradient Boosting Machines, Neural Networks, or Random Forest) is trained on these engineered features and their corresponding labels (phishing/legitimate). The `Trojan_detection.csv` might be used to train a sub-model or add specific features related to malware hosting.
    4.  **Model Serialization**: The trained model is saved as `phishing_model.pkl` for efficient deployment and inference.
    5.  **Deployment & Inference**: When a user encounters a new URL, the Phishing Detection module extracts the same set of features, loads the `phishing_model.pkl`, and feeds the features to the model. The model then predicts whether the URL is legitimate or a phishing attempt, providing real-time protection.

## 7. Design and Styling

The project aims for a clean, intuitive, and responsive user interface.

*   **Design Principles**: Emphasis on clarity, ease of use, and quick access to critical security information. Clean visual cues (color-coded badges, gradients) highlight threats and component statuses intuitively.
*   **Styling**: Integrated global Qt Stylesheets with dynamically swapping Light/Dark themes and interactive charting components (animated donuts and line graphs).

## 8. Installation and Setup

*(Provide instructions here for setting up the project locally. This would typically include cloning the repository, installing dependencies, configuring environment variables, and running the application.)*

```bash
# Example steps (replace with actual instructions)
git clone https://github.com/your-username/nexashield-app.git
cd nexashield-app

# Setup Python Environment
pip install -r requirements.txt

# Run the Application (Requires Admin/Root for full NIDS capabilities)
python main.py
```

## 9. Usage

*(Explain how to use the NexaShield application, including how to initiate scans, view reports, and interact with its features.)*

## 10. Contributing

We welcome contributions to NexaShield! Please refer to `CONTRIBUTING.md` (if available) for guidelines on how to contribute.

## 11. License

This project is licensed under the [Your Chosen License] - see the `LICENSE` file for details.
