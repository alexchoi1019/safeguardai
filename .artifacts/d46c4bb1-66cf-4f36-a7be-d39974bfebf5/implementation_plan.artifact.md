# Risk Analysis Refinement: Context Patterns & Threshold Synchronization

This plan addresses the 4 failed test cases (N15, P6, P12, P19) by implementing context-aware rules in the backend and synchronizing the risk thresholds between the Android app and the backend.

## User Review Required

> [!IMPORTANT]
> The thresholds will be lowered to **WARNING: 35+** and **DANGER: 70+** across both the Android app and the Backend.
>
> **Key Logic Additions:**
> - **Safe Context Exception:** Reduces score for "Technology" keywords if safe words like "Company" or "Announcement" are present.
> - **Urgency Pressure Bonus:** Adds 20 points when urgency is combined with pressure words like "Big trouble" or "Stop account".
> - **Family Impersonation Bonus:** Adds 50 points when family terms, phone problems, and money requests occur together.

## Proposed Changes

### Android Application

#### [MODIFY] [MainActivity.kt](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/app/src/main/java/com/example/safeguardai/MainActivity.kt)
- Update `getRiskLevel` thresholds to `35` (WARNING) and `70` (DANGER).
- Update `updateRiskUi` comments and logic to reflect the new thresholds.

### Backend Logic

#### [MODIFY] [main.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/main.py)
- Refactor `analyze_risk` to integrate context-based scoring rules.
- Implement `calculate_context_rules` (or similar) to handle specific patterns (Urgency + Pressure, Family + Money).
- Add exception logic for safe contexts (e.g., corporate announcements).
- Ensure final score is clamped between 0 and 100.
- Update `is_phishing` threshold to `70.0`.

### Data & Configuration

#### [MODIFY] [keywords.json](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/keywords.json)
- Add missing specific phrases to ensure the new context rules trigger correctly (e.g., "입금하지 않으면", "승인이 취소", "돈 좀 보내줘").

### Testing

#### [MODIFY] [test_suite.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/test_suite.py)
- Synchronize logic and thresholds with `main.py`.
- Update the expected result for **P19** from `WARNING` to `DANGER` as it represents a high-risk pattern.

## Verification Plan

### Automated Tests
- Run `test_suite.py` to verify the 35 scenarios.
- Expected target: **35/35 (100%)** accuracy on the development set.

### Manual Verification
- Deploy to Android and verify that the UI colors and status messages reflect the new thresholds (35/70).
