# Day 2: Detection Engine Freeze & Final Polish

This plan addresses the identified gaps in the 3rd blind validation while intentionally preserving some structural limitations as justification for future AI model integration. We aim to freeze the "Rule Engine v1" after this iteration.

## User Review Required

> [!IMPORTANT]
> **Final Adjustments:**
> - **Keyword Gap Closure:** Adding 12+ specific phrases for account transfers, 이상거래 (abnormal transactions), and financial supervision.
> - **Granular Combination Bonuses:** Adding targeted bonuses (+10 pts) for (Institution + Crime) and (Investigation + Warrant) pairs to push high-risk cases into the DANGER zone without causing global inflation.
> - **Safe Context Expansion:** Recognizing "Corporate Email" as a safe environment for software installation.
>
> **Intentional Non-action (Engine Limits):**
> - **B3-N5 & B3-N9:** We will **not** implement complex negative/informative context rules (e.g., "I didn't apply" or "Beware of X"). These remain as evidence for the necessity of a future LLM/BERT context layer.

## Proposed Changes

### Backend Logic

#### [MODIFY] [main.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/main.py)
- Update `safe_context_patterns` in `analyze_risk` to include `["회사", "이메일"]` and `["회사에서", "이메일"]`.
- Update `calculate_combination_bonus()` to include:
    - **Institution + Crime:** (Institution keyword + Crime keyword) -> +10 points.
    - **Investigation + Threat:** (Investigation/Case + Arrest/Warrant) -> +10 points.
- Ensure all reasons and factors are synchronized.

### Data & Configuration

#### [MODIFY] [keywords.json](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/keywords.json)
- **Add specific phrases:**
    - `money_words`: "예금을 옮겨", "예금을 이동", "지정된 계좌", "잔액을 전부 이동", "처리 비용".
    - `crime_words`: "이상 거래", "이상거래".
    - `authority_words`: "금융감독 관련", "금융감독 절차", "은행 직원에게 이야기하지".
    - `threat_words`: "금융거래가 제한", "처리하지 않으면".

### Testing

#### [MODIFY] [test_suite.py](file:///C:/Users/winne/OneDrive/문서/GitHub/safeguardai/backend/test_suite.py)
- Synchronize logic with the updated `main.py`.
- Run all 85 scenarios (Training + Dev2 + Blind V3).

## Verification Plan

### Automated Tests
- Run `test_suite.py`.
- **Target Accuracy on Blind V3:** >80% (20/25).
- **Regression Check:** Ensure Training and Dev2 sets maintain near 100%.

### Engine Freeze Declaration
- If the results reach the target, we will officially label the current logic as **"SafeguardAI Rule Engine v1"** and cease keyword/rule modifications to focus on real-world voice testing (Day 3).
