import uvicorn
from fastapi import FastAPI

app = FastAPI(
    title="GenAI-CreditEngine",
    description="Plataforma Multiagente de Hiperautomação e Concessão de Crédito",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
