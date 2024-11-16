from database import (
    VolunteerDatabase,
    OrganizerDatabase,
    search_user_by_token,
    Applications,
)
from fastapi import APIRouter, HTTPException, status as sf, Query
from typing import List
from datetime import datetime

router = APIRouter()


@router.post("/create_app")
def create_app(
    title: str = Query(...),
    description: str = Query(...),
    langitude: float = Query(...),
    longitude: float = Query(...),
    landmark: str = Query(...),
    skills: List[str] = Query(
        [], title="skills", description="List of skills required for the application"
    ),
    start_time: str = Query(...),
    end_time: str = Query(...),
    reward: bool = Query(...),
    token: str = Query(...),
):
    user = search_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=sf.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to create an application",
        )

    if user["role"] != "Organizer":
        raise HTTPException(
            status_code=sf.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to create an application",
        )

    app = Applications()
    app.create_application(
        {
            "id": app._get_last_id() + 1,
            "title": title,
            "description": description,
            "langitude": langitude,
            "longitude": longitude,
            "landmark": landmark,
            "created_at": datetime.now().isoformat(),
            "who_created": user["data"]["username"],
            "skills": skills,
            "start_time": start_time,
            "end_time": end_time,
            "reward": reward,
            "volunteers": [],
        }
    )
    return {"status": "success", "message": "Application created successfully"}


@router.get("/get_apps")
def get_apps():
    app = Applications()
    return app.get_applications()


@router.patch("/assign_volunteer")
def assign_volunteer(
    app_id: int = Query(...),
    token: str = Query(...),
):
    user = search_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=sf.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to assign a volunteer, invalid token",
        )

    if user["role"] == "Organizer":
        raise HTTPException(
            status_code=sf.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to assign a volunteer",
        )

    app = Applications()
    if status := app.assign_volunteer(app_id, user["data"]["username"]):
        return {"status": "success", "message": "Volunteer assigned successfully"}
    else:
        return {"status": "failed", "message": "Volunteer already assigned"}

@router.patch("/get_volunteers")
def get_volunteers(
    app_id: int = Query(...),
    token: str = Query(...),
):
    user = search_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=sf.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to get volunteers, invalid token",
        )

    if user["role"] != "Organizer":
        raise HTTPException(
            status_code=sf.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to get volunteers",
        )

    app = Applications()
    return app.get_volunteers(app_id)

@router.patch("/get_my_apps")
def get_my_apps(
    token: str = Query(...),
):
    user = search_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=sf.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to get your applications, invalid token",
        )

    app = Applications()
    return app.get_my_applications(user["data"]["username"])
