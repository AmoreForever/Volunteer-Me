from fastapi import FastAPI
from routers import auth, application
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    docs_url="/api/docs/",
    redoc_url="/api/redoc/",
    title="Workify API v1",
    version="1.0.0",
    description="This is the API for Workify, a specialized application for managing work orders.",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Operations related to authentication",
        }
    ],
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

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(application.router, prefix="/api/app", tags=["app"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8777)
