# This sholuld never change lightly.
# This is the OS contract.

from pydantic import BaseModel, Field # type: ignore
from typing import List, Dict, Any


class Step(BaseModel):
    tool: str = Field(..., description="Tool name, e.g. FileOps")
    action: str = Field(..., description="Action name")
    args: Dict[str, Any] = Field(default_factory=dict)
    risk: int = Field(..., ge=0, le=3)


class IntentIR(BaseModel):
    goal: str
    requires_confirmation: bool
    steps: List[Step]
