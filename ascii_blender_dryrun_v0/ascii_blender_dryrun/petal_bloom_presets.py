"""
Petal bloom preset compiler.

Presets keep floral math reusable. Source recipes can name a preset and apply
small overrides; this compiler expands that into the low-level AddPetalBloom op
that ASCII and Blender already consume.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .ops import AddPetalBloom, AddPetalBloomPreset, BuildOp


DEFAULT_PRESET_PATH = Path(__file__).resolve().parents[1] / "presets" / "petal_bloom_presets_v0.json"
SCALE_KEYS = {
    "length",
    "base_width",
    "max_width",
    "tip_width",
    "min_width",
    "base_thickness",
    "min_thickness",
    "max_thickness",
    "tip_thickness",
}
LAYER_SCALE_KEYS = {"radius", "z_offset"}


def compile_petal_bloom_presets(
    ops: list[BuildOp],
    preset_path: Path | str = DEFAULT_PRESET_PATH,
) -> list[BuildOp]:
    presets = load_petal_bloom_presets(preset_path)
    compiled: list[BuildOp] = []
    for op in ops:
        if isinstance(op, AddPetalBloomPreset):
            compiled.append(compile_petal_bloom_preset(op, presets))
        else:
            compiled.append(op)
    return compiled


def load_petal_bloom_presets(path: Path | str = DEFAULT_PRESET_PATH) -> dict[str, dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    presets = payload.get("presets", [])
    result: dict[str, dict[str, Any]] = {}
    for preset in presets:
        preset_id = str(preset["id"])
        if preset_id in result:
            raise ValueError(f"Duplicate petal bloom preset id: {preset_id}")
        result[preset_id] = preset
    return result


def compile_petal_bloom_preset(
    op: AddPetalBloomPreset,
    presets: dict[str, dict[str, Any]],
) -> AddPetalBloom:
    if op.preset not in presets:
        raise ValueError(f"{op.name} references unknown petal bloom preset: {op.preset}")
    if op.scale <= 0:
        raise ValueError(f"{op.name} preset scale must be positive.")

    preset = presets[op.preset]
    petal = copy.deepcopy(preset["petal"])
    layers = copy.deepcopy(preset["layers"])

    _scale_petal(petal, op.scale)
    for layer in layers:
        _scale_layer(layer, op.scale)

    if op.petal_overrides:
        petal.update(copy.deepcopy(op.petal_overrides))

    if op.layer_overrides:
        for override in op.layer_overrides:
            index = int(override["index"])
            if index < 0 or index >= len(layers):
                raise ValueError(f"{op.name} layer override index out of range: {index}")
            layer_update = {key: value for key, value in override.items() if key != "index"}
            layers[index].update(copy.deepcopy(layer_update))

    return AddPetalBloom(
        name=op.name,
        petal=petal,
        layers=layers,
        x=op.x,
        y=op.y,
        z=op.z,
        material=op.material or str(preset.get("material", "stone")),
    )


def _scale_petal(petal: dict[str, Any], scale: float) -> None:
    if scale == 1.0:
        return
    for key in SCALE_KEYS:
        if key in petal:
            petal[key] = round(float(petal[key]) * scale, 6)


def _scale_layer(layer: dict[str, Any], scale: float) -> None:
    if scale == 1.0:
        return
    for key in LAYER_SCALE_KEYS:
        if key in layer:
            layer[key] = round(float(layer[key]) * scale, 6)
