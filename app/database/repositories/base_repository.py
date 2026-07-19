from loguru import logger
from app.database.db_connection import db

async def insert(collection_name:str,new_obj,session=None):
    logger.debug(f"Inserting document | collection={collection_name}")

    try:
        result= await db[collection_name].insert_one(
            new_obj.model_dump(),
            session=session
        )

        return result
    except Exception as e:
        logger.error(f"Insert is failed | error={e}")
        raise

async def count_any_doc(collection_name:str,query_filter:dict,session=None):
    logger.debug(f"count any doc started | workspace_id:{query_filter["workspace_id"]}")
    try:
        result= await db[collection_name].count_documents(
            query_filter,
            session=session
        )

        return result
    except Exception as e:
        logger.error(f"count any doc failed | error={e}")
        raise