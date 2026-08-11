import json
import os

# 1. Load keywords
KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "keywords.json")
with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
    keywords_data = json.load(f)

# Weights (Day 13 Final Tuning)
weights = {
    "institution": 30.0,
    "crime_words": 35.0,
    "money_words": 40.0,
    "technology_words": 45.0,
    "urgency_words": 15.0,
    "threat_words": 30.0,
    "authority_words": 25.0,
    "loan_scam_words": 35.0,
    "messenger_words": 25.0
}

category_labels = {
    "institution": "기관 사칭",
    "crime_words": "범죄 관련",
    "money_words": "금전 요구",
    "technology_words": "앱/원격제어",
    "urgency_words": "긴급성",
    "threat_words": "협박/위협",
    "authority_words": "권위/비밀",
    "loan_scam_words": "대출 사기",
    "messenger_words": "지인/메신저"
}

def analyze_risk_detailed(text: str):
    score = 0.0
    detected_cats = []

    for cat, weight in weights.items():
        if any(word in text for word in keywords_data.get(cat, [])):
            score += weight
            detected_cats.append(category_labels.get(cat))

    final_score = min(score, 100.0)

    # Thresholds
    risk_level = "SAFE"
    if final_score >= 70: risk_level = "DANGER"
    elif final_score >= 35: risk_level = "WARNING"

    return final_score, risk_level, detected_cats

# 2. 35 Scenarios
scenarios = [
    ("N1", "오늘 저녁에 뭐 먹을까?", "SAFE"),
    ("N2", "내일 병원 예약 시간이 10시야.", "SAFE"),
    ("N3", "엄마 나 지금 학교 끝나고 집에 가는 중이야.", "SAFE"),
    ("N4", "이번 달 관리비가 얼마 나왔는지 확인해줘.", "SAFE"),
    ("N5", "은행에 가서 통장 정리 좀 해야겠다.", "SAFE"),
    ("N6", "경찰서 앞에서 만나자.", "SAFE"),
    ("N7", "검찰 관련 뉴스 봤어?", "SAFE"),
    ("N8", "계좌번호 다시 알려줘. 내가 밥값 보내줄게.", "SAFE"),
    ("N9", "앱 업데이트가 필요하대.", "SAFE"),
    ("N10", "대출 금리가 많이 올랐더라.", "SAFE"),
    ("N11", "급하게 오지 말고 천천히 와.", "SAFE"),
    ("N12", "돈은 내일 송금해도 돼.", "SAFE"),
    ("N13", "오늘 경찰에서 보이스피싱 예방 문자가 왔어.", "SAFE"),
    ("N14", "가족 단톡방에 사진 올렸어.", "SAFE"),
    ("N15", "회사에서 보안 앱을 설치하라고 공지가 왔어.", "SAFE"),
    ("P1", "서울중앙지검 검사입니다. 본인 확인이 필요합니다.", "WARNING"),
    ("P2", "안전계좌로 돈을 송금하셔야 합니다.", "WARNING"),
    ("P3", "검찰입니다. 사건 확인을 위해 안전계좌로 송금하세요.", "DANGER"),
    ("P4", "당신 계좌가 범죄에 연루됐습니다.", "WARNING"),
    ("P5", "협조하지 않으면 체포될 수 있습니다.", "WARNING"),
    ("P6", "지금 바로 처리하지 않으면 큰일 납니다.", "WARNING"),
    ("P7", "휴대폰에 AnyDesk를 설치하세요.", "WARNING"),
    ("P8", "확인을 위해 보안 앱을 설치해야 합니다.", "WARNING"),
    ("P9", "금융감독원입니다. 앱을 설치하고 원격제어를 허용하세요.", "DANGER"),
    ("P10", "대출 승인을 위해 먼저 수수료를 입금하세요.", "WARNING"),
    ("P11", "저금리 대출로 바꿔드릴 테니 보증금을 먼저 송금하세요.", "DANGER"),
    ("P12", "엄마 나 휴대폰 고장났어. 이 계좌로 돈 좀 보내줘.", "DANGER"),
    ("P13", "아빠 지금 급해. 바로 송금해줘.", "WARNING"),
    ("P14", "수사 기밀이니 가족에게도 말하면 안 됩니다.", "WARNING"),
    ("P15", "경찰입니다. 응하지 않으면 구속 절차를 진행합니다.", "DANGER"),
    ("P16", "검찰입니다. 계좌가 범죄에 연루됐고 지금 바로 송금해야 합니다.", "DANGER"),
    ("P17", "금융감독원입니다. 원격 앱을 설치하고 안전계좌로 이체하세요.", "DANGER"),
    ("P18", "대출 심사 중입니다. 수수료를 입금하지 않으면 승인이 취소됩니다.", "DANGER"),
    ("P19", "나 아들인데 폰이 망가졌어. 다른 번호로 연락 중이야. 돈 좀 보내줘.", "WARNING"),
    ("P20", "검찰입니다. 사건에 연루됐으니 아무에게도 말하지 말고 지금 안전계좌로 전액 송금하세요.", "DANGER")
]

# 3. Execution
print(f"{'ID':<4} | {'Score':<5} | {'Actual':<8} | {'Expected':<8} | {'Success':<7} | {'Categories'}")
print("-" * 100)

passed = 0
for sid, text, expected in scenarios:
    score, actual_level, cats = analyze_risk_detailed(text)

    is_success = False
    if expected == "SAFE":
        is_success = (actual_level == "SAFE")
    else:
        level_map = {"SAFE": 0, "WARNING": 1, "DANGER": 2}
        is_success = level_map.get(actual_level, 0) >= level_map.get(expected, 0)

    if is_success: passed += 1

    print(f"{sid:<4} | {score:<5.1f} | {actual_level:<8} | {expected:<8} | {'PASS' if is_success else 'FAIL':<7} | {', '.join(cats)}")

print("-" * 100)
print(f"Total Pass Rate: {passed}/{len(scenarios)} ({passed/len(scenarios)*100:.1f}%)")
