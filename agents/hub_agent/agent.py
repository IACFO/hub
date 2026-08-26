"""ADK entrypoint. `adk web` / `adk run hub_agent` load root_agent from here."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from hub.agent import root_agent

__all__ = ["root_agent"]
