from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional
from app.core.enum import SprintStatus

class SprintInput(BaseModel):
    sprint_name:str
    sprint_start_date:datetime
    sprint_end_date:datetime
    project_id:str

class SprintStatusInput(BaseModel):
    project_id:str
    sprint_id:str
    status:SprintStatus

class SprintResponse(BaseModel):
    sprint_id:str
    sprint_name:str
    sprint_start_date:datetime
    sprint_end_date:datetime
    project_id:str
    status:Optional[str]=Field(default=SprintStatus.PLANNED.value)