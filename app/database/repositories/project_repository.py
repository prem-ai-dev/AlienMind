from loguru import logger
from bson import ObjectId
from app.database.db_connection import db,client
from pymongo import ReturnDocument
from app.core.enum import CollectionNames,TaskStatus,SprintStatus
from app.core.exception import NotFoundError,UpdateFailedError

async def find_project_by_title(workspace_id:str,project_title:str):
    logger.debug(f"searching project by name started | collection_name:{CollectionNames.projects.value} project_title:{project_title}")

    try:
        result = await db[CollectionNames.projects.value].find_one(
            {
                "workspace_id":workspace_id,
                "project_title":project_title
            }
        )

        return result
    except Exception as e:
            logger.error(f"fetch project by title function failed | error: {e}")
            raise

async def find_project_by_id(workspace_id:str,project_id:str):
    logger.debug(f"searching project by id started | workspace_id:{workspace_id} project_id:{project_id}")\
     
    try:
        result=await db[CollectionNames.projects.value].find_one(
           {
                "workspace_id":workspace_id,
                "_id":ObjectId(project_id)
           }
        )
        return result
    except Exception as e:
            logger.error(f"searching project by id failed | error: {e}")
            raise 

async def insert_manager_to_project(workspace_id:str,project_id:str,manager_id:str):
    logger.debug(f"insert manager id to project is started | project_id:{project_id}")

    try:
        result= await db[CollectionNames.projects.value].find_one_and_update(
            {
                "workspace_id":workspace_id,
                "_id":ObjectId(project_id)
            },
            {
                 "$set":{
                      "project_manager_id":manager_id
                    }
            },
            return_document=ReturnDocument.AFTER
        )    
        if result is None:
            raise NotFoundError(f"project_id: {project_id} is not found")
        
        return result
    except Exception as e:
        logger.error(f"inserting manager id to project failed | error: {e}")
        raise

async def find_and_update_project_status(workspace_id:str,project_id:str,status:str):
    logger.debug(f"find_and_update_project_status started | workspace_id:{workspace_id} project_id:{project_id}")
    try:
        result = await db[CollectionNames.projects.value].find_one_and_update(
            {
                "workspace_id": workspace_id,
                "_id": ObjectId(project_id),
            },
            {
                "$set": {
                    "status": status
                }
            },
            return_document=ReturnDocument.AFTER,
        )

        if result is None:
            raise UpdateFailedError(f"project update failed — project may have been modified or reassigned")

        return result

    except Exception as e:
        logger.error(f"find_and_update_project_status failed | error={e}")
        raise

async def insert_team_in_project(workspace_id:str,project_id:str,team_id:str,):
    logger.debug(f"insert_team_in_project started | workspace_id:{workspace_id} project_id:{project_id}")
    async with await client.start_session() as session: 
        try:
            async with session.start_transaction():
                project_result = await db[CollectionNames.projects.value].find_one_and_update(
                    {
                        "workspace_id": workspace_id,
                        "_id": ObjectId(project_id),
                    },
                    {
                        "$addToSet": {
                            "team_ids": team_id
                        }
                    },
                    session=session,
                    return_document=ReturnDocument.AFTER,
                )

                if project_result is None:
                    raise NotFoundError(f"project_id: {project_id} not found")

                team_result = await db[CollectionNames.teams.value].find_one_and_update(
                    {
                        "workspace_id": workspace_id,
                        "_id": ObjectId(team_id),
                    },
                    {
                        "$addToSet": {
                            "project_ids": project_id
                        }
                    },
                    session=session,
                    return_document=ReturnDocument.AFTER,
                )

                if team_result is None:
                    raise NotFoundError(f"team_id: {team_id} not found")

                return project_result

        except Exception as e:
            logger.error(f"insert_team_in_project failed | error={e}")
            raise

async def pull_team_from_project(workspace_id:str,project_id:str,team_id:str,):
    logger.debug(f"pull_team_from_project started | workspace_id:{workspace_id} project_id:{project_id}")
    async with await client.start_session() as session: 
        try:
            async with session.start_transaction():
                project_result = await db[CollectionNames.projects.value].find_one_and_update(
                    {
                        "workspace_id": workspace_id,
                        "_id": ObjectId(project_id),
                        "team_ids":team_id
                    },
                    {
                        "$pull": {
                            "team_ids": team_id
                        }
                    },
                    session=session,
                    return_document=ReturnDocument.AFTER,
                )

                if project_result is None:
                    raise NotFoundError(f"project_id: {project_id} not found")

                team_result = await db[CollectionNames.teams.value].find_one_and_update(
                    {
                        "workspace_id": workspace_id,
                        "_id": ObjectId(team_id),
                        "project_ids":project_id
                    },
                    {
                        "$pull": {
                            "project_ids": project_id
                        }
                    },
                    session=session,
                    return_document=ReturnDocument.AFTER,
                )

                if team_result is None:
                    raise NotFoundError(f"team_id: {team_id} not found")

                return project_result

        except Exception as e:
            logger.error(f"pull_team_from_project failed | error={e}")
            raise

