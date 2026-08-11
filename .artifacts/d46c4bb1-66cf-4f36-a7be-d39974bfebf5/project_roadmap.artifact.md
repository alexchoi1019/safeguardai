# 🛡️ SafeguardAI Project Roadmap (7 Days)

Project schedule for finalizing the voice phishing detection system.

| Day | Goal | Key Tasks | Completion Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Day 1** | **탐지 엔진 마무리** | 2차 실패 13건 보완, 키워드 확장, 문맥/조합 규칙 적용 | 치명적 오탐/미탐 제거 | **[x] DONE** |
| **Day 2** | **3차 블라인드 검증** | 신규 정상 10개 + 피싱 15개 테스트 및 결과 기록 | 전체 80%↑, 정상 SAFE 9/10↑ | [ ] TODO |
| **Day 3** | **실제 음성 검증** | 실물 기기 10~15개 음성 테스트, STT 오차 확인 | 텍스트 vs 음성 결과 차이 파악 | [ ] TODO |
| **Day 4** | **안정성 테스트** | 5초 분할 누적, 20분 연속 실행, 파일/네트워크 안정성 | 크래시 없이 장시간 동작 | [ ] TODO |
| **Day 5** | **UI/UX 마무리** | 가독성 개선, 큰 글씨, 대처법 명확화 (고령층 최적화) | 한 화면에서 위험도/대처법 명확 | [ ] TODO |
| **Day 6** | **발표 시연 준비** | 시연용 시나리오 3종 선정, 서버/폰 연결 최종 체크 | 시나리오별 안정적 재현 가능 | [ ] TODO |
| **Day 7** | **최종 점검** | 버그 수정, README 정리, 백업 영상 촬영 | 발표 실패 시나리오 대비 완료 | [ ] TODO |

## Day 1 Summary (Completed)
- **Refined Engine:** Added context suppression (News/Bills) and behavioral bonuses (Loan+Fee).
- **Keyword Expansion:** Added linguistic variants (Financial inst, broken screen, etc.).
- **Threshold Sync:** Unified at 35 (WARNING) / 70 (DANGER).
- **Cumulative Risk Fix:** Integrated patterns into `risk_factors`.
- **Validation:** 59/60 (98.3%) pass rate on current development set.
