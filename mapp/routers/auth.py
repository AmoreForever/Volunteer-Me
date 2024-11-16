import os
from typing import Tuple, List

from database import VolunteerDatabase, OrganizerDatabase, search_user_by_token
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse

router = APIRouter()
security = HTTPBasic()


def get_current_username(
    credentials: HTTPBasicCredentials = Depends(security), role: str = "volunteer"
) -> Tuple[str, str]:

    if role == "volunteer":
        db = VolunteerDatabase(credentials.username)
        db.update_token()
    elif role == "organizer":
        db = OrganizerDatabase(credentials.username)
        db.update_token()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role specified",
        )

    if not db.verify_user(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error ",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username, (
        db.get_token() if db.verify_user(credentials.password) else None
    )


@router.get("/login/as/{role}")
def login(role: str, username: Tuple[str, str] = Depends(get_current_username)):
    return {
        "role": role,
        "username": username[0],
        "logged_in": True,
        "status": "success",
        "token": username[1],
    }


@router.get("/get_user/")
def get_user(token: str):
    user = dict(search_user_by_token(token))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


    return {
        "username": user['data']["username"],
        "role": user["role"],
        "password": 123,
        "token": user['data']["token"],
        "skills": user['data']["skills"],
        "pfp": "http://172.16.11.247:8777/api/auth/get_user_pfp/?token="
        + user['data']["token"],
    }


@router.get("/get_user_pfp/")
def get_user_pfp(token: str):
    user = search_user_by_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    file_path = os.path.join(
        "workify", "database", user["role"], user["data"]["username"], "_pfp.jpg"
    )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found",
        )

    return FileResponse(file_path, media_type="image/jpeg")


@router.patch("/update_user_pfp/")
async def update_user_pfp(token: str, file: UploadFile = File(...)):
    user = search_user_by_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    file_path = os.path.join(
        "workify", "database", user["role"], user["data"]["username"], "_pfp.jpg"
    )

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile picture: {e}",
        ) from e

    return {"status": "success", "message": "Profile picture updated successfully"}


@router.post("/set_skills/")
def set_skills(
    token: str,
    skills: List[str] = Query(
        [], title="skills", description="List of skills required for the application"
    ),
):
    user = search_user_by_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    db = VolunteerDatabase(user["data"]["username"])

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    db.set_skills(skills)

    return {"status": "success", "message": "Skills updated successfully"}


@router.get("/get_skills/")
def get_skills(token: str):
    user = search_user_by_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    db = VolunteerDatabase(user["data"]["username"])

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return {"skills": db.get_skills()}

 