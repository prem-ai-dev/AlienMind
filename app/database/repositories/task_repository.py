from loguru import logger
from bson import ObjectId
from typing import Optional
from datetime import datetime,timezone,timedelta
from pymongo import ReturnDocument
from app.database.db_connection import db
from app.core.enum import CollectionNames,TaskStatus
from app.core.exception import NotFoundError

async def find_task_by_name(workspace_id:str,task_name:str):
    logger.debug(f"find task by name started | workspace:{workspace_id}")
    try:
        result= await db[CollectionNames.tasks.value].find_one(
            {
                "workspace_id":workspace_id,
                "task_name":task_name
            }
        )

        return result
    except Exception as e:
        logger.error(f"find task by name failed | error={e}")
        raise

async def find_task_by_id(workspace_id:str,task_id:str):
    logger.debug(f"find task by id started | workspace:{workspace_id} task_id:{task_id}")
    try:
        result= await db[CollectionNames.tasks.value].find_one(
            {
                "workspace_id":workspace_id,
                "_id":ObjectId(task_id)
            }
        )

        return result
    except Exception as e:
        logger.error(f"find task by name failed | error={e}")
        raise

async def update_sprint_in_task(workspace_id:str,project_id:str,task_id:str,sprint_id:str):
    logger.debug(f"update sprint in task started | workspace:{workspace_id} task_id:{task_id} sprint_id:{sprint_id}")
    try:
        result= await db[CollectionNames.tasks.value].find_one_and_update(
            {
                "workspace_id":workspace_id,
                "project_id":project_id,
                "_id":ObjectId(task_id)
            },
            {
                "$set":{
                    "sprint_id":sprint_id
                }
            },
            return_document=ReturnDocument.AFTER
        )
        if result is None:
            raise NotFoundError(f"task_id: {task_id} is not found")
        
        return result
    except Exception as e:
        logger.error(f"update sprint in task failed | error={e}")
        raise

async def remove_sprint_in_task(workspace_id:str,project_id:str,task_id:str,sprint_id:str):
    logger.info(f"remove sprint in task | workspace:{workspace_id} task_id:{task_id} sprint_id:{sprint_id}")
    try:
        result= await db[CollectionNames.tasks.value].find_one_and_update(
            {
                "workspace_id":workspace_id,
                "_id":ObjectId(task_id),
                "project_id":project_id,
                "sprint_id":sprint_id
            },
            {
                "$set":{
                    "sprint_id":None
                }
            },
            return_document=ReturnDocument.AFTER
        )
        if result is None:
            raise NotFoundError(f"task_id:{task_id} is not found")
        
        return result
    except Exception as e:
        logger.error(f"remove sprint in task failed | error={e}")
        raise

