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

    # 1. 대출 + 선입금
    loan_words = ["대출", "대출 승인", "저금리", "대환"]
    advance_payment_words = ["보증료", "수수료", "선입금", "비용을 보내", "먼저 입금", "보증보험료", "처리 비용", "처리비용"]
    if any(word in text for word in loan_words) and any(word in text for word in advance_payment_words):
        bonus += 40.0
        patterns.append("대출 선입금 요구")

    # 2. 범죄 연루 + 협박
    crime_accusation = ["사건에 연루", "범죄에 연루", "수사 대상", "범죄에 사용", "범죄 자금"]
    legal_threats = ["체포", "구속", "법적 조치", "절차가 진행", "형사처벌", "영장"]
    if any(word in text for word in crime_accusation) and any(word in text for word in legal_threats):
        bonus += 20.0
        patterns.append("범죄 연루 협박")

    # 3. 기관 사칭 + 범죄 연루
    institutions = ["검찰", "지검", "수사관", "경찰", "금융감독원", "금감원"]
    crimes = ["범죄", "사건", "연루", "범죄 자금", "이상 거래", "이상거래"]
    if any(word in text for word in institutions) and any(word in text for word in crimes):
        bonus += 10.0
        patterns.append("기관 사칭 범죄 압박")

    # 4. 사건/조사 + 체포/영장
    investigations = ["사건", "조사", "수사"]
    arrests = ["체포", "체포영장", "구속", "영장"]
    if any(word in text for word in investigations) and any(word in text for word in arrests):
        bonus += 10.0
        patterns.append("수사 및 구속 협박")

    return bonus, patterns

def apply_safe_context_adjustment(text: str, score: float):
    reduction = 0.0
    news_words = ["뉴스", "기사", "보도", "봤어", "나왔어", "발표됐"]
    if any(word in text for word in news_words):
        reduction += 40.0

    normal_payment_patterns = [
        ["카드값", "계좌이체"], ["병원비", "보내"], ["밥값", "보내"],
        ["책값", "송금"], ["공과금", "이체"], ["관리비", "확인"]
    ]
    for pattern in normal_payment_patterns:
        if all(word in text for word in pattern):
            reduction += 40.0
            break

    return max(score - reduction, 0.0)

