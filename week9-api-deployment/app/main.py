from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from typing import Dict
from datetime import datetime

from .models import (
    CreateJobRequest,
    JobStatusResponse,
    JobResultResponse,
    ErrorResponse
)
from .pipeline import run_pipeline, PipelineState

# 환경변수 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FastAPI 앱 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

app = FastAPI(
    title="Week 9 Pipeline API",
    version="1.0.0",
    description="8주차 파이프라인을 RESTful API로 배포",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 인메모리 저장소 (간단한 구현)
# 실제 프로덕션에서는 Redis나 DB 사용
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

jobs: Dict[str, PipelineState] = {}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 백그라운드 작업 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def execute_pipeline(run_id: str, user_goal: str):
    """백그라운드에서 파이프라인 실행"""
    try:
        jobs[run_id]["status"] = "running"
        result = run_pipeline(user_goal)
        jobs[run_id] = {**jobs[run_id], **result}
    except Exception as e:
        jobs[run_id]["status"] = "failed"
        jobs[run_id]["error"] = str(e)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API 엔드포인트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Week 9 Pipeline API",
        "docs": "/docs",
        "endpoints": {
            "create_job": "POST /api/v1/run",
            "get_status": "GET /api/v1/status/{run_id}",
            "get_result": "GET /api/v1/result/{run_id}"
        }
    }

@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post(
    "/api/v1/run",
    response_model=JobStatusResponse,
    summary="파이프라인 실행",
    description="새로운 파이프라인 작업을 시작합니다",
    responses={
        200: {"description": "작업 생성 성공"},
        500: {"model": ErrorResponse}
    }
)
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks
):
    """파이프라인 실행 시작"""
    from .pipeline import create_initial_state

    # 초기 State 생성
    state = create_initial_state(request.user_goal)
    run_id = state["run_id"]

    # 저장
    jobs[run_id] = state

    # 백그라운드 실행
    background_tasks.add_task(execute_pipeline, run_id, request.user_goal)

    return JobStatusResponse(
        run_id=run_id,
        status="pending",
        current_step=0,
        completed_steps=[],
        created_at=state["timestamp"]
    )

@app.get(
    "/api/v1/status/{run_id}",
    response_model=JobStatusResponse,
    summary="작업 상태 조회",
    description="실행 중인 작업의 상태를 확인합니다",
    responses={
        200: {"description": "상태 조회 성공"},
        404: {"model": ErrorResponse}
    }
)
async def get_status(run_id: str):
    """작업 상태 조회"""
    if run_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[run_id]

    return JobStatusResponse(
        run_id=run_id,
        status=job["status"],
        current_step=job["current_step"],
        completed_steps=job["completed_steps"],
        created_at=job["timestamp"]
    )

@app.get(
    "/api/v1/result/{run_id}",
    response_model=JobResultResponse,
    summary="작업 결과 조회",
    description="완료된 작업의 결과를 조회합니다",
    responses={
        200: {"description": "결과 조회 성공"},
        404: {"model": ErrorResponse},
        425: {"description": "작업이 아직 완료되지 않음"}
    }
)
async def get_result(run_id: str):
    """작업 결과 조회"""
    if run_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[run_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=425,
            detail=f"Job is still {job['status']}"
        )

    # 최종 출력 생성
    final_output = job["step_outputs"].get("step_2", {}).get("content", "")

    return JobResultResponse(
        run_id=run_id,
        status=job["status"],
        user_goal=job["user_goal"],
        final_output=final_output,
        step_outputs=job["step_outputs"]
    )
