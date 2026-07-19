from fastapi import APIRouter, Depends
from app.services.workspace_service import WorkspaceService
from app.core.dependencies import get_workspace_service,RoleChecker
from app.schemas.token_data import LongTokenData
from app.schemas.workspace import CreateWorkspaceInput,CreateWorkspaceResponse,AddDomainInput,WorkspaceResponse
from app.core.auth import create_token
from app.core.enum import TokenTime,Role

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.post("/create", response_model=CreateWorkspaceResponse)
async def create_workspace_route(
    data: CreateWorkspaceInput,
    workspace_manager: WorkspaceService = Depends(get_workspace_service),
    user_data: LongTokenData = Depends(RoleChecker(min_role=Role.MEMBER.value)),
):
    result = await workspace_manager.create_workspace(
        username=data.username,
        company_name=data.company_name,
        owner_id=user_data.user_id,
    )
    token = create_token(
        data={
            "workspace_id": result.workspace_id,
            "user_id": result.user_id,
            "role": result.role,
        },
        minutes=TokenTime.long_token.value,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "data": result,
    }


@router.post("/add_domain", response_model=WorkspaceResponse)
async def add_domain_route(
    data: AddDomainInput,
    workspace_manager: WorkspaceService = Depends(get_workspace_service),
    user_data: LongTokenData = Depends(RoleChecker(min_role=Role.COMPANY_ADMIN.value)),
):
    result = await workspace_manager.add_allowed_domain(
        workspace_id=user_data.workspace_id,
        admin_id=user_data.user_id,
        domain=data.domain,
    )
    return result