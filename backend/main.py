import os
# Hugging Face 심볼릭 링크 오류 방지 (윈도우 권한 문제 해결)
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

import json
import shutil
import time
import imageio_ffmpeg
from faster_whisper import WhisperModel
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

# 1. ffmpeg 경로 동적 등록
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)
ffmpeg_alias = os.path.join(ffmpeg_dir, "ffmpeg.exe")

if not os.path.exists(ffmpeg_alias):
    shutil.copy2(ffmpeg_exe, ffmpeg_alias)

os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# 2. FastAPI 앱 및 Faster-Whisper 모델 초기화
app = FastAPI(title="SafeguardAI Phishing Detection Server")

# CPU 환경 최적화를 위해 compute_type="int8" 사용
print("🎙️ Faster-Whisper 모델(small)을 로딩 중입니다...")
stt_model = WhisperModel("small", device="cpu", compute_type="int8")
print("✅ Faster-Whisper 모델 로딩 완료!")

# 3. 키워드 데이터셋 로드
KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "keywords.json")
keywords_data = {}
if os.path.exists(KEYWORDS_PATH):
    with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
        keywords_data = json.load(f)

# 4. 고도화된 위험도 분석 함수
def calculate_context_bonus(text: str, keywords_data: dict):
    bonus = 0.0
    reasons = []
    actions = []
    context_factors = []

    # 1. 긴급 압박 (긴급성 + 불이익 표현)
    urgency_trigger_words = keywords_data.get("urgency_words", [])
    pressure_words = ["큰일", "취소", "정지", "불이익", "문제가 생", "처리하지 않으면", "지금 바로"]

    has_urgency = any(word in text for word in urgency_trigger_words)
    has_pressure = any(word in text for word in pressure_words)

    if has_urgency and has_pressure:
        bonus += 20.0
        label = "긴급 행동 압박"
        reasons.append("즉시 행동하지 않으면 문제가 생긴다고 압박하는 표현이 감지되었습니다.")
        actions.append("상대방의 독촉에 따르지 말고 전화를 끊은 뒤 내용을 다시 확인하세요.")
        context_factors.append({
            "category": "urgent_pressure_pattern",
            "label": label,
            "score": 20.0
        })

    # 2. 지인 사칭 고위험 패턴 (가족 + 휴대폰 문제 + 송금 요구)
    family_words = ["엄마", "아빠", "아들", "딸", "형", "누나", "언니", "오빠"]
    phone_problem_words = [
        "휴대폰 고장", "폰 고장", "폰이 망가", "휴대폰이 망가",
        "액정이 깨져", "액정 깨져", "다른 번호", "친구 번호", "번호 바뀌"
    ]
    money_request_words = [
        "돈 좀 보내", "돈 보내", "송금해", "입금해", "계좌로", "보내줘",
        "결제", "대신 보내", "계좌로 부탁"
    ]

    has_family = any(word in text for word in family_words)
    has_phone_problem = any(word in text for word in phone_problem_words)
    has_money_request = any(word in text for word in money_request_words)

    if has_family and has_phone_problem and has_money_request:
        bonus += 50.0
        label = "가족 사칭 송금 요구 패턴"
        reasons.append("가족을 사칭하면서 휴대폰 문제를 이유로 송금을 요구하는 전형적인 지인 사칭 패턴이 감지되었습니다.")
        actions.append("돈을 보내지 말고 기존에 알고 있던 가족의 전화번호로 직접 연락해 본인인지 확인하세요.")
        context_factors.append({
            "category": "family_impersonation_pattern",
            "label": label,
            "score": 50.0
        })

    return bonus, reasons, actions, context_factors

