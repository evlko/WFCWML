from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

from project.config import DATA_SOURCE
from project.wfc.factory import Factory
from project.wfc.repository import repository
from project.wfc.grid import Grid, Rect
from project.wfc.judge import AlwaysContinueJudge
from project.wfc.advisor import RandomAdvisor
from project.wfc.wfc import WFC

app = FastAPI(title="WFCWML API")


class GenerateRequest(BaseModel):
    width: int = Field(default=20, ge=1, description="Width of the grid")
    height: int = Field(default=20, ge=1, description="Height of the grid")
    generations: int = Field(default=1, ge=1, description="Target number of successful generations")


@app.get("/ping")
async def ping():
    """Health check endpoint that returns pong."""
    return {"message": "pong"}


@app.post("/generate")
async def generate(request: GenerateRequest):
    """Generate a grid using Wave Function Collapse algorithm."""
    factory = Factory(DATA_SOURCE)
    factory.create_patterns()
    rect = Rect(width=request.width, height=request.height)
    grid = Grid(rect=rect, patterns=repository.get_all_patterns())
    
    judge = AlwaysContinueJudge()
    advisor = RandomAdvisor()
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