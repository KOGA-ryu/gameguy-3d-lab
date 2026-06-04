"""
Build operation schema.

The point of this module is to keep design logic out of Blender calls.
A recipe compiles into BuildOp objects. The same BuildOp stream can be
interpreted by an ASCII backend, a validation backend, or a Blender bpy
script emitter.

Coordinate convention:
- X: left/right
- Y: depth, front/back
- Z: height/up
- Front elevation projects X/Z.
- Side elevation projects Y/Z.
- Top footprint projects X/Y.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Union


@dataclass(frozen=True)
class AddBox:
    name: str
    width: float
    depth: float
    height: float
    z: float
    x: float = 0.0
    y: float = 0.0
    material: str = "stone"


@dataclass(frozen=True)
class AddCylinder:
    name: str
    radius: float
    height: float
    z: float
    x: float = 0.0
    y: float = 0.0
    vertices: int = 96
    material: str = "stone"
    taper_top_radius: float | None = None
    entasis: bool = False


@dataclass(frozen=True)
class AddRing:
    name: str
    radius: float
    tube_height: float
    z: float
    overhang: float = 0.0
    x: float = 0.0
    y: float = 0.0
    vertices: int = 96
    material: str = "stone"


@dataclass(frozen=True)
class CutFlutes:
    target: str
    count: int
    depth: float
    width_ratio: float = 0.28
    start_z: float | None = None
    end_z: float | None = None


@dataclass(frozen=True)
class AddLabel:
    name: str
    text: str
    x: float
    y: float
    z: float


BuildOp = Union[AddBox, AddCylinder, AddRing, CutFlutes, AddLabel]


OP_CLASSES = {
    "AddBox": AddBox,
    "AddCylinder": AddCylinder,
    "AddRing": AddRing,
    "CutFlutes": CutFlutes,
    "AddLabel": AddLabel,
}


def op_from_dict(data: Dict[str, Any]) -> BuildOp:
    """Deserialize one operation dictionary into a typed BuildOp."""
    op_type = data.get("op")
    if op_type not in OP_CLASSES:
        raise ValueError(f"Unknown op type: {op_type!r}")
    kwargs = {k: v for k, v in data.items() if k != "op"}
    return OP_CLASSES[op_type](**kwargs)


def op_to_dict(op: BuildOp) -> Dict[str, Any]:
    """Serialize one BuildOp into a JSON-friendly dictionary."""
    result = {"op": type(op).__name__}
    result.update(op.__dict__)
    return result


def load_ops(path: str) -> List[BuildOp]:
    import json
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "ops" in data:
        data = data["ops"]
    if not isinstance(data, list):
        raise ValueError("Recipe JSON must be a list of ops or an object with an 'ops' list.")
    return [op_from_dict(item) for item in data]


def save_ops(path: str, ops: Iterable[BuildOp]) -> None:
    import json
    payload = {"ops": [op_to_dict(op) for op in ops]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