async def list_projects_aggregated(workspace_id:str):
    logger.debug(f"list projects aggregated started | workspace_id:{workspace_id}")

    try:
        pipeline=[
            {"$match":{"workspace_id":workspace_id}},
            {
                "$lookup":{
                    "from":CollectionNames.workspace_members.value,
                    "localField":"project_manager_id",
                    "foreignField":"user_id",
                    "as":"manager_info"
                }
            },
            {
                "$unwind":{
                    "path":"$manager_info",
                    "preserveNullAndEmptyArrays":True
                }
            },
            {
                "$lookup":{
                    "from":CollectionNames.teams.value,
                    "let":{"team_ids":"$team_ids"},
                    "pipeline":[
                        {"$match":{"$expr":{"$in":[{"$toString":"$_id"},"$$team_ids"]}}},
                        {"$project":{"_id":0,"team_id":{"$toString":"$_id"},"name":"$team_name"}}
                    ],
                    "as":"teams"
                }
            },
            {
                "$lookup":{
                    "from":CollectionNames.tasks.value,
                    "let":{"project_id":{"$toString":"$_id"}},
                    "pipeline":[
                        {"$match":{"$expr":{"$eq":["$project_id","$$project_id"]}}}
                    ],
                    "as":"tasks"
                }
            },
            {
                "$lookup":{
                    "from":CollectionNames.sprints.value,
                    "let":{"project_id":{"$toString":"$_id"}},
                    "pipeline":[
                        {"$match":{"$expr":{"$eq":["$project_id","$$project_id"]}}},
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
                                "status":1,
                                "progress":{
                                    "$cond":[
                                        {"$eq":["$total_tasks",0]},
                                        0,
                                        {"$round":[{"$multiply":[{"$divide":["$completed_tasks","$total_tasks"]},100]},0]}
                                    ]
                                }
                            }
                        }
                    ],
                    "as":"sprints"
                }
            },
            {
                "$project":{
                    "_id":0,
                    "project_id":{"$toString":"$_id"},
                    "project_title":1,
                    "status":1,
                    "project_manager_id":1,
                    "project_manager_name":"$manager_info.username",
                    "teams":1,
                    "task_count":{"$size":"$tasks"},
                    "tasks_summary":{
                        "todo":{
                            "$size":{
                                "$filter":{
                                    "input":"$tasks",
                                    "cond":{"$eq":["$$this.status",TaskStatus.TODO.value]}
                                }
                            }
                        },
                        "in_progress":{
                            "$size":{
                                "$filter":{
                                    "input":"$tasks",
                                    "cond":{"$eq":["$$this.status",TaskStatus.IN_PROGRESS.value]}
                                }
                            }
                        },
                        "completed":{
                            "$size":{
                                "$filter":{
                                    "input":"$tasks",
                                    "cond":{"$eq":["$$this.status",TaskStatus.DONE.value]}
                                }
                            }
                        },
                        "in_review":{
                            "$size":{
                                "$filter":{
                                    "input":"$tasks",
                                    "cond":{"$eq":["$$this.status",TaskStatus.IN_REVIEW.value]}
                                }
                            }
                        },
                        "cancelled":{
                            "$size":{
                                "$filter":{
                                    "input":"$tasks",
                                    "cond":{"$eq":["$$this.status",TaskStatus.CANCELLED.value]}
                                }
                            }
                        }
                    },
                    "sprints":1
                }
            }
        ]

        result= await db[CollectionNames.projects.value].aggregate(pipeline).to_list()

        return result
    except Exception as e:
        logger.error(f"list projects aggregated failed | error={e}")
        raise

async def get_project_dashboard_stats(workspace_id:str):
    logger.debug(f"get project dashboard stats started | workspace_id:{workspace_id}")

    try:
        total_projects= await db[CollectionNames.projects.value].count_documents(
            {"workspace_id":workspace_id}
        )
        active_sprints= await db[CollectionNames.sprints.value].count_documents(
            {"workspace_id":workspace_id,"status":SprintStatus.ACTIVE.value}
        )
        total_tasks= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id}
        )
        completed_tasks= await db[CollectionNames.tasks.value].count_documents(
            {"workspace_id":workspace_id,"status":TaskStatus.DONE.value}
        )
        completion_pct= round((completed_tasks/total_tasks)*100) if total_tasks else 0

        return {
            "total_projects":total_projects,
            "active_sprints":active_sprints,
            "total_tasks":total_tasks,
            "completion_pct":completion_pct
        }
    except Exception as e:
        logger.error(f"get project dashboard stats failed | error={e}")
        raise

async def count_total_projects(workspace_id:str) -> int:
    logger.debug(f"count total projects started | workspace_id:{workspace_id}")
    try:
        result= await db[CollectionNames.projects.value].count_documents(
            {"workspace_id":workspace_id}
        )

        return result
    except Exception as e:
        logger.error(f"count total projects failed | error={e}")
        raise

async def find_project_ids_by_manager(workspace_id:str,manager_id:str) -> list[str]:
    logger.debug(f"find project ids by manager started | workspace_id:{workspace_id} manager_id:{manager_id}")
    try:
        result= await db[CollectionNames.projects.value].find(
            {
                "workspace_id":workspace_id,
                "project_manager_id":manager_id
            },
            {"_id":1}
        ).to_list()

        return [str(doc["_id"]) for doc in result]
    except Exception as e:
        logger.error(f"find project ids by manager failed | error={e}")
        raise

async def find_projects_by_manager(workspace_id:str,manager_id:str) -> list[dict]:
    logger.debug(f"find projects by manager started | workspace_id:{workspace_id} manager_id:{manager_id}")
    try:
        result= await db[CollectionNames.projects.value].find(
            {
                "workspace_id":workspace_id,
                "project_manager_id":manager_id
            },
            {"team_ids":1}
        ).to_list()

        return result
    except Exception as e:
        logger.error(f"find projects by manager failed | error={e}")
        raise

async def remove_project_manager_from_project(workspace_id:str,user_id:str,session=None):
    logger.debug(f"remove project manager from project started |workspace_id:{workspace_id} user_id:{user_id}")
    try:
        await db[CollectionNames.projects.value].update_many(
            {
                "workspace_id":workspace_id,
                "project_manager_id":user_id
            },
            {
                "$set":{
                    "project_manager_id":None
                }
            },
            session=session
        )
    except Exception as e:
        logger.error(f"remove project manager from project failed | error={e}")
        raise