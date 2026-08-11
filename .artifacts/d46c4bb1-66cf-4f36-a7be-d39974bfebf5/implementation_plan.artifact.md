# Detection Engine Refinement: Context Layers & Pattern Expansion

This plan addresses the limitations identified in the 2nd blind validation (48% pass rate). We will move beyond simple keyword scoring to a multi-layered analysis that includes context suppression, advanced pattern bonuses, and a broader keyword dictionary.

## User Review Required

> [!IMPORTANT]
> **Shift to Multi-Layered Analysis:**
> Instead of just increasing keyword weights, we are adding:
> 1. **Context Suppression Layer:** Reduces risk scores in safe contexts like news reports or personal bills.
> 2. **Behavioral Combination Layer:** Grants bonuses for specific high-risk pairings (e.g., Loan Approval + Advance Fee Request).
> 3. **Linguistic Variant Expansion:** Broadens the dictionary to catch phrases like "Screen is broken" or "Payment on my behalf."

## Proposed Changes

### Backend Logic

#### [MODIFY] [main.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/main.py)
- **Safe Context Adjustment:** Add `apply_safe_context_adjustment()` to mitigate scores when "News", "Report", or specific "Normal Bill" keywords are present.
- **Combination Bonuses:** Add `calculate_combination_bonus()` for pairs like:
    - Loan + Advance Payment (40 points)
    - Crime Accusation + Threat/Arrest (20 points)
- **Family Pattern Expansion:** Update `calculate_context_bonus()` to include variants for phone issues ("Broken screen", "Friend's number") and financial requests ("Payment instead", "Ask for account").
- **Clamping:** Ensure all scores are safely clamped between 0 and 100.

### Data & Configuration

#### [MODIFY] [keywords.json](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/keywords.json)
- **Expand Dictionary:** Add missing phrases identified in VP2-VP15:
    - *Institution:* "Financial institution", "Bank employee".
    - *Money:* "Transfer funds to another account", "Designated account", "Payment fee", "On behalf of payment".
    - *Tech:* "Remote support program", "Allow remote access", "Program I tell you".
    - *Authority:* "Do not tell anyone", "Do not tell bank staff".
    - *Messenger:* "Screen is broken", "Phone is messed up", "Friend's number", "Number changed".

### Testing

#### [MODIFY] [test_suite.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/test_suite.py)
- Synchronize logic with the new backend layers.
- Retain current 60 scenarios (35 Training + 25 Blind) as a "Development Set" for regression testing.
- **Note:** A 3rd blind validation set will be required after these changes to verify generalization.

## Verification Plan

### Automated Tests
- Run `test_suite.py`.
- **Target Accuracy on Development Set (60 scenarios):**
    - Normal (Training 15 + Blind 10): 24/25 SAFE (96%)
    - Phishing (Training 20 + Blind 15): 30/35 WARNING+ (85%)
    - Total: >90%

### Manual Verification
- Specifically verify **VN10** (News about phishing) and **VP9** (Broken screen impersonation) to confirm the new layers work as intended.
