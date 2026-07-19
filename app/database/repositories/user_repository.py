from loguru import logger
from bson import ObjectId
from app.database.db_connection import db

async def find_user(collection_name:str,email:str,session=None):
    logger.debug(f"searching user | collection={collection_name}")
    try:
        result= await db[collection_name].find_one(
            {
                "email":email
            },
            session=session
            )

        return result
    except Exception as e:
        logger.error(f"find user failed | error={e}")
        raise

async def find_user_by_id(collection_name:str,user_id:str,session=None):
    logger.debug(f"find user by id is started | user_id:{user_id}")
    try:
        result=await db[collection_name].find_one(
            {
                "_id":ObjectId(user_id)
            },
            session=session
        )
        return result
    except Exception as e:
        logger.error(f"find user by id is failed | error={e}")
        raise