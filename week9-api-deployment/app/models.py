from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 요청 모델
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CreateJobRequest(BaseModel):
    """파이프라인 실행 요청"""
    user_goal: str = Field(..., description="사용자 요청", example="AI 윤리 에세이")

    class Config:
        json_schema_extra = {
            "example": {
                "user_goal": "AI 윤리에 대한 300자 에세이"
            }
        }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 응답 모델
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class JobStatusResponse(BaseModel):
    """작업 상태 응답"""
    run_id: str
    status: str  # pending, running, completed, failed
    current_step: int
    completed_steps: List[int]
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_abc123",
                "status": "running",
                "current_step": 2,
                "completed_steps": [1, 2],
                "created_at": "2026-01-11T12:00:00"
            }
        }

class JobResultResponse(BaseModel):
    """작업 결과 응답"""
    run_id: str
    status: str
    user_goal: str
    final_output: Optional[str] = None
    step_outputs: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_abc123",
                "status": "completed",
                "user_goal": "AI 윤리 에세이",
                "final_output": "AI 윤리는..."
            }
        }

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
