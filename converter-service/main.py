
def clean_cpp(code):
    if not code:
        return code

    import re

    code = re.sub(r"\bstd::(?=[A-Za-z_])", "", code)

    if "using namespace std;" not in code:
        lines = code.splitlines()
        pos = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("#include"):
                pos = i + 1
        lines.insert(pos, "using namespace std;")
        code = "\n".join(lines)

    return code

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from converter import PythonToCppConverter, ConversionError

app = FastAPI(title="AST Conversion Service")


class ConversionRequest(BaseModel):
    sourceCode: str = Field(min_length=1, max_length=10000)
    stdin: str = Field(default="", max_length=4000)


@app.get("/health")
def health():
    return {"status": "running"}


@app.post("/convert")
def convert(request: ConversionRequest):
    try:
        converter = PythonToCppConverter()
        code = converter.convert(request.sourceCode)

        return {
            "success": True,
            "convertedCode": code,
            "method": "ast-based"
        }

    except ConversionError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "message": str(error),
                "errorCode": error.code
            }
        )


@app.post("/dual-validate")
def dual_validate(request: ConversionRequest):
    from dual_validator import validate_dual_conversion

    try:
        result = validate_dual_conversion(request.sourceCode, request.stdin)

        return {
            "success": result["validated"],
            "validated": result["validated"],
            "convertedCode": clean_cpp(result.get("ollama_cpp") if result.get("method") == "ollama-fallback" else result.get("ast_cpp")),
            "method": result.get("method"),
            "ollamaCode": result.get("ollama_cpp"),
            "pythonOutput": result.get("python_output"),
            "astOutput": result.get("ast_output"),
            "ollamaOutput": result.get("ollama_output"),
            "error": result.get("error"),
            "failedConverter": result.get("failed_converter")
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
