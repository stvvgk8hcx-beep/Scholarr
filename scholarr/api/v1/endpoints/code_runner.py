"""Code execution endpoint for note editor code blocks."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from scholarr.core.security import verify_api_key
from scholarr.services.code_runner_service import run_code

router = APIRouter()


class RunCodeRequest(BaseModel):
    language: str = Field(..., pattern="^(python|javascript|bash)$")
    code: str = Field(..., max_length=50000)


class RunCodeResponse(BaseModel):
    success: bool
    output: str
    error: bool
    exit_code: int | None = None


@router.post("/run", response_model=RunCodeResponse)
async def execute_code(
    body: RunCodeRequest,
    api_key: str = Depends(verify_api_key),
):
    """Execute a code snippet and return the output."""
    result = await run_code(body.language, body.code)
    return result
