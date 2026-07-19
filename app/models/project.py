from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional
from app.core.enum import ProjectStatus

class Project(BaseModel):
    project_title:str
    created_at:datetime
    workspace_id:str
    project_manager_id:Optional[str]=Field(default=None)
    team_ids:list[str]=Field(default_factory=list)
    sprint_ids:list[str]=Field(default_factory=list)
    status:ProjectStatus=Field(default=ProjectStatus.PLANNED.value)