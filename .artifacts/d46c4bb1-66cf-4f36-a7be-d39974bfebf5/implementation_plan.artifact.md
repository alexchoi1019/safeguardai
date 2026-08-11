# SafeguardAI: Cumulative Risk Sync & New Validation Set

This plan aims to synchronize the "Context Bonus" logic with the Android application's cumulative risk mechanism and introduce a new set of 25 scenarios for unbiased validation.

## User Review Required

> [!IMPORTANT]
> - **Risk Factor Synchronization:** "Context Bonuses" (e.g., Family Impersonation, Urgency Pressure) will now be included in the `risk_factors` list returned by the backend. This ensures the Android app's cumulative risk calculation correctly accounts for these bonuses across multiple segments.
> - **New Validation Set:** 25 entirely new scenarios (10 Normal, 15 Phishing) will be generated to test the generalization of the current detection logic.

## Proposed Changes

### Backend Logic

#### [MODIFY] [main.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/main.py)
- Refactor `calculate_context_bonus` to return `context_factors` (list of dicts with category, label, and score).
- Update `analyze_risk` to extend the `risk_factors` list with these new context-based factors.
- Ensure the Android app receives these factors in the JSON response.

#### [MODIFY] [test_suite.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/test_suite.py)
- Sync the `analyze_risk_detailed` logic with the updated `main.py`.
- Add a new "Validation Set" containing 25 new scenarios:
    - **10 Normal:** Daily life, official banking queries, real security alerts, etc.
    - **15 Phishing:** Variations of impersonation (government, logistics, family), investment scams, and remote access lures.

## Verification Plan

### Automated Tests
- Run the updated `test_suite.py` against both the **Training Set (35 scenarios)** and the **Validation Set (25 scenarios)**.
- **Success Criteria:**
    - Training Set: Maintain 100% accuracy.
    - Validation Set: Achieve >80% accuracy without further code tweaks.

### Manual Verification
- Verify the backend JSON response via a tool like Postman or by logging to ensure `risk_factors` now contains items like `family_impersonation_pattern`.
