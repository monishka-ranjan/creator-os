from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.workspaces.router import router as workspaces_router

app = FastAPI(title="CreatorOS API", version="0.1.0")

app.include_router(auth_router)
app.include_router(workspaces_router)


@app.get("/health")
async def health():
    return {"status": "ok"}