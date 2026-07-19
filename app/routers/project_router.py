from fastapi import APIRouter,Depends
from app.services.project_service import ProjectService
from app.core.dependencies import get_project_service,RoleChecker
from app.schemas.token_data import LongTokenData
from app.schemas.project import ProjectInput,ProjectResponse,AssignProjectManagerInput,ProjectStatusInput,ProjectTeamInput,ProjectListResponse,DashboardStatsResponse
from app.core.enum import Role

router=APIRouter(prefix="/project_service",tags=["PROJECT"])

@router.post("/create_project",response_model=ProjectResponse)
async def create_new_project(
    project_title:ProjectInput,
    project_manager:ProjectService=Depends(get_project_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))
):
    result= await project_manager.create_project(
        workspace_id=user_data.workspace_id,
        admin_id=user_data.user_id,
        project_title=project_title.project_title
    )
    return result

@router.post("/assign_manager",response_model=ProjectResponse)
async def assign_manager_to_project(
    data:AssignProjectManagerInput,
    project_manager:ProjectService=Depends(get_project_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))   
):
    result=await project_manager.assign_project_manager(
        workspace_id=user_data.workspace_id,
        admin_id=user_data.user_id,
        manager_id=data.manager_id,
        project_id=data.project_id
    )
    return result

@router.post("/update_project_status",response_model=ProjectResponse)
async def project_status(
    data:ProjectStatusInput,
    project_manager:ProjectService=Depends(get_project_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result= await project_manager.update_project_status(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        project_id=data.project_id,
        status=data.status
    )
    return result

@router.post("/add_team",response_model=ProjectResponse)
async def add_team_id_to_project(
    data:ProjectTeamInput,
    project_manager:ProjectService=Depends(get_project_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result=await project_manager.add_team_to_project(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        project_id=data.project_id,
        team_id=data.team_id
    )
    return result

@router.post("/remove_team",response_model=ProjectResponse)
async def remove_team_id_to_project(
    data:ProjectTeamInput,
    project_manager:ProjectService=Depends(get_project_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result= await project_manager.remove_team_from_project(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        project_id=data.project_id,
        team_id=data.team_id
    )
    return result

@router.get("/list_projects",response_model=list[ProjectListResponse])
async def get_all_projects(
    project_manager:ProjectService=Depends(get_project_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result= await project_manager.list_projects(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id
    )
    return result

@router.get("/dashboard_stats",response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    project_manager:ProjectService=Depends(get_project_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result= await project_manager.get_dashboard_stats(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id
    )
    return result