from fastapi import APIRouter,Depends
from app.schemas.token_data import LongTokenData
from app.schemas.dashboard import DashboardStatsResponse,MemberDashboardStatsResponse,ManagerDashboardStatsResponse
from app.services.dashboard.admin_dashboard_service import AdminDashboardService
from app.services.dashboard.member_dashboard_service import MemberDashboardService
from app.services.dashboard.manager_dashboard_service import ManagerDashboardService
from app.core.dependencies import get_admin_dashboard_service,get_member_dashboard_service,get_manager_dashboard_service,RoleChecker
from app.core.enum import Role

router=APIRouter(prefix="/dashboard_service",tags=["DASHBOARD"])

@router.get("/dashboard_stats",response_model=DashboardStatsResponse)
async def dashboard_stats(
    dashboard_manager:AdminDashboardService=Depends(get_admin_dashboard_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value))
):
    return await dashboard_manager.get_dashboard_stats(workspace_id=user_data.workspace_id)

@router.get("/member_dashboard_stats",response_model=MemberDashboardStatsResponse)
async def member_dashboard_stats(
    dashboard_manager:MemberDashboardService=Depends(get_member_dashboard_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    return await dashboard_manager.get_dashboard_stats(workspace_id=user_data.workspace_id,user_id=user_data.user_id)

@router.get("/manager_dashboard_stats",response_model=ManagerDashboardStatsResponse)
async def manager_dashboard_stats(
    dashboard_manager:ManagerDashboardService=Depends(get_manager_dashboard_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    return await dashboard_manager.get_dashboard_stats(workspace_id=user_data.workspace_id,user_id=user_data.user_id)
