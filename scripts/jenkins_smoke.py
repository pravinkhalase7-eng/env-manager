from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import build_state


def main() -> None:
    state = build_state()
    titles = [app["id"] for app in state["apps"]]
    assert "doc-vault" in titles, titles
    assert "ai-coder" in titles, titles
    assert "unknown host" in state["nginx"]
    assert "docvault.doxstation.com" in state["nginx"]
    print("env-manager smoke ok")


if __name__ == "__main__":
    main()
