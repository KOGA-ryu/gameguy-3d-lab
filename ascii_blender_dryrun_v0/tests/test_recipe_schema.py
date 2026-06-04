import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "recipe_v0.schema.json"
RECIPE_PATHS = [
    ROOT / "examples" / "doric_column_recipe_v0.json",
    ROOT / "out" / "compiled_recipe.json",
]


def test_recipe_schema_is_valid():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_doric_recipes_match_schema():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    for path in RECIPE_PATHS:
        payload = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(payload), key=lambda error: error.json_path)
        assert not errors, [f"{path}: {error.json_path} {error.message}" for error in errors]