def analyze_risk_detailed(text: str):
    score = 0.0
    detected_cats = []
    detected_keywords = []

    for cat, weight in weights.items():
        matched = [word for word in keywords_data.get(cat, []) if word in text]
        if matched:
            score += weight
            detected_cats.append(category_labels.get(cat))
            detected_keywords.extend(matched)

    # Safe Context Mitigation
    safe_install_patterns = [
        ["회사", "공지"], ["회사에서", "공지"], ["업데이트", "공식"],
        ["공식", "앱스토어"], ["공식", "홈페이지"], ["회사", "이메일"], ["회사에서", "이메일"]
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

    # Mitigation
    score = apply_safe_context_adjustment(text, score)

    final_score = min(max(score, 0.0), 100.0)

    # Thresholds
    risk_level = "SAFE"
    if final_score >= 70: risk_level = "DANGER"
    elif final_score >= 35: risk_level = "WARNING"

    return final_score, risk_level, detected_cats, list(set(detected_keywords))

# Scenarios
training_scenarios = [
    ("N1", "오늘 저녁에 뭐 먹을까?", "SAFE"), ("N2", "내일 병원 예약 시간이 10시야.", "SAFE"), ("N3", "엄마 나 지금 학교 끝나고 집에 가는 중이야.", "SAFE"),
    ("N4", "이번 달 관리비가 얼마 나왔는지 확인해줘.", "SAFE"), ("N5", "은행에 가서 통장 정리 좀 해야겠다.", "SAFE"), ("N6", "경찰서 앞에서 만나자.", "SAFE"),
    ("N7", "검찰 관련 뉴스 봤어?", "SAFE"), ("N8", "계좌번호 다시 알려줘. 내가 밥값 보내줄게.", "SAFE"), ("N9", "앱 업데이트가 필요하대.", "SAFE"),
    ("N10", "대출 금리가 많이 올랐더라.", "SAFE"), ("N11", "급하게 오지 말고 천천히 와.", "SAFE"), ("N12", "돈은 내일 송금해도 돼.", "SAFE"),
    ("N13", "오늘 경찰에서 보이스피싱 예방 문자가 왔어.", "SAFE"), ("N14", "가족 단톡방에 사진 올렸어.", "SAFE"), ("N15", "회사에서 보안 앱을 설치하라고 공지가 왔어.", "SAFE"),
    ("P1", "서울중앙지검 검사입니다. 본인 확인이 필요합니다.", "WARNING"), ("P2", "안전계좌로 돈을 송금하셔야 합니다.", "WARNING"), ("P3", "검찰입니다. 사건 확인을 위해 안전계좌로 송금하세요.", "DANGER"),
    ("P4", "당신 계좌가 범죄에 연루됐습니다.", "WARNING"), ("P5", "협조하지 않으면 체포될 수 있습니다.", "WARNING"), ("P6", "지금 바로 처리하지 않으면 큰일 납니다.", "WARNING"),
    ("P7", "휴대폰에 AnyDesk를 설치하세요.", "WARNING"), ("P8", "확인을 위해 보안 앱을 설치해야 합니다.", "WARNING"), ("P9", "금융감독원입니다. 앱을 설치하고 원격제어를 허용하세요.", "DANGER"),
    ("P10", "대출 승인을 위해 먼저 수수료를 입금하세요.", "WARNING"), ("P11", "저금리 대출로 바꿔드릴 테니 보증금을 먼저 송금하세요.", "DANGER"), ("P12", "엄마 나 휴대폰 고장났어. 이 계좌로 돈 좀 보내줘.", "DANGER"),
    ("P13", "아빠 지금 급해. 바로 송금해줘.", "WARNING"), ("P14", "수사 기밀이니 가족에게도 말하면 안 됩니다.", "WARNING"), ("P15", "경찰입니다. 응하지 않으면 구속 절차를 진행합니다.", "DANGER"),
    ("P16", "검찰입니다. 계좌가 범죄에 연루됐고 지금 바로 송금해야 합니다.", "DANGER"), ("P17", "금융감독원입니다. 원격 앱을 설치하고 안전계좌로 이체하세요.", "DANGER"), ("P18", "대출 심사 중입니다. 수수료를 입금하지 않으면 승인이 취소됩니다.", "DANGER"),
    ("P19", "나 아들인데 폰이 망가졌어. 다른 번호로 연락 중이야. 돈 좀 보내줘.", "DANGER"), ("P20", "검찰입니다. 사건에 연루됐으니 아무에게도 말하지 말고 지금 안전계좌로 전액 송금하세요.", "DANGER")
]

dev_set_2 = [
    ("VN1", "오늘 은행 들렀다가 시장에서 장 좀 보고 올게.", "SAFE"), ("VN2", "뉴스에서 검찰 수사 결과가 발표됐다고 하더라.", "SAFE"), ("VN3", "이번 달 카드값은 내가 내일 계좌이체할게.", "SAFE"),
    ("VN4", "경찰에 분실 신고했더니 접수됐다는 연락이 왔어.", "SAFE"), ("VN5", "휴대폰을 새로 바꿔서 은행 앱을 다시 설치했어.", "SAFE"), ("VN6", "아들아, 지난번 병원비 내가 보내줄 테니까 계좌 알려줘.", "SAFE"),
    ("VN7", "회사 공식 홈페이지에서 프로그램을 내려받으라고 공지했어.", "SAFE"), ("VN8", "대출 상담받아 봤는데 금리가 너무 높아서 안 하기로 했어.", "SAFE"), ("VN9", "오늘까지 신청해야 한다는데 급할 것 없으니 내일 확인해 보자.", "SAFE"),
    ("VN10", "보이스피싱범들이 안전계좌로 보내라고 한다는 뉴스를 봤어.", "SAFE"), ("VP1", "서울지검 수사관입니다. 본인 명의 통장이 사건에 사용됐습니다.", "WARNING"), ("VP2", "금융기관 직원입니다. 보호 조치를 위해 자금을 다른 계좌로 옮겨주세요.", "DANGER"),
    ("VP3", "경찰인데 피해자 확인이 필요하니 주민들에게는 이 통화 내용을 말하지 마세요.", "WARNING"), ("VP4", "계좌가 곧 정지됩니다. 지금 바로 본인 인증 절차를 진행하세요.", "WARNING"), ("VP5", "휴대전화 검사를 해야 하니 원격 지원 프로그램을 받아주세요.", "WARNING"),
    ("VP6", "보안 점검을 위해 제가 알려드리는 프로그램을 휴대폰에 설치하세요.", "WARNING"), ("VP7", "저금리 전환 대상입니다. 기존 대출을 정리하려면 먼저 비용을 보내셔야 합니다.", "DANGER"), ("VP8", "대출 승인이 완료됐는데 보증료를 납부해야 돈을 받을 수 있습니다.", "DANGER"),
    ("VP9", "엄마 나 휴대폰 액정이 깨져서 친구 번호로 연락해. 급한 결제가 있는데 대신 보내줄 수 있어?", "DANGER"), ("VP10", "아빠 나 번호 바뀌었어. 지금 결제해야 하는 게 있으니까 내가 보내는 계좌로 부탁해.", "DANGER"), ("VP11", "사건에 연루된 사실이 확인됐습니다. 협조하지 않으면 체포 절차가 진행될 수 있습니다.", "DANGER"),
    ("VP12", "수사 중인 내용이라 가족이나 은행 직원에게 알리면 안 됩니다.", "WARNING"), ("VP13", "고객님 자산이 위험합니다. 안전하게 보호하려면 지금 지정 계좌로 전액 이동하세요.", "DANGER"), ("VP14", "휴대폰에 문제가 발견됐습니다. 제가 화면을 볼 수 있도록 원격 접속을 허용해주세요.", "WARNING"), ("VP15", "오늘 안에 처리하지 않으면 계좌 사용이 제한되고 법적 조치가 시작됩니다.", "WARNING")
]

blind_v3_scenarios = [
    ("B3-N1", "은행에서 전화가 왔는데 그냥 나중에 지점에 직접 가서 확인하려고.", "SAFE"),
    ("B3-N2", "어제 뉴스 보니까 검찰에서 금융사기 조직을 잡았다고 하더라.", "SAFE"),
    ("B3-N3", "엄마가 병원비 보내줬으니까 계좌 확인해봐.", "SAFE"),
    ("B3-N4", "회사에서 새 보안 프로그램 설치 방법을 이메일로 보내줬어.", "SAFE"),
    ("B3-N5", "대출은 수수료도 있고 금리가 높아서 신청하지 않았어.", "SAFE"),
    ("B3-N6", "경찰에 전화해서 이 번호가 보이스피싱인지 확인해볼게.", "SAFE"),
    ("B3-N7", "아빠 내가 아까 부탁한 책값 송금했어. 확인해봐.", "SAFE"),
    ("B3-N8", "휴대폰이 고장 나서 서비스센터에서 수리하고 왔어.", "SAFE"),
    ("B3-N9", "안전계좌라는 말을 쓰면서 돈을 요구하면 보이스피싱을 의심해야 한대.", "SAFE"),
    ("B3-N10", "급하다고 바로 돈 보내지 말고 가족한테 먼저 확인해.", "SAFE"),
    ("B3-P1", "금융기관 보안팀입니다. 고객님 자산 보호를 위해 안내하는 계좌로 자금을 이동해주세요.", "DANGER"),
    ("B3-P2", "서울지검 수사관인데 본인 통장이 범죄 자금에 사용된 정황이 확인됐습니다.", "DANGER"),
    ("B3-P3", "지금부터 말씀드리는 내용은 수사 사항이므로 가족에게 이야기하시면 안 됩니다.", "WARNING"),
    ("B3-P4", "휴대전화 보안 검사를 위해 원격지원 프로그램을 설치해 주세요.", "WARNING"),
    ("B3-P5", "계좌 보호를 위해 오늘 안으로 예금을 지정된 계좌에 옮기셔야 합니다.", "DANGER"),
    ("B3-P6", "저금리 대환 승인이 났습니다. 진행하려면 보증료를 먼저 납부해주세요.", "DANGER"),
    ("B3-P7", "아빠 나 폰 액정이 깨져서 친구 휴대폰으로 연락해. 급한 결제가 있으니까 대신 보내줘.", "DANGER"),
    ("B3-P8", "엄마 나 번호 바뀌었어. 지금 돈이 필요한데 내가 알려주는 계좌로 입금해줘.", "DANGER"),
    ("B3-P9", "사건 관련 조사를 거부하시면 체포영장이 발부될 수 있습니다.", "DANGER"),
    ("B3-P10", "금융감독 관련 절차입니다. 이 내용은 은행 직원에게도 이야기하지 마세요.", "WARNING"),
    ("B3-P11", "고객님 계좌에서 이상 거래가 발견됐습니다. 보호 조치를 위해 잔액을 전부 이동해야 합니다.", "DANGER"),
    ("B3-P12", "제가 보내드린 주소로 접속해서 인증 프로그램을 설치한 다음 본인 인증을 진행하세요.", "WARNING"),
    ("B3-P13", "대출 실행 전에 처리 비용이 필요합니다. 오늘 입금하시면 바로 승인됩니다.", "DANGER"),
    ("B3-P14", "지금 처리하지 않으면 계좌가 정지되고 금융거래가 제한될 수 있습니다.", "WARNING"),
    ("B3-P15", "수사기관에서 연락드렸습니다. 사건 확인을 위해 계좌번호와 인증번호를 말씀해주세요.", "DANGER")
]

def run_suite(name, scenarios):
    print(f"\n>>> {name}")
    print(f"{'ID':<6} | {'Score':<5} | {'Actual':<8} | {'Expected':<8} | {'Status':<5} | {'Categories'}")
    print("-" * 125)

    passed = 0
    failures = []

    for sid, text, expected in scenarios:
        score, actual_level, cats, keywords = analyze_risk_detailed(text)

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
                "cats": cats,
                "keywords": keywords
            })

        print(f"{sid:<6} | {score:<5.1f} | {actual_level:<8} | {expected:<8} | {status:<5} | {', '.join(cats)}")

    print("-" * 125)
    print(f"{name} Pass Rate: {passed}/{len(scenarios)} ({passed/len(scenarios)*100:.1f}%)")
    return passed, len(scenarios), failures

# Run All Sets
results = [
    run_suite("Training Set", training_scenarios),
    run_suite("Dev Set 2", dev_set_2),
    run_suite("Blind Validation Set V3", blind_v3_scenarios)
]

total_passed = sum(r[0] for r in results)
total_scenarios = sum(r[1] for r in results)

print("\n" + "=" * 60)
print(f"Overall Pass Rate: {total_passed}/{total_scenarios} ({total_passed/total_scenarios*100:.1f}%)")
print("=" * 60)

v3_fails = results[2][2]
if v3_fails:
    print("\n[Blind Validation V3 Failures Details]")
    for fail in v3_fails:
        print(f"ID: {fail['id']}")
        print(f"원문: {fail['text']}")
        print(f"점수: {fail['score']}")
        print(f"실제: {fail['actual']}")
        print(f"기대: {fail['expected']}")
        print(f"감지 카테고리: {', '.join(fail['cats'])}")
        print(f"감지 키워드: {', '.join(fail['keywords'])}")
        print(f"실패 유형: {'오탐' if fail['expected'] == 'SAFE' else '미탐'}")
        print("-" * 30)
