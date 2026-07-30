import os
import json
import shutil
import imageio_ffmpeg
import whisper
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

# 1. ffmpeg 경로 동적 등록 (어제 검증된 방식)
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)
ffmpeg_alias = os.path.join(ffmpeg_dir, "ffmpeg.exe")

if not os.path.exists(ffmpeg_alias):
    shutil.copy2(ffmpeg_exe, ffmpeg_alias)

os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# 2. FastAPI 앱 및 Whisper 모델 초기화
app = FastAPI(title="SafeguardAI Phishing Detection Server")

print("🎙️ Whisper 모델을 로딩 중입니다...")
stt_model = whisper.load_model("base")
print("✅ Whisper 모델 로딩 완료!")

# 3. 키워드 데이터셋 로드
KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "keywords.json")
keywords_data = {}
if os.path.exists(KEYWORDS_PATH):
    with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
        keywords_data = json.load(f)

# 4. 간단한 위험도 산출 함수 (키워드 매칭 기반 기초 알고리즘)
def calculate_risk_score(text: str) -> float:
    score = 0.0
    
    # 키워드 범주별 가중치 설정
    for word in keywords_data.get("institution", []):
        if word in text:
            score += 25.0  # 기관 사칭 단어
            
    for word in keywords_data.get("crime_words", []):
        if word in text:
            score += 30.0  # 범죄 관련 단어
            
    for word in keywords_data.get("money_words", []):
        if word in text:
            score += 35.0  # 금전 이체 요구 단어
            
    # 최대 100점으로 제한
    return min(score, 100.0)

# 5. 음성 분석 API 엔드포인트
@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    # 수신받은 임시 음성 파일 저장
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # STT 실행
        result = stt_model.transcribe(temp_file_path, language="ko")
        transcribed_text = result.get("text", "").strip()
        
        # 위험도 측정
        risk_score = calculate_risk_score(transcribed_text)
        is_phishing = risk_score >= 80.0  # 80점 이상일 때 피싱 경고 판정
        
        return {
            "status": "success",
            "text": transcribed_text,
            "risk_score": risk_score,
            "is_phishing": is_phishing
        }
        
    finally:
        # 작업 종료 후 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/")
def read_root():
    return {"message": "SafeguardAI Backend Server is Running!"}