from loguru import logger
from bson import ObjectId
from datetime import datetime,timezone
from app.database.repositories.base_repository import insert
from app.database.repositories.team_repository import (
    find_team_by_name,
    find_team_by_id,
    insert_new_member,
    remove_member_and_unassign_tasks,
    insert_team_manager,
    delete_team_and_remove_from_lists,
    list_teams,
    list_teams_detailed,
    find_teams_by_manager
)
from app.database.repositories.project_repository import find_projects_by_manager
from app.models.team import Team
from app.utils.role_checker import verify_role
from app.core.enum import CollectionNames
from app.core.enum import Role
from app.schemas.team import TeamResponse,TeamListResponse,TeamDetailListResponse
from app.core.exception import AlreadyExistsError,NotFoundError,NotAuthorizedError

class TeamService:
    def __init__(self):
        pass

    async def create_team(self,workspace_id:str,admin_id:str,team_name:str):
        logger.info(f"create team function started by | admin_id:{admin_id}")

        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=admin_id,
                min_role=Role.COMPANY_ADMIN.value
            )
            team_result= await find_team_by_name(
                workspace_id=workspace_id,
                team_name=team_name
            )
            if team_result:
                raise AlreadyExistsError(f"team name: {team_name} is already taken")
            
            created_at=datetime.now(timezone.utc)

            new_team=Team(
                team_name=team_name,
                created_at=created_at,
                workspace_id=workspace_id
            )
            team_response= await insert(
                collection_name=CollectionNames.teams.value,
                new_obj=new_team
            )
            logger.info(f"new team is created successful | admin_id:{admin_id} team_id:{team_response.inserted_id}")

            return TeamResponse(
                team_id=str(team_response.inserted_id),
                team_name=new_team.team_name,
                created_at=new_team.created_at
            )
        
        except Exception as e:
            logger.error(f"team creation is failed | error: {e}")
            raise
    
    async def insert_team_member(self,workspace_id:str,team_id:str,team_manager_id:str,member_id:str):
        logger.info(f"insert team member function started by | manager_id:{team_manager_id}")

        try:
            role_result=await verify_role(
                workspace_id=workspace_id,
                user_id=team_manager_id,
                min_role=Role.MANAGER.value
            )
            team_result = await find_team_by_id(
                workspace_id=workspace_id,
                team_id=team_id
            )
            if team_result is None:
                raise NotFoundError(f"team_id: {team_id} is not found")
            
            if team_result.get("team_manager_id") != team_manager_id and role_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"manager_id: {team_manager_id} does not manage team_id: {team_id}")

            result = await insert_new_member(
                workspace_id=workspace_id,
                team_id=team_id,
                user_id=member_id
            )
            logger.info(f"new team member inserted successfully  | manager_id:{team_manager_id}")
            
            return TeamResponse(
                team_id=str(ObjectId(result["_id"])),
                team_name=result["team_name"],
                team_manager_id=result["team_manager_id"],
                created_at=result["created_at"],
                member_ids=result["member_ids"],
                status=result["status"]
            )

        except Exception as e:
            logger.error(f"insert team member function failed | error: {e}")
            raise
    
    async def remove_team_member(self,workspace_id: str, team_id: str, team_manager_id: str, member_id: str):
        logger.info(f"remove team member function started by | manager_id:{team_manager_id}")

        try:
            role_result=await verify_role(
                workspace_id=workspace_id,
                user_id=team_manager_id,
                min_role=Role.MANAGER.value
            )
            team_result = await find_team_by_id(
                workspace_id=workspace_id,
                team_id=team_id
            )
            if team_result is None:
                raise NotFoundError(f"team_id: {team_id} is not found")
            
            if team_result.get("team_manager_id") != team_manager_id and role_result.role != Role.COMPANY_ADMIN.value:
                raise NotAuthorizedError(f"manager_id: {team_manager_id} does not manage team_id: {team_id}")

            result= await remove_member_and_unassign_tasks(
                workspace_id=workspace_id,
                team_id=team_id,
                user_id=member_id
            )
            logger.info(f"team member removed successfully | manager_id:{team_manager_id}")

            return TeamResponse(
                team_id=str(result.get("_id")),
                team_name=result["team_name"],
                team_manager_id=result["team_manager_id"],
                created_at=result["created_at"],
                member_ids=result["member_ids"],
                status=result["status"]
            )        
        except Exception as e:
            logger.error(f"remove team member function failed | error: {e}")
            raise
    
    async def assign_team_manager(self,workspace_id:str,admin_id:str,team_id:str,team_manager_id:str):
        logger.info(f"Assign team manager started | workspace_id={workspace_id} team_id={team_id} admin_id={admin_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=admin_id,
                min_role=Role.COMPANY_ADMIN.value
            )
            await verify_role(
                workspace_id=workspace_id,
                user_id=team_manager_id,
                min_role=Role.MANAGER.value
            )
            team = await find_team_by_id(
                workspace_id=workspace_id,
                team_id=team_id
            )
            if team is None:
                raise NotFoundError(f"team_id: {team_id} not found")

            result = await insert_team_manager(
                workspace_id=workspace_id,
                team_id=team_id,
                team_manager_id=team_manager_id
            )
            logger.info(f"Assign team manager function completed successfully | workspace_id={workspace_id}, team_id={team_id}")

            return TeamResponse(
                team_id=str(ObjectId(result["_id"])),
                team_name=result["team_name"],
                team_manager_id=result["team_manager_id"],
                created_at=result["created_at"],
                member_ids=result["member_ids"],
                status=result["status"]
            )

        except Exception as e:
            logger.error(f"Failed to assign team manager | error={e}")
            raise
    
    async def delete_team(self,workspace_id:str,admin_id:str,team_id:str):
        logger.info(f"delete team function started | workspace={workspace_id} admin_id:{admin_id} team_id:{team_id}")

        try:
            await verify_role(workspace_id=workspace_id,
                              user_id=admin_id,
                              min_role=Role.COMPANY_ADMIN.value)

            team_result= await find_team_by_id(workspace_id=workspace_id,
                                               team_id=team_id
                                               )
            
            if team_result is None:
                raise NotFoundError(f" team_id: {team_id} is not found")
            
            result= await delete_team_and_remove_from_lists(workspace_id=workspace_id,
                                                            team_id=team_id
                                                            )
            logger.info(f"delete team function completed | workspace={workspace_id} admin_id:{admin_id} team_id:{team_id}")

        except Exception as e:
            logger.error(f"delete team function failed | error={e}")
            raise

    async def list_teams(self,workspace_id:str,user_id:str):
        logger.info(f"list teams function started | workspace_id:{workspace_id} user_id:{user_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )
            result= await list_teams(workspace_id=workspace_id)
            logger.info(f"list teams function completed | workspace_id:{workspace_id} count:{len(result)}")

            return [TeamListResponse(**team) for team in result]
        except Exception as e:
            logger.error(f"list teams function failed | error={e}")
            raise

    async def get_team_detail_list(self,workspace_id:str,user_id:str):
        logger.info(f"get team detail list function started | workspace_id:{workspace_id} user_id:{user_id}")
        try:
            member_result= await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )

            team_ids_filter=None
            if member_result.role == Role.MANAGER.value:
                managed_teams= await find_teams_by_manager(workspace_id=workspace_id,manager_id=user_id)
                owned_team_ids=[str(team["_id"]) for team in managed_teams]

                managed_projects= await find_projects_by_manager(workspace_id=workspace_id,manager_id=user_id)
                project_team_ids=[tid for project in managed_projects for tid in project.get("team_ids",[])]

                team_ids_filter= list(set(owned_team_ids) | set(project_team_ids))

            result= await list_teams_detailed(workspace_id=workspace_id,team_ids_filter=team_ids_filter)
            logger.info(f"get team detail list function completed | workspace_id:{workspace_id} count:{len(result)}")

            return [TeamDetailListResponse(**team) for team in result]
        except Exception as e:
            logger.error(f"get team detail list function failed | error={e}")
            raise