from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth_routes, plan_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Fitness Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://fitness-ai-agent-bice.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(plan_routes.router)


@app.get("/health")
def health():
    return {"status": "ok"}
