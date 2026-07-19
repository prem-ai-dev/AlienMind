from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional
from app.core.enum import TeamStatus

class Team(BaseModel):

    team_name:str
    team_manager_id: Optional[str]=Field(default=None)
    created_at:datetime
    workspace_id:str
    member_ids:list[str]=Field(default_factory=list)
    project_ids:list[str]=Field(default_factory=list)
    status:TeamStatus=Field(default=TeamStatus.ACTIVE.value)