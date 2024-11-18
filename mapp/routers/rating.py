from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from database.database import UserAdvancements

router = APIRouter()
security = HTTPBasic()
user_advancements = UserAdvancements()


@router.patch("/rate")
def rate_user(
    username: str,
    rate: float = Query(..., ge=0, le=5),
    comment: str = Query(None),
    credentials: HTTPBasicCredentials = Depends(security),
):
    user_data = user_advancements.search_user_by_username(credentials.username)

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user_advancements.rate_user(credentials.username, username, rate, comment)

    return {"message": "User rated successfully"}

@router.get("/get_avg_rating")
def get_avg_rating(
    username: str,
    # credentials: HTTPBasicCredentials = Depends(security),
):
    user_data = user_advancements.search_user_by_username(username)

    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    avg_rating = user_advancements.get_avg_rating(username)

    return {"avg_rating": avg_rating}

