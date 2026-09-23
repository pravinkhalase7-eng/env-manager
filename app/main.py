from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import yaml

from app import GENERATED_DIR, REGISTRY_PATH, ROOT, load_registry, save_registry
from app.conflicts import find_conflicts
from app.nginx_gen import render_edge_nginx, write_generated
from app.scan import scan_workspace

TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))
STATIC = ROOT / "static"

app = FastAPI(title="Env Manager")
if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


def build_state() -> dict:
    registry = load_registry()
    workspace = Path(registry.get("workspace") or ROOT.parent)
    scans = scan_workspace(workspace, registry.get("apps") or [])
    conflicts = find_conflicts(registry, scans)
    nginx = render_edge_nginx(registry)
    write_generated(registry, GENERATED_DIR)
    rows = []
    for item in registry.get("apps") or []:
        rows.append({**item, "scan": scans.get(item["id"]) or {}})
    return {
        "registry": registry,
        "workspace": str(workspace),
        "apps": rows,
        "conflicts": conflicts,
        "error_count": sum(1 for c in conflicts if c["level"] == "error"),
        "warn_count": sum(1 for c in conflicts if c["level"] == "warn"),
        "nginx": nginx,
        "yaml_text": REGISTRY_PATH.read_text(),
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return TEMPLATES.TemplateResponse(request, "index.html", {"state": build_state()})


@app.get("/api/state")
async def api_state():
    return build_state()


@app.get("/nginx.conf", response_class=PlainTextResponse)
async def nginx_conf():
    return render_edge_nginx(load_registry())


class RegistryBody(BaseModel):
    yaml_text: str


@app.post("/api/registry")
async def replace_registry(body: RegistryBody):
    parsed = yaml.safe_load(body.yaml_text)
    if not isinstance(parsed, dict) or "apps" not in parsed:
        return {"ok": False, "error": "YAML must include an apps list"}
    save_registry(parsed)
    return {"ok": True}


@app.post("/rescan")
async def rescan():
    build_state()
    return RedirectResponse("/", status_code=303)
