import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def mini_cfg():
    return {
        "seed": 0,
        "data": {"min_seq_len": 2, "max_seq_len": 100, "val_frac": 0.2, "test_frac": 0.2},
        "monitoring": {"psi_warn": 0.1, "psi_alert": 0.25},
    }


@pytest.fixture
def raw_long():
    """Small deterministic long frame: 10 students, 3 skills."""
    rng = np.random.default_rng(0)
    rows = []
    for uid in range(10):
        n = rng.integers(8, 16)
        for j in range(n):
            skill = int(rng.integers(0, 3))
            correct = int(rng.random() < 0.5 + 0.1 * skill)
            rows.append((uid, j, skill, correct))
    return pd.DataFrame(rows, columns=["user_id", "order_idx", "skill_id", "correct"])
