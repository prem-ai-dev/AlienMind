from pydantic import BaseModel, Field
from datetime import datetime
from app.core.enum import WorkspaceMemberStatus

class WorkspaceMember(BaseModel):
    user_id: str
    username:str
    workspace_id: str
    role: str
    team_ids:list[str]=Field(default_factory=list)
    joined_at: datetime
    status: WorkspaceMemberStatus = Field(default=WorkspaceMemberStatus.ACTIVE.value)