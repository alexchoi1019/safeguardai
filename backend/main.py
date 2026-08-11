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
def analyze_risk(text: str):
    score = 0.0

    weights = {
        "institution": 25.0,    # 기관 사칭
        "crime_words": 30.0,    # 범죄 관련
        "money_words": 35.0,    # 금전 요구
        "technology_words": 30.0, # 원격제어/악성앱
        "urgency_words": 15.0,   # 시급성 강조
        "threat_words": 25.0,    # 협박/법적 책임
        "authority_words": 20.0, # 권위 사칭/비밀유지
        "loan_scam_words": 30.0, # 대출 사기
        "messenger_words": 15.0  # 메신저 유도/지인 사칭
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

    for category, weight in weights.items():
        matched_words = []
        for word in keywords_data.get(category, []):
            if word in text:
                matched_words.append(word)

        if matched_words:
            score += weight
            detected_categories.append(category_labels.get(category, category))
            detected_keywords.extend(matched_words)
            reasons.append(f"{category_labels.get(category, category)} 관련 표현이 감지되었습니다.")

            # 해당 카테고리에 맞는 행동 지침 추가
            if category in action_map:
                actions.append(action_map[category])

    # 위험도가 높을 경우 기본 행동 지침 추가
    if score >= 40 and not actions:
        actions.append("보이스피싱이 의심되오니 즉시 통화를 종료하시고 112에 신고하세요.")

    return {
        "risk_score": min(score, 100.0),
        "detected_categories": detected_categories,
        "detected_keywords": list(set(detected_keywords)),
        "reasons": reasons,
        "actions": list(dict.fromkeys(actions))  # 순서 유지하며 중복 제거
    }

# 5. 음성 분석 API 엔드포인트
@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    start_time = time.time()
    print(f"\n[Request] 음성 분석 요청 수신: {file.filename}")

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
        is_phishing = risk_score >= 80.0

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
