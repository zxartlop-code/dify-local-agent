"""
Unit tests for Conway's Game of Life backend.
Run with:  pytest tests/test_backend.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from fastapi.testclient import TestClient
from main import app, step, count_neighbours, make_empty, make_random, get_preset

client = TestClient(app)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

class TestCountNeighbours:
    def test_isolated_cell(self):
        g = [[0,0,0],[0,1,0],[0,0,0]]
        assert count_neighbours(g, 1, 1) == 0

    def test_all_neighbours_alive(self):
        g = [[1,1,1],[1,0,1],[1,1,1]]
        assert count_neighbours(g, 1, 1) == 8

    def test_wrap_around(self):
        # Cell at top-left should see bottom-right corner (toroidal grid)
        g = [[0,0,0],[0,0,0],[0,0,1]]
        assert count_neighbours(g, 0, 0) == 1


class TestStep:
    def test_blinker_oscillates(self):
        # Horizontal blinker
        g = [[0,0,0,0,0],
             [0,0,1,0,0],
             [0,0,1,0,0],
             [0,0,1,0,0],
             [0,0,0,0,0]]
        g2 = step(g)
        # Should become vertical
        assert g2[2][1] == 1
        assert g2[2][2] == 1
        assert g2[2][3] == 1
        assert g2[1][2] == 0
        assert g2[3][2] == 0

    def test_block_is_stable(self):
        g = [[0,0,0,0],
             [0,1,1,0],
             [0,1,1,0],
             [0,0,0,0]]
        assert step(g) == g

    def test_lonely_cell_dies(self):
        g = [[0,0,0],[0,1,0],[0,0,0]]
        assert step(g) == make_empty(3, 3)

    def test_three_cells_birth(self):
        # Three cells in an L — middle of left column should be born
        g = [[1,0,0],[1,0,0],[1,0,0]]
        g2 = step(g)
        assert g2[1][1] == 1   # born with 3 neighbours


class TestMakeRandom:
    def test_shape(self):
        g = make_random(5, 7, 0.5)
        assert len(g) == 5
        assert all(len(r) == 7 for r in g)

    def test_values_binary(self):
        g = make_random(10, 10, 0.5)
        vals = {v for row in g for v in row}
        assert vals <= {0, 1}

    def test_density_zero(self):
        g = make_random(10, 10, 0.0)
        assert all(v == 0 for row in g for v in row)

    def test_density_one(self):
        g = make_random(10, 10, 1.0)
        assert all(v == 1 for row in g for v in row)


class TestGetPreset:
    def test_glider_loads(self):
        g = get_preset("glider", 10, 10)
        assert len(g) == 10
        assert len(g[0]) == 10
        alive = sum(v for row in g for v in row)
        assert alive == 5   # glider has 5 live cells

    def test_unknown_preset_raises(self):
        with pytest.raises(ValueError):
            get_preset("nonexistent_xyz", 10, 10)


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestPresetEndpoints:
    def test_list_presets(self):
        r = client.get("/presets")
        assert r.status_code == 200
        data = r.json()
        assert "presets" in data
        assert "glider" in data["presets"]
        assert "block" in data["presets"]

    def test_load_preset(self):
        r = client.post("/preset", json={"name": "glider", "rows": 15, "cols": 15})
        assert r.status_code == 200
        data = r.json()
        assert data["generation"] == 0
        assert len(data["grid"]) == 15
        assert len(data["grid"][0]) == 15

    def test_unknown_preset_404(self):
        r = client.post("/preset", json={"name": "does_not_exist", "rows": 10, "cols": 10})
        assert r.status_code == 404


class TestRandomEndpoint:
    def test_random_grid(self):
        r = client.post("/random", json={"rows": 10, "cols": 12, "density": 0.4})
        assert r.status_code == 200
        data = r.json()
        assert len(data["grid"]) == 10
        assert len(data["grid"][0]) == 12
        assert data["generation"] == 0

    def test_random_grid_full_density(self):
        r = client.post("/random", json={"rows": 5, "cols": 5, "density": 1.0})
        data = r.json()
        alive = sum(v for row in data["grid"] for v in row)
        assert alive == 25


class TestStepEndpoint:
    def _blinker_grid(self):
        g = make_empty(7, 7)
        g[3][2] = g[3][3] = g[3][4] = 1
        return g

    def test_step_single(self):
        g = self._blinker_grid()
        r = client.post("/step", json={"grid": g, "generation": 0, "steps": 1})
        assert r.status_code == 200
        data = r.json()
        assert data["generation"] == 1

    def test_step_multiple(self):
        g = self._blinker_grid()
        r = client.post("/step", json={"grid": g, "generation": 0, "steps": 10})
        assert r.status_code == 200
        assert r.json()["generation"] == 10

    def test_step_blinker_period_2(self):
        # After 2 steps the blinker should return to original state
        g = self._blinker_grid()
        r = client.post("/step", json={"grid": g, "generation": 0, "steps": 2})
        assert r.json()["grid"] == g

    def test_step_empty_grid_400(self):
        r = client.post("/step", json={"grid": [], "generation": 0, "steps": 1})
        assert r.status_code == 400


class TestResetEndpoint:
    def test_reset(self):
        r = client.post("/reset", params={"rows": 8, "cols": 8})
        assert r.status_code == 200
        data = r.json()
        assert data["generation"] == 0
        assert all(v == 0 for row in data["grid"] for v in row)
        assert len(data["grid"]) == 8
