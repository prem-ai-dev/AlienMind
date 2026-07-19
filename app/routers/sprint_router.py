from fastapi import APIRouter,Depends
from app.services.sprint_service import SprintService
from app.core.dependencies import get_sprint_service,RoleChecker
from app.core.enum import Role
from app.schemas.sprint import SprintInput,SprintResponse,SprintStatusInput
from app.schemas.token_data import LongTokenData

router=APIRouter(prefix="/sprint_service",tags=["SPRINT"])

@router.post("/create_sprint",response_model=SprintResponse)
async def create_new_sprint(
    data:SprintInput,
    sprint_manager:SprintService=Depends(get_sprint_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result=await sprint_manager.create_sprint(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        **data.model_dump()
    )
    return result

@router.post("/update_status",response_model=SprintResponse)
async def sprint_status_update(
    data:SprintStatusInput,
    sprint_manager:SprintService=Depends(get_sprint_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result=await sprint_manager.update_sprint_status(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        project_id=data.project_id,
        sprint_id=data.sprint_id,
        status=data.status
    )
    return result