# Architecture Test Fixtures

This folder holds tiny source-only fixtures for validators and unit tests.

Fixtures here are not generated proof maps and do not contain render, media, mesh, screenshot, or Blender output data. Keep them small, deterministic, and readable enough to inspect in code review.

Current fixture:

- `tiny_map_building_connector_fixture_v0.json`: seven hex cells, one building plug, one road plug, one connector/path segment, one connector asset reference, and one terrain height change.

Use these fixtures to test source validators before running compilers that write generated outputs.
