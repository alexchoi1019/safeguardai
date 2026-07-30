import os
import shutil
import imageio_ffmpeg
import whisper

# ffmpeg 경로를 파이썬 실행 환경에 등록 (Whisper가 ffmpeg를 찾도록 보장)
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)
ffmpeg_alias = os.path.join(ffmpeg_dir, "ffmpeg.exe")

if not os.path.exists(ffmpeg_alias):
    shutil.copy2(ffmpeg_exe, ffmpeg_alias)

os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

print("🎙️ Whisper STT 모델을 로드 중입니다... (base 모델)")
model = whisper.load_model("base")

# 테스트할 음성 파일명 (대소문자 정확히 확인!)
audio_path = os.path.join(os.path.dirname(__file__), "Sample.m4a")

if not os.path.exists(audio_path):
    print(f"❌ '{audio_path}' 파일이 backend 폴더에 없습니다! 파일명을 확인해 주세요.")
else:
    print(f"🎧 '{audio_path}' 음성 변환 시작...")
    result = model.transcribe(audio_path, language="ko")

    print("\n================ [STT 변환 결과] ================")
    print(result["text"])
    print("==================================================")
    print("✅ STT 테스트 성공!")