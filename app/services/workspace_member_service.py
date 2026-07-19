from loguru import logger
from datetime import datetime,timezone
from app.database.db_connection import client
from app.database.repositories.user_repository import find_user
from app.database.repositories.base_repository import insert
from app.database.repositories.workspace_member_repository import (
    find_workspace_member,
    update_member_role,
    count_document,
    update_member_to_admin,
    update_admin_to_member,
    member_status_to_delete
    )
from app.database.repositories.team_repository import remove_member_from_team,remove_team_manager_from_project
from app.database.repositories.project_repository import remove_project_manager_from_project
from app.database.repositories.workspace_repository import remove_member_from_workspace
from app.database.repositories.task_repository import remove_assignee_from_task
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.core.auth import hash_pw
from app.schemas.user import UserValidation
from app.utils.role_checker import verify_role
from app.core.enum import CollectionNames
from app.core.enum import Role
from app.core.exception import NotFoundError,AlreadyExistsError,MaximumLimitReachedError
from app.schemas.workspace_member import WorkspaceMemberResponse

class WorkspaceMemberService:
    def __init__(self):
        pass

    async def for_new_admin(self,workspace_id:str,**data):
        logger.info(f"for new admin function started")
        
        try:        
            created_at=datetime.now(timezone.utc)
            data["created_at"]=created_at
            
            hashed_password=hash_pw(password=data["password"])
            data["password"]=hashed_password
            
            new_admin=User(**data)

            response= await insert(
                collection_name=CollectionNames.users.value,
                new_obj=new_admin
            )
            logger.info(f"new user is created | new_user_id:{response.inserted_id}")

            new_workspace_member=WorkspaceMember(
                user_id=response.inserted_id,
                username=data["username"],
                workspace_id=workspace_id,
                role=Role.COMPANY_ADMIN.value,
                joined_at=created_at
            )            
            workspace_member_response= await insert(
                collection_name=CollectionNames.workspace_members.value,
                new_obj=new_workspace_member
            )
            logger.info(f"new workspace_member is created for new admin | new_user_id:{response.inserted_id} and workspace_id: {workspace_id}")
            
            return new_workspace_member
        
        except Exception as e:
            logger.error(f"new admin is not created | error={e}")
            raise
    
    async def for_existing_admin(self,workspace_id:str,**data):
        logger.info(f"for existing admin function started")

        try:
            email=data["email"]

            result= await find_user(
                collection_name=CollectionNames.users.value,
                email=email
            )
            if result is None:
                raise NotFoundError(f"email: {email} is not found")
            
            result_data=UserValidation.model_validate(result)
            user_id=result_data.user_id

            user_response= await find_workspace_member(
                workspace_id=workspace_id,
                user_id=user_id
            )
            if user_response:
                raise AlreadyExistsError(f"user_id: {user_id} is already exist")
            
            new_workspace_member=WorkspaceMember(
                user_id=user_id,
                username=data["username"],
                workspace_id=workspace_id,
                role=Role.COMPANY_ADMIN.value,
                joined_at=datetime.now(timezone.utc)
            )
            workspace_member_response=await insert(
                collection_name=CollectionNames.workspace_members.value,
                new_obj=new_workspace_member
            )
            logger.info(f"new user is created | new_user_id:{user_id}")

            return new_workspace_member
        
        except Exception as e:
            logger.error(f"new admin is not created | error={e}")
            raise

    async def create_new_admin(self, workspace_id: str, current_admin_id: str, **data):
        logger.info(f"new admin creation is started by | current_user_id:{current_admin_id}")

        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=current_admin_id,
                min_role="COMPANY_ADMIN"
            )

            admin_count = await count_document(
                collection_name=CollectionNames.workspace_members.value,
                workspace_id=workspace_id
            )
            if admin_count >= 3:
                raise MaximumLimitReachedError("maximum number of admin reached")

            email = data["email"]
            existing_user = await find_user(
                collection_name=CollectionNames.users.value,
                email=email
            )

            if existing_user:
                workspace_member_response = await self.for_existing_admin(
                    workspace_id=workspace_id,
                    **data
                )
            else:
                if not data.get("password"):
                    raise ValueError("password is required to create a new user")
                workspace_member_response = await self.for_new_admin(
                    workspace_id=workspace_id,
                    **data
                )

            return WorkspaceMemberResponse(
                user_id=workspace_member_response.user_id,
                username=workspace_member_response.username,
                role=workspace_member_response.role,
                joined_at=workspace_member_response.joined_at,
                status=workspace_member_response.status
            )

        except Exception as e:
            logger.error(f"new admin is not created | error={e}")
            raise
    
    async def admin_transfer(self,workspace_id:str,current_admin_id:str,user_id:str):
        logger.info(f"admin transfer function is started by | current_user_id:{current_admin_id}")
        async with await client.start_session() as session:
            try:
                async with session.start_transaction():
                    await verify_role(
                        workspace_id=workspace_id,
                        user_id=current_admin_id,
                        min_role=Role.COMPANY_ADMIN.value
                    )
                    result= await find_workspace_member(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        session=session
                    )
                    if result is None:
                        raise NotFoundError(f"user_id: {user_id} is not found")
                    
                    new_admin_result=await update_member_to_admin(
                        workspace_id=workspace_id,
                        new_admin_id=user_id,
                        session=session
                    )
                    await update_admin_to_member(
                        workspace_id=workspace_id,
                        current_admin_id=current_admin_id,
                        session=session
                    )
                    logger.info(f"admin transfer is completed by | current_admin_id:{current_admin_id}")

                    return WorkspaceMemberResponse(
                            user_id=new_admin_result["user_id"],
                            username=new_admin_result["username"],
                            role=new_admin_result["role"],
                            joined_at=new_admin_result["joined_at"],
                            status=new_admin_result["status"]
                        )
            except Exception as e:
                logger.error(f"new admin is not created | error={e}")
                raise
    
    async def update_member_position(self,workspace_id:str,admin_id:str,member_id:str,role:str):
        logger.info(f"update member role function is started by | admin_id: {admin_id}")

        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=admin_id,
                min_role=Role.COMPANY_ADMIN.value
            )
            result=await update_member_role(
                workspace_id=workspace_id,
                user_id=member_id,
                role=role
            )
            logger.info(f"member position updated successfully | member_id:{member_id} admin_id:{admin_id}")

            return WorkspaceMemberResponse(
                    user_id=result["user_id"],
                    username=result["username"],
                    role=result["role"],
                    joined_at=result["joined_at"],
                    status=result["status"]
                )

        except Exception as e:
            logger.error(f"member role update failed | error: {e}")
            raise
    
    async def remove_member_from_workspace(self,workspace_id:str,admin_id:str,user_id:str):
        logger.info(f"remove member function started by | admin_id:{admin_id}")
        async with await client.start_session() as session:
            try:
                async with session.start_transaction():
                    await verify_role(
                        workspace_id=workspace_id,
                        user_id=admin_id,
                        min_role=Role.COMPANY_ADMIN.value
                    )
                    result= await find_workspace_member(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        session=session
                    )
                    if result is None:
                        raise NotFoundError(f"user_id: {user_id} is not found")
                    
                    await member_status_to_delete(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        session=session
                    )
                    await remove_member_from_team(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        session=session
                    )
                    await remove_team_manager_from_project(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        session=session
                    )
                    await remove_project_manager_from_project(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        session=session
                    )
                    await remove_member_from_workspace(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        session=session
                    )
                    await remove_assignee_from_task(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        session=session
                    )
                    logger.info(f"member removed successfully by | admin_id:{admin_id} removed_user_id:{user_id}")
            
            except Exception as e:
                logger.error(f"member role update failed | error: {e}")
                raise