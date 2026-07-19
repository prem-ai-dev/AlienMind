from loguru import logger
from datetime import datetime,timezone
from app.database.db_connection import client
from app.models.workspace import Workspace
from app.database.repositories.base_repository import insert
from app.database.repositories.user_repository import find_user_by_id
from app.database.repositories.workspace_repository import add_domain_to_workspace
from app.models.workspace_member import WorkspaceMember
from app.core.enum import CollectionNames,Role
from app.core.exception import NotFoundError
from app.schemas.signup import SignupResponse
from app.utils.role_checker import verify_role
from app.core.enum import Role
from app.schemas.workspace import WorkspaceResponse

class WorkspaceService:
    def __init__(self):
        pass

    async def create_workspace(self,username:str,company_name:str,owner_id:str):
        logger.info(f"Creating workspace | user_id:{owner_id}")        
        async with await client.start_session() as session:    
            try:
                async with session.start_transaction():
                    
                    user=await find_user_by_id(
                        collection_name=CollectionNames.users.value,
                        user_id=owner_id,
                        session=session
                    )
                    if user is None:
                        raise NotFoundError(f"user_id:{owner_id} is not found")

                    created_at=datetime.now(timezone.utc)

                    new_workspace=Workspace(
                        company_name=company_name,
                        created_at=created_at,
                        owner_ids=[owner_id],
                        member_ids=[owner_id]
                    )
                    result= await insert(
                        collection_name=CollectionNames.workspaces.value,
                        new_obj=new_workspace,
                        session=session
                    )
                    logger.info(f"Workspace created successful | workspace_id:{result.inserted_id}")

                    new_workspace_member=WorkspaceMember(
                        user_id=owner_id,
                        username=username,
                        workspace_id=str(result.inserted_id),
                        role=Role.COMPANY_ADMIN.value,
                        joined_at=created_at
                    )
                    response=await insert(
                        collection_name=CollectionNames.workspace_members.value,
                        new_obj=new_workspace_member,
                        session=session
                    )            
                    logger.info(f"Workspace_member created successful | workspace_member_id:{response.inserted_id}")

                    return SignupResponse(
                        workspace_id=str(result.inserted_id),
                        user_id=owner_id,
                        username=username,
                        role=new_workspace_member.role,
                        joined_at=created_at
                    )
            
            except Exception as e:
                logger.error(f"Workspace creation failed | error={e}")
                raise

    async def add_allowed_domain(self,workspace_id:str,admin_id:str,domain:str):
        logger.info(f"Adding allowed domain | workspace_id:{workspace_id} domain:{domain}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=admin_id,
                min_role=Role.COMPANY_ADMIN.value
            )
            result=await add_domain_to_workspace(
                workspace_id=workspace_id,
                domain=domain
            )
            logger.info(f"Allowed domain added successfully | workspace_id:{workspace_id}")

            return WorkspaceResponse(
                workspace_id=str(result["_id"]),
                company_name=result["company_name"],
                allowed_domains=result["allowed_domains"],
                created_at=result["created_at"]
            )
        except Exception as e:
            logger.error(f"Adding allowed domain failed | error={e}")
            raise