from fastapi import APIRouter,Depends
from app.core.dependencies import get_team_service,RoleChecker
from app.core.enum import Role
from app.services.team_service import TeamService
from app.schemas.team import TeamInput,TeamResponse,TeamMemberInput,TeamDeleteInput,TeamListResponse,TeamDetailListResponse
from app.schemas.token_data import LongTokenData

router=APIRouter(prefix="/team_service",tags=["TEAM"])

@router.post("/create_team",response_model=TeamResponse)
async def create_new_team(
    team_name:TeamInput,
    team_manager:TeamService=Depends(get_team_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))
):
    result= await team_manager.create_team(
        workspace_id=user_data.workspace_id,
        admin_id=user_data.user_id,
        team_name=team_name.team_name
    )
    return result

@router.post("/assign_team_member",response_model=TeamResponse)
async def assign_member_to_team(
    data:TeamMemberInput,
    team_manager:TeamService=Depends(get_team_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result= await team_manager.insert_team_member(
        workspace_id=user_data.workspace_id,
        team_id=data.team_id,
        team_manager_id=user_data.user_id,
        member_id=data.member_id
    )
    return result

@router.post("/remove_member_from_team")
async def team_member_remove(
    data:TeamMemberInput,
    team_manager:TeamService=Depends(get_team_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result =await team_manager.remove_team_member(
        workspace_id=user_data.workspace_id,
        team_id=data.team_id,
        team_manager_id=user_data.user_id,
        member_id=data.member_id
    )
    return result

@router.post("/assign_manager_to_team",response_model=TeamResponse)
async def assign_team_manager(
    data:TeamMemberInput,
    team_manager:TeamService=Depends(get_team_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))
):
    result=await team_manager.assign_team_manager(
        workspace_id=user_data.workspace_id,
        admin_id=user_data.user_id,
        team_id=data.team_id,
        team_manager_id=data.member_id
    )
    return result

@router.delete("/remove_team")
async def delete_full_team(
    data:TeamDeleteInput,
    team_manager:TeamService=Depends(get_team_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))
):
    await team_manager.delete_team(
        workspace_id=user_data.workspace_id,
        admin_id=user_data.user_id,
        team_id=data.team_id
    )
    return {"status":"Removed successfuly"}

@router.get("/list_teams",response_model=list[TeamListResponse])
async def get_all_teams(
    team_manager:TeamService=Depends(get_team_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result= await team_manager.list_teams(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id
    )
    return result

@router.get("/list_teams_detailed",response_model=list[TeamDetailListResponse])
async def get_teams_detailed(
    team_manager:TeamService=Depends(get_team_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result= await team_manager.get_team_detail_list(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id
    )
    return result