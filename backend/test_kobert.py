import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 1. 한국어 BERT 토크나이저 및 모델 불러오기
MODEL_NAME = "klue/bert-base"

print("모델과 토크나이저를 다운로드 중입니다... (최초 1회 소요)")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

print("✅ 모델 로드 성공!")

# 2. 간단한 텍스트 토큰화 테스트
sample_text = "서울중앙지검 김민수 검사입니다. 명의도용 사건으로 연락드렸습니다."
inputs = tokenizer(sample_text, return_tensors="pt")

print(f"\n입력 문장: {sample_text}")
print(f"토큰화 결과 (input_ids 일부): {inputs['input_ids'][0][:5]}")