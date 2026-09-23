# Env Manager

Local map of every public hostname and host port under `cursor/`, so
`docvault.doxstation.com` cannot fall through to Byte.

## Why this exists

The VPS has **one** process on `:80/:443` (`aicoder-nginx`). If that nginx uses
`server_name _` as default, unknown (or not-yet-wired) hostnames open **Byte**.
This app is the source of truth: domain → app → upstream port, plus a generated
edge config whose catch-all is **404**, not an application.

## Run

```bash
cd /Users/pravinkhalase/Desktop/Pravin/cursor/env-manager
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run.sh
```

Open http://127.0.0.1:3050

## Rules

| Hostname | App | Upstream |
|---|---|---|
| `docvault.doxstation.com` | DocVault | `:8088` |
| `play.doxstation.com` | Byte | aicoder frontend |
| `doxstation.com` | AI Teacher | `:3000` / `:8000` |
| `shorts.doxstation.com` | Short Video Maker | `:3123` |

- Only **one** app may `bind_public_http`.
- Other apps publish a high port. Edge nginx proxies the hostname there.
- Unknown Host headers must **reject**, never proxy to Byte.

After editing the registry, copy `generated/edge-http.conf` into aicoder-nginx
(or rebuild that image) and keep the DocVault Jenkins job on **8088**.
