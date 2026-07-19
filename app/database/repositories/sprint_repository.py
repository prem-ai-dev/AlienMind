from loguru import logger
from bson import ObjectId
from pymongo import ReturnDocument
from app.database.db_connection import db,client
from app.database.repositories.base_repository import insert
from app.models.sprint import Sprint
from app.core.enum import CollectionNames,SprintStatus,TaskStatus
from app.core.exception import NotFoundError,NotCreatedError

async def insert_and_add_sprint_in_project(new_sprint:Sprint,workspace_id:str,project_id:str):
    logger.debug(f"add sprint in project started | workspace_id:{workspace_id}, project_id:{project_id}")
    async with await client.start_session() as session:
        try:
            async with session.start_transaction():
                insert_result= await insert(collection_name=CollectionNames.sprints.value,new_obj=new_sprint,session=session)

                if not insert_result.acknowledged:
                    raise NotCreatedError(f"sprint not created")
                
                project_result=await db[CollectionNames.projects.value].find_one_and_update(     
                    {
                        "workspace_id":workspace_id,
                        "_id":ObjectId(project_id),
                    },
                    {
                    "$addToSet":{
                            "sprint_ids":str(insert_result.inserted_id)
                    }
                },
                return_document=ReturnDocument.AFTER,
                session=session
                )

                if project_result is None:
                    raise NotFoundError(f"project_id{project_id} is not found")
                
                result= await db[CollectionNames.sprints.value].find_one(
                    {
                        "workspace_id":workspace_id,
                        "_id":ObjectId(insert_result.inserted_id)     
                    },
                    session=session
                )

                return result
        except Exception as e:
                logger.error(f"add sprint in project is failed |error={e}")
                raise

async def get_active_sprints_summary(workspace_id:str) -> list[dict]:
    logger.debug(f"get active sprints summary started | workspace_id:{workspace_id}")
    try:
        pipeline=[
            {"$match":{"workspace_id":workspace_id,"status":SprintStatus.ACTIVE.value}},
            {
                "$lookup":{
                    "from":CollectionNames.tasks.value,
                    "let":{"sprint_id":{"$toString":"$_id"}},
                    "pipeline":[
                        {"$match":{"$expr":{"$eq":["$sprint_id","$$sprint_id"]}}}
                    ],
                    "as":"sprint_tasks"
                }
            },
            {
                "$addFields":{
                    "total_tasks":{"$size":"$sprint_tasks"},
                    "completed_tasks":{
                        "$size":{
                            "$filter":{
                                "input":"$sprint_tasks",
                                "cond":{"$eq":["$$this.status",TaskStatus.DONE.value]}
                            }
                        }
                    }
                }
            },
            {
                "$project":{
                    "_id":0,
                    "sprint_id":{"$toString":"$_id"},
                    "name":"$sprint_name",
                    "due_date":"$sprint_end_date",
                    "progress":{
                        "$cond":[
                            {"$eq":["$total_tasks",0]},
                            0,
                            {"$round":[{"$multiply":[{"$divide":["$completed_tasks","$total_tasks"]},100]},0]}
                        ]
                    }
                }
            }
        ]

        result= await db[CollectionNames.sprints.value].aggregate(pipeline).to_list()

        return result
    except Exception as e:
        logger.error(f"get active sprints summary failed | error={e}")
        raise

async def get_active_sprints_for_projects(workspace_id:str,project_ids:list[str]) -> list[dict]:
    logger.debug(f"get active sprints for projects started | workspace_id:{workspace_id} project_ids:{project_ids}")
    try:
        pipeline=[
            {"$match":{"workspace_id":workspace_id,"status":SprintStatus.ACTIVE.value,"project_id":{"$in":project_ids}}},
            {
                "$lookup":{
                    "from":CollectionNames.tasks.value,
                    "let":{"sprint_id":{"$toString":"$_id"}},
                    "pipeline":[
                        {"$match":{"$expr":{"$eq":["$sprint_id","$$sprint_id"]}}}
                    ],
                    "as":"sprint_tasks"
                }
            },
            {
                "$addFields":{
                    "total_tasks":{"$size":"$sprint_tasks"},
                    "completed_tasks":{
                        "$size":{
                            "$filter":{
                                "input":"$sprint_tasks",
                                "cond":{"$eq":["$$this.status",TaskStatus.DONE.value]}
                            }
                        }
                    }
                }
            },
            {
                "$project":{
                    "_id":0,
                    "sprint_id":{"$toString":"$_id"},
                    "name":"$sprint_name",
                    "due_date":"$sprint_end_date",
                    "progress":{
                        "$cond":[
                            {"$eq":["$total_tasks",0]},
                            0,
                            {"$round":[{"$multiply":[{"$divide":["$completed_tasks","$total_tasks"]},100]},0]}
                        ]
                    }
                }
            }
        ]

        result= await db[CollectionNames.sprints.value].aggregate(pipeline).to_list()

        return result
    except Exception as e:
        logger.error(f"get active sprints for projects failed | error={e}")
        raise

async def change_sprint_status(workspace_id:str,sprint_id:str,project_id:str,status:str):
    logger.debug(f"change sprint status started | workspace_id:{workspace_id} sprint_id:{sprint_id}")
    try:
        result =await db[CollectionNames.sprints.value].find_one_and_update(
            {
                "workspace_id":workspace_id,
                "_id":ObjectId(sprint_id),
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
            raise NotFoundError(f"sprint_id:{sprint_id} is not found")
        
        return result
    except Exception as e:
            logger.error(f"change sprint status is failed |error={e}")
            raise