def calculate_combination_bonus(text: str):
    bonus = 0.0
    reasons = []
    actions = []
    factors = []

    # 1. 대출 + 선입금 요구 (대출 사기)
    loan_words = ["대출", "대출 승인", "저금리", "대환"]
    advance_payment_words = ["보증료", "수수료", "선입금", "비용을 보내", "먼저 입금", "보증보험료", "처리 비용", "처리비용"]

    if any(word in text for word in loan_words) and any(word in text for word in advance_payment_words):
        bonus += 40.0
        label = "대출 선입금 요구 패턴"
        reasons.append("대출을 조건으로 먼저 돈(수수료, 보증료 등)을 요구하는 전형적인 대출 사기 패턴이 감지되었습니다.")
        actions.append("대출 실행 전 수수료나 보증료를 송금하지 마세요. 이는 명백한 불법 사기입니다.")
        factors.append({
            "category": "loan_advance_payment_pattern",
            "label": label,
            "score": 40.0
        })

    # 2. 범죄 연루 + 체포/법적 위협
    crime_accusation = ["사건에 연루", "범죄에 연루", "수사 대상", "범죄에 사용", "범죄 자금"]
    legal_threats = ["체포", "구속", "법적 조치", "절차가 진행", "형사처벌", "영장"]

    if any(word in text for word in crime_accusation) and any(word in text for word in legal_threats):
        bonus += 20.0
        label = "범죄 연루 협박 패턴"
        reasons.append("범죄 연루를 주장하면서 체포나 법적 조치를 언급하며 심리적으로 압박하는 패턴이 감지되었습니다.")
        factors.append({
            "category": "crime_threat_pattern",
            "label": label,
            "score": 20.0
        })

    # 3. 기관 사칭 + 범죄 연루 (P2, P9 보완)
    institutions = ["검찰", "지검", "수사관", "경찰", "금융감독원", "금감원"]
    crimes = ["범죄", "사건", "연루", "범죄 자금", "이상 거래", "이상거래"]

    if any(word in text for word in institutions) and any(word in text for word in crimes):
        bonus += 10.0
        label = "기관 사칭 범죄 압박"
        reasons.append("정부 기관을 사칭하며 범죄 연루 사실을 강조하고 있습니다.")
        factors.append({
            "category": "inst_crime_pattern",
            "label": label,
            "score": 10.0
        })

    # 4. 사건/조사 + 체포/영장 (P9 보완)
    investigations = ["사건", "조사", "수사"]
    arrests = ["체포", "체포영장", "구속", "영장"]

    if any(word in text for word in investigations) and any(word in text for word in arrests):
        bonus += 10.0
        label = "수사 및 구속 협박"
        reasons.append("사건 수사를 이유로 구속이나 영장 발부를 언급하며 협박하고 있습니다.")
        factors.append({
            "category": "inv_arrest_pattern",
            "label": label,
            "score": 10.0
        })

    return bonus, reasons, actions, factors

def apply_safe_context_adjustment(text: str, score: float):
    reduction = 0.0

    # 1. 뉴스/보도 문맥 (VN2, VN10 대응)
    news_words = ["뉴스", "기사", "보도", "봤어", "나왔어", "발표됐"]
    if any(word in text for word in news_words):
        reduction += 40.0

    # 2. 정상적인 개인 송금/납부 문맥 (VN3, VN6, B3-N7 대응)
    normal_payment_patterns = [
        ["카드값", "계좌이체"],
        ["병원비", "보내"],
        ["밥값", "보내"],
        ["책값", "송금"],
        ["공과금", "이체"],
        ["관리비", "확인"]
    ]

    for pattern in normal_payment_patterns:
        if all(word in text for word in pattern):
            reduction += 40.0
            break # 중복 감쇄 방지

    return max(score - reduction, 0.0)

