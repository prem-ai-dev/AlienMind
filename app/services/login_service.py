from loguru import logger
from app.database.repositories.user_repository import find_user
from app.core.enum import CollectionNames
from app.core.exception import NotFoundError
from app.schemas.user import UserValidation
from app.core.auth import verify_pw
from app.database.repositories.workspace_repository import find_workspace_list
from app.schemas.workspace import WorkspaceValidate
from app.utils.role_checker import verify_role
from app.core.enum import Role
from app.database.repositories.workspace_member_repository import find_workspace_member
from app.core.exception import NotFoundError,EnteredWrongPasswordError

class LoginService:
    def __init__(self):
        pass

    async def verify_login(self,email:str,password:str):
        logger.info(f"verify login function started | email:{email}")
        try:
            result= await find_user(
                collection_name=CollectionNames.users.value,
                email=email
            )
            if result is None:
                raise NotFoundError(f"email:{email} is not found")
            
            user= UserValidation.model_validate(result)
            
            status= verify_pw(
                password=password,
                hashed_password=user.password
            )
            if not status:
                raise EnteredWrongPasswordError("password is wrong")
            
            workspace_result= await find_workspace_list(user_id=user.user_id)

            workspace_list=[WorkspaceValidate.model_validate(res) for res in workspace_result]
            
            return user,workspace_list
        
        except Exception as e:
            logger.error(f"verify login function failed | email:{email}")
            raise
    
    async def verify_membership(self,workspace_id:str,user_id:str):
        logger.info(f"verify membership function started | user_id:{user_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MEMBER.value
            )

            result= await find_workspace_member(
                workspace_id=workspace_id,
                user_id=user_id
            )
            if result is None:
                raise NotFoundError(f"user_id:{user_id} is not found")
            
            logger.info(f"verify membership function completed | user_id:{user_id}")
            return result
        
        except Exception as e:
            logger.error(f"verify membership function is failed | error={e}")
            raise