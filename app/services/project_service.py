from loguru import logger
from bson import ObjectId
from datetime import datetime,timezone
from app.database.repositories.project_repository import find_project_by_title,insert_manager_to_project,find_and_update_project_status,find_project_by_id,insert_team_in_project,pull_team_from_project,list_projects_aggregated,get_project_dashboard_stats
from app.database.repositories.base_repository import insert
from app.models.project import Project
from app.utils.role_checker import verify_role
from app.core.enum import CollectionNames,Role
from app.schemas.project import ProjectResponse,ProjectListResponse,DashboardStatsResponse
from app.core.exception import AlreadyExistsError,NotFoundError,NotAuthorizedError

class ProjectService:
    def __init__(self):
        pass

    async def create_project(self,workspace_id:str,admin_id:str,project_title:str):
        logger.info(f"create project function started by | admin_id:{admin_id}")

        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=admin_id,
                min_role=Role.COMPANY_ADMIN.value
            )
            result= await find_project_by_title(
                workspace_id=workspace_id,
                project_title=project_title
            )
            if result:
                raise AlreadyExistsError(f"project_title: {project_title} is already exist")
            
            created_at=datetime.now(timezone.utc)

            new_project=Project(
                project_title=project_title,
                created_at=created_at,
                workspace_id=workspace_id
            )
            project_result= await insert(collection_name=CollectionNames.projects.value,new_obj=new_project)

            logger.info(f"new project is created successfully | new_project_id: {project_result.inserted_id}")

            return ProjectResponse(
                    project_id=str(project_result.inserted_id),
                    project_title=new_project.project_title,
                    created_at=new_project.created_at,
                    manager_id=None
                )
        except Exception as e:
            logger.error(f"creating new project is failed | error: {e}")
            raise
    
    async def assign_project_manager(self,workspace_id:str,admin_id:str,manager_id:str,project_id:str):
        logger.info(f"assign manager function started by | admin_id:{admin_id}")

        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=admin_id,
                min_role=Role.COMPANY_ADMIN.value
            )
            await verify_role(
                workspace_id=workspace_id,
                user_id=manager_id,
                min_role=Role.MANAGER.value
            )            
            project_result= await insert_manager_to_project(
                workspace_id=workspace_id,
                project_id=project_id,
                manager_id=manager_id
            )            
            logger.info(f"manager is assigned to project successfully | project_id:{project_id} manager_id:{manager_id}")
            
            return ProjectResponse(
                project_id=str(ObjectId(project_result["_id"])),
                project_title=project_result["project_title"],
                created_at=project_result["created_at"],
                manager_id=project_result["project_manager_id"]
            )        
        except Exception as e:
            logger.error(f"assigning manager to project is failed | error={e}")
            raise
    
    async def update_project_status(self,workspace_id:str,project_manager_id:str,project_id:str,status:str):
        logger.info(f"Update project status function started | workspace_id={workspace_id} project_id={project_id} project_manager_id={project_manager_id}")
        try:
            manager_result=await verify_role(
                workspace_id=workspace_id,
                user_id=project_manager_id,
                min_role=Role.MANAGER.value
            )
            project_result= await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id
            )
            if project_result is None:
                raise NotFoundError(f"project_id:{project_id} is not found")

            if manager_result.role != Role.COMPANY_ADMIN.value and project_manager_id != project_result.get("project_manager_id"):
                raise NotAuthorizedError(f"manager_id: {project_manager_id} cannot access the projects")
        
            result = await find_and_update_project_status(
                workspace_id=workspace_id,
                project_id=project_id,
                status=status
            )
            logger.info(f"Update project status completed successfully | workspace_id={workspace_id} project_id={project_id}")

            return ProjectResponse(
                project_id=str(ObjectId(project_result["_id"])),
                project_title=project_result["project_title"],
                created_at=project_result["created_at"],
                manager_id=project_result["project_manager_id"],
                status=result["status"]
            )
        except Exception as e:
            logger.error(f"Failed to update project status | workspace_id={workspace_id} project_id={project_id} error={e}")
            raise

    async def add_team_to_project(self,workspace_id:str,project_manager_id:str,project_id:str,team_id:str):
        logger.info(f"Add team to project function started | workspace_id={workspace_id}, project_id={project_id}, project_manager_id={project_manager_id}")
        try:
            current_user_result=await verify_role(
                workspace_id=workspace_id,
                user_id=project_manager_id,
                min_role=Role.MANAGER.value
            )
            project = await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id
            )
            if project is None:
                raise NotFoundError(f"project_id: {project_id} not found")
            
            if project_manager_id != project.get("project_manager_id") and current_user_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"manager_id: {project_manager_id} cannot access the projects")

            result = await insert_team_in_project(
                workspace_id=workspace_id,
                project_id=project_id,
                team_id=team_id
            )
            logger.info(f"Add team to project function completed successfully | workspace_id={workspace_id}, project_id={project_id}, team_id={team_id}")

            return ProjectResponse(
                project_id=str(ObjectId(result["_id"])),
                project_title=result["project_title"],
                created_at=result["created_at"],
                manager_id=result["project_manager_id"],
                team_ids=result["team_ids"]
            )
        
        except Exception as e:
            logger.error(f"Failed to add team to project | error={e}")
            raise
    
    async def remove_team_from_project(self,workspace_id:str,project_manager_id:str,project_id:str,team_id:str):
        logger.info(f"remove team from project function started | workspace_id={workspace_id}, project_id={project_id}, project_manager_id={project_manager_id}")
        try:
            current_user_result=await verify_role(
                workspace_id=workspace_id,
                user_id=project_manager_id,
                min_role=Role.MANAGER.value
            )            
            project = await find_project_by_id(
                workspace_id=workspace_id,
                project_id=project_id
            )
            if project is None:
                raise NotFoundError(f"project_id: {project_id} not found")
            
            if project_manager_id != project.get("project_manager_id") and current_user_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f" manager_id: {project_manager_id} cannot access the projects")
            
            result = await pull_team_from_project(
                workspace_id=workspace_id,
                project_id=project_id,
                team_id=team_id
            )
            logger.info(f"remove team from project function completed successfully | workspace_id={workspace_id}, project_id={project_id}, team_id={team_id}")

            return ProjectResponse(
                project_id=str(result["_id"]),
                project_title=result["project_title"],
                created_at=result["created_at"],
                manager_id=result["project_manager_id"],
                team_ids=result["team_ids"]
            )

        except Exception as e:
            logger.error(f"Failed to remove team from project | error={e}")
            raise

    async def list_projects(self,workspace_id:str,user_id:str):
        logger.info(f"list projects function started | workspace_id:{workspace_id} user_id:{user_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )
            result= await list_projects_aggregated(workspace_id=workspace_id)
            logger.info(f"list projects function completed | workspace_id:{workspace_id} count:{len(result)}")

            return [ProjectListResponse(**project) for project in result]
        except Exception as e:
            logger.error(f"list projects function failed | error={e}")
            raise

    async def get_dashboard_stats(self,workspace_id:str,user_id:str):
        logger.info(f"get dashboard stats function started | workspace_id:{workspace_id} user_id:{user_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )
            result= await get_project_dashboard_stats(workspace_id=workspace_id)
            logger.info(f"get dashboard stats function completed | workspace_id:{workspace_id}")

            return DashboardStatsResponse(**result)
        except Exception as e:
            logger.error(f"get dashboard stats function failed | error={e}")
            raise