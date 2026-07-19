from fastapi import APIRouter,Depends
from app.services.workspace_member_service import WorkspaceMemberService
from app.core.dependencies import get_workspace_member_service,RoleChecker
from app.schemas.workspace_member import (
    CreateAdminInput,
    WorkspaceMemberResponse,
    AdminInput,
    UpdateRoleInput,
    MemberListResponse,
    MemberSearchInput
)
from app.schemas.token_data import LongTokenData
from app.core.enum import Role
from app.services.dashboard.admin_dashboard_service import list_of_member

router=APIRouter(prefix="/workspace_member_service",tags=["WORKSPACE_MEMBER"])

@router.post("/create_new_admin", response_model=WorkspaceMemberResponse)
async def new_admin_creation(
    data: CreateAdminInput,
    workspace_member_manager: WorkspaceMemberService = Depends(get_workspace_member_service),
    user_data: LongTokenData = Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))
):
    result= await workspace_member_manager.create_new_admin(
        workspace_id=user_data.workspace_id,
        current_admin_id=user_data.user_id,
        **data.model_dump()
    )    
    return result

@router.post("/transfer_admin",response_model=WorkspaceMemberResponse)
async def admin_role_transfer(
    data:AdminInput,
    workspace_member_manager:WorkspaceMemberService=Depends(get_workspace_member_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))
):
    result=await workspace_member_manager.admin_transfer(
        workspace_id=user_data.workspace_id,
        current_admin_id=user_data.user_id,
        user_id=data.user_id
    )
    return result

@router.post("/update_member_role",response_model=WorkspaceMemberResponse)
async def member_role_update(
    data:UpdateRoleInput,
    workspace_member_manager:WorkspaceMemberService=Depends(get_workspace_member_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))
):
    result= await workspace_member_manager.update_member_position(
        workspace_id=user_data.workspace_id,
        admin_id=user_data.user_id,
        member_id=data.member_id,
        role=data.role
    )
    return result

@router.delete("/remove_member_from_workspace")
async def delete_member_from_workspace(
    data:AdminInput,
    workspace_member_manager:WorkspaceMemberService=Depends(get_workspace_member_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))
):
    await workspace_member_manager.remove_member_from_workspace(
        workspace_id=user_data.workspace_id,
        admin_id=user_data.user_id,
        user_id=data.user_id
    )
    return {"status":"Member removed successfully"}

@router.get("/memberlist",response_model=MemberListResponse)
async def get_member_list(
    search:MemberSearchInput=Depends(),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result= await list_of_member(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id,
        **search.model_dump()
    )
    return result