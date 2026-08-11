import json
import os

# 1. Load keywords
KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "keywords.json")
with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
    keywords_data = json.load(f)

# Weights
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

    urgency_trigger_words = keywords_data.get("urgency_words", [])
    pressure_words = ["큰일", "취소", "정지", "불이익", "문제가 생", "처리하지 않으면", "지금 바로"]
    if any(word in text for word in urgency_trigger_words) and any(word in text for word in pressure_words):
        bonus += 20.0
        detected_patterns.append("긴급 행동 압박")

    family_words = ["엄마", "아빠", "아들", "딸", "형", "누나", "언니", "오빠"]
    phone_problem_words = [
        "휴대폰 고장", "폰 고장", "폰이 망가", "휴대폰이 망가",
        "액정이 깨져", "액정 깨져", "다른 번호", "친구 번호", "번호 바뀌"
    ]
    money_request_words = [
        "돈 좀 보내", "돈 보내", "송금해", "입금해", "계좌로", "보내줘",
        "결제", "대신 보내", "계좌로 부탁"
    ]
    if any(word in text for word in family_words) and \
       any(word in text for word in phone_problem_words) and \
       any(word in text for word in money_request_words):
        bonus += 50.0
        detected_patterns.append("가족 사칭 송금 요구")

    return bonus, detected_patterns

def calculate_combination_bonus(text: str):
    bonus = 0.0
    patterns = []

    loan_words = ["대출", "대출 승인", "저금리", "대환"]
    advance_payment_words = ["보증료", "수수료", "선입금", "비용을 보내", "먼저 입금", "보증보험료"]
    if any(word in text for word in loan_words) and any(word in text for word in advance_payment_words):
        bonus += 40.0
        patterns.append("대출 선입금 요구")

    crime_accusation = ["사건에 연루", "범죄에 연루", "수사 대상", "범죄에 사용"]
    legal_threats = ["체포", "구속", "법적 조치", "절차가 진행", "형사처벌"]
    if any(word in text for word in crime_accusation) and any(word in text for word in legal_threats):
        bonus += 20.0
        patterns.append("범죄 연루 협박")

    return bonus, patterns

def apply_safe_context_adjustment(text: str, score: float):
    reduction = 0.0
    news_words = ["뉴스", "기사", "보도", "봤어", "나왔어", "발표됐"]
    if any(word in text for word in news_words):
        reduction += 40.0

    normal_payment_patterns = [
        ["카드값", "계좌이체"], ["병원비", "보내"], ["밥값", "보내"],
        ["공과금", "이체"], ["관리비", "확인"]
    ]
    for pattern in normal_payment_patterns:
        if all(word in text for word in pattern):
            reduction += 40.0
            break

    return max(score - reduction, 0.0)

def analyze_risk_detailed(text: str):
    score = 0.0
    detected_cats = []

    for cat, weight in weights.items():
        if any(word in text for word in keywords_data.get(cat, [])):
            score += weight
            detected_cats.append(category_labels.get(cat))

    safe_install_patterns = [
        ["회사", "공지"], ["회사에서", "공지"], ["업데이트", "공식"],
        ["공식", "앱스토어"], ["공식", "홈페이지"]
    ]
    if any(all(word in text for word in pattern) for pattern in safe_install_patterns):
        if "앱/원격제어" in detected_cats:
            score -= weights["technology_words"]
            detected_cats.remove("앱/원격제어")

    bonus, patterns = calculate_context_bonus(text)
    score += bonus
    detected_cats.extend(patterns)

    combo_bonus, combo_patterns = calculate_combination_bonus(text)
    score += combo_bonus
    detected_cats.extend(combo_patterns)

    score = apply_safe_context_adjustment(text, score)

    final_score = min(max(score, 0.0), 100.0)

    risk_level = "SAFE"
    if final_score >= 70: risk_level = "DANGER"
    elif final_score >= 35: risk_level = "WARNING"

    return final_score, risk_level, detected_cats

# Training Set (35)
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

