#!/usr/bin/env python3
"""Serve a local pattern segment selection studio.

This is a source-authoring helper:

pattern segment JSON -> browser selection/color editor -> deterministic recipe JSON

It does not create mesh, run Blender, or write generated outputs into the repo.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATTERN_FIELD_OUT = Path("/tmp/gameguy_pattern_field_v0")
DEFAULT_PATTERN_SEGMENT_OUT = Path("/tmp/gameguy_pattern_segments_v0")
DEFAULT_SEGMENT_SET = DEFAULT_PATTERN_SEGMENT_OUT / "segment_sets" / "hex_rosette_pattern_segments_v0.json"
DEFAULT_SELECTION_OUT = (
    Path("/tmp/gameguy_pattern_selection_studio_v0")
    / "selection_recipes"
    / "hex_rosette_user_selection_v0.json"
)
SELECTION_SCHEMA = "pattern_selection_recipe_v0"
MAX_POST_BYTES = 80 * 1024 * 1024


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pattern Selection Studio</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f5ef;
      --panel: #efebe1;
      --panel2: #e5dfd2;
      --ink: #1f2524;
      --muted: #66706b;
      --line: #b7afa1;
      --selected: #151817;
      --accent: #2f6f72;
      --danger: #b7402c;
      --focus: #d4982d;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.35 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    button, input, select {
      font: inherit;
      color: var(--ink);
    }
    .app {
      height: 100%;
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      min-width: 760px;
    }
    aside {
      background: var(--panel);
      border-right: 1px solid #d2cabc;
      padding: 14px;
      overflow: auto;
    }
    main {
      min-width: 0;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
    }
    .topbar {
      display: flex;
      align-items: center;
      gap: 10px;
      min-height: 48px;
      padding: 8px 12px;
      border-bottom: 1px solid #d2cabc;
      background: #fbfaf6;
    }
    .title {
      font-weight: 700;
      white-space: nowrap;
    }
    .stats {
      color: var(--muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .stage {
      position: relative;
      overflow: hidden;
      background: #fbfaf6;
    }
    svg {
      display: block;
      width: 100%;
      height: 100%;
      background: #fbfaf6;
      cursor: crosshair;
    }
    .sheet { fill: none; stroke: #c2baad; stroke-width: 1.3; vector-effect: non-scaling-stroke; }
    .segment {
      stroke: var(--line);
      stroke-width: .7;
      opacity: .22;
      vector-effect: non-scaling-stroke;
      cursor: pointer;
    }
    .segment.visible { opacity: .44; }
    .segment.selected {
      stroke: var(--selected);
      stroke-width: 1.8;
      opacity: .92;
    }
    .segment.omit {
      stroke-dasharray: 5 3;
      opacity: .2;
    }
    .intersection {
      fill: var(--danger);
      opacity: .55;
      pointer-events: none;
    }
    .marquee {
      fill: rgba(47, 111, 114, .12);
      stroke: var(--accent);
      stroke-width: 1.2;
      vector-effect: non-scaling-stroke;
      pointer-events: none;
    }
    .stack { display: grid; gap: 12px; }
    .group {
      display: grid;
      gap: 8px;
      padding-bottom: 12px;
      border-bottom: 1px solid #d7d0c2;
    }
    .group:last-child { border-bottom: 0; }
    label {
      display: grid;
      gap: 4px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 650;
      text-transform: uppercase;
    }
    input[type="text"], input[type="number"], select {
      width: 100%;
      height: 34px;
      border: 1px solid #c9c0b2;
      background: #fbfaf6;
      border-radius: 6px;
      padding: 6px 8px;
    }
    input[type="color"] {
      width: 100%;
      height: 34px;
      border: 1px solid #c9c0b2;
      background: #fbfaf6;
      border-radius: 6px;
      padding: 3px;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .btnrow {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    button {
      height: 34px;
      border: 1px solid #bdb4a6;
      background: #fbfaf6;
      border-radius: 6px;
      padding: 0 10px;
      cursor: pointer;
    }
    button.primary {
      border-color: #245b5e;
      background: var(--accent);
      color: #fff;
    }
    button.warn {
      border-color: #8c3829;
      color: #8c3829;
    }
    button:focus-visible, input:focus-visible, select:focus-visible {
      outline: 2px solid var(--focus);
      outline-offset: 1px;
    }
    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--ink);
      font-size: 13px;
      font-weight: 500;
      text-transform: none;
    }
    .check input { width: 16px; height: 16px; }
    .readout {
      min-height: 84px;
      padding: 8px;
      background: var(--panel2);
      border: 1px solid #d1c8ba;
      border-radius: 6px;
      font: 12px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }
    .swatches {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 6px;
    }
    .swatch {
      height: 24px;
      border-radius: 5px;
      border: 1px solid rgba(0,0,0,.25);
      padding: 0;
    }
    .toast {
      position: absolute;
      left: 14px;
      bottom: 14px;
      max-width: min(560px, calc(100% - 28px));
      padding: 9px 11px;
      border-radius: 6px;
      background: rgba(31, 37, 36, .92);
      color: #fff;
      opacity: 0;
      transform: translateY(8px);
      transition: opacity .16s ease, transform .16s ease;
      pointer-events: none;
    }
    .toast.show {
      opacity: 1;
      transform: translateY(0);
    }
    @media (max-width: 900px) {
      .app { grid-template-columns: 280px minmax(0, 1fr); min-width: 700px; }
      aside { padding: 10px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="stack">
        <div class="group">
          <div class="title">Pattern Selection Studio</div>
          <div class="readout" id="selectionReadout">Loading...</div>
        </div>
        <div class="group">
          <label>Filter
            <input id="filterInput" type="text" placeholder="tag or segment id" />
          </label>
          <div class="row">
            <label>Role
              <select id="roleSelect">
                <option value="keep">keep</option>
                <option value="guide">guide</option>
                <option value="omit">omit</option>
                <option value="rib">rib</option>
                <option value="tracery">tracery</option>
                <option value="ornament">ornament</option>
                <option value="cutline">cutline</option>
              </select>
            </label>
            <label>Width
              <input id="widthInput" type="number" min="0.2" max="8" step="0.1" value="2" />
            </label>
          </div>
          <label>Color
            <input id="colorInput" type="color" value="#151817" />
          </label>
          <div class="swatches">
            <button class="swatch" data-color="#151817" style="background:#151817" title="black"></button>
            <button class="swatch" data-color="#b7402c" style="background:#b7402c" title="red"></button>
            <button class="swatch" data-color="#2f6f72" style="background:#2f6f72" title="teal"></button>
            <button class="swatch" data-color="#c6972e" style="background:#c6972e" title="gold"></button>
            <button class="swatch" data-color="#315a99" style="background:#315a99" title="blue"></button>
            <button class="swatch" data-color="#8a4b8f" style="background:#8a4b8f" title="violet"></button>
          </div>
          <label class="check"><input id="boxMode" type="checkbox" /> Box select</label>
          <label class="check"><input id="showSelectedOnly" type="checkbox" /> Selected only</label>
          <label class="check"><input id="showIntersections" type="checkbox" /> Intersections</label>
        </div>
        <div class="group">
          <div class="btnrow">
            <button id="selectVisibleBtn">Select visible</button>
            <button id="clearVisibleBtn">Clear visible</button>
            <button id="clearAllBtn" class="warn">Clear all</button>
          </div>
          <div class="btnrow">
            <button id="saveBtn" class="primary">Save</button>
            <button id="loadBtn">Load</button>
            <button id="downloadBtn">Download</button>
          </div>
        </div>
        <div class="group">
          <label>Segment
            <div class="readout" id="segmentReadout">None</div>
          </label>
        </div>
      </div>
    </aside>
    <main>
      <div class="topbar">
        <div class="title" id="sourceTitle">Loading</div>
        <div class="stats" id="statsText"></div>
      </div>
      <div class="stage" id="stage">
        <svg id="svg" viewBox="0 0 1100 1100" role="img" aria-label="pattern segment editor">
          <rect class="sheet" x="70" y="70" width="960" height="960"></rect>
          <g id="segmentsLayer"></g>
          <g id="intersectionsLayer"></g>
          <rect id="marquee" class="marquee" hidden x="0" y="0" width="0" height="0"></rect>
        </svg>
        <div class="toast" id="toast"></div>
      </div>
    </main>
  </div>
  <script>
    const state = {
      graph: null,
      segmentById: new Map(),
      lineById: new Map(),
      selected: new Map(),
      visibleIds: new Set(),
      lastSegmentId: null,
      viewSize: 1100,
      margin: 70,
      scale: 1,
      drag: null,
      savePath: null
    };

    const els = {
      svg: document.getElementById("svg"),
      segmentsLayer: document.getElementById("segmentsLayer"),
      intersectionsLayer: document.getElementById("intersectionsLayer"),
      marquee: document.getElementById("marquee"),
      filterInput: document.getElementById("filterInput"),
      roleSelect: document.getElementById("roleSelect"),
      widthInput: document.getElementById("widthInput"),
      colorInput: document.getElementById("colorInput"),
      boxMode: document.getElementById("boxMode"),
      showSelectedOnly: document.getElementById("showSelectedOnly"),
      showIntersections: document.getElementById("showIntersections"),
      selectionReadout: document.getElementById("selectionReadout"),
      segmentReadout: document.getElementById("segmentReadout"),
      sourceTitle: document.getElementById("sourceTitle"),
      statsText: document.getElementById("statsText"),
      toast: document.getElementById("toast")
    };

    function toast(message) {
      els.toast.textContent = message;
      els.toast.classList.add("show");
      clearTimeout(toast.timer);
      toast.timer = setTimeout(() => els.toast.classList.remove("show"), 1800);
    }

    function api(path, options) {
      return fetch(path, options).then(async response => {
        const text = await response.text();
        if (!response.ok) throw new Error(text || response.statusText);
        return text ? JSON.parse(text) : null;
      });
    }

    function sx(x) {
      return state.margin + x * state.scale;
    }

    function sy(y) {
      return state.margin + (state.graph.bounds_m.height - y) * state.scale;
    }

    function svgPoint(evt) {
      const pt = els.svg.createSVGPoint();
      pt.x = evt.clientX;
      pt.y = evt.clientY;
      return pt.matrixTransform(els.svg.getScreenCTM().inverse());
    }

    function currentStyle() {
      return {
        role: els.roleSelect.value,
        stroke: els.colorInput.value,
        stroke_width: Number(els.widthInput.value || 2)
      };
    }

    function segmentMatches(segment, filter) {
      if (!filter) return true;
      const text = filter.toLowerCase();
      if (segment.segment_id.toLowerCase().includes(text)) return true;
      if (segment.source_edge_id.toLowerCase().includes(text)) return true;
      return segment.tags.some(tag => tag.toLowerCase().includes(text));
    }

    function applyLineStyle(segmentId) {
      const line = state.lineById.get(segmentId);
      if (!line) return;
      const style = state.selected.get(segmentId);
      line.classList.toggle("selected", Boolean(style));
      line.classList.toggle("omit", style && style.role === "omit");
      if (style) {
        line.style.stroke = style.stroke;
        line.style.strokeWidth = String(style.stroke_width);
      } else {
        line.style.stroke = "";
        line.style.strokeWidth = "";
      }
    }

    function updateReadout() {
      const roles = {};
      for (const style of state.selected.values()) {
        roles[style.role] = (roles[style.role] || 0) + 1;
      }
      const roleText = Object.keys(roles).sort().map(role => `${role}:${roles[role]}`).join(" ");
      els.selectionReadout.textContent =
        `selected ${state.selected.size}\nvisible ${state.visibleIds.size}\n${roleText || "none"}\n${state.savePath || ""}`;
    }

    function showSegment(segmentId) {
      state.lastSegmentId = segmentId;
      const segment = state.segmentById.get(segmentId);
      if (!segment) {
        els.segmentReadout.textContent = "None";
        return;
      }
      els.segmentReadout.textContent = [
        segment.segment_id,
        `source ${segment.source_edge_id}`,
        `type ${segment.source_edge_type}`,
        `len ${segment.length_m}`,
        segment.tags.join("\n")
      ].join("\n");
    }

    function setSelected(segmentId, style) {
      if (style) state.selected.set(segmentId, {...style});
      else state.selected.delete(segmentId);
      applyLineStyle(segmentId);
    }

    function toggleSegment(segmentId, forceStyle) {
      const style = forceStyle || currentStyle();
      if (state.selected.has(segmentId) && !forceStyle) setSelected(segmentId, null);
      else setSelected(segmentId, style);
      showSegment(segmentId);
      updateReadout();
      applyFilters();
    }

    function applyFilters() {
      const filter = els.filterInput.value.trim();
      const selectedOnly = els.showSelectedOnly.checked;
      state.visibleIds.clear();
      for (const segment of state.graph.segments) {
        const visible = segmentMatches(segment, filter) && (!selectedOnly || state.selected.has(segment.segment_id));
        const line = state.lineById.get(segment.segment_id);
        if (line) {
          line.style.display = visible ? "" : "none";
          line.classList.toggle("visible", visible);
        }
        if (visible) state.visibleIds.add(segment.segment_id);
      }
      els.intersectionsLayer.style.display = els.showIntersections.checked ? "" : "none";
      updateReadout();
    }

    function renderSegments() {
      const bounds = state.graph.bounds_m;
      state.scale = Math.min((state.viewSize - state.margin * 2) / bounds.width, (state.viewSize - state.margin * 2) / bounds.height);
      const sheet = document.querySelector(".sheet");
      sheet.setAttribute("width", (bounds.width * state.scale).toFixed(3));
      sheet.setAttribute("height", (bounds.height * state.scale).toFixed(3));
      const frag = document.createDocumentFragment();
      for (const segment of state.graph.segments) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", sx(segment.start_xy_m[0]).toFixed(3));
        line.setAttribute("y1", sy(segment.start_xy_m[1]).toFixed(3));
        line.setAttribute("x2", sx(segment.end_xy_m[0]).toFixed(3));
        line.setAttribute("y2", sy(segment.end_xy_m[1]).toFixed(3));
        line.setAttribute("class", "segment visible");
        line.dataset.segmentId = segment.segment_id;
        line.addEventListener("pointerdown", event => {
          if (els.boxMode.checked) return;
          event.stopPropagation();
          toggleSegment(segment.segment_id);
        });
        line.addEventListener("pointerenter", () => showSegment(segment.segment_id));
        state.lineById.set(segment.segment_id, line);
        frag.appendChild(line);
      }
      els.segmentsLayer.replaceChildren(frag);
    }

    function renderIntersections() {
      const frag = document.createDocumentFragment();
      for (const point of state.graph.intersections || []) {
        const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        c.setAttribute("cx", sx(point.xy_m[0]).toFixed(3));
        c.setAttribute("cy", sy(point.xy_m[1]).toFixed(3));
        c.setAttribute("r", "1.5");
        c.setAttribute("class", "intersection");
        frag.appendChild(c);
      }
      els.intersectionsLayer.replaceChildren(frag);
      els.intersectionsLayer.style.display = "none";
    }

    function selectionPayload() {
      const segmentStyles = {};
      for (const [segmentId, style] of state.selected) {
        segmentStyles[segmentId] = style;
      }
      return {
        schema: "pattern_selection_recipe_v0",
        selection_id: "hex_rosette_user_selection_v0",
        source_segment_set_id: state.graph.segment_set_id,
        source_field_id: state.graph.source_field_id,
        selected_segment_ids: Array.from(state.selected.keys()).sort(),
        segment_styles: segmentStyles,
        role_defaults: {
          keep: {stroke: "#151817", stroke_width: 2},
          guide: {stroke: "#b7afa1", stroke_width: 0.7},
          omit: {stroke: "#b7afa1", stroke_width: 0.7},
          rib: {stroke: "#315a99", stroke_width: 2.4},
          tracery: {stroke: "#151817", stroke_width: 2},
          ornament: {stroke: "#c6972e", stroke_width: 1.8},
          cutline: {stroke: "#b7402c", stroke_width: 1.5}
        }
      };
    }

    function loadSelection(recipe) {
      state.selected.clear();
      const styles = recipe.segment_styles || {};
      for (const segmentId of recipe.selected_segment_ids || []) {
        if (!state.segmentById.has(segmentId)) continue;
        const style = styles[segmentId] || {role: "keep", stroke: "#151817", stroke_width: 2};
        state.selected.set(segmentId, style);
      }
      for (const segmentId of state.lineById.keys()) applyLineStyle(segmentId);
      state.savePath = recipe.output_path || state.savePath;
      applyFilters();
      updateReadout();
    }

    function setVisible(style) {
      for (const segmentId of state.visibleIds) setSelected(segmentId, style);
      applyFilters();
      updateReadout();
    }

    function downloadSelection() {
      const blob = new Blob([JSON.stringify(selectionPayload(), null, 2) + "\n"], {type: "application/json"});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "hex_rosette_user_selection_v0.json";
      a.click();
      URL.revokeObjectURL(url);
    }

    function beginBoxSelect(event) {
      if (!els.boxMode.checked) return;
      const p = svgPoint(event);
      state.drag = {x0: p.x, y0: p.y, x1: p.x, y1: p.y};
      drawMarquee();
    }

    function updateBoxSelect(event) {
      if (!state.drag) return;
      const p = svgPoint(event);
      state.drag.x1 = p.x;
      state.drag.y1 = p.y;
      drawMarquee();
    }

    function endBoxSelect() {
      if (!state.drag) return;
      const box = normalizedBox(state.drag);
      state.drag = null;
      els.marquee.hidden = true;
      const style = currentStyle();
      for (const segmentId of state.visibleIds) {
        const line = state.lineById.get(segmentId);
        if (!line) continue;
        const x1 = Number(line.getAttribute("x1"));
        const y1 = Number(line.getAttribute("y1"));
        const x2 = Number(line.getAttribute("x2"));
        const y2 = Number(line.getAttribute("y2"));
        if (pointInBox(x1, y1, box) || pointInBox(x2, y2, box)) setSelected(segmentId, style);
      }
      applyFilters();
      updateReadout();
    }

    function pointInBox(x, y, box) {
      return x >= box.x && x <= box.x + box.w && y >= box.y && y <= box.y + box.h;
    }

    function normalizedBox(drag) {
      const x = Math.min(drag.x0, drag.x1);
      const y = Math.min(drag.y0, drag.y1);
      return {x, y, w: Math.abs(drag.x1 - drag.x0), h: Math.abs(drag.y1 - drag.y0)};
    }

    function drawMarquee() {
      const box = normalizedBox(state.drag);
      els.marquee.hidden = false;
      els.marquee.setAttribute("x", box.x);
      els.marquee.setAttribute("y", box.y);
      els.marquee.setAttribute("width", box.w);
      els.marquee.setAttribute("height", box.h);
    }

    async function init() {
      const graph = await api("/api/segment-set");
      state.graph = graph;
      for (const segment of graph.segments) state.segmentById.set(segment.segment_id, segment);
      els.sourceTitle.textContent = graph.segment_set_id;
      els.statsText.textContent = `segments ${graph.summary.segment_count} intersections ${graph.summary.intersection_point_count}`;
      renderSegments();
      renderIntersections();
      applyFilters();
      const recipe = await api("/api/selection");
      loadSelection(recipe);
      toast("Ready");
    }

    els.filterInput.addEventListener("input", applyFilters);
    els.showSelectedOnly.addEventListener("change", applyFilters);
    els.showIntersections.addEventListener("change", applyFilters);
    document.querySelectorAll(".swatch").forEach(button => {
      button.addEventListener("click", () => { els.colorInput.value = button.dataset.color; });
    });
    document.getElementById("selectVisibleBtn").addEventListener("click", () => setVisible(currentStyle()));
    document.getElementById("clearVisibleBtn").addEventListener("click", () => setVisible(null));
    document.getElementById("clearAllBtn").addEventListener("click", () => {
      state.selected.clear();
      for (const segmentId of state.lineById.keys()) applyLineStyle(segmentId);
      applyFilters();
      updateReadout();
    });
    document.getElementById("downloadBtn").addEventListener("click", downloadSelection);
    document.getElementById("loadBtn").addEventListener("click", async () => {
      loadSelection(await api("/api/selection"));
      toast("Loaded");
    });
    document.getElementById("saveBtn").addEventListener("click", async () => {
      const result = await api("/api/selection", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(selectionPayload())
      });
      state.savePath = result.output_path;
      updateReadout();
      toast("Saved");
    });
    els.svg.addEventListener("pointerdown", beginBoxSelect);
    els.svg.addEventListener("pointermove", updateBoxSelect);
    window.addEventListener("pointerup", endBoxSelect);

    init().catch(error => {
      console.error(error);
      els.selectionReadout.textContent = String(error);
      toast("Load failed");
    });
  </script>
</body>
</html>
"""


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    raise SystemExit(1)


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {repo_path(path)}")
    except json.JSONDecodeError as exc:
        fail(f"malformed JSON {repo_path(path)}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail(f"{repo_path(path)} must contain a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def ensure_default_segment_set(path: Path, *, compile_missing: bool) -> None:
    if path.exists():
        return
    if not compile_missing:
        fail(f"segment set does not exist: {path}")
    subprocess.run(
        [
            sys.executable,
            "scripts/compile_pattern_field_v0.py",
            "--clean",
            "--out",
            str(DEFAULT_PATTERN_FIELD_OUT),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/compile_pattern_segments_v0.py",
            "--clean",
            "--pattern-field-manifest",
            str(DEFAULT_PATTERN_FIELD_OUT / "manifest.json"),
            "--out",
            str(DEFAULT_PATTERN_SEGMENT_OUT),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if not path.exists():
        fail(f"compiler did not create expected segment set: {path}")


def validate_segment_graph(graph: dict[str, Any]) -> None:
    if graph.get("schema") != "gameguy_pattern_segment_graph_v0":
        fail("segment graph schema must be gameguy_pattern_segment_graph_v0")
    for key in ("segment_set_id", "source_field_id"):
        if not isinstance(graph.get(key), str) or not graph[key]:
            fail(f"segment graph requires non-empty {key}")
    bounds = graph.get("bounds_m")
    if not isinstance(bounds, dict) or not isinstance(bounds.get("width"), (int, float)) or not isinstance(bounds.get("height"), (int, float)):
        fail("segment graph requires numeric bounds_m width/height")
    segments = graph.get("segments")
    if not isinstance(segments, list) or not segments:
        fail("segment graph requires non-empty segments")
    seen: set[str] = set()
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            fail(f"segments[{index}] must be an object")
        segment_id = segment.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id:
            fail(f"segments[{index}].segment_id must be a non-empty string")
        if segment_id in seen:
            fail(f"duplicate segment_id: {segment_id}")
        seen.add(segment_id)
        for point_key in ("start_xy_m", "end_xy_m"):
            point = segment.get(point_key)
            if (
                not isinstance(point, list)
                or len(point) != 2
                or not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in point)
            ):
                fail(f"{segment_id}.{point_key} must be two numbers")
        if not isinstance(segment.get("tags"), list) or not all(isinstance(tag, str) for tag in segment["tags"]):
            fail(f"{segment_id}.tags must be a string list")


def segment_ids(graph: dict[str, Any]) -> set[str]:
    return {segment["segment_id"] for segment in graph["segments"]}


def default_selection_recipe(graph: dict[str, Any], segment_set_path: Path) -> dict[str, Any]:
    return {
        "schema": SELECTION_SCHEMA,
        "selection_id": "hex_rosette_user_selection_v0",
        "source_segment_set_id": graph["segment_set_id"],
        "source_field_id": graph["source_field_id"],
        "source_segment_set_path": str(segment_set_path),
        "selected_segment_ids": [],
        "segment_styles": {},
        "role_defaults": {
            "keep": {"stroke": "#151817", "stroke_width": 2.0},
            "guide": {"stroke": "#b7afa1", "stroke_width": 0.7},
            "omit": {"stroke": "#b7afa1", "stroke_width": 0.7},
            "rib": {"stroke": "#315a99", "stroke_width": 2.4},
            "tracery": {"stroke": "#151817", "stroke_width": 2.0},
            "ornament": {"stroke": "#c6972e", "stroke_width": 1.8},
            "cutline": {"stroke": "#b7402c", "stroke_width": 1.5},
        },
        "rules": {
            "manual_source_selection": True,
            "outer_rings_can_remain_guides": True,
            "does_not_modify_source_segment_graph": True,
            "generated_outputs_stay_under_tmp": True,
        },
    }


def validate_style(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    role = value.get("role", "keep")
    if not isinstance(role, str) or not role:
        fail(f"{field}.role must be a non-empty string")
    stroke = value.get("stroke", "#151817")
    if not isinstance(stroke, str) or not stroke:
        fail(f"{field}.stroke must be a non-empty string")
    stroke_width = value.get("stroke_width", 2.0)
    if not isinstance(stroke_width, (int, float)) or isinstance(stroke_width, bool) or stroke_width <= 0:
        fail(f"{field}.stroke_width must be a positive number")
    return {"role": role, "stroke": stroke, "stroke_width": round(float(stroke_width), 3)}


def normalize_selection_recipe(recipe: dict[str, Any], graph: dict[str, Any], segment_set_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    if recipe.get("schema") != SELECTION_SCHEMA:
        fail(f"selection recipe schema must be {SELECTION_SCHEMA}")
    selection_id = recipe.get("selection_id", "hex_rosette_user_selection_v0")
    if not isinstance(selection_id, str) or not selection_id:
        fail("selection_id must be a non-empty string")
    if recipe.get("source_segment_set_id") not in {None, graph["segment_set_id"]}:
        fail("source_segment_set_id must match loaded segment graph")
    ids = recipe.get("selected_segment_ids", [])
    if not isinstance(ids, list):
        fail("selected_segment_ids must be a list")
    known_ids = segment_ids(graph)
    normalized_ids: list[str] = []
    for index, segment_id in enumerate(ids):
        if not isinstance(segment_id, str) or not segment_id:
            fail(f"selected_segment_ids[{index}] must be a non-empty string")
        if segment_id not in known_ids:
            fail(f"selected_segment_ids[{index}] references unknown segment: {segment_id}")
        normalized_ids.append(segment_id)
    normalized_ids = sorted(set(normalized_ids))
    styles_source = recipe.get("segment_styles", {})
    if not isinstance(styles_source, dict):
        fail("segment_styles must be an object")
    styles: dict[str, Any] = {}
    for segment_id in normalized_ids:
        styles[segment_id] = validate_style(styles_source.get(segment_id, {"role": "keep"}), f"segment_styles.{segment_id}")
    normalized = default_selection_recipe(graph, segment_set_path)
    normalized.update(
        {
            "selection_id": selection_id,
            "selected_segment_ids": normalized_ids,
            "segment_styles": styles,
            "updated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
    )
    if output_path is not None:
        normalized["output_path"] = str(output_path)
    return normalized


class StudioState:
    def __init__(self, segment_set_path: Path, selection_out: Path, compile_missing: bool) -> None:
        self.segment_set_path = segment_set_path
        self.selection_out = selection_out
        self.compile_missing = compile_missing
        self._graph: dict[str, Any] | None = None

    def graph(self) -> dict[str, Any]:
        if self._graph is None:
            ensure_default_segment_set(self.segment_set_path, compile_missing=self.compile_missing)
            graph = load_json(self.segment_set_path)
            validate_segment_graph(graph)
            self._graph = graph
        return self._graph

    def selection(self) -> dict[str, Any]:
        graph = self.graph()
        if not self.selection_out.exists():
            return default_selection_recipe(graph, self.segment_set_path)
        recipe = load_json(self.selection_out)
        return normalize_selection_recipe(recipe, graph, self.segment_set_path, self.selection_out)

    def save_selection(self, recipe: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_selection_recipe(recipe, self.graph(), self.segment_set_path, self.selection_out)
        write_json(self.selection_out, normalized)
        return normalized


def json_bytes(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, indent=2) + "\n").encode("utf-8")


def make_handler(state: StudioState) -> type[BaseHTTPRequestHandler]:
    class PatternSelectionStudioHandler(BaseHTTPRequestHandler):
        server_version = "PatternSelectionStudio/0.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            print(f"{self.address_string()} - {fmt % args}")

        def send_bytes(self, body: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, data: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            self.send_bytes(json_bytes(data), "application/json; charset=utf-8", status)

        def send_error_text(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
            self.send_bytes((message + "\n").encode("utf-8"), "text/plain; charset=utf-8", status)

        def do_GET(self) -> None:
            route = urlparse(self.path).path
            try:
                if route in {"/", "/index.html"}:
                    self.send_bytes(HTML.encode("utf-8"), "text/html; charset=utf-8")
                elif route == "/api/status":
                    graph = state.graph()
                    self.send_json(
                        {
                            "schema": "pattern_selection_studio_status_v0",
                            "segment_set_id": graph["segment_set_id"],
                            "segment_count": graph["summary"]["segment_count"],
                            "selection_out": str(state.selection_out),
                        }
                    )
                elif route == "/api/segment-set":
                    self.send_json(state.graph())
                elif route == "/api/selection":
                    self.send_json(state.selection())
                else:
                    self.send_error_text("not found", HTTPStatus.NOT_FOUND)
            except SystemExit as exc:
                self.send_error_text(str(exc), HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # pragma: no cover - defensive server boundary.
                self.send_error_text(str(exc), HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_POST(self) -> None:
            route = urlparse(self.path).path
            if route != "/api/selection":
                self.send_error_text("not found", HTTPStatus.NOT_FOUND)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error_text("invalid Content-Length")
                return
            if length > MAX_POST_BYTES:
                self.send_error_text("payload too large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    self.send_error_text("selection payload must be an object")
                    return
                self.send_json(state.save_selection(payload))
            except json.JSONDecodeError as exc:
                self.send_error_text(f"malformed JSON: line {exc.lineno} column {exc.colno}: {exc.msg}")
            except SystemExit as exc:
                self.send_error_text(str(exc), HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # pragma: no cover - defensive server boundary.
                self.send_error_text(str(exc), HTTPStatus.INTERNAL_SERVER_ERROR)

    return PatternSelectionStudioHandler


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the local pattern selection studio.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--segment-set", type=Path, default=DEFAULT_SEGMENT_SET)
    parser.add_argument("--selection-out", type=Path, default=DEFAULT_SELECTION_OUT)
    parser.add_argument("--no-compile-missing", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    segment_set = args.segment_set if args.segment_set.is_absolute() else ROOT / args.segment_set
    selection_out = args.selection_out if args.selection_out.is_absolute() else ROOT / args.selection_out
    state = StudioState(segment_set, selection_out, compile_missing=not args.no_compile_missing)
    graph = state.graph()
    selection = normalize_selection_recipe(default_selection_recipe(graph, segment_set), graph, segment_set)
    if args.validate_only:
        print(
            "PASS pattern selection studio validation: "
            f"segment_set={graph['segment_set_id']} segments={graph['summary']['segment_count']} "
            f"default_selection={selection['selection_id']}"
        )
        return 0
    server = ThreadingHTTPServer((args.host, args.port), make_handler(state))
    url = f"http://{args.host}:{args.port}"
    print(f"Serving pattern selection studio at {url}")
    print(f"Selection output: {selection_out}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping pattern selection studio")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
