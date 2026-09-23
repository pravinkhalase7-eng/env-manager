from __future__ import annotations

from collections import defaultdict


def find_conflicts(registry: dict, scans: dict[str, dict]) -> list[dict]:
    conflicts: list[dict] = []
    apps = registry.get("apps") or []
    edge = registry.get("edge") or {}
    catch = (edge.get("catch_all") or "reject").lower()

    domain_owners: dict[str, list[str]] = defaultdict(list)
    port_owners: dict[int, list[str]] = defaultdict(list)
    public_binders: list[str] = []

    for app in apps:
        title = app.get("title") or app["id"]
        for domain in app.get("domains") or []:
            domain_owners[domain.lower()].append(title)
        for port in app.get("host_ports") or []:
            port_owners[int(port)].append(title)
        if app.get("bind_public_http"):
            public_binders.append(title)
        scan = scans.get(app["id"]) or {}
        if scan.get("default_server") and catch == "reject":
            conflicts.append(
                {
                    "level": "error",
                    "code": "DEFAULT_SERVER_CATCHALL",
                    "app": title,
                    "detail": (
                        f"{title} nginx uses default_server with server_name _. "
                        "Unknown hostnames (including other apps) will open this product."
                    ),
                }
            )

    for domain, owners in domain_owners.items():
        if len(owners) > 1:
            conflicts.append(
                {
                    "level": "error",
                    "code": "DOMAIN_COLLISION",
                    "app": ", ".join(owners),
                    "detail": f"{domain} is claimed by {', '.join(owners)}.",
                }
            )

    for port, owners in port_owners.items():
        unique = list(dict.fromkeys(owners))
        if port in {80, 443} and len(unique) > 1:
            conflicts.append(
                {
                    "level": "error",
                    "code": "EDGE_PORT_COLLISION",
                    "app": ", ".join(unique),
                    "detail": f"Host :{port} is claimed by {', '.join(unique)}. Only the edge nginx may bind it.",
                }
            )
        elif port not in {80, 443} and len(unique) > 1:
            conflicts.append(
                {
                    "level": "warn",
                    "code": "HOST_PORT_SHARED",
                    "app": ", ".join(unique),
                    "detail": f"Host :{port} is listed for {', '.join(unique)}.",
                }
            )

    if len(public_binders) > 1:
        conflicts.append(
            {
                "level": "error",
                "code": "MULTIPLE_EDGE_OWNERS",
                "app": ", ".join(public_binders),
                "detail": f"{', '.join(public_binders)} all want to bind public HTTP. Pick one edge owner.",
            }
        )

    claimed_domains = {d.lower() for app in apps for d in (app.get("domains") or [])}
    for app in apps:
        scan = scans.get(app["id"]) or {}
        extra = [h for h in (scan.get("vhosts") or []) if h.lower() not in claimed_domains and h != "__DOMAIN__"]
        if extra and app.get("bind_public_http"):
            conflicts.append(
                {
                    "level": "warn",
                    "code": "UNREGISTERED_VHOST",
                    "app": app.get("title") or app["id"],
                    "detail": f"Nginx also mentions {', '.join(extra)} — add them to the registry so they are not treated as catch-all.",
                }
            )

    return conflicts
