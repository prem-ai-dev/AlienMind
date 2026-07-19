from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional
from app.core.enum import TaskStatus

class Task(BaseModel):
    task_name:str
    description:str
    created_by:str
    created_at:datetime
    workspace_id:str
    project_id:str
    sprint_id:Optional[str]=None
    assignee_id: Optional[str]=None
    priority:str
    due_date:datetime
    status:TaskStatus=Field(default=TaskStatus.TODO.value)