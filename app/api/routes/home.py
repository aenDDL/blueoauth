from typing import Annotated, Any, Protocol

from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, Cookie, Depends
from pydantic import BaseModel

from app.services.tokens import InvalidTokenError

router = APIRouter(route_class=DishkaRoute)


class VerifyTokenFn(Protocol):
    def __call__(self, token: str) -> dict[str, Any]: ...


class Cookies(BaseModel):
    access_token: str


@inject
async def get_current_user_id(
    cookies: Annotated[Cookies, Cookie()],
    verify_token: FromDishka[VerifyTokenFn],
) -> str:
    data = verify_token(cookies.access_token)
    user_id = data.get("sub")
    if not user_id:
        msg = "Missing sub in claims."
        raise InvalidTokenError(msg)
    return user_id


@router.get("/home", name="home")
async def home(user_id: Annotated[str, Depends(get_current_user_id)]):
    return {"user_id": user_id}
