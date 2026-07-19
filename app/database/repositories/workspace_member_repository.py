from loguru import logger
from bson import ObjectId
from app.database.db_connection import db,client
from pymongo import ReturnDocument
from app.core.enum import CollectionNames,Role,WorkspaceMemberStatus
from app.core.exception import NotFoundError

async def find_workspace_member(workspace_id:str,user_id:str,session=None):
    logger.debug(f"searching workspace member | collection={CollectionNames.workspace_members.value}")
    try:
        result= await db[CollectionNames.workspace_members.value].find_one(
            {
                "user_id":user_id,
                "workspace_id":workspace_id
            },
            session=session
        )
        return result
    except Exception as e:
        logger.error(f"find workspace member failed | error={e}")
        raise

async def count_document(collection_name:str,workspace_id:str):
    logger.debug(f"count document is started | collection={collection_name} workspace_id:{workspace_id}")
    try:
        result= await db[collection_name].count_documents(
            {
                "workspace_id":workspace_id,
                "role":Role.COMPANY_ADMIN.value
            }
        )
        
        return result
    except Exception as e:
        logger.error(f"count document failed | error={e}")
        raise

async def update_member_to_admin(workspace_id:str,new_admin_id:str,session=None):
    logger.debug(f"update member to admin started | workspace_id:{workspace_id}")
    try:
        result=await db[CollectionNames.workspace_members.value].find_one_and_update(
            {
                        "workspace_id":workspace_id,
                        "user_id":new_admin_id
                    },
                    {
                        "$set":{
                            "role":Role.COMPANY_ADMIN.value
                        }
                    },
                    session=session
        )
        if result is None:
            raise NotFoundError(f"new_admin_id:{new_admin_id} not found")

        return result
    except Exception as e:
        logger.error(f"update member to admin failed | error: {e}")
        raise

async def update_admin_to_member(workspace_id:str,current_admin_id:str,session=None):
    logger.debug(f"update admin to member started | workspace_id:{workspace_id}")
    try:
        result= await db[CollectionNames.workspace_members.value].find_one_and_update(
            {
                "workspace_id":workspace_id,
                "user_id":current_admin_id
            },
            {
                "$set":{
                    "role":Role.MEMBER.value
                }
            },
            session=session
        )
        if result is None:
            raise NotFoundError(f"user_id:{current_admin_id} is not found")
        return result
    except Exception as e:
        logger.error(f"update admin to member failed | error={e}")
        raise

async def update_member_role(workspace_id:str,user_id:str,role:str):
    logger.debug(f"searching workspace member for update | collection={CollectionNames.workspace_members.value}")
    try:
        result=await db[CollectionNames.workspace_members.value].find_one_and_update(
            {
                "workspace_id":workspace_id,
                "user_id":user_id
            },
            {
                "$set":{
                    "role":role
                    }
            },
            return_document=ReturnDocument.AFTER)
        
        if result is None:
            raise NotFoundError(f"member_id: {user_id} is not found")
        
        logger.info(f"member role updated |  member_id:{user_id}")
        return result
        
    except Exception as e:
        logger.error(f"member role update failed | error: {e}")
        raise

async def member_status_to_delete(workspace_id:str,user_id:str,session=None):
    logger.debug(f"workspace member status to delete is started | workspace_id:{workspace_id} user_id:{user_id}")
    try:
        result=await db[CollectionNames.workspace_members.value].update_one(
            {
                "workspace_id": workspace_id,
                "user_id": user_id
            },
            {
                "$set":{
                    "status":WorkspaceMemberStatus.DELETED.value
                }
            },
            session=session
        )
        if result is None:
            raise NotFoundError(f"user_id:{user_id} is not found")
        
        return result
    except Exception as e:
        logger.error(f"workspace member status to delete is failed | error={e}")
        raise

async def count_workspace_stats(workspace_id:str) -> dict:
    logger.debug(f"count workspace stats started | workspace_id:{workspace_id}")
    try:
        total_members= await db[CollectionNames.workspace_members.value].count_documents(
            {
                "workspace_id":workspace_id,
                "status":WorkspaceMemberStatus.ACTIVE.value
            }
        )
        admin_seats_used= await db[CollectionNames.workspace_members.value].count_documents(
            {
                "workspace_id":workspace_id,
                "role":Role.COMPANY_ADMIN.value
            }
        )

        return {
            "total_members":total_members,
            "pending_invites":0,  # no Invitation model/collection exists yet
            "admin_seats_used":admin_seats_used,
            "admin_seats_max":3
        }
    except Exception as e:
        logger.error(f"count workspace stats failed | error={e}")
        raise

async def get_all_member_list(query_filter,session=None):
    logger.debug(f"get all member list is started | workspace:{query_filter["workspace_id"]}")
    try:
        result= await db[CollectionNames.workspace_members.value].find(
            query_filter,
            session=session
            ).to_list()

        return result
    except Exception as e:
        logger.error(f"get all member list is failed | error={e}")
        raise