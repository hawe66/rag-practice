update 예정  
  
# Week 9: AI Application Deployment

FastAPI 기반 AI 파이프라인 배포 프로젝트

## 기능

- 8주차 파이프라인을 RESTful API로 제공
- Swagger UI 자동 문서화
- LangSmith 모니터링 연동

## API 엔드포인트

- `POST /api/v1/run` - 파이프라인 실행
- `GET /api/v1/status/{run_id}` - 상태 조회
- `GET /api/v1/result/{run_id}` - 결과 조회

## 로컬 실행
```bash
poetry install
poetry run uvicorn app.main:app --reload