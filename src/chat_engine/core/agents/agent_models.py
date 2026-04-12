from dataclasses import dataclass
from typing import List


@dataclass
class AgentContext:
    authenticated: bool = False
    username: str = None
    selected_vehicle: int | None = None
    selected_location: str = None
    preferences: List[str] = None
