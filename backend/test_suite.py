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

def calculate_context_bonus(text: str):
    bonus = 0.0
    detected_patterns = []

    # 1. 긴급 압박
    urgency_trigger_words = keywords_data.get("urgency_words", [])
    pressure_words = ["큰일", "취소", "정지", "불이익", "문제가 생", "처리하지 않으면", "지금 바로"]
    if any(word in text for word in urgency_trigger_words) and any(word in text for word in pressure_words):
        bonus += 20.0
        detected_patterns.append("긴급 행동 압박")

    # 2. 지인 사칭 고위험 패턴
    family_words = ["엄마", "아빠", "아들", "딸", "형", "누나", "언니", "오빠"]
    phone_problem_words = ["휴대폰 고장", "폰 고장", "폰이 망가", "휴대폰이 망가", "다른 번호", "번호가 바뀌"]
    money_request_words = ["돈 좀 보내", "돈 보내", "송금해", "입금해", "계좌로", "보내줘"]
    if any(word in text for word in family_words) and \
       any(word in text for word in phone_problem_words) and \
       any(word in text for word in money_request_words):
        bonus += 50.0
        detected_patterns.append("가족 사칭 송금 요구")

    return bonus, detected_patterns

def analyze_risk_detailed(text: str):
    score = 0.0
    detected_cats = []

    for cat, weight in weights.items():
        if any(word in text for word in keywords_data.get(cat, [])):
            score += weight
            detected_cats.append(category_labels.get(cat))

    # --- Context Rules (Sync with main.py) ---

    # N15 Safe Context Mitigation
    safe_context_patterns = [["회사", "공지"], ["회사에서", "공지"], ["업데이트", "공식"], ["공식", "앱스토어"]]
    safe_tech = any(all(word in text for word in pattern) for pattern in safe_context_patterns)
    if safe_tech and "앱/원격제어" in detected_cats:
        score -= weights["technology_words"]
        detected_cats.remove("앱/원격제어")

    # Bonus Rules
    bonus, patterns = calculate_context_bonus(text)
    score += bonus
    detected_cats.extend(patterns)

    final_score = min(max(score, 0.0), 100.0)

    # Thresholds
    risk_level = "SAFE"
    if final_score >= 70: risk_level = "DANGER"
    elif final_score >= 35: risk_level = "WARNING"

    return final_score, risk_level, detected_cats

# 1. Training Set (35 Scenarios)
training_scenarios = [
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
    ("P19", "나 아들인데 폰이 망가졌어. 다른 번호로 연락 중이야. 돈 좀 보내줘.", "DANGER"),
    ("P20", "검찰입니다. 사건에 연루됐으니 아무에게도 말하지 말고 지금 안전계좌로 전액 송금하세요.", "DANGER")
]

# 2. Validation Set (25 Scenarios)
validation_scenarios = [
    # Normal (10)
    ("V_N1", "주말에 캠핑 가기로 한 거 잊지 않았지?", "SAFE"),
    ("V_N2", "택배가 문 앞에 도착했다고 문자 왔네.", "SAFE"),
    ("V_N3", "이번 연휴에 고향 내려갈 계획이야?", "SAFE"),
    ("V_N4", "카드 결제일이 모레인데 잔액이 충분한가?", "SAFE"),
    ("V_N5", "스타벅스 쿠폰 선물받았는데 같이 갈래?", "SAFE"),
    ("V_N6", "내일 오전 회의 자료 미리 공유해줄게.", "SAFE"),
    ("V_N7", "동네 새로 생긴 빵집 빵이 정말 맛있더라.", "SAFE"),
    ("V_N8", "이번 주말에 비 소식이 있으니 우산 챙겨.", "SAFE"),
    ("V_N9", "은행 앱에서 정기 점검 공지가 떴어.", "SAFE"),
    ("V_N10", "넷플릭스 구독료가 다음 주에 결제될 예정이야.", "SAFE"),
    # Phishing (15)
    ("V_P1", "우체국입니다. 주소 불명으로 택배가 반송되었으니 확인 앱을 설치하세요.", "WARNING"),
    ("V_P2", "국민연금공단입니다. 환급금이 발생했으니 링크를 클릭해 본인인증 하세요.", "WARNING"),
    ("V_P3", "본인 명의로 핸드폰이 개통되었습니다. 확인을 위해 원격 지원을 받으세요.", "DANGER"),
    ("V_P4", "카드 부정 결제가 감지되었습니다. 보안을 위해 안전계좌로 자금을 옮기세요.", "DANGER"),
    ("V_P5", "서울지방경찰청입니다. 중고거래 사기에 연루되어 조사가 필요합니다.", "WARNING"),
    ("V_P6", "소상공인 지원금 대상입니다. 지금 바로 입금해야 혜택을 받습니다.", "WARNING"),
    ("V_P7", "딸인데 폰 액정 깨졌어. 수리비 급하니까 이 번호로 돈 보내줘.", "DANGER"),
    ("V_P8", "신한은행입니다. 저금리 정부지원 대출 한도가 발생했습니다. 수수료 입금하세요.", "DANGER"),
    ("V_P9", "검찰청입니다. 자금 출처 확인을 위해 전액 현금으로 인출해 보관하세요.", "DANGER"),
    ("V_P10", "법원입니다. 민사 소송이 접수되었으니 전자 소송 앱을 설치하세요.", "WARNING"),
    ("V_P11", "휴대폰 소액결제 50만원 완료. 본인이 아니면 상담원 연결 후 보안앱 설치.", "DANGER"),
    ("V_P12", "가족에게 알리면 수사 기밀 유설로 처벌받습니다. 절대 말하지 마세요.", "WARNING"),
    ("V_P13", "금융감독원입니다. 불법 자금 세탁 혐의로 계좌가 동결될 예정입니다.", "DANGER"),
    ("V_P14", "정부 보조금 신청 기간이 오늘까지입니다. 즉시 신청하지 않으면 취소됩니다.", "WARNING"),
    ("V_P15", "나 아빠인데 폰 잃어버렸어. 급하게 돈 쓸 데가 있으니 송금 부탁해.", "DANGER")
]

def run_suite(name, scenarios):
    print(f"\n>>> Running {name} ({len(scenarios)} scenarios)")
    print(f"{'ID':<6} | {'Score':<5} | {'Actual':<8} | {'Expected':<8} | {'Success':<7} | {'Categories'}")
    print("-" * 110)

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

        print(f"{sid:<6} | {score:<5.1f} | {actual_level:<8} | {expected:<8} | {'PASS' if is_success else 'FAIL':<7} | {', '.join(cats)}")

    print("-" * 110)
    print(f"{name} Pass Rate: {passed}/{len(scenarios)} ({passed/len(scenarios)*100:.1f}%)")
    return passed, len(scenarios)

# 3. Run Both
t_passed, t_total = run_suite("Training Set", training_scenarios)
v_passed, v_total = run_suite("Validation Set", validation_scenarios)

print("\n" + "=" * 40)
print(f"Overall Pass Rate: {t_passed + v_passed}/{t_total + v_total} ({(t_passed + v_passed)/(t_total + v_total)*100:.1f}%)")
print("=" * 40)