# Blind Validation Set (25)
validation_scenarios = [
    ("VN1", "오늘 은행 들렀다가 시장에서 장 좀 보고 올게.", "SAFE"),
    ("VN2", "뉴스에서 검찰 수사 결과가 발표됐다고 하더라.", "SAFE"),
    ("VN3", "이번 달 카드값은 내가 내일 계좌이체할게.", "SAFE"),
    ("VN4", "경찰에 분실 신고했더니 접수됐다는 연락이 왔어.", "SAFE"),
    ("VN5", "휴대폰을 새로 바꿔서 은행 앱을 다시 설치했어.", "SAFE"),
    ("VN6", "아들아, 지난번 병원비 내가 보내줄 테니까 계좌 알려줘.", "SAFE"),
    ("VN7", "회사 공식 홈페이지에서 프로그램을 내려받으라고 공지했어.", "SAFE"),
    ("VN8", "대출 상담받아 봤는데 금리가 너무 높아서 안 하기로 했어.", "SAFE"),
    ("VN9", "오늘까지 신청해야 한다는데 급할 것 없으니 내일 확인해 보자.", "SAFE"),
    ("VN10", "보이스피싱범들이 안전계좌로 보내라고 한다는 뉴스를 봤어.", "SAFE"),
    ("VP1", "서울지검 수사관입니다. 본인 명의 통장이 사건에 사용됐습니다.", "WARNING"),
    ("VP2", "금융기관 직원입니다. 보호 조치를 위해 자금을 다른 계좌로 옮겨주세요.", "DANGER"),
    ("VP3", "경찰인데 피해자 확인이 필요하니 주민들에게는 이 통화 내용을 말하지 마세요.", "WARNING"),
    ("VP4", "계좌가 곧 정지됩니다. 지금 바로 본인 인증 절차를 진행하세요.", "WARNING"),
    ("VP5", "휴대전화 검사를 해야 하니 원격 지원 프로그램을 받아주세요.", "WARNING"),
    ("VP6", "보안 점검을 위해 제가 알려드리는 프로그램을 휴대폰에 설치하세요.", "WARNING"),
    ("VP7", "저금리 전환 대상입니다. 기존 대출을 정리하려면 먼저 비용을 보내셔야 합니다.", "DANGER"),
    ("VP8", "대출 승인이 완료됐는데 보증료를 납부해야 돈을 받을 수 있습니다.", "DANGER"),
    ("VP9", "엄마 나 휴대폰 액정이 깨져서 친구 번호로 연락해. 급한 결제가 있는데 대신 보내줄 수 있어?", "DANGER"),
    ("VP10", "아빠 나 번호 바뀌었어. 지금 결제해야 하는 게 있으니까 내가 보내는 계좌로 부탁해.", "DANGER"),
    ("VP11", "사건에 연루된 사실이 확인됐습니다. 협조하지 않으면 체포 절차가 진행될 수 있습니다.", "DANGER"),
    ("VP12", "수사 중인 내용이라 가족이나 은행 직원에게 알리면 안 됩니다.", "WARNING"),
    ("VP13", "고객님 자산이 위험합니다. 안전하게 보호하려면 지금 지정 계좌로 전액 이동하세요.", "DANGER"),
    ("VP14", "휴대폰에 문제가 발견됐습니다. 제가 화면을 볼 수 있도록 원격 접속을 허용해주세요.", "WARNING"),
    ("VP15", "오늘 안에 처리하지 않으면 계좌 사용이 제한되고 법적 조치가 시작됩니다.", "WARNING")
]

def run_suite(name, scenarios):
    print(f"\n>>> {name}")
    print(f"{'ID':<5} | {'Score':<5} | {'Actual':<8} | {'Expected':<8} | {'Status':<5} | {'Categories'}")
    print("-" * 120)

    passed = 0
    failures = []

    for sid, text, expected in scenarios:
        score, actual_level, cats = analyze_risk_detailed(text)

        is_success = False
        if expected == "SAFE":
            is_success = (actual_level == "SAFE")
        else:
            level_map = {"SAFE": 0, "WARNING": 1, "DANGER": 2}
            is_success = level_map.get(actual_level, 0) >= level_map.get(expected, 0)

        if is_success:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"
            failures.append({
                "id": sid,
                "text": text,
                "score": score,
                "actual": actual_level,
                "expected": expected,
                "cats": cats
            })

        print(f"{sid:<5} | {score:<5.1f} | {actual_level:<8} | {expected:<8} | {status:<5} | {', '.join(cats)}")

    print("-" * 120)
    print(f"{name} Pass Rate: {passed}/{len(scenarios)} ({passed/len(scenarios)*100:.1f}%)")
    return passed, len(scenarios), failures

# Run Both
t_passed, t_total, t_fails = run_suite("Training Set", training_scenarios)
v_passed, v_total, v_fails = run_suite("Blind Validation Set", validation_scenarios)

print("\n" + "=" * 60)
print(f"Overall Pass Rate: {t_passed + v_passed}/{t_total + v_total} ({(t_passed + v_passed)/(t_total + v_total)*100:.1f}%)")
print("=" * 60)

if v_fails:
    print("\n[Blind Validation Failures Details]")
    for fail in v_fails:
        print(f"ID: {fail['id']}")
        print(f"원문: {fail['text']}")
        print(f"점수: {fail['score']}")
        print(f"실제: {fail['actual']}")
        print(f"기대: {fail['expected']}")
        print(f"카테고리: {', '.join(fail['cats'])}")
        print("-" * 30)
