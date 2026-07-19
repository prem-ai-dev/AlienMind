from pydantic import BaseModel,Field,field_validator,ConfigDict
from datetime import datetime
from typing import Optional
from app.core.enum import WorkspaceMemberStatus
from typing import Literal
from app.core.enum import Role

class CreateAdminInput(BaseModel):
    email: str
    username: str
    password: Optional[str] = None  # required only when creating a brand-new user

class AdminInput(BaseModel):
    user_id:str

class UpdateRoleInput(BaseModel):
    member_id:str
    role:Literal[Role.MANAGER, Role.MEMBER]

class MemberSearchInput(BaseModel):
    username:Optional[str]=None
    role:Optional[str]=None

class WorkspaceMemberValidate(BaseModel):
    id:str=Field(alias="_id")
    user_id: str
    username:str
    workspace_id: str
    role: str
    team_ids:list[str]=Field(default_factory=list)
    joined_at: datetime
    status: WorkspaceMemberStatus = Field(default=WorkspaceMemberStatus.ACTIVE.value)

    model_config=ConfigDict(populate_by_name=True)

    @field_validator("id",mode="before")
    @classmethod
    def convert(cls,v):
        return str(v)

class WorkspaceMemberResponse(BaseModel):
    user_id:str
    username:str
    role:str
    joined_at:datetime
    status:str=Field(default=WorkspaceMemberStatus.ACTIVE.value)

    model_config=ConfigDict(from_attributes=True)

class MemberList(BaseModel):
    user_id:str
    username:str
    role:str
    joined_at:datetime

class MemberListResponse(BaseModel):
    members:list[MemberList]
    count:int