import math
from loguru import logger
from bson import ObjectId
from typing import Optional
from datetime import datetime,timezone
from app.utils.role_checker import verify_role
from app.database.repositories.base_repository import insert
from app.database.repositories.project_repository import find_project_by_id,find_project_ids_by_manager
from app.database.repositories.team_repository import find_teams_by_manager,find_teams_by_ids
from app.database.repositories.workspace_member_repository import find_workspace_member
from app.database.repositories.task_repository import (
    find_task_by_name,
    update_sprint_in_task,
    task_status_update,
    update_member_to_task,
    remove_sprint_in_task,
    change_member_from_task,
    find_task_by_id,
    list_tasks_by_sprint,
    list_tasks_aggregated,
    get_task_detail
)
from app.models.task import Task
from app.core.enum import CollectionNames
from app.core.enum import Role,TaskStatus
from app.schemas.task import (
    TaskResponse,
    SprintTaskResponse,
    TaskListResponse,
    TaskListItem,
    TaskDetailResponse
)
from app.core.exception import (
    NotFoundError,
    NotAuthorizedError,
    AlreadyExistsError,
    InvalidDateError,
    MemberNotInListError
)

class TaskService:
    def __init__(self):
        pass

    async def create_task(self,workspace_id:str,project_manager_id:str,**data):
        logger.info(f"create task function started | workspace_id:{workspace_id} project_manager_id:{project_manager_id}")
        try:
            current_user_result=await verify_role(
                workspace_id=workspace_id,
                user_id=project_manager_id,
                min_role=Role.MANAGER.value
                )

            project_result= await find_project_by_id(
                workspace_id=workspace_id,
                project_id=data["project_id"]
            )
            if project_result is None:
                raise NotFoundError(f"project_id: {data["project_id"]} is not found")
            
            if project_manager_id != project_result.get("project_manager_id") and current_user_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"user_id:{project_manager_id} does not have access to task")
            
            task_result= await find_task_by_name(
                workspace_id=workspace_id,
                task_name=data["task_name"]
            )            
            if task_result:
                raise AlreadyExistsError(f"task name: {data['task_name']} is already exist")

            created_at=datetime.now()
            data["created_at"]=created_at
            data["created_by"]=project_manager_id
            data["workspace_id"]=workspace_id

            if created_at >= data["due_date"]:
                raise InvalidDateError(f"due_date:{data['due_date']} cannot come before created date: {created_at}")
            
            new_task=Task(**data)

            result= await insert(
                collection_name=CollectionNames.tasks.value,
                new_obj=new_task
            )
            logger.info(f"create task function completed | workspace_id:{workspace_id} project_manager_id:{project_manager_id} project_id:{data['project_id']} task_id:{result.inserted_id}")

            return TaskResponse(
                task_id=str(result.inserted_id),
                task_name=new_task.task_name,
                created_at=new_task.created_at,
                created_by=new_task.created_by,
                project_id=new_task.project_id,
                due_date=new_task.due_date
            )
        except Exception as e:
            logger.error(f"create task function failed | error={e}")
            raise

    async def assign_task_to_sprint(self,workspace_id:str,project_manager_id:str,project_id:str,sprint_id:str,task_id:str):
        logger.info(f"assign task to sprint function started | workspace_id:{workspace_id} project_manager_id:{project_manager_id}")
        try:
            current_user_result=await verify_role(
                workspace_id=workspace_id,
                user_id=project_manager_id,
                min_role=Role.MANAGER.value
            )
            project_result= await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id,
            )
            if project_result is None:
                raise NotFoundError(f"project_id: {project_id} is not found")
            
            if project_manager_id != project_result.get("project_manager_id") and current_user_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"user_id:{project_manager_id} does not have access to task")
            
            if sprint_id not in project_result.get("sprint_ids",[]):
                raise NotFoundError(f"sprint_id:{sprint_id} is not available")
            
            result= await update_sprint_in_task(
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
                sprint_id=sprint_id
            )
            logger.info(f"assign task to sprint function completed |workspace_id:{workspace_id} task_id:{task_id} sprint_id:{sprint_id}")
            
            return TaskResponse(
                task_id=str(ObjectId(result["_id"])),
                task_name=result["task_name"],
                created_at=result["created_at"],
                created_by=result["created_by"],
                project_id=result["project_id"],
                sprint_id=result["sprint_id"],
                due_date=result["due_date"]
            )
        except Exception as e:
            logger.error(f"assign task to sprint function failed | error={e}")
            raise
    
    async def change_task_from_sprint(self,workspace_id:str,project_manager_id:str,project_id:str,sprint_id:str,task_id:str):
        logger.info(f"change task from sprint function started | workspace_id:{workspace_id} project_manager_id:{project_manager_id} task_id:{task_id}")
        try:
            current_user_result=await verify_role(
                workspace_id=workspace_id,
                user_id=project_manager_id,
                min_role=Role.MANAGER.value
            )
            project_result= await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id,
            )
            if project_result is None:
                raise NotFoundError(f"project_id: {project_id} is not found")
            
            if project_manager_id != project_result.get("project_manager_id") and current_user_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"user_id:{project_manager_id} does not have access to task")
            
            if sprint_id not in project_result.get("sprint_ids",[]):
                raise NotFoundError(f"sprint_id:{sprint_id} is not available")

            result= await remove_sprint_in_task(
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
                sprint_id=sprint_id
            )
            logger.info(f"change task from sprint function completed | workspace_id:{workspace_id} project_manager_id:{project_manager_id}")
            
            return TaskResponse(
                task_id=str(ObjectId(result["_id"])),
                task_name=result["task_name"],
                created_at=result["created_at"],
                created_by=result["created_by"],
                project_id=result["project_id"],
                sprint_id=result["sprint_id"],
                due_date=result["due_date"]
            )
        except Exception as e:
            logger.error(f"change task from sprint function failed | error={e}")
            raise

    async def update_task_status(self,workspace_id:str,member_id:str,project_id:str,task_id:str,status:TaskStatus):
        logger.info(f"update task status function started | workspace_id:{workspace_id} member_id:{member_id} task_id:{task_id}")
        try:
            member_result=await verify_role(
                workspace_id=workspace_id,
                user_id=member_id,
                min_role=Role.MEMBER.value
            )            
            task_result= await find_task_by_id(
                workspace_id=workspace_id,
                task_id=task_id
            )
            if task_result is None:
                raise NotFoundError(f"task_id:{task_id} is not found")

            project_result= await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id
            )            
            if project_result is None:
                raise NotFoundError(f"project_id:{project_id} is not found")
            
            if member_id != task_result.get("assignee_id") and member_id != project_result.get("project_manager_id") and member_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"member_id:{member_id} do not have access to task_id:{task_id}")

            if member_result.role != Role.COMPANY_ADMIN.value and not (set(project_result.get("team_ids", [])) & set(member_result.team_ids)):
                raise MemberNotInListError(f"member_id:{member_id} is not in project_id:{project_id}")
            
            result= await task_status_update(
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
                status=status
            )
            logger.info(f"update task status function completed | workspace_id:{workspace_id} member_id:{member_id} task_id:{task_id}")
            
            return TaskResponse(
                task_id=str(ObjectId(result["_id"])),
                task_name=result["task_name"],
                created_at=result["created_at"],
                created_by=result["created_by"],
                project_id=result["project_id"],
                sprint_id=result["sprint_id"],
                due_date=result["due_date"],
                status=result["status"]
            )
        except Exception as e:
            logger.error(f"update task status function failed | error={e}")
            raise
    
    async def assign_task_to_self(self,workspace_id:str,user_id:str,project_id:str,task_id:str):
        logger.info(f"assign task to self func started | workspace_id:{workspace_id} user_id:{user_id} task_id:{task_id}")
        try:
            member_result=await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )
            project_result= await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id
            )
            if project_result is None:
                raise NotFoundError(f"project_id:{project_id} is not found")

            if not (set(project_result.get("team_ids",[])) & set(member_result.team_ids)):
                raise MemberNotInListError(f"user_id:{user_id} is not in project_id:{project_id}")
            
            task = await update_member_to_task(
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
                member_id=user_id
            )
            if not task:
                raise NotFoundError("Task not found")
            
            logger.info(f"assign task to self func completed | workspace_id:{workspace_id} user_id:{user_id} task_id:{task_id}")
            return TaskResponse(
                task_id=task_id,
                task_name=task["task_name"],
                created_at=task["created_at"],
                created_by=task["created_by"],
                project_id=task["project_id"],
                sprint_id=task["sprint_id"],
                assignee_id=task["assignee_id"],
                due_date=task["due_date"],
                status=task["status"]
            )
        except Exception as e:
            logger.error(f"assign task to self func failed | error={e}")
            raise
    
    async def assign_task_to_member(self,workspace_id:str,project_manager_id:str,project_id:str,task_id:str,member_id:str):
        logger.info(f"assign task to member function started | workspace_id:{workspace_id} project_manager_id:{project_manager_id} task_id:{task_id}")
        try:
            user_result=await verify_role(
                workspace_id=workspace_id,
                user_id=project_manager_id,
                min_role=Role.MANAGER.value
            )
            member_result=await verify_role(
                workspace_id=workspace_id,
                user_id=member_id,
                min_role=Role.MEMBER.value
            )
            project_result= await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id
            )            
            if project_result is None:
                raise NotFoundError(f"project_id:{project_id} is not found")
            
            if project_manager_id != project_result.get("project_manager_id") and user_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"project_maanager_id:{project_manager_id} does not have access to task")
            
            if user_result.role != Role.COMPANY_ADMIN.value and not (set(project_result.get("team_ids", [])) & set(member_result.team_ids)):
                raise MemberNotInListError(f"member_id:{member_id} is not in project_id:{project_id}")
            
            result= await update_member_to_task(
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
                member_id=member_id
            )
            logger.info(f"assign task to member function completed | workspace_id:{workspace_id} project_manager_id:{project_manager_id} task_id:{task_id} member_id:{member_id}")
            
            return TaskResponse(
                task_id=task_id,
                task_name=result["task_name"],
                created_at=result["created_at"],
                created_by=result["created_by"],
                project_id=result["project_id"],
                sprint_id=result["sprint_id"],
                assignee_id=result["assignee_id"],
                due_date=result["due_date"],
                status=result["status"]
            )
        except Exception as e:
            logger.error(f"assign task to member function failed | error={e}")
            raise
    
    async def remove_member_from_task(self,workspace_id:str,project_manager_id:str,project_id:str,task_id:str,member_id:str):
        logger.info(f"remove member from task function started | workspace_id:{workspace_id} project_manager_id:{project_manager_id} task_id:{task_id}")
        try:
            current_user_result=await verify_role(
                workspace_id=workspace_id,
                user_id=project_manager_id,
                min_role=Role.MANAGER.value
            )
            member_result=await verify_role(
                workspace_id=workspace_id,
                user_id=member_id,
                min_role=Role.MEMBER.value
            )
            project_result= await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id
            )            
            if project_result is None:
                raise NotFoundError(f"project_id:{project_id} is not found")
            
            if project_manager_id != project_result.get("project_manager_id") and current_user_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"project_maanager_id:{project_manager_id} does not have access to task")
            
            if current_user_result.role != Role.COMPANY_ADMIN.value and not (set(project_result.get("team_ids",[])) & set(member_result.team_ids)):
                raise MemberNotInListError(f"member_id:{member_id} is not in project_id:{project_id}")
            
            result= await change_member_from_task(
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
                member_id=member_id
            )
            logger.info(f"remove member from task function completed | workspace_id:{workspace_id} project_manager_id:{project_manager_id} task_id:{task_id}")

            return TaskResponse(
                task_id=str(result["_id"]),
                task_name=result["task_name"],
                created_at=result["created_at"],
                created_by=result["created_by"],
                project_id=result["project_id"],
                sprint_id=result["sprint_id"],
                assignee_id=result["assignee_id"],
                due_date=result["due_date"],
                status=result["status"]
            )
        except Exception as e:
            logger.error(f"remove member from task function failed | error={e}")
            raise
    
    async def unassign_self_from_task(self,workspace_id:str,user_id:str,project_id:str,task_id:str):
        logger.info(f"unassign self func started | workspace_id:{workspace_id} user_id:{user_id} task_id:{task_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )
            task = await find_task_by_id(
                workspace_id=workspace_id,
                task_id=task_id
            )
            if task is None:
                raise NotFoundError(f"task_id:{task_id} not found")

            if task.get("assignee_id") != user_id:
                raise NotAuthorizedError(f"user_id:{user_id} is not the assignee of task_id:{task_id}")

            updated_task = await update_member_to_task(
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
                member_id=None
            )

            logger.info(f"unassign self func completed | workspace_id:{workspace_id} user_id:{user_id} task_id:{task_id}")
            return TaskResponse(
                task_id=task_id,
                task_name=updated_task["task_name"],
                created_at=updated_task["created_at"],
                created_by=updated_task["created_by"],
                project_id=updated_task["project_id"],
                sprint_id=updated_task["sprint_id"],
                assignee_id=updated_task["assignee_id"],
                due_date=updated_task["due_date"],
                status=updated_task["status"]
            )
        except Exception as e:
            logger.error(f"unassign self func failed | error={e}")
            raise

    async def assign_member_to_task(self,workspace_id:str,user_id:str,project_id:str,task_id:str,member_id:str) -> TaskResponse:
        logger.info(f"assign member to task func started | workspace_id:{workspace_id} user_id:{user_id} task_id:{task_id} member_id:{member_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MANAGER.value
            )
            project_result= await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id
            )
            if project_result is None:
                raise NotFoundError(f"project_id:{project_id} is not found")

            member= await find_workspace_member(
                workspace_id=workspace_id,
                user_id=member_id
            )
            if member is None:
                raise NotFoundError(f"member_id:{member_id} not found in workspace_id:{workspace_id}")

            teams= await find_teams_by_ids(
                workspace_id=workspace_id,
                team_ids=project_result.get("team_ids",[])
            )
            if not any(member_id in team.get("member_ids",[]) for team in teams):
                raise MemberNotInListError(f"member_id:{member_id} is not in project_id:{project_id}")

            result= await update_member_to_task(
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
                member_id=member_id
            )
            if not result:
                raise NotFoundError(f"task_id:{task_id} is not found")

            logger.info(f"assign member to task func completed | workspace_id:{workspace_id} task_id:{task_id} member_id:{member_id}")
            return TaskResponse(
                task_id=task_id,
                task_name=result["task_name"],
                created_at=result["created_at"],
                created_by=result["created_by"],
                project_id=result["project_id"],
                sprint_id=result["sprint_id"],
                assignee_id=result["assignee_id"],
                due_date=result["due_date"],
                status=result["status"]
            )
        except Exception as e:
            logger.error(f"assign member to task func failed | error={e}")
            raise

    async def list_tasks_by_sprint(self,workspace_id:str,user_id:str,sprint_id:str):
        logger.info(f"list tasks by sprint function started | workspace_id:{workspace_id} user_id:{user_id} sprint_id:{sprint_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )
            result= await list_tasks_by_sprint(workspace_id=workspace_id,sprint_id=sprint_id)
            logger.info(f"list tasks by sprint function completed | workspace_id:{workspace_id} sprint_id:{sprint_id} count:{len(result)}")

            return [SprintTaskResponse(**task) for task in result]
        except Exception as e:
            logger.error(f"list tasks by sprint function failed | error={e}")
            raise

    async def list_tasks(
        self,
        workspace_id:str,
        user_id:str,
        search:Optional[str],
        project_id:Optional[str],
        assignee_id:Optional[str],
        status:Optional[TaskStatus],
        priority:Optional[str],
        page:int,
        page_size:int,
        mine_or_unassigned:bool=False
    ):
        logger.info(f"list tasks function started | workspace_id:{workspace_id} user_id:{user_id} page:{page} page_size:{page_size}")
        try:
            member_result= await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )

            manager_project_ids=None
            scoped_assignee_id=None if mine_or_unassigned else assignee_id
            scoped_mine_or_unassigned_user_id=user_id if mine_or_unassigned else None

            if member_result.role == Role.MANAGER.value:
                owned_project_ids= await find_project_ids_by_manager(workspace_id=workspace_id,manager_id=user_id)
                managed_teams= await find_teams_by_manager(workspace_id=workspace_id,manager_id=user_id)
                team_project_ids=[pid for team in managed_teams for pid in team.get("project_ids",[])]
                manager_project_ids= list(set(owned_project_ids) | set(team_project_ids))
                scoped_assignee_id=None
                scoped_mine_or_unassigned_user_id=None

            tasks,total_count= await list_tasks_aggregated(
                workspace_id=workspace_id,
                search=search,
                project_id=project_id,
                assignee_id=scoped_assignee_id,
                status=status.value if status else None,
                priority=priority,
                page=page,
                page_size=page_size,
                mine_or_unassigned_user_id=scoped_mine_or_unassigned_user_id,
                manager_project_ids=manager_project_ids
            )
            total_pages= math.ceil(total_count/page_size) if page_size else 0
            logger.info(f"list tasks function completed | workspace_id:{workspace_id} count:{total_count}")

            return TaskListResponse(
                tasks=[TaskListItem(**task) for task in tasks],
                total_count=total_count,
                page=page,
                total_pages=total_pages
            )
        except Exception as e:
            logger.error(f"list tasks function failed | error={e}")
            raise

    async def get_task_detail(self,workspace_id:str,user_id:str,task_id:str) -> dict:
        logger.info(f"get task detail function started | workspace_id:{workspace_id} task_id:{task_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )
            result= await get_task_detail(
                workspace_id=workspace_id,
                task_id=task_id
            )
            if result is None:
                raise NotFoundError(f"task_id:{task_id} is not found")

            logger.info(f"get task detail function completed | workspace_id:{workspace_id} task_id:{task_id}")

            return TaskDetailResponse(
                task_id=str(result["_id"]),
                task_name=result["task_name"],
                description=result["description"],
                status=result["status"],
                priority=result["priority"],
                project_id=result["project_id"],
                sprint_id=result["sprint_id"],
                due_date=result["due_date"],
                created_at=result["created_at"],
                created_by=result["created_by"],
                assignee=result["assignee_id"]
            )
        except Exception as e:
            logger.error(f"get task detail function failed | error={e}")
            raise