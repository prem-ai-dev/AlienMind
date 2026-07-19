from fastapi import APIRouter,Depends
from app.schemas.task import TaskInput
from app.schemas.token_data import LongTokenData
from app.services.task_service import TaskService
from app.core.dependencies import get_task_service,RoleChecker
from app.core.enum import Role
from app.schemas.task import (
    TaskResponse,
    SprintIdActionInput,
    TaskStatusInput,
    MemberTaskInput,
    SelfTaskInput,
    AssignMemberInput,
    SprintTaskQuery,
    SprintTaskResponse,
    TaskListQuery,
    TaskListResponse,
    TaskDetailResponse
    )

router=APIRouter(prefix="/task_service",tags=["TASK"])

@router.post("/create_task",response_model=TaskResponse)
async def create_new_task(
    data:TaskInput,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result=await task_manager.create_task(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        **data.model_dump()
    )
    return result

@router.post("/assign_task_to_sprint",response_model=TaskResponse)
async def assign_sprint_id_to_task(
    data:SprintIdActionInput,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result=await task_manager.assign_task_to_sprint(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        project_id=data.project_id,
        sprint_id=data.sprint_id,
        task_id=data.task_id
    )
    return result

@router.post("/remove_sprint_id",response_model=TaskResponse)
async def remove_sprint_id_from_task(
    data:SprintIdActionInput,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result=await task_manager.change_task_from_sprint(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        project_id=data.project_id,
        sprint_id=data.sprint_id,
        task_id=data.task_id
    )
    return result

@router.post("/update_task_status",response_model=TaskResponse)
async def task_status_update(
    data:TaskStatusInput,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result=await task_manager.update_task_status(
        workspace_id=user_data.workspace_id,
        member_id=user_data.user_id,
        project_id=data.project_id,
        task_id=data.task_id,
        status=data.status
    )
    return result

@router.post("/assign_member_to_task",response_model=TaskResponse)
async def assign_member_to_task(
    data:MemberTaskInput,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result=await task_manager.assign_task_to_member(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        project_id=data.project_id,
        task_id=data.task_id,
        member_id=data.member_id
    )
    return result

@router.post("/remove_member_from_task",response_model=TaskResponse)
async def remove_member_id_from_task(
    data:MemberTaskInput,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    result= await task_manager.remove_member_from_task(
        workspace_id=user_data.workspace_id,
        project_manager_id=user_data.user_id,
        project_id=data.project_id,
        task_id=data.task_id,
        member_id=data.member_id
    )
    return result

@router.post("/self_assign",response_model=TaskResponse)
async def self_assign_task(
    data:SelfTaskInput,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result=await task_manager.assign_task_to_self(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id,
        project_id=data.project_id,
        task_id=data.task_id
    )
    return result

@router.post("/self_unassign",response_model=TaskResponse)
async def self_unassign_task(
    data:SelfTaskInput,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result= await task_manager.unassign_self_from_task(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id,
        project_id=data.project_id,
        task_id=data.task_id
    )
    return result

@router.post("/assign_member",response_model=TaskResponse)
async def assign_team_member_to_task(
    data:AssignMemberInput,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MANAGER.value))
):
    return await task_manager.assign_member_to_task(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id,
        project_id=data.project_id,
        task_id=data.task_id,
        member_id=data.member_id
    )

@router.get("/list_by_sprint",response_model=list[SprintTaskResponse])
async def get_tasks_by_sprint(
    query:SprintTaskQuery=Depends(),
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result= await task_manager.list_tasks_by_sprint(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id,
        sprint_id=query.sprint_id
    )
    return result

@router.get("/list_tasks",response_model=TaskListResponse)
async def get_all_tasks(
    query:TaskListQuery=Depends(),
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result= await task_manager.list_tasks(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id,
        search=query.search,
        project_id=query.project_id,
        assignee_id=query.assignee_id,
        status=query.status,
        priority=query.priority,
        page=query.page,
        page_size=query.page_size,
        mine_or_unassigned=query.mine_or_unassigned
    )
    return result

@router.get("/get_task_detail",response_model=TaskDetailResponse)
async def get_task_detail(
    task_id:str,
    task_manager:TaskService=Depends(get_task_service),
    user_data:LongTokenData=Depends(RoleChecker(min_role=Role.MEMBER.value))
):
    result= await task_manager.get_task_detail(
        workspace_id=user_data.workspace_id,
        user_id=user_data.user_id,
        task_id=task_id
    )
    return result