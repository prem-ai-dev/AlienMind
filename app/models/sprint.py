from pydantic import BaseModel,Field
from datetime import datetime
from app.core.enum import SprintStatus

class Sprint(BaseModel):
    sprint_name:str
    created_at:datetime
    workspace_id:str
    sprint_start_date:datetime
    sprint_end_date:datetime
    project_id:str
    status:SprintStatus=Field(default=SprintStatus.PLANNED.value)