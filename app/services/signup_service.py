from loguru import logger
from datetime import datetime,timezone
from app.core.enum import CollectionNames,Role
from app.core.exception import AlreadyExistsError
from app.core.auth import hash_pw
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.database.db_connection import client
from app.database.repositories.base_repository import insert
from app.database.repositories.workspace_repository import find_workspaces_by_domain,insert_member_in_workspace,find_workspaces_by_id
from app.database.repositories.user_repository import find_user
from app.database.repositories.workspace_member_repository import find_workspace_member
from app.core.exception import NotFoundError
from app.schemas.signup import DomainLookupResponse,SignupResponse,NewUserResponse

class SignupService:
    def __init__(self):
        pass

    async def create_fresh_user(self,name: str, email: str, password: str):
        logger.info(f"create fresh user started | email:{email}")
        try:
            existing = await find_user(
                collection_name=CollectionNames.users.value,
                email=email
            )
            if existing:
                raise AlreadyExistsError(f"email:{email} already registered")

            created_at = datetime.now(timezone.utc)

            new_user = User(
                name=name,
                email=email,
                password=hash_pw(password=password),
                created_at=created_at
            )
            result = await insert(
                collection_name=CollectionNames.users.value,
                new_obj=new_user
            )
            user_id = str(result.inserted_id)
            logger.info(f"create fresh user completed | user_id:{user_id} email:{email}")

            return NewUserResponse(
                user_id=user_id,
                name=name,
                email=email,
                created_at=created_at
            )
        except Exception as e:
            logger.error(f"create fresh user failed | error:{e}")
            raise

    async def fresh_signup(self,user_id:str,username:str,email:str,company_name:str):
        logger.info(f"Fresh signup started | email:{email}")
        async with await client.start_session() as session:
            try:
                async with session.start_transaction():
                    created_at = datetime.now(timezone.utc)
                    
                    new_workspace=Workspace(
                        company_name=company_name,
                        created_at=created_at,
                        owner_ids=[user_id]
                    )
                    result= await insert(
                        collection_name=CollectionNames.workspaces.value,
                        new_obj=new_workspace,
                        session=session
                    )
                    workspace_id=str(result.inserted_id)
                    new_member=WorkspaceMember(
                        user_id=user_id,
                        username=username,
                        workspace_id=workspace_id,
                        role=Role.COMPANY_ADMIN.value,
                        joined_at=created_at
                    )
                    member_result= await insert(
                        collection_name=CollectionNames.workspace_members.value,
                        new_obj=new_member,
                        session=session
                    )
                    insert_member=await insert_member_in_workspace(
                        collection_name=CollectionNames.workspaces.value,
                        workspace_id=workspace_id,
                        user_id=new_member.user_id,
                        session=session
                    )
                    logger.info(f"Fresh signup complete | user_id:{user_id} workspace_id:{workspace_id}")
                    
                    return SignupResponse(
                        workspace_id=workspace_id,
                        user_id=user_id,
                        username=username,
                        role=new_member.role,
                        joined_at=created_at
                    )
            except Exception as e:
                logger.error(f"Fresh signup failed | email:{email} error:{e}")
                raise
    
    async def get_workspaces_for_domain(self,email: str):
        user = await find_user(
            collection_name=CollectionNames.users.value,
            email=email
        )
        if user is None:
            raise NotFoundError(f"email:{email} is not found")

        domain = email.split("@")[1]
        workspaces=await find_workspaces_by_domain(
            collection_name=CollectionNames.workspaces.value,
            domain=domain
        )

        return DomainLookupResponse(workspaces=[
            {
                "workspace_id":w.workspace_id,
                "company_name":w.company_name
            }
            for w in workspaces
        ]
        )

    async def domain_signup(self,email:str,workspace_id:str,username:str):
        logger.info(f"Domain signup started | email:{email} workspace_id:{workspace_id}")
        async with await client.start_session() as session:
            try:
                async with session.start_transaction():
                    
                    user = await find_user(
                        collection_name=CollectionNames.users.value,
                        email=email,
                        session=session
                    )
                    if user is None:
                        raise NotFoundError(f"email:{email} is not found")

                    existing_member = await find_workspace_member(
                        workspace_id=workspace_id,
                        user_id=str(user["_id"]),
                        session=session
                    )
                    if existing_member:
                        raise AlreadyExistsError(f"user already member of workspace_id:{workspace_id}")
                    
                    domain = email.split("@")[1]

                    workspace = await find_workspaces_by_id(
                        collection_name=CollectionNames.workspaces.value,
                        domain=domain,
                        workspace_id=workspace_id,
                        session=session
                    )
                    if not workspace:
                        raise NotFoundError(f"No workspace found matching domain:{domain}")
                    
                    created_at=datetime.now(timezone.utc)
                    
                    new_member=WorkspaceMember(
                        user_id=str(user["_id"]),
                        username=username,
                        workspace_id=workspace_id,
                        role=Role.MEMBER.value,
                        joined_at=created_at
                    )
                    result=await insert(
                        collection_name=CollectionNames.workspace_members.value,
                        new_obj=new_member,
                        session=session
                    )
                    insert_member=await insert_member_in_workspace(
                        collection_name=CollectionNames.workspaces.value,
                        workspace_id=workspace_id,
                        user_id=new_member.user_id,
                        session=session
                    )
                    logger.info(f"Domain signup complete | user_id:{new_member.user_id} workspace_id:{workspace_id}")
                    
                    return SignupResponse(
                        workspace_id=workspace_id,
                        user_id=new_member.user_id,
                        username=username,
                        role=new_member.role,
                        joined_at=created_at
                    ) 
            except Exception as e:
                logger.error(f"Domain signup failed | error:{e}")
                raise