def analyze_risk(text: str):
    score = 0.0

    # 카테고리별 가중치 설정 (Day 13 최적화: 최종 튜닝)
    weights = {
        "institution": 30.0,    # 기관 사칭
        "crime_words": 35.0,    # 범죄 관련
        "money_words": 40.0,    # 금전 요구
        "technology_words": 45.0, # 원격제어/악성앱
        "urgency_words": 15.0,   # 시급성 강조
        "threat_words": 30.0,    # 협박/법적 책임
        "authority_words": 25.0, # 권위 사칭/비밀유지
        "loan_scam_words": 35.0, # 대출 사기
        "messenger_words": 25.0  # 메신저 유도/지인 사칭
    }

    category_labels = {
        "institution": "기관 사칭",
        "crime_words": "범죄 관련 언급",
        "money_words": "금전 요구",
        "technology_words": "앱 설치 또는 원격제어 요구",
        "urgency_words": "긴급 상황 강조",
        "threat_words": "협박 또는 법적 위협",
        "authority_words": "권위 사칭",
        "loan_scam_words": "대출 사기 의심",
        "messenger_words": "지인 사칭 또는 메신저 유도"
    }

    detected_categories = []
    detected_keywords = []
    reasons = []
    actions = []
    risk_factors = []

    # 카테고리별 행동 지침 매핑
    action_map = {
        "institution": "전화를 끊고 해당 기관의 공식 번호로 직접 전화하여 확인하세요.",
        "crime_words": "경찰이나 검찰은 전화를 통해 돈을 요구하거나 앱 설치를 유도하지 않습니다.",
        "money_words": "절대 모르는 사람에게 돈을 송금하거나 현금을 전달하지 마세요.",
        "technology_words": "원격 제어 앱(AnyDesk 등)을 설치하거나 실행하지 마세요.",
        "urgency_words": "상대방의 독촉에 당황하지 말고 잠시 전화를 끊고 주위에 도움을 요청하세요.",
        "threat_words": "법적 처벌이나 구속 협박에 속지 마세요. 즉시 통화를 종료해도 괜찮습니다.",
        "authority_words": "수사 기밀이라며 주변에 알리지 말라고 하는 것은 100% 사기입니다.",
        "loan_scam_words": "대출을 위해 선입금이나 수수료를 요구하는 것은 불법 사기 대출입니다.",
        "messenger_words": "가족이나 지인을 사칭한 메시지라면, 반드시 본인과 직접 통화하여 확인하세요."
    }

    # 1. 기본 키워드 기반 점수 계산
    for category, weight in weights.items():
        matched_words = []
        for word in keywords_data.get(category, []):
            if word in text:
                matched_words.append(word)

        if matched_words:
            score += weight
            label = category_labels.get(category, category)
            detected_categories.append(label)
            detected_keywords.extend(matched_words)
            reasons.append(f"{label} 관련 표현이 감지되었습니다.")

            # 누적 위험도 계산을 위한 상세 요인 추가
            risk_factors.append({
                "category": category,
                "label": label,
                "score": weight
            })

            # 해당 카테고리에 맞는 행동 지침 추가
            if category in action_map:
                actions.append(action_map[category])

    # 2. 오탐 완화 (N15 대응: 공식 설치 문맥)
    safe_install_patterns = [
        ["회사", "공지"], ["회사에서", "공지"], ["업데이트", "공식"],
        ["공식", "앱스토어"], ["공식", "홈페이지"], ["회사", "이메일"], ["회사에서", "이메일"]
    ]
    is_safe_install = any(all(word in text for word in pattern) for pattern in safe_install_patterns)

    if is_safe_install and "앱 설치 또는 원격제어 요구" in detected_categories:
        score -= weights["technology_words"]
        # 리스트 정리
        detected_categories = [c for c in detected_categories if c != "앱 설치 또는 원격제어 요구"]
        risk_factors = [f for f in risk_factors if f["category"] != "technology_words"]
        reasons = [r for r in reasons if "앱 설치 또는 원격제어" not in r]
        actions = [a for a in actions if "원격 제어 앱" not in a]

    # 3. 문맥 기반 보너스 (P6, P12, P19, VP8, VP9, VP11 등 대응)
    context_bonus, c_reasons, c_actions, c_factors = calculate_context_bonus(text, keywords_data)
    combo_bonus, combo_reasons, combo_actions, combo_factors = calculate_combination_bonus(text)

    score += (context_bonus + combo_bonus)
    reasons.extend(c_reasons + combo_reasons)
    actions.extend(c_actions + combo_actions)
    risk_factors.extend(c_factors + combo_factors)

    # 4. 최종 문맥 보정 (뉴스, 일상 거래 등 감쇄)
    score = apply_safe_context_adjustment(text, score)

    # 위험도가 높을 경우 기본 행동 지침 추가
    if score >= 35 and not actions:
        actions.append("보이스피싱이 의심되오니 즉시 통화를 종료하시고 112에 신고하세요.")

    return {
        "risk_score": min(max(score, 0.0), 100.0),
        "detected_categories": detected_categories,
        "detected_keywords": list(set(detected_keywords)),
        "reasons": reasons,
        "actions": list(dict.fromkeys(actions)),  # 순서 유지하며 중복 제거
        "risk_factors": risk_factors
    }

# 5. 음성 분석 API 엔드포인트
@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    start_time = time.time()
    print(f"\n[Request] 음성 분석 요청 수수료: {file.filename}")

    # 수신받은 임시 음성 파일 저장
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # STT 실행
        print("🎙️ Faster-Whisper 분석 시작...")
        stt_start_time = time.time()

        # beam_size=5는 정확도와 속도의 균형을 맞춘 설정입니다.
        segments, info = stt_model.transcribe(temp_file_path, beam_size=5, language="ko")

        transcribed_text = ""
        for segment in segments:
            transcribed_text += segment.text

        stt_end_time = time.time()

        transcribed_text = transcribed_text.strip()
        stt_duration = stt_end_time - stt_start_time
        print(f"✅ STT 완료 ({stt_duration:.2f}초): {transcribed_text[:50]}...")

        # 위험도 측정 및 근거 분석
        risk_result = analyze_risk(transcribed_text)
        risk_score = risk_result["risk_score"]
        is_phishing = risk_score >= 70.0 # 임계값 조정 (80 -> 70)

        total_duration = time.time() - start_time
        print(f"📊 분석 결과: 위험도 {risk_score}점 (총 소요 시간: {total_duration:.2f}초)")
        
        return {
            "status": "success",
            "text": transcribed_text,
            "risk_score": risk_score,
            "is_phishing": is_phishing,
            "detected_categories": risk_result["detected_categories"],
            "detected_keywords": risk_result["detected_keywords"],
            "reasons": risk_result["reasons"],
            "actions": risk_result["actions"],
            "risk_factors": risk_result["risk_factors"],
            "processing_time": round(total_duration, 2)
        }

    except Exception as e:
        print(f"❌ 분석 오류 발생: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        # 작업 종료 후 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/")
def read_root():
    return {"message": "SafeguardAI Backend Server is Running!"}
