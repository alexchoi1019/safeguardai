# Voice Phishing Detection Test Suite & Weight Tuning Plan

This plan aims to implement the 35 test scenarios provided by the user, update the risk analysis weights, and refine the testing tool to provide detailed results in the requested format.

## User Review Required

> [!IMPORTANT]
> The weights will be updated to the recommended values. Please verify if these values align with your expectations for the MVP.
>
> **Recommended Weights:**
> - Money Words: 40.0
> - Technology Words: 40.0
> - Loan Scam Words: 35.0
> - Institution / Crime / Threat: 25.0
> - Authority / Messenger: 20.0
> - Urgency: 10.0

## Proposed Changes

### Backend Logic

#### [MODIFY] [main.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/main.py)
- Update weights to match the recommended tuning criteria.
- Ensure the `analyze_risk` function returns sufficient data for the detailed test report.

#### [MODIFY] [test_suite.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/test_suite.py)
- Update weights to match `main.py`.
- Refine the output format to match the user's requested "Recording Table" (ID, Actual Sentence, STT Result, Immediate Score, Cumulative Score, Final Stage, Category, Expected, Success).
- Add the 15 Normal + 20 Phishing scenarios (already partially present, but need full synchronization).

### Data & Configuration

#### [MODIFY] [keywords.json](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/keywords.json)
- Review and potentially add missing keywords from the new scenarios (e.g., "AnyDesk", "AnyDesk" is already there, but checking others like "밥값", "관리비").

## Verification Plan

### Automated Tests
- Run the updated `test_suite.py` to generate the full report for 35 scenarios.
- Verify the pass rate against the user's target:
    - Normal: 13/15 SAFE
    - Phishing: 17/20 WARNING+
    - High-risk: Most DANGER

### Manual Verification
- Review the generated table to identify specific failures (STT vs. Keywords vs. Weights).
