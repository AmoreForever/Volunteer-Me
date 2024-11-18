import os
from typing import Tuple, List

from database.database import UserRole, UserProfile, UserManager, UserAdvancements
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse

router = APIRouter()
security = HTTPBasic()
user_advancements = UserAdvancements()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    username: str = Query(..., min_length=3),
    name: str = Query(...),
    surname: str = Query(...),
    password: str = Query(..., min_length=8),
    email: str = Query(None),
    role: int = Query(1),
    specializations: List[str] = Query(None),
    skills: List[str] = Query(None),
):

    user_advancements.create_user(
        username,
        name,
        surname,
        UserRole(role),
        password,
        email,
        specializations,
        skills,
    )

    return {"message": "User registered successfully"}


@router.post("/login")
def login_user(credentials: HTTPBasicCredentials = Depends(security)):
    user_data = user_advancements.search_user_by_username(credentials.username)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return {"role": user_data["role"], "token": user_data["data"]["token"]}


@router.get("/profile")
def get_user_profile(credentials: HTTPBasicCredentials = Depends(security)):
    user_data = user_advancements.search_user_by_username(credentials.username)

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user_data["data"]


@router.patch("/follow")
def follow_user(
    username: str,
    credentials: HTTPBasicCredentials = Depends(security),
):
    user_data = user_advancements.search_user_by_username(credentials.username)

    if user_data["role"] == UserRole.ORGANIZER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organizers cannot follow other users",
        )

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # user_manager = UserManager(credentials.username, user_data["role"])
    user_advancements.follow_user_(credentials.username, username)

    return {"message": "User followed successfully"}

@router.delete("/unfollow")
def unfollow_user(
    username: str,
    credentials: HTTPBasicCredentials = Depends(security),
):
    user_data = user_advancements.search_user_by_username(credentials.username)

    if user_data["role"] == UserRole.ORGANIZER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organizers cannot unfollow other users",
        )

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user_advancements.unfollow_user_(credentials.username, username)

    return {"message": "User unfollowed successfully"}

@router.get("/followers")
def get_followers(
    credentials: HTTPBasicCredentials = Depends(security),
):
    user_data = user_advancements.search_user_by_username(credentials.username)

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    followers = user_advancements.get_followers(credentials.username)

    return {"followers": followers}

@router.get("/following")
def get_following(
    credentials: HTTPBasicCredentials = Depends(security),
):
    user_data = user_advancements.search_user_by_username(credentials.username)

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    following = user_advancements.get_following(credentials.username)

    return {"following": following}

