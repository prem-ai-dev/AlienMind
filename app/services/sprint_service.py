from loguru import logger
from datetime import datetime,timezone
from bson import ObjectId
from app.utils.role_checker import verify_role
from app.database.repositories.project_repository import find_project_by_id
from app.database.repositories.sprint_repository import change_sprint_status,insert_and_add_sprint_in_project
from app.models.sprint import Sprint
from app.core.enum import Role,SprintStatus
from app.schemas.sprint import SprintResponse
from app.core.exception import NotFoundError,NotAuthorizedError,InvalidDateError

class SprintService:
    def __init__(self):
        pass

    async def create_sprint(self,workspace_id:str,project_manager_id:str,**data):
        logger.info(f"create sprint function started | workspace_id:{workspace_id} project_manager_id:{project_manager_id} project_id:{data["project_id"]}")

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
                raise NotAuthorizedError(f" current manager_id: {project_manager_id} cannot access the sprint creation")
            
            if data["sprint_start_date"] > data["sprint_end_date"]:
                raise InvalidDateError(f"startdate: {data["sprint_start_date"]} cannot come after end_date: {data["sprint_end_date"]}")

            created_at=datetime.now(timezone.utc)
            data["created_at"]=created_at
            data["workspace_id"]=workspace_id

            new_sprint=Sprint(**data)

            result= await insert_and_add_sprint_in_project(
                new_sprint=new_sprint,
                workspace_id=workspace_id,
                project_id=data["project_id"]
            )
            logger.info(f"create sprint function completed | workspace_id:{workspace_id} project_id:{data["project_id"]} sprint_id:{result["_id"]}")

            return SprintResponse(
                sprint_id=str(result["_id"]),
                sprint_name=result["sprint_name"],
                sprint_start_date=result["sprint_start_date"],
                sprint_end_date=result["sprint_end_date"],
                project_id=result["project_id"],
            )        
        except Exception as e:
            logger.error(f"create sprint function failed | error={e}")
            raise

    async def update_sprint_status(self,workspace_id:str,project_manager_id:str,project_id:str,sprint_id:str,status:SprintStatus):
        logger.info(f"Update sprint status started | workspace_id={workspace_id}, project_manager_id:{project_manager_id} project_id={project_id}, sprint_id={sprint_id}")
        try:
            current_user_result=await verify_role(workspace_id=workspace_id,
                              user_id=project_manager_id,
                              min_role=Role.MANAGER.value
                              )

            project_result = await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id
            )
            if project_result is None:
                raise NotFoundError(f"project_id: {project_id} not found")
            
            if project_manager_id != project_result.get("project_manager_id") and current_user_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"current manager_id:{project_manager_id} cannot access sprint")

            result = await change_sprint_status(
                workspace_id=workspace_id,
                sprint_id=sprint_id,
                project_id=project_id,
                status=status
            )
            logger.info(f"Update sprint status completed successfully | workspace_id={workspace_id}, project_id={project_id}, sprint_id={sprint_id}")

            return SprintResponse(
                sprint_id=str(ObjectId(result["_id"])),
                sprint_name=result["sprint_name"],
                sprint_start_date=result["sprint_start_date"],
                sprint_end_date=result["sprint_end_date"],
                project_id=result["project_id"],
                status=result["status"]
            )

        except Exception as e:
            logger.error(f"Failed to update sprint status |error={e}")
            raise