async def task_status_update(workspace_id:str,project_id:str,task_id:str,status:str):
    logger.debug(f"task status update started | workspace_id:{workspace_id} task_id:{task_id}")
    try:
        result= await db[CollectionNames.tasks.value].find_one_and_update(
            {
                "workspace_id":workspace_id,
                "_id":ObjectId(task_id),
                "project_id":project_id
            },
            {
                "$set":{
                    "status":status
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if result is None:
            raise NotFoundError(f"task_id:{task_id} is not found")
        
        return result
    except Exception as e:
        logger.error(f"task status update failed | error={e}")
        raise

async def update_member_to_task(workspace_id:str,project_id:str,task_id:str,member_id:str):
    logger.debug(f"update member to task started | workspace_id:{workspace_id} task_id:{task_id} member_id:{member_id}")
    try:
        result= await db[CollectionNames.tasks.value].find_one_and_update(
            {
                "workspace_id":workspace_id,
                "_id":ObjectId(task_id),
                "project_id":project_id
            },
            {
                "$set":{
                    "assignee_id":member_id
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if result is None:
            raise NotFoundError(f"task_id:{task_id} is not found")
        
        return result
    except Exception as e:
        logger.error(f"update member to task failed | error={e}")
        raise

async def change_member_from_task(workspace_id:str,project_id:str,task_id:str,member_id:str):
    logger.debug(f"change member from task started | workspace_id:{workspace_id} task_id:{task_id} member_id:{member_id}")
    try:
        result= await db[CollectionNames.tasks.value].find_one_and_update(
            {
                "workspace_id":workspace_id,
                "_id":ObjectId(task_id),
                "project_id":project_id,
                "assignee_id":member_id
            },
            {
                "$set":{
                    "assignee_id":None
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if result is None:
            raise NotFoundError(f"task_id:{task_id} is not found")
        
        return result
    except Exception as e:
        logger.error(f"change member from task failed | error={e}")
        raise

async def list_tasks_by_sprint(workspace_id:str,sprint_id:str):
    logger.debug(f"list tasks by sprint started | workspace_id:{workspace_id} sprint_id:{sprint_id}")
    try:
        pipeline=[
            {"$match":{"workspace_id":workspace_id,"sprint_id":sprint_id}},
            {
                "$lookup":{
                    "from":CollectionNames.workspace_members.value,
                    "localField":"assignee_id",
                    "foreignField":"user_id",
                    "as":"assignee_info"
                }
            },
            {
                "$project":{
                    "_id":0,
                    "task_id":{"$toString":"$_id"},
                    "title":"$task_name",
                    "status":1,
                    "priority":1,
                    "assignee":{
                        "$cond":[
                            {"$eq":["$assignee_id",None]},
                            None,
                            {"user_id":"$assignee_id","username":{"$arrayElemAt":["$assignee_info.username",0]}}
                        ]
                    }
                }
            }
        ]

        result= await db[CollectionNames.tasks.value].aggregate(pipeline).to_list()

        return result
    except Exception as e:
        logger.error(f"list tasks by sprint failed | error={e}")
        raise

async def list_tasks_aggregated(
    workspace_id:str,
    search:Optional[str],
    project_id:Optional[str],
    assignee_id:Optional[str],
    status:Optional[str],
    priority:Optional[str],
    page:int,
    page_size:int,
    mine_or_unassigned_user_id:Optional[str]=None,
    manager_project_ids:Optional[list[str]]=None
) -> tuple[list[dict], int]:
    logger.debug(f"list tasks aggregated started | workspace_id:{workspace_id} page:{page} page_size:{page_size}")
    try:
        if mine_or_unassigned_user_id is not None and assignee_id is not None:
            raise ValueError("assignee_id and mine_or_unassigned_user_id are mutually exclusive")

        query_filter={"workspace_id":workspace_id}

        if project_id is not None:
            query_filter["project_id"]=project_id
        if assignee_id is not None:
            query_filter["assignee_id"]=assignee_id
        if status is not None:
            query_filter["status"]=status
        if priority is not None:
            query_filter["priority"]=priority
        if search:
            query_filter["$or"]=[
                {"task_name":{"$regex":search,"$options":"i"}},
                {"$expr":{"$eq":[{"$toString":"$_id"},search]}}
            ]
        if mine_or_unassigned_user_id is not None:
            query_filter["$or"] = [
                {"assignee_id": mine_or_unassigned_user_id},
                {"assignee_id": None}
            ]
        if manager_project_ids is not None and project_id is None:
            query_filter["project_id"] = {"$in": manager_project_ids}

        total_count= await db[CollectionNames.tasks.value].count_documents(query_filter)

        pipeline=[
            {"$match":query_filter},
            {
                "$lookup":{
                    "from":CollectionNames.workspace_members.value,
                    "localField":"assignee_id",
                    "foreignField":"user_id",
                    "as":"assignee_info"
                }
            },
            {
                "$unwind":{
                    "path":"$assignee_info",
                    "preserveNullAndEmptyArrays":True
                }
            },
            {"$skip":(page-1)*page_size},
            {"$limit":page_size},
            {
                "$project":{
                    "_id":0,
                    "task_id":{"$toString":"$_id"},
                    "task_name":1,
                    "status":1,
                    "priority":1,
                    "project_id":1,
                    "sprint_id":1,
                    "due_date":1,
                    "assignee":{
                        "$cond":[
                            {"$eq":["$assignee_id",None]},
                            None,
                            {"user_id":"$assignee_id","username":"$assignee_info.username"}
                        ]
                    }
                }
            }
        ]

        result= await db[CollectionNames.tasks.value].aggregate(pipeline).to_list()

        return result, total_count
    except Exception as e:
        logger.error(f"list tasks aggregated failed | error={e}")
        raise

async def get_task_detail(workspace_id:str,task_id:str):
    logger.debug(f"get task detail started | workspace_id:{workspace_id} task_id:{task_id}")
    try:
        result = await db[CollectionNames.tasks.value].find_one(
            {
                "workspace_id":workspace_id,
                "_id":ObjectId(task_id)
            }
        )
        return result
    except Exception as e:
        logger.error(f"get task detail failed | error={e}")
        raise

async def count_tasks_by_status(workspace_id:str):
    logger.debug(f"count tasks by status started | workspace_id:{workspace_id}")
    try:
        in_progress= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"status":TaskStatus.IN_PROGRESS.value}
        )
        in_review= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"status":TaskStatus.IN_REVIEW.value}
        )
        completed= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"status":TaskStatus.DONE.value}
        )
        cancelled= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"status":TaskStatus.CANCELLED.value}
        )

        return {
            "in_progress":in_progress,
            "in_review":in_review,
            "completed":completed,
            "cancelled":cancelled
        }
    except Exception as e:
        logger.error(f"count tasks by status failed | error={e}")
        raise

async def count_tasks_by_status_for_user(workspace_id:str,user_id:str) -> dict:
    logger.debug(f"count tasks by status for user started | workspace_id:{workspace_id} user_id:{user_id}")
    try:
        todo= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"assignee_id":user_id,"status":TaskStatus.TODO.value}
        )
        in_progress= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"assignee_id":user_id,"status":TaskStatus.IN_PROGRESS.value}
        )
        in_review= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"assignee_id":user_id,"status":TaskStatus.IN_REVIEW.value}
        )
        completed= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"assignee_id":user_id,"status":TaskStatus.DONE.value}
        )
        cancelled= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"assignee_id":user_id,"status":TaskStatus.CANCELLED.value}
        )

        return {
            "todo":todo,
            "in_progress":in_progress,
            "in_review":in_review,
            "completed":completed,
            "cancelled":cancelled
        }
    except Exception as e:
        logger.error(f"count tasks by status for user failed | error={e}")
        raise

