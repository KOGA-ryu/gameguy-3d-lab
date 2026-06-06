#!/usr/bin/env python3
"""Serve a local recipe stack workbench for ASCII-to-Blender recipes.

This is a human control surface for procedural script generation:

recipe ops -> parameter UI -> validation/ASCII compile -> Blender Python script

It intentionally keeps the recipe JSON as the source of truth. The browser does
not maintain a second geometry model.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = Path("/tmp/gameguy_recipe_stack_workbench_v0")
EXAMPLES_DIR = ROOT / "ascii_blender_dryrun_v0" / "examples"
DEFAULT_RECIPE = EXAMPLES_DIR / "petal_scroll_column_ornament_recipe_v0.json"
MAX_POST_BYTES = 80 * 1024 * 1024


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Recipe Stack Workbench</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f4f1;
      --panel: #e8e7e2;
      --panel2: #deddd7;
      --ink: #202322;
      --muted: #666b68;
      --line: #c1c0b9;
      --accent: #2d6568;
      --accent2: #8a5f1e;
      --bad: #9b3428;
      --good: #2f6b3f;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 12px/1.35 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    button, input, select, textarea { font: inherit; color: var(--ink); }
    .app {
      height: 100%;
      min-width: 920px;
      display: grid;
      grid-template-rows: 40px minmax(0, 1fr) 150px;
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-bottom: 1px solid var(--line);
      background: #fafaf7;
    }
    .toolbar .grow { flex: 1; min-width: 0; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .work {
      min-height: 0;
      display: grid;
      grid-template-columns: 250px minmax(0, 1fr) 360px;
    }
    .pane {
      min-height: 0;
      overflow: auto;
      border-right: 1px solid var(--line);
      background: var(--panel);
    }
    .pane:last-child { border-right: 0; }
    .pane-head {
      height: 30px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 0 10px;
      border-bottom: 1px solid var(--line);
      background: var(--panel2);
      font-weight: 650;
    }
    .stack-list { padding: 8px; display: grid; gap: 4px; }
    .op-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      align-items: center;
      min-height: 30px;
      border: 1px solid transparent;
      padding: 4px 7px;
      background: transparent;
      cursor: pointer;
    }
    .op-row.active { border-color: #2d6568; background: #f8f8f4; }
    .op-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .op-type { color: var(--muted); font-size: 11px; }
    .preview {
      min-height: 0;
      display: grid;
      grid-template-rows: 32px minmax(0, 1fr);
      background: #f9f9f5;
    }
    .tabs {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 4px 8px;
      border-bottom: 1px solid var(--line);
      background: #efeee9;
    }
    button, select {
      min-height: 28px;
      border: 1px solid #b9b8b0;
      background: #fbfbf7;
      padding: 3px 8px;
      border-radius: 4px;
      cursor: pointer;
    }
    button.primary { border-color: #1f5558; background: var(--accent); color: #fff; }
    button.danger { border-color: #8c2e24; color: var(--bad); }
    button.active { border-color: #2d6568; background: #dfeceb; }
    button:disabled { opacity: .5; cursor: default; }
    select { max-width: 100%; }
    .preview-body {
      min-height: 0;
      margin: 0;
      padding: 10px;
      overflow: auto;
      font: 11px/1.05 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      white-space: pre;
      background: #f9f9f5;
    }
    .inspector {
      min-height: 0;
      display: grid;
      grid-template-rows: 30px auto;
      background: var(--panel);
    }
    .controls { padding: 8px; display: grid; gap: 8px; }
    .control {
      display: grid;
      grid-template-columns: 132px minmax(0, 1fr) 74px;
      gap: 6px;
      align-items: center;
    }
    .control label {
      color: var(--muted);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    input[type="number"], input[type="text"] {
      width: 100%;
      min-width: 0;
      height: 26px;
      border: 1px solid #bdbcb4;
      border-radius: 4px;
      background: #fbfbf7;
      padding: 2px 6px;
    }
    input[type="range"] { width: 100%; min-width: 0; }
    input[type="checkbox"] { width: 16px; height: 16px; }
    .jsonbox {
      width: 100%;
      min-height: 180px;
      resize: vertical;
      border: 1px solid #bdbcb4;
      border-radius: 4px;
      background: #fbfbf7;
      padding: 6px;
      font: 11px/1.25 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .bottom {
      min-height: 0;
      display: grid;
      grid-template-columns: 1fr 1fr;
      border-top: 1px solid var(--line);
      background: var(--panel2);
    }
    .bottom pre {
      margin: 0;
      padding: 8px 10px;
      overflow: auto;
      border-right: 1px solid var(--line);
      white-space: pre-wrap;
      font: 11px/1.3 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .status-ok { color: var(--good); }
    .status-bad { color: var(--bad); }
  </style>
</head>
<body>
  <div class="app">
    <div class="toolbar">
      <select id="recipeSelect" title="Load example recipe"></select>
      <button id="loadRecipe">Load</button>
      <select id="moduleSelect" title="Append module"></select>
      <button id="addModule">Add</button>
      <button id="dupOp">Duplicate</button>
      <button id="delOp" class="danger">Delete</button>
      <button id="compile" class="primary">Compile ASCII</button>
      <button id="save">Save</button>
      <div id="pathReadout" class="grow"></div>
    </div>
    <div class="work">
      <section class="pane">
        <div class="pane-head"><span>Stack</span><span id="opCount"></span></div>
        <div id="stackList" class="stack-list"></div>
      </section>
      <section class="preview">
        <div class="tabs">
          <button data-tab="front" class="active">Front</button>
          <button data-tab="side">Side</button>
          <button data-tab="top">Top</button>
          <button data-tab="script">Script</button>
          <button data-tab="json">JSON</button>
        </div>
        <pre id="previewBody" class="preview-body"></pre>
      </section>
      <section class="inspector">
        <div class="pane-head"><span>Parameters</span><span id="selectedOp"></span></div>
        <div id="controls" class="controls"></div>
      </section>
    </div>
    <div class="bottom">
      <pre id="validation"></pre>
      <pre id="log"></pre>
    </div>
  </div>
  <script>
    const state = {
      recipe: {ops: []},
      recipePath: "",
      sessionPath: "",
      examples: [],
      modules: [],
      selected: 0,
      tab: "front",
      previews: {front: "", side: "", top: "", script: "", json: ""},
      validation: null,
      log: ""
    };

    const els = {
      recipeSelect: document.getElementById("recipeSelect"),
      loadRecipe: document.getElementById("loadRecipe"),
      moduleSelect: document.getElementById("moduleSelect"),
      addModule: document.getElementById("addModule"),
      dupOp: document.getElementById("dupOp"),
      delOp: document.getElementById("delOp"),
      compile: document.getElementById("compile"),
      save: document.getElementById("save"),
      pathReadout: document.getElementById("pathReadout"),
      stackList: document.getElementById("stackList"),
      opCount: document.getElementById("opCount"),
      selectedOp: document.getElementById("selectedOp"),
      controls: document.getElementById("controls"),
      previewBody: document.getElementById("previewBody"),
      validation: document.getElementById("validation"),
      log: document.getElementById("log")
    };

    async function api(path, body = null) {
      const opts = body ? {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)} : {};
      const res = await fetch(path, opts);
      const text = await res.text();
      let data;
      try { data = JSON.parse(text); } catch { data = {ok: false, error: text}; }
      if (!res.ok || data.ok === false) throw new Error(data.error || text);
      return data;
    }

    function clone(value) {
      return JSON.parse(JSON.stringify(value));
    }

    function titleForPath(path) {
      return path.split("/").pop().replace("_recipe_v0.json", "").replaceAll("_", " ");
    }

    function opLabel(op, index) {
      return op.name || op.target || `${op.op}_${index + 1}`;
    }

    function renderSelectors() {
      els.recipeSelect.innerHTML = state.examples.map(path => `<option value="${path}">${titleForPath(path)}</option>`).join("");
      els.recipeSelect.value = state.recipePath;
      els.moduleSelect.innerHTML = state.modules.map((item, i) => `<option value="${i}">${item.label}</option>`).join("");
    }

    function renderStack() {
      const ops = state.recipe.ops || [];
      els.opCount.textContent = `${ops.length}`;
      els.stackList.innerHTML = "";
      ops.forEach((op, index) => {
        const row = document.createElement("div");
        row.className = `op-row${index === state.selected ? " active" : ""}`;
        row.innerHTML = `<div class="op-name" title="${opLabel(op, index)}">${opLabel(op, index)}</div><div class="op-type">${op.op}</div>`;
        row.addEventListener("click", () => {
          state.selected = index;
          render();
        });
        els.stackList.appendChild(row);
      });
      els.delOp.disabled = ops.length < 2;
      els.dupOp.disabled = ops.length < 1;
    }

    function numericMeta(value) {
      const abs = Math.abs(Number(value) || 1);
      const max = Math.max(1, abs * 3);
      const min = value < 0 ? -max : 0;
      const step = Number.isInteger(value) ? 1 : 0.01;
      return {min, max, step};
    }

    function flattenControls(value, base = "") {
      const rows = [];
      if (!value || typeof value !== "object") return rows;
      for (const [key, child] of Object.entries(value)) {
        if (key === "op") continue;
        const pointer = `${base}/${key}`;
        if (child === null) continue;
        if (typeof child === "number" || typeof child === "string" || typeof child === "boolean") {
          rows.push({pointer, key, value: child, type: typeof child});
        } else if (Array.isArray(child)) {
          child.forEach((item, index) => {
            if (item && typeof item === "object") rows.push(...flattenControls(item, `${pointer}/${index}`));
          });
        } else {
          rows.push(...flattenControls(child, pointer));
        }
      }
      return rows;
    }

    function getPointer(root, pointer) {
      return pointer.split("/").slice(1).reduce((obj, key) => obj?.[key], root);
    }

    function setPointer(root, pointer, value) {
      const parts = pointer.split("/").slice(1);
      let obj = root;
      while (parts.length > 1) obj = obj[parts.shift()];
      obj[parts[0]] = value;
    }

    function renderControls() {
      const op = (state.recipe.ops || [])[state.selected];
      els.controls.innerHTML = "";
      els.selectedOp.textContent = op ? op.op : "";
      if (!op) return;
      for (const row of flattenControls(op)) {
        const wrap = document.createElement("div");
        wrap.className = "control";
        const label = row.pointer.replace(/^\/?/, "").replaceAll("/", ".");
        if (row.type === "number") {
          const meta = numericMeta(row.value);
          wrap.innerHTML = `<label title="${label}">${label}</label><input type="range" min="${meta.min}" max="${meta.max}" step="${meta.step}"><input type="number" step="${meta.step}">`;
          const range = wrap.children[1];
          const number = wrap.children[2];
          range.value = row.value;
          number.value = row.value;
          const update = raw => {
            const parsed = Number(raw);
            if (Number.isFinite(parsed)) {
              setPointer(op, row.pointer, parsed);
              range.value = parsed;
              number.value = parsed;
              syncJsonPreview();
            }
          };
          range.addEventListener("input", () => update(range.value));
          number.addEventListener("change", () => update(number.value));
        } else if (row.type === "boolean") {
          wrap.style.gridTemplateColumns = "132px 1fr";
          wrap.innerHTML = `<label title="${label}">${label}</label><input type="checkbox">`;
          const input = wrap.children[1];
          input.checked = Boolean(row.value);
          input.addEventListener("change", () => {
            setPointer(op, row.pointer, input.checked);
            syncJsonPreview();
          });
        } else {
          wrap.style.gridTemplateColumns = "132px minmax(0, 1fr)";
          wrap.innerHTML = `<label title="${label}">${label}</label><input type="text">`;
          const input = wrap.children[1];
          input.value = String(row.value);
          input.addEventListener("change", () => {
            setPointer(op, row.pointer, input.value);
            renderStack();
            syncJsonPreview();
          });
        }
        els.controls.appendChild(wrap);
      }
      const box = document.createElement("textarea");
      box.className = "jsonbox";
      box.value = JSON.stringify(op, null, 2);
      box.addEventListener("change", () => {
        try {
          state.recipe.ops[state.selected] = JSON.parse(box.value);
          render();
        } catch (err) {
          state.log = `Bad op JSON: ${err.message}`;
          renderLog();
        }
      });
      els.controls.appendChild(box);
    }

    function renderPreview() {
      if (state.tab === "json") {
        els.previewBody.textContent = JSON.stringify(state.recipe, null, 2);
      } else {
        els.previewBody.textContent = state.previews[state.tab] || "";
      }
      document.querySelectorAll(".tabs button").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tab === state.tab);
      });
    }

    function renderLog() {
      const report = state.validation;
      if (!report) {
        els.validation.textContent = "No validation run yet.";
        els.validation.className = "";
      } else {
        els.validation.className = report.ok ? "status-ok" : "status-bad";
        els.validation.textContent = JSON.stringify(report, null, 2);
      }
      els.log.textContent = state.log || "";
    }

    function syncJsonPreview() {
      state.previews.json = JSON.stringify(state.recipe, null, 2);
      renderPreview();
    }

    function render() {
      els.pathReadout.textContent = `${state.recipePath || "unsaved"} -> ${state.sessionPath || ""}`;
      renderSelectors();
      renderStack();
      renderControls();
      syncJsonPreview();
      renderLog();
    }

    async function loadInitial() {
      const data = await api("/api/state");
      Object.assign(state, data);
      render();
    }

    document.querySelectorAll(".tabs button").forEach(btn => {
      btn.addEventListener("click", () => {
        state.tab = btn.dataset.tab;
        renderPreview();
      });
    });

    els.loadRecipe.addEventListener("click", async () => {
      const data = await api("/api/load", {path: els.recipeSelect.value});
      Object.assign(state, data);
      state.selected = 0;
      render();
    });

    els.addModule.addEventListener("click", () => {
      const module = state.modules[Number(els.moduleSelect.value)];
      if (!module) return;
      state.recipe.ops.push(clone(module.op));
      state.selected = state.recipe.ops.length - 1;
      render();
    });

    els.dupOp.addEventListener("click", () => {
      const op = state.recipe.ops[state.selected];
      if (!op) return;
      const next = clone(op);
      if (next.name) next.name = `${next.name}.copy`;
      state.recipe.ops.splice(state.selected + 1, 0, next);
      state.selected += 1;
      render();
    });

    els.delOp.addEventListener("click", () => {
      if (state.recipe.ops.length < 2) return;
      state.recipe.ops.splice(state.selected, 1);
      state.selected = Math.max(0, Math.min(state.selected, state.recipe.ops.length - 1));
      render();
    });

    els.compile.addEventListener("click", async () => {
      els.compile.disabled = true;
      try {
        const data = await api("/api/compile", {recipe: state.recipe});
        state.sessionPath = data.sessionPath;
        state.previews = data.previews;
        state.validation = data.validation;
        state.log = data.log;
        if (!["front", "side", "top", "script", "json"].includes(state.tab)) state.tab = "front";
        render();
      } catch (err) {
        state.log = err.message;
        renderLog();
      } finally {
        els.compile.disabled = false;
      }
    });

    els.save.addEventListener("click", async () => {
      const data = await api("/api/save", {recipe: state.recipe});
      state.recipePath = data.recipePath;
      state.sessionPath = data.sessionPath;
      state.log = `Saved ${data.recipePath}`;
      render();
    });

    loadInitial().catch(err => {
      state.log = err.message;
      renderLog();
    });
  </script>
</body>
</html>
"""


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    try:
      data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
      fail(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
      fail(f"malformed JSON {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
      fail(f"{path} must contain a JSON object")
    return data


def normalize_recipe(data: dict[str, Any]) -> dict[str, Any]:
    ops = data.get("ops")
    if not isinstance(ops, list) or not ops:
        fail("recipe.ops must be a non-empty list")
    for index, op in enumerate(ops):
        if not isinstance(op, dict):
            fail(f"recipe.ops[{index}] must be an object")
        op_type = op.get("op")
        if not isinstance(op_type, str) or not op_type:
            fail(f"recipe.ops[{index}].op must be a non-empty string")
    return {"ops": ops}


def recipe_paths() -> list[str]:
    return [str(path) for path in sorted(EXAMPLES_DIR.glob("*_recipe_v0.json"))]


def module_library() -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for path in sorted(EXAMPLES_DIR.glob("*_recipe_v0.json")):
        recipe = normalize_recipe(load_json(path))
        for index, op in enumerate(recipe["ops"]):
            name = op.get("name") or op.get("target") or f"{op.get('op', 'op')}_{index + 1}"
            modules.append(
                {
                    "label": f"{path.stem.replace('_recipe_v0', '')}: {name}",
                    "source_path": str(path),
                    "op": op,
                }
            )
    return modules


def session_recipe_path(out_root: Path) -> Path:
    return out_root / "active_recipe.json"


def write_recipe(out_root: Path, recipe: dict[str, Any]) -> Path:
    out_root.mkdir(parents=True, exist_ok=True)
    path = session_recipe_path(out_root)
    path.write_text(json.dumps(normalize_recipe(recipe), indent=2) + "\n", encoding="utf-8")
    return path


def compile_recipe(recipe: dict[str, Any], out_root: Path, width: int = 96, height: int = 72) -> dict[str, Any]:
    recipe_path = write_recipe(out_root, recipe)
    compile_out = out_root / "compiled"
    if compile_out.exists():
        shutil.rmtree(compile_out)
    compile_out.mkdir(parents=True)
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    dryrun_path = str(ROOT / "ascii_blender_dryrun_v0")
    env["PYTHONPATH"] = dryrun_path if not existing else f"{dryrun_path}{os.pathsep}{existing}"
    cmd = [
        sys.executable,
        "-m",
        "ascii_blender_dryrun.cli",
        "--recipe",
        str(recipe_path),
        "--out",
        str(compile_out),
        "--width",
        str(width),
        "--height",
        str(height),
    ]
    result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    previews = {
        "front": read_text_if_exists(compile_out / "doric_front_preview.txt"),
        "side": read_text_if_exists(compile_out / "doric_side_preview.txt"),
        "top": read_text_if_exists(compile_out / "doric_top_preview.txt"),
        "script": read_text_if_exists(compile_out / "build_doric_column_v0.py"),
        "json": json.dumps(recipe, indent=2),
    }
    validation = load_json(compile_out / "validation_report.json") if (compile_out / "validation_report.json").exists() else {"ok": False}
    return {
        "sessionPath": str(out_root),
        "recipePath": str(recipe_path),
        "previews": previews,
        "validation": validation,
        "log": "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part),
        "returncode": result.returncode,
    }


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


class RecipeStackHandler(BaseHTTPRequestHandler):
    server: "RecipeStackServer"

    def log_message(self, fmt: str, *args: Any) -> None:
        if self.server.quiet:
            return
        super().log_message(fmt, *args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_text(HTML, "text/html; charset=utf-8")
            return
        if parsed.path == "/api/state":
            recipe = normalize_recipe(load_json(self.server.recipe_path))
            self.send_json(
                {
                    "ok": True,
                    "recipe": recipe,
                    "recipePath": str(self.server.recipe_path),
                    "sessionPath": str(self.server.out_root),
                    "examples": recipe_paths(),
                    "modules": module_library(),
                    "previews": {"front": "", "side": "", "top": "", "script": "", "json": json.dumps(recipe, indent=2)},
                    "validation": None,
                    "log": "",
                }
            )
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json_body()
            if parsed.path == "/api/load":
                path = Path(str(payload.get("path", ""))).resolve()
                if not path.is_file() or EXAMPLES_DIR.resolve() not in path.parents:
                    self.send_json({"ok": False, "error": "recipe path must be an example recipe"}, HTTPStatus.BAD_REQUEST)
                    return
                self.server.recipe_path = path
                recipe = normalize_recipe(load_json(path))
                self.send_json(
                    {
                        "ok": True,
                        "recipe": recipe,
                        "recipePath": str(path),
                        "sessionPath": str(self.server.out_root),
                        "examples": recipe_paths(),
                        "modules": module_library(),
                        "previews": {"front": "", "side": "", "top": "", "script": "", "json": json.dumps(recipe, indent=2)},
                        "validation": None,
                        "log": "",
                    }
                )
                return
            if parsed.path == "/api/save":
                path = write_recipe(self.server.out_root, self.require_recipe(payload))
                self.send_json({"ok": True, "recipePath": str(path), "sessionPath": str(self.server.out_root)})
                return
            if parsed.path == "/api/compile":
                result = compile_recipe(self.require_recipe(payload), self.server.out_root)
                result["ok"] = True
                self.send_json(result)
                return
        except SystemExit as exc:
            self.send_json({"ok": False, "error": f"request failed: {exc}"}, HTTPStatus.BAD_REQUEST)
            return
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def require_recipe(self, payload: dict[str, Any]) -> dict[str, Any]:
        recipe = payload.get("recipe")
        if not isinstance(recipe, dict):
            fail("request.recipe must be an object")
        return normalize_recipe(recipe)

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_POST_BYTES:
            fail("request body too large")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            fail("request body must be a JSON object")
        return data

    def send_text(self, text: str, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class RecipeStackServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler: type[RecipeStackHandler], recipe_path: Path, out_root: Path, quiet: bool) -> None:
        super().__init__(server_address, handler)
        self.recipe_path = recipe_path
        self.out_root = out_root
        self.quiet = quiet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the local recipe stack workbench.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--recipe", type=Path, default=DEFAULT_RECIPE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    recipe_path = args.recipe.resolve()
    if not recipe_path.exists():
        fail(f"missing recipe: {recipe_path}")
    normalize_recipe(load_json(recipe_path))
    args.out.mkdir(parents=True, exist_ok=True)
    if args.validate_only:
        print(f"PASS recipe stack workbench validation: recipe={recipe_path} out={args.out}")
        return 0
    server = RecipeStackServer((args.host, args.port), RecipeStackHandler, recipe_path, args.out, args.quiet)
    url = f"http://{args.host}:{server.server_port}"
    print(f"Recipe stack workbench: {url}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
