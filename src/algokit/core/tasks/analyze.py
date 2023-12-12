from typing import Optional

from pydantic import BaseModel, Field


class TealerBlock(BaseModel):
    short: str
    blocks: list[list[str]]


class TealerExecutionPath(BaseModel):
    data_type: str = Field(alias="type")
    count: int
    description: str
    check: str
    impact: str
    confidence: str
    data_help: str = Field(alias="help")
    paths: list[TealerBlock]


class TealerAnalysisReport(BaseModel):
    success: bool
    data_error: Optional[str] = Field(alias="error")
    result: list[TealerExecutionPath]


# Usage
# data = json.loads(json_string)
# root = Root(**data)
