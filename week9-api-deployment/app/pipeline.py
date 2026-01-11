import os
from typing import TypedDict, List, Dict, Any
from datetime import datetime
import uuid
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# State 정의 (8주차 재사용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PipelineState(TypedDict):
    run_id: str
    user_goal: str
    current_step: int
    completed_steps: List[int]
    step_outputs: Dict[str, Any]
    status: str
    timestamp: str

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 간소화된 노드 (실제로는 8주차 4개 Step 사용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def step_1_node(state: PipelineState) -> PipelineState:
    """Step 1: 요구사항 분석"""
    print(f"[Step 1] 분석 중: {state['user_goal']}")

    prompt = f"다음 요청을 분석하세요: {state['user_goal']}"
    result = llm.invoke(prompt).content

    step_outputs = state.get("step_outputs", {})
    step_outputs["step_1"] = {"analysis": result}

    return {
        "current_step": 1,
        "completed_steps": [1],
        "step_outputs": step_outputs,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

def step_2_node(state: PipelineState) -> PipelineState:
    """Step 2: 콘텐츠 생성"""
    print(f"[Step 2] 생성 중")

    analysis = state["step_outputs"]["step_1"]["analysis"]
    prompt = f"다음 분석을 바탕으로 콘텐츠를 작성하세요:\n{analysis}"
    result = llm.invoke(prompt).content

    step_outputs = state["step_outputs"]
    step_outputs["step_2"] = {"content": result}

    return {
        "current_step": 2,
        "completed_steps": [1, 2],
        "step_outputs": step_outputs,
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 그래프 구성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

graph_builder = StateGraph(PipelineState)
graph_builder.add_node("step_1", step_1_node)
graph_builder.add_node("step_2", step_2_node)
graph_builder.add_edge(START, "step_1")
graph_builder.add_edge("step_1", "step_2")
graph_builder.add_edge("step_2", END)

pipeline_graph = graph_builder.compile()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 헬퍼 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_initial_state(user_goal: str) -> PipelineState:
    """초기 State 생성"""
    return {
        "run_id": "run_" + uuid.uuid4().hex[:8],
        "user_goal": user_goal,
        "current_step": 0,
        "completed_steps": [],
        "step_outputs": {},
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }

def run_pipeline(user_goal: str) -> PipelineState:
    """파이프라인 실행"""
    state = create_initial_state(user_goal)
    result = pipeline_graph.invoke(state)
    return {**state, **result}