async def get_overdue_and_upcoming_tasks(workspace_id:str,user_id:str) -> dict:
    logger.debug(f"get overdue and upcoming tasks started | workspace_id:{workspace_id} user_id:{user_id}")
    try:
        now= datetime.now(timezone.utc)
        projection={"task_name":1,"due_date":1,"status":1,"priority":1,"project_id":1}

        overdue_docs= await db[CollectionNames.tasks.value].find(
            {
                "workspace_id":workspace_id,
                "assignee_id":user_id,
                "due_date":{"$lt":now},
                "status":{"$nin":[TaskStatus.DONE.value,TaskStatus.CANCELLED.value]}
            },
            projection
        ).sort("due_date",1).to_list()

        upcoming_docs= await db[CollectionNames.tasks.value].find(
            {
                "workspace_id":workspace_id,
                "assignee_id":user_id,
                "due_date":{"$gte":now,"$lte":now + timedelta(days=7)},
                "status":{"$nin":[TaskStatus.DONE.value,TaskStatus.CANCELLED.value]}
            },
            projection
        ).sort("due_date",1).to_list()

        def _project_task(doc):
            return {
                "task_id":str(doc["_id"]),
                "task_name":doc["task_name"],
                "due_date":doc["due_date"],
                "status":doc["status"],
                "priority":doc["priority"],
                "project_id":doc["project_id"]
            }

        return {
            "overdue":[_project_task(doc) for doc in overdue_docs],
            "upcoming":[_project_task(doc) for doc in upcoming_docs]
        }
    except Exception as e:
        logger.error(f"get overdue and upcoming tasks failed | error={e}")
        raise

async def count_tasks_by_status_for_projects(workspace_id:str,project_ids:list[str]) -> dict:
    logger.debug(f"count tasks by status for projects started | workspace_id:{workspace_id} project_ids:{project_ids}")
    try:
        todo= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"project_id":{"$in":project_ids},"status":TaskStatus.TODO.value}
        )
        in_progress= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"project_id":{"$in":project_ids},"status":TaskStatus.IN_PROGRESS.value}
        )
        in_review= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"project_id":{"$in":project_ids},"status":TaskStatus.IN_REVIEW.value}
        )
        completed= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"project_id":{"$in":project_ids},"status":TaskStatus.DONE.value}
        )
        cancelled= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"project_id":{"$in":project_ids},"status":TaskStatus.CANCELLED.value}
        )

        return {
            "todo":todo,
            "in_progress":in_progress,
            "in_review":in_review,
            "completed":completed,
            "cancelled":cancelled
        }
    except Exception as e:
        logger.error(f"count tasks by status for projects failed | error={e}")
        raise

async def get_overdue_tasks_for_projects(workspace_id:str,project_ids:list[str]) -> list[dict]:
    logger.debug(f"get overdue tasks for projects started | workspace_id:{workspace_id} project_ids:{project_ids}")
    try:
        now= datetime.now(timezone.utc)

        docs= await db[CollectionNames.tasks.value].find(
            {
                "workspace_id":workspace_id,
                "project_id":{"$in":project_ids},
                "due_date":{"$lt":now},
                "status":{"$nin":[TaskStatus.DONE.value,TaskStatus.CANCELLED.value]}
            },
            {"task_name":1,"due_date":1,"priority":1,"project_id":1}
        ).sort("due_date",1).to_list()

        return [
            {
                "task_id":str(doc["_id"]),
                "task_name":doc["task_name"],
                "due_date":doc["due_date"],
                "priority":doc["priority"],
                "project_id":doc["project_id"]
            }
            for doc in docs
        ]
    except Exception as e:
        logger.error(f"get overdue tasks for projects failed | error={e}")
        raise

async def remove_assignee_from_task(workspace_id:str,user_id:str,session=None):
    logger.debug(f"remove assignee from task started |workspace_id:{workspace_id} user_id:{user_id}")
    try:
        await db[CollectionNames.tasks.value].update_many(
            {
                "workspace_id":workspace_id,
                "assignee_id":user_id,
                "status":{
                    "$ne":"COMPLETED"
                }
            },
            {
                "$set":{
                    "assignee_id":None
                }
            },
            session=session
        )
    except Exception as e:
        logger.error(f"remove assignee from task failed | error={e}")
        raise