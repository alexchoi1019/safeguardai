# Voice Phishing Detection Test Suite & Tuning Walkthrough

Successfully implemented the 35 test scenarios, tuned the risk weights, and achieved the MVP goals for phishing detection accuracy.

## Changes Made

### 1. Weight & Threshold Optimization
Applied fine-tuned weights and thresholds to prioritize "Money" and "Technology" risks while maintaining safety for normal conversations.
- **Weights:** Institution (30), Crime (35), Money (40), Tech (45), Urgency (15), Threat (30), Authority (25), Loan (35), Messenger (25).
- **Thresholds:** WARNING (35+), DANGER (70+).

### 2. Keyword Dataset Refinement
Updated [keywords.json](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/keywords.json) with more specific phrases to reduce False Positives (Normal calls) and catch more Phishing variants.
- Replaced generic "송금" with specific "송금하세요", "송금해줘".
- Added high-risk phrases like "범죄에 연루됐습니다", "대출 심사", "구속 절차".

### 3. Automated Test Suite
Enhanced [test_suite.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/test_suite.py) to execute all 35 scenarios and generate a detailed report.

## Test Results Summary

> [!TIP]
> **Total Pass Rate: 31/35 (88.6%)**
> - **Normal Scenarios:** 14/15 SAFE (Target: 13/15) - **EXCEEDED**
> - **Phishing Scenarios:** 17/20 WARNING+ (Target: 17/20) - **ACHIEVED**
> - **High-Risk (P16, P20, etc.):** Successfully detected as **DANGER**.

### Detailed Report snippet
```text
ID   | Score | Actual   | Expected | Success | Categories
------------------------------------------------------------
N7   | 30.0  | SAFE     | SAFE     | PASS    | 기관 사칭
N12  | 0.0   | SAFE     | SAFE     | PASS    |
P3   | 100.0 | DANGER   | DANGER   | PASS    | 기관 사칭, 범죄 관련, 금전 요구
P16  | 100.0 | DANGER   | DANGER   | PASS    | 기관 사칭, 범죄 관련, 금전 요구, 긴급성
P18  | 75.0  | DANGER   | DANGER   | PASS    | 금전 요구, 대출 사기
```

## How to Verify
Run the following command in the terminal to see the full report:
```powershell
backend\venv\Scripts\python backend\test_suite.py
```
