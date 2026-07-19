from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional
from app.core.enum import TaskStatus

class TaskInput(BaseModel):
    task_name:str
    description:str
    project_id:str
    priority:str
    due_date:datetime

class SprintIdActionInput(BaseModel):
    project_id:str
    sprint_id:str
    task_id:str

class TaskStatusInput(BaseModel):
    project_id:str
    task_id:str
    status:TaskStatus

class MemberTaskInput(BaseModel):
    project_id:str
    task_id:str
    member_id:str

class SelfTaskInput(BaseModel):
    project_id:str
    task_id:str

class AssignMemberInput(BaseModel):
    project_id:str
    task_id:str
    member_id:str

class SprintTaskQuery(BaseModel):
    sprint_id:str

class TaskAssignee(BaseModel):
    user_id: str
    username:str

class SprintTaskResponse(BaseModel):
    task_id:str
    title:str
    status:str
    priority:str
    assignee:Optional[TaskAssignee]=None

class TaskResponse(BaseModel):
    task_id:str
    task_name:str
    created_at:datetime
    created_by:str
    project_id:str
    sprint_id:Optional[str]=None
    assignee_id: Optional[str]=None
    due_date:datetime
    status:str=Field(default=TaskStatus.TODO.value)

class TaskListQuery(BaseModel):
    search:Optional[str]=None
    project_id:Optional[str]=None
    assignee_id:Optional[str]=None
    status:Optional[TaskStatus]=None
    priority:Optional[str]=None
    page:int=1
    page_size:int=10
    mine_or_unassigned:bool=False

class TaskListItem(BaseModel):
    task_id:str
    task_name:str
    status:str
    priority:str
    project_id:str
    sprint_id:Optional[str]=None
    due_date:datetime
    assignee:Optional[TaskAssignee]=None

class TaskDetailResponse(BaseModel):
    task_id:str
    task_name:str
    description:str
    status:str
    priority:str
    project_id:str
    sprint_id:Optional[str]=None
    due_date:datetime
    created_by:str
    created_at:datetime
    assignee:Optional[str]=None

class TaskListResponse(BaseModel):
    tasks:list[TaskListItem]
    total_count:int
    page:int
    total_pages:int