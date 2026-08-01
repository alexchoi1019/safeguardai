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

# 4. 간단한 위험도 산출 함수
def calculate_risk_score(text: str) -> float:
    score = 0.0
    
    # 키워드 범주별 가중치 설정
    for word in keywords_data.get("institution", []):
        if word in text:
            score += 25.0
            
    for word in keywords_data.get("crime_words", []):
        if word in text:
            score += 30.0
            
    for word in keywords_data.get("money_words", []):
        if word in text:
            score += 35.0
            
    return min(score, 100.0)

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

        # 위험도 측정
        risk_score = calculate_risk_score(transcribed_text)
        is_phishing = risk_score >= 80.0

        total_duration = time.time() - start_time
        print(f"📊 분석 결과: 위험도 {risk_score}점 (총 소요 시간: {total_duration:.2f}초)")
        
        return {
            "status": "success",
            "text": transcribed_text,
            "risk_score": risk_score,
            "is_phishing": is_phishing,
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
