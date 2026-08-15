"""
Base class every agent inherits from.

WHY A BASE CLASS:
It forces every agent to have the same shape: a `run()` method that
takes structured input and returns structured output. This is what
lets the LangGraph Supervisor treat all agents interchangeably —
it doesn't need to know HOW the Verification Agent checks a PAN
number, only that calling `.run(input)` gives back an output dict.

INTERVIEW TALKING POINT:
"All agents share a common interface, which means the Supervisor
only depends on an abstraction, not on each agent's internals —
classic dependency inversion."
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    name: str = "base_agent"

    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Every agent takes a dict in, returns a dict out."""
        raise NotImplementedError
