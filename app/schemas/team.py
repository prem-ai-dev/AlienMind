from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional
from app.core.enum import TeamStatus

class TeamInput(BaseModel):
    team_name:str

class TeamDeleteInput(BaseModel):
    team_id:str

class TeamMemberInput(BaseModel):
    team_id:str
    member_id:str

class TeamResponse(BaseModel):
    team_id:str
    team_name:str
    team_manager_id:Optional[str]=Field(default="Not Yet assigned")
    created_at:datetime
    member_ids:list[str]=Field(default_factory=list)
    status:str=Field(default=TeamStatus.ACTIVE.value)

class TeamListResponse(BaseModel):
    team_id:str
    name:str

class TeamMemberDetail(BaseModel):
    user_id:str
    username:str
    pending_count:int
    in_progress_count:int

class TeamDetailListResponse(BaseModel):
    team_id:str
    team_name:str
    team_manager_id:Optional[str]=None
    team_manager_name:Optional[str]=None
    member_count:int
    members:list[TeamMemberDetail]=Field(default_factory=list)
    pending_count:int
    in_progress_count:int
    completed_count:int