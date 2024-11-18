from fastapi import FastAPI
from routers import user, rating
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    docs_url="/api/docs/",
    redoc_url="/api/redoc/",
    title="Volunteer API v2",
    version="1.0.0",
    description="This is the API for Volunteer Application",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://172.16.11.247:8777",
        "http://172.16.12.126:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(rating.router, prefix="/api/rating", tags=["rating"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8777)
