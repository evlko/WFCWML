from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from project.config import DATA_SOURCE
from project.wfc.factory import JsonFactory, ApiFactory
from project.wfc.repository import repository
from project.wfc.grid import Grid, Rect
from project.wfc.judge import AlwaysContinueJudge, RandomJudge, Judge
from project.wfc.advisor import RandomAdvisor, GreedyAdvisor, Advisor
from project.wfc.wfc import WFC

app = FastAPI(title="WFCWML API")

# Judge implementations map
JUDGES = {
    0: lambda: AlwaysContinueJudge(),
    1: lambda: RandomJudge(rollback_chance=0.1),
}

# Advisor implementations map
ADVISORS = {
    0: lambda: RandomAdvisor(),
    1: lambda: GreedyAdvisor(),
}


class WFCConfig(BaseModel):
    """Configuration for WFC generation containing pattern data."""
    images_folder: str = Field(description="Path to images folder (e.g., 'sprites/forest/')")
    patterns: list[dict[str, Any]] = Field(description="List of pattern definitions with rules")


class GenerateRequest(BaseModel):
    width: int = Field(default=20, ge=1, description="Width of the grid")
    height: int = Field(default=20, ge=1, description="Height of the grid")
    generations: int = Field(default=1, ge=1, description="Target number of successful generations")
    config: WFCConfig | None = Field(default=None, description="Optional WFC configuration. If not provided, uses default config from project settings.")
    judge_id: int = Field(default=0, description="Judge ID: 0=AlwaysContinue, 1=90%Continue")
    advisor_id: int = Field(default=0, description="Advisor ID: 0=Random, 1=Greedy")


@app.get("/ping")
async def ping():
    """Health check endpoint that returns pong."""
    return {"message": "pong"}


def preprocess_patterns(patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert string numbers in rules back to integers"""
    for pattern in patterns:
        if "rules" in pattern:
            for direction in ["up", "down", "left", "right"]:
                if direction in pattern["rules"]:
                    processed_rules = []
                    for rule in pattern["rules"][direction]:
                        # Try to convert to int, keep as string if it fails
                        if isinstance(rule, str) and rule.isdigit():
                            processed_rules.append(int(rule))
                        else:
                            processed_rules.append(rule)
                    pattern["rules"][direction] = processed_rules
    return patterns


@app.post("/generate")
async def generate(request: GenerateRequest):
    """Generate a grid using Wave Function Collapse algorithm."""
    repository.clear()

    # Validate and create judge
    if request.judge_id not in JUDGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown judge_id: {request.judge_id}. Available: {list(JUDGES.keys())}"
        )
    
    # Validate and create advisor
    if request.advisor_id not in ADVISORS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown advisor_id: {request.advisor_id}. Available: {list(ADVISORS.keys())}"
        )

    if request.config:
        processed_patterns = preprocess_patterns(request.config.patterns)
        factory = ApiFactory(
            images_folder=request.config.images_folder,
            patterns_data=processed_patterns
        )
    else:
        factory = JsonFactory(DATA_SOURCE)
    
    factory.create_patterns()
    rect = Rect(width=request.width, height=request.height)
    grid = Grid(rect=rect, patterns=repository.get_all_patterns())
    
    judge = JUDGES[request.judge_id]()
    advisor = ADVISORS[request.advisor_id]()
    wfc = WFC(grid=grid, judge=judge, advisor=advisor)
    
    successful_generations = 0
    while successful_generations < request.generations:
        is_succeeded = wfc.generate()
        if is_succeeded:
            successful_generations += 1
    
    return {
        "grid": grid.uids
    }



def main():
    """Run the FastAPI application using uvicorn."""
    uvicorn.run(
        "project.api.app:app",
        host="::",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()