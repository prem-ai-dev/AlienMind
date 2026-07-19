from bson import ObjectId
from pymongo import ReturnDocument
from app.database.db_connection import db
from loguru import logger
from app.core.enum import CollectionNames
from app.schemas.workspace import WorkspaceValidate
from app.core.exception import NotFoundError

async def find_workspace_list(user_id:str):
    logger.debug(f"find workspace list is started | user_id:{user_id}")
    try:
        result= await db[CollectionNames.workspaces.value].find({"member_ids":user_id}).to_list()

        return result
    except Exception as e:
        logger.error(f"find workspace list is failed | error={e}")
        raise

async def find_workspaces_by_domain(collection_name:str,domain:str,session=None):
    logger.debug(f"find workspace by domain is started | domain:{domain}")
    try:
        result= await db[collection_name].find(
            {
                "allowed_domains":domain
            },
            session=session
            ).to_list()

        result_list=[WorkspaceValidate.model_validate(res) for res in result]

        return result_list
    except Exception as e:
        logger.error(f"find workspace by domain is failed | error={e}")
        raise

async def find_workspaces_by_id(collection_name:str,domain:str,workspace_id:str,session=None):
    logger.debug(f"find workspace by id is started | workspace_id:{workspace_id}")
    try:
        result= await db[collection_name].find_one(
            {
                "allowed_domains":domain,
                "_id":ObjectId(workspace_id)
            },
            session=session
            )

        return result
    except Exception as e:
        logger.error(f"find workspace by id is failed | error={e}")
        raise

async def insert_member_in_workspace(collection_name:str,workspace_id:str,user_id:str,session=None):
    logger.debug(f"insert member in workspace is started | workspace_id:{workspace_id} user_id:{user_id}")
    try:
        result=await db[collection_name].find_one_and_update(
            {
                "_id":ObjectId(workspace_id)
            },
            {
                "$addToSet":{
                    "member_ids":user_id
                }
            },
            session=session
        )
        if result is None:
            raise NotFoundError(f"user_id:{user_id} is not found")
        
        return result
    except Exception as e:
        logger.error(f"insert member in workspace is failed | workspace_id:{workspace_id} user_id:{user_id}")
        raise

async def add_domain_to_workspace(workspace_id:str,domain:str,session=None):
    logger.debug(f"add domain to workspace is started | workspace_id:{workspace_id} domain:{domain}")
    try:
        result=await db[CollectionNames.workspaces.value].find_one_and_update(
            {
                "_id":ObjectId(workspace_id)
            },
            {
                "$addToSet":{
                    "allowed_domains":domain
                }
            },
            return_document=ReturnDocument.AFTER,
            session=session
        )
        if result is None:
            raise NotFoundError(f"workspace_id:{workspace_id} is not found")

        return result
    except Exception as e:
        logger.error(f"add domain to workspace is failed | error={e}")
        raise

async def remove_member_from_workspace(workspace_id:str,user_id,session=None):
    logger.debug(f"remove member from workspace started |workspace_id:{workspace_id} user_id:{user_id}")
    try:
        result=await db[CollectionNames.workspaces.value].find_one_and_update(
            {
                "_id": ObjectId(workspace_id)
            },
            {
                "$pull":{
                    "members_ids":user_id
                }
            },
            return_document=ReturnDocument.AFTER,
            session=session
        )
        if result is None:
            raise NotFoundError(f"workspace:{workspace_id} is not found")
        return result
    except Exception as e:
        logger.error(f"remove member from workspace failed | error={e}")
        raise