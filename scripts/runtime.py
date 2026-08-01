"""Runtime helpers shared by the MuJoCo transfer demos and tests."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import onnxruntime as ort


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PI2_ONNX = REPO_ROOT / "sim_to_real/unitree_bringup/config/go1/pi2.onnx"


def require_file(path: str | os.PathLike[str] | None, label: str) -> Path:
    """Return an existing required file or raise an actionable error."""
    if not path:
        raise FileNotFoundError(
            f"{label} is required. Pass its path explicitly or set the documented "
            "environment variable."
        )
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"{label} not found: {resolved}")
    return resolved


def actuator_net_path(value: str | None) -> Path:
    """Resolve the separately obtained Walk These Ways actuator network."""
    if not value:
        raise FileNotFoundError(
            "Go1 actuator network is required. Clone https://github.com/Improbable-AI/"
            "walk-these-ways and pass --actuator-net "
            "<clone>/resources/actuator_nets/unitree_go1.pt, or set "
            "GO1_ACTUATOR_NET. The model is intentionally not vendored here."
        )
    return require_file(value, "Go1 actuator network")


class Pi2OnnxPolicy:
    """CPU ONNX Runtime wrapper for the committed 39D-to-12D pi2 policy."""

    def __init__(self, model_path: str | os.PathLike[str] = DEFAULT_PI2_ONNX):
        path = require_file(model_path, "pi2 ONNX policy")
        self._session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        self._input = self._session.get_inputs()[0].name
        self._output = self._session.get_outputs()[0].name
        input_shape = self._session.get_inputs()[0].shape
        output_shape = self._session.get_outputs()[0].shape
        if input_shape[-1] != 39 or output_shape[-1] != 12:
            raise ValueError(
                f"Unexpected pi2 ONNX dimensions: input={input_shape}, output={output_shape}; "
                "expected 39 -> 12."
            )
        print(f"[pi2] Loaded ONNX policy from {path} ({input_shape[-1]} -> {output_shape[-1]})")

    def __call__(self, observation: np.ndarray) -> np.ndarray:
        batch = np.asarray(observation, dtype=np.float32).reshape(1, 39)
        return self._session.run([self._output], {self._input: batch})[0][0]
