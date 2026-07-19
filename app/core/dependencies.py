from fastapi import Depends
from app.services.workspace_service import WorkspaceService
from app.services.login_service import LoginService
from fastapi.security import OAuth2PasswordBearer
from app.core.auth import decode_token
from app.schemas.token_data import TempTokenData
from app.services.project_service import ProjectService
from app.schemas.token_data import LongTokenData
from app.services.sprint_service import SprintService
from app.services.task_service import TaskService
from app.services.team_service import TeamService
from app.services.workspace_member_service import WorkspaceMemberService
from app.services.signup_service import SignupService
from app.services.workspace_service import WorkspaceService
from app.services.dashboard.admin_dashboard_service import AdminDashboardService
from app.services.dashboard.member_dashboard_service import MemberDashboardService
from app.services.dashboard.manager_dashboard_service import ManagerDashboardService
from app.core.enum import ROLE_RANK
from app.core.exception import UnauthorizedEntryError,InvalidTokenError

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")

new_wrokspace_manager=WorkspaceService()
project_manager=ProjectService()
sprint_manager=SprintService()
task_manager=TaskService()
team_manager=TeamService()
workspace_member_manager=WorkspaceMemberService()
signup_manager = SignupService()
workspace_manager=WorkspaceService()
admin_dashboard_manager=AdminDashboardService()
member_dashboard_manager=MemberDashboardService()
manager_dashboard_manager=ManagerDashboardService()

def get_login_service():
    login_manager=LoginService()
    return login_manager

def get_create_workspace_service():
    return new_wrokspace_manager

def get_project_service():
     return project_manager

def get_sprint_service():
    return sprint_manager

def get_task_service():
    return task_manager

def get_team_service():
    return team_manager

def get_workspace_member_service():
    return workspace_member_manager

def get_signup_service():
    return signup_manager 

def get_workspace_service():
    return workspace_manager

def get_admin_dashboard_service():
    return admin_dashboard_manager

def get_member_dashboard_service():
    return member_dashboard_manager

def get_manager_dashboard_service():
    return manager_dashboard_manager

def get_temp_user_data(token:str=Depends(oauth2_scheme)):
    payload=decode_token(token=token)
        
    if payload is None:
        raise InvalidTokenError(f"invalid token or expire token")         
        
    return TempTokenData(**payload)

def get_long_user_data(token:str=Depends(oauth2_scheme)):
    payload=decode_token(token=token)
        
    if payload is None:
        raise InvalidTokenError(f"invalid token or expire token")         
        
    return LongTokenData(**payload)

class RoleChecker:
    def __init__(self,min_role:str):
        self.min_role=min_role
    
    def __call__(self,user_data:LongTokenData=Depends(get_long_user_data)):
        if ROLE_RANK[user_data.role] < ROLE_RANK[self.min_role]:
            raise UnauthorizedEntryError(f"user_id:{user_data.user_id} does not authorized role:{self.min_role} is required")
        
        return user_data