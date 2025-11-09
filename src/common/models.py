from typing import Annotated
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    user_id: Annotated[int, Field(ge=1)]
    email: EmailStr
    first_name: Annotated[str, Field(min_length=1, max_length=50)]
    last_name: Annotated[str, Field(min_length=1, max_length=50)]
    assigned_role: Annotated[str, Field(min_length=1)]


class Role(BaseModel):
    role_id: Annotated[int, Field(ge=1)]
    role_name: Annotated[str, Field(min_length=2)]
    permissions: Annotated[list[str], Field(default_factory=list)]
