from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DashboardStatsResponse(BaseModel):
    totalMembers:int
    totalProjects:int
    pendingInvites:int
    adminSeatsUsed:int
    adminSeatsMax:int
    inProgressTasks:int
    reviewTasks:int
    completedTasks:int
    cancelledTasks:int
    activeSprints:list[dict]
    recentActivity:list=[]

class MemberTaskStats(BaseModel):
    todo:int
    inProgress:int
    inReview:int
    completed:int
    cancelled:int

class MyTeamMember(BaseModel):
    user_id:str
    username:str

class MyTeamInfo(BaseModel):
    team_name:str
    members:list[MyTeamMember]

class MemberDashboardStatsResponse(BaseModel):
    taskStats:MemberTaskStats
    overdueTasks:list[dict]
    upcomingTasks:list[dict]
    myTeam:Optional[MyTeamInfo]=None
    totalProjects:int

class ManagerTaskStats(BaseModel):
    todo:int
    inProgress:int
    inReview:int
    completed:int
    cancelled:int

class ManagerActiveSprint(BaseModel):
    sprint_id:str
    name:str
    progress:int
    due_date:datetime

class ManagerTeamSummary(BaseModel):
    team_id:str
    team_name:str
    member_count:int
    pending_count:int
    in_progress_count:int

class ManagerOverdueTask(BaseModel):
    task_id:str
    task_name:str
    due_date:datetime
    priority:str
    project_id:str

class ManagerDashboardStatsResponse(BaseModel):
    totalProjectsManaged:int
    totalTeamsManaged:int
    taskStats:ManagerTaskStats
    activeSprints:list[ManagerActiveSprint]
    myTeams:list[ManagerTeamSummary]
    overdueTasks:list[ManagerOverdueTask]
