"""
Conway's Game of Life - FastAPI Backend
Rules:
  1. Any live cell with 2 or 3 live neighbours survives.
  2. Any dead cell with exactly 3 live neighbours becomes alive.
  3. All other live cells die; all other dead cells remain dead.
"""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Conway's Game of Life API",
    description="REST API for Conway's Game of Life cellular automaton",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

Grid = List[List[int]]  # 0 = dead, 1 = alive


class GridState(BaseModel):
    grid: Grid = Field(..., description="2-D list of 0/1 values")
    generation: int = Field(0, description="Current generation number")


class StepRequest(BaseModel):
    grid: Grid
    generation: int = 0
    steps: int = Field(1, ge=1, le=1000, description="Number of steps to advance")


class PresetRequest(BaseModel):
    name: str
    rows: int = Field(20, ge=5, le=200)
    cols: int = Field(20, ge=5, le=200)


class RandomRequest(BaseModel):
    rows: int = Field(20, ge=5, le=200)
    cols: int = Field(20, ge=5, le=200)
    density: float = Field(0.3, ge=0.0, le=1.0, description="Probability a cell starts alive")


# ---------------------------------------------------------------------------
# Core automaton logic
# ---------------------------------------------------------------------------

def count_neighbours(grid: Grid, r: int, c: int) -> int:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    total = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = (r + dr) % rows, (c + dc) % cols  # toroidal (wrap-around)
            total += grid[nr][nc]
    return total


def step(grid: Grid) -> Grid:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    new_grid: Grid = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            neighbours = count_neighbours(grid, r, c)
            alive = grid[r][c] == 1
            if alive and neighbours in (2, 3):
                new_grid[r][c] = 1
            elif not alive and neighbours == 3:
                new_grid[r][c] = 1
    return new_grid


def make_empty(rows: int, cols: int) -> Grid:
    return [[0] * cols for _ in range(rows)]


def make_random(rows: int, cols: int, density: float) -> Grid:
    import random
    return [[1 if random.random() < density else 0 for _ in range(cols)] for _ in range(rows)]


# ---------------------------------------------------------------------------
# Built-in presets
# ---------------------------------------------------------------------------

def _embed(rows: int, cols: int, pattern: Grid, offset_r: int = 0, offset_c: int = 0) -> Grid:
    grid = make_empty(rows, cols)
    for r, row in enumerate(pattern):
        for c, val in enumerate(row):
            gr, gc = r + offset_r, c + offset_c
            if 0 <= gr < rows and 0 <= gc < cols:
                grid[gr][gc] = val
    return grid


PRESETS: dict[str, Grid] = {
    # Still lifes
    "block": [
        [1, 1],
        [1, 1],
    ],
    "beehive": [
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [0, 1, 1, 0],
    ],
    "loaf": [
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [0, 1, 0, 1],
        [0, 0, 1, 0],
    ],
    # Oscillators
    "blinker": [
        [1, 1, 1],
    ],
    "toad": [
        [0, 1, 1, 1],
        [1, 1, 1, 0],
    ],
    "beacon": [
        [1, 1, 0, 0],
        [1, 1, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 1, 1],
    ],
    "pulsar": [
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [1,0,0,0,0,1,0,1,0,0,0,0,1],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,1,1,1,0,0,0,1,1,1,0,0],
    ],
    # Spaceships
    "glider": [
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
    ],
    "lwss": [
        [0, 1, 0, 0, 1],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 1],
        [1, 1, 1, 1, 0],
    ],
    # Methuselahs
    "r_pentomino": [
        [0, 1, 1],
        [1, 1, 0],
        [0, 1, 0],
    ],
    "diehard": [
        [0, 0, 0, 0, 0, 0, 1, 0],
        [1, 1, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 1, 1, 1],
    ],
    "acorn": [
        [0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [1, 1, 0, 0, 1, 1, 1],
    ],
    # Guns
    "gosper_glider_gun": [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
}


def get_preset(name: str, rows: int, cols: int) -> Grid:
    if name not in PRESETS:
        raise ValueError(f"Unknown preset '{name}'. Available: {sorted(PRESETS)}")
    pattern = PRESETS[name]
    pr, pc = len(pattern), max(len(row) for row in pattern)
    # Centre pattern in the grid
    offset_r = max(0, (rows - pr) // 2)
    offset_c = max(0, (cols - pc) // 2)
    return _embed(rows, cols, pattern, offset_r, offset_c)


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.get("/", summary="Health check")
def root():
    return {"status": "ok", "app": "Conway's Game of Life API"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/presets", summary="List available presets")
def list_presets():
    return {"presets": sorted(PRESETS.keys())}


@app.post("/preset", response_model=GridState, summary="Load a named preset")
def load_preset(req: PresetRequest):
    try:
        grid = get_preset(req.name, req.rows, req.cols)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return GridState(grid=grid, generation=0)


@app.post("/random", response_model=GridState, summary="Generate a random grid")
def random_grid(req: RandomRequest):
    grid = make_random(req.rows, req.cols, req.density)
    return GridState(grid=grid, generation=0)


@app.post("/step", response_model=GridState, summary="Advance the simulation N steps")
def advance(req: StepRequest):
    grid = req.grid
    if not grid or not grid[0]:
        raise HTTPException(status_code=400, detail="Grid must not be empty")
    for _ in range(req.steps):
        grid = step(grid)
    return GridState(grid=grid, generation=req.generation + req.steps)


@app.post("/reset", response_model=GridState, summary="Return an empty grid")
def reset(rows: int = 20, cols: int = 20):
    return GridState(grid=make_empty(rows, cols), generation=0)
