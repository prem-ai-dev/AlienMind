from pydantic import BaseModel,Field,field_validator,ConfigDict
from datetime import datetime
from typing import Optional
from app.core.enum import ProjectStatus

class ProjectInput(BaseModel):
    project_title:str

class AssignProjectManagerInput(BaseModel):
    manager_id:str
    project_id:str

class ProjectStatusInput(BaseModel):
    project_id:str
    status:ProjectStatus

class ProjectTeamInput(BaseModel):
    project_id:str
    team_id:str

class ProjectResponse(BaseModel):
    project_id: str
    project_title: str
    created_at: datetime
    manager_id: Optional[str] = None
    status: Optional[str] = None
    team_ids:list[str]=Field(default_factory=list)

class ProjectTeamSummary(BaseModel):
    team_id:str
    name:str

class ProjectTasksSummary(BaseModel):
    todo:int
    in_progress:int
    completed:int

class ProjectSprintSummary(BaseModel):
    sprint_id:str
    name:str
    progress:int
    due_date:datetime
    status:str

class ProjectListResponse(BaseModel):
    project_id:str
    project_title:str
    status:str
    project_manager_id:Optional[str]=None
    project_manager_name:Optional[str]=None
    teams:list[ProjectTeamSummary]=Field(default_factory=list)
    task_count:int
    tasks_summary:ProjectTasksSummary
    sprints:list[ProjectSprintSummary]=Field(default_factory=list)

class DashboardStatsResponse(BaseModel):
    total_projects:int
    active_sprints:int
    total_tasks:int
    completion_pct:int