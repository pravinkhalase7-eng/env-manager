from __future__ import annotations

import re
from pathlib import Path

COMPOSE_NAMES = ("docker-compose.yml", "docker-compose.yaml", "compose.yml")
PORT_RE = re.compile(r"""["'](?:\$\{[^:]+:-(\d+)\}|(\d+)):(\d+)["']""")
HOST_RE = re.compile(
    r"(?:PUBLIC_HOST|PUBLIC_APP_URL|APP_URL|NGINX_SERVER_NAME)\s*=\s*(\S+)",
    re.I,
)
SERVER_RE = re.compile(r"server_name\s+([^;]+);")
DEFAULT_SERVER_RE = re.compile(r"listen\s+[^\n]*default_server", re.I)


def _skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & {"node_modules", ".git", ".venv", "dist", ".next", "Pods"})


def scan_folder(folder: Path) -> dict:
    compose_ports: list[int] = []
    env_hosts: list[str] = []
    vhosts: list[str] = []
    default_server = False
    compose_files: list[str] = []

    if not folder.is_dir():
        return {
            "exists": False,
            "compose_ports": [],
            "env_hosts": [],
            "vhosts": [],
            "default_server": False,
            "compose_files": [],
        }

    for name in COMPOSE_NAMES:
        path = folder / name
        if path.exists():
            compose_files.append(name)
            text = path.read_text(errors="ignore")
            for match in PORT_RE.finditer(text):
                host = match.group(1) or match.group(2)
                if host:
                    compose_ports.append(int(host))

    for path in folder.rglob("*"):
        if _skip(path) or not path.is_file():
            continue
        if path.name.endswith(".env.example") or path.name.endswith(".env.sample"):
            text = path.read_text(errors="ignore")
            for match in HOST_RE.finditer(text):
                raw = match.group(1).strip().strip("\"'")
                raw = raw.split("://")[-1].split("/")[0].split(":")[0]
                if raw:
                    env_hosts.append(raw)
        if path.suffix == ".conf":
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            if DEFAULT_SERVER_RE.search(text) and re.search(r"server_name\s+[^;]*\s_", text):
                default_server = True
            for match in SERVER_RE.finditer(text):
                for token in match.group(1).split():
                    token = token.strip()
                    if token and token != "_":
                        vhosts.append(token)

    def uniq(items: list) -> list:
        seen = []
        for item in items:
            if item not in seen:
                seen.append(item)
        return seen

    return {
        "exists": True,
        "compose_ports": uniq(compose_ports),
        "env_hosts": uniq(env_hosts),
        "vhosts": uniq(vhosts),
        "default_server": default_server,
        "compose_files": compose_files,
    }


def scan_workspace(workspace: Path, apps: list[dict]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for app in apps:
        folder = workspace / str(app.get("folder") or app.get("id"))
        found[app["id"]] = scan_folder(folder)
    return found
