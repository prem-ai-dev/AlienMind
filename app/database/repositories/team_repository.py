from loguru import logger
from bson import ObjectId
from typing import Optional
from app.database.db_connection import db,client
from pymongo import ReturnDocument
from app.core.enum import CollectionNames, TeamStatus, TaskStatus
from app.core.exception import NotFoundError
from app.database.repositories.workspace_member_repository import find_workspace_member

async def find_team_by_name(workspace_id:str,team_name:str):
    logger.debug(f"searching for team by name | workspace_id:{workspace_id} collection={CollectionNames.teams.value}")
    try:
        result=await db[CollectionNames.teams.value].find_one(
            {
                "workspace_id":workspace_id,
                "team_name":team_name
            }
        )
        return result
    except Exception as e:
        logger.error(f"fetching team function failed | error: {e}")
        raise

async def find_team_by_id(workspace_id: str, team_id: str):
    logger.debug(f"searching for team by id | team_id={team_id}")
    try:
        result = await db[CollectionNames.teams.value].find_one(
            {
                "workspace_id": workspace_id,
                "_id": ObjectId(team_id)
            }
        )
        return result
    except Exception as e:
        logger.error(f"fetching team by id failed | error: {e}")
        raise

async def insert_new_member(workspace_id:str,team_id:str,user_id:str):
    logger.debug(f"search and insert new member started | team_id={team_id} user_id:{user_id}")
    async with await client.start_session() as session:
        try:
            async with session.start_transaction():
                result = await db[CollectionNames.teams.value].find_one_and_update(
                    {
                        "workspace_id": workspace_id,
                        "_id": ObjectId(team_id)
                    },
                    {
                        "$addToSet": {
                            "member_ids": user_id
                        }
                    },
                    return_document=ReturnDocument.AFTER,
                    session=session
                )

                if result is None:
                    raise NotFoundError(f"team_id: {team_id} not found or update failed")

                await db[CollectionNames.workspace_members.value].update_one(
                    {
                        "workspace_id":workspace_id,
                        "user_id":user_id
                    },
                    {
                        "$addToSet":{
                            "team_ids":team_id
                        }
                    },
                    session=session
                )
                
                return result
        except Exception as e:
            logger.error(f"inserting new member to team failed | error: {e}")
            raise

async def remove_member_and_unassign_tasks(workspace_id: str,team_id: str,user_id: str):
    logger.debug(f"search and remove team member started | team_id={team_id} user_id:{user_id}")
    async with await client.start_session() as session:
        try:
            async with session.start_transaction():
                team = await db[CollectionNames.teams.value].find_one_and_update(
                    {
                        "workspace_id": workspace_id,
                        "_id":ObjectId(team_id)
                    },
                    {
                        "$pull": {
                            "member_ids": user_id
                        }
                    },
                    return_document=ReturnDocument.AFTER,
                    session=session,
                )

                if team is None:
                    raise NotFoundError(f"Team_id: {team_id} is not found")

                update_result = await db[CollectionNames.tasks.value].update_many(
                    {
                        "project_id": {"$in": team.get("project_ids",[])},
                        "assignee_id": user_id,
                        "status": {"$ne": TaskStatus.DONE.value},
                    },
                    {
                        "$set": {
                            "assignee_id": None
                        }
                    },
                    session=session,
                )

                await db[CollectionNames.teams.value].update_one(
                    {
                        "workspace_id":workspace_id,
                        "_id":ObjectId(team_id),
                        "team_manager_id":user_id
                    },
                    {
                        
                        "$set":{
                            "team_manager_id":None
                        }                        
                    },
                    session=session
                )

                await db[CollectionNames.workspace_members.value].update_one(
                    {
                        "workspace_id":workspace_id,
                        "user_id":user_id
                    },
                    {
                        "$pull":{
                            "team_ids":team_id
                        }
                    },
                    session=session
                )
                if team.get("team_manager_id") == user_id:
                    team["team_manager_id"] = None

                return team
        
        except Exception as e:
            logger.error(f"removing team member from team failed | error: {e}")
            raise

async def insert_team_manager(workspace_id:str,team_id:str,team_manager_id:str):
    logger.debug(f"search and insert team manager started | workspace_id={workspace_id}, team_id={team_id}")
    try:
        result = await db[CollectionNames.teams.value].find_one_and_update(
            {
                "workspace_id": workspace_id,
                "_id": ObjectId(team_id),
            },
            {
                "$set":{
                    "team_manager_id": team_manager_id
                },
                "$addToSet":{
                    "member_ids": team_manager_id
                }
            },
            return_document=ReturnDocument.AFTER
        )
        if result is None:
            raise NotFoundError(f"Team_id: {team_id} is not found")
        
        return result
    
    except Exception as e:
        logger.error(f"insert_team_manager failed: {e}")
        raise

async def delete_team_and_remove_from_lists(workspace_id: str, team_id: str):
    logger.debug(f"delete team function started | team_id={team_id}")
    async with await client.start_session() as session:
        try:
            async with session.start_transaction():
                team = await db[CollectionNames.teams.value].find_one_and_update(
                    {
                        "workspace_id": workspace_id,
                        "_id": ObjectId(team_id)
                    },
                    {
                        "$set": {"status": TeamStatus.DELETED.value}
                    },
                    return_document=ReturnDocument.BEFORE,
                    session=session,
                )

                if team is None:
                    raise NotFoundError(f"team_id: {team_id} is not found")

                await db[CollectionNames.workspaces.value].update_one(
                    {
                        "_id": ObjectId(workspace_id)
                    },
                    {
                        "$pull": {"teams_ids": team_id}
                    },
                    session=session,
                )
                await db[CollectionNames.projects.value].update_many(
                    {
                        "workspace_id": workspace_id,
                        "team_ids": team_id
                    },
                    {
                        "$pull": {
                            "team_ids": team_id
                        }
                    },
                    session=session,
                )
                task_result = await db[CollectionNames.tasks.value].update_many(
                    {
                        "project_id": {"$in": team.get("project_ids", [])},
                        "assignee_id": {"$in": team.get("member_ids", [])},
                        "status": {"$ne": TaskStatus.DONE.value},
                    },
                    {"$set": {"assignee_id": None}},
                    session=session,
                )
                await db[CollectionNames.workspace_members.value].update_many(
                    {
                        "workspace_id": workspace_id,
                        "team_ids": team_id
                    },
                    {
                        "$pull": {
                            "team_ids": team_id
                        }
                    },
                    session=session,
                )

                logger.info(f"team deleted successfully | team_id={team_id}")
                return {"team": team, "tasks_unassigned": task_result.modified_count}

        except Exception as e:
            logger.error(f"delete team failed | error: {e}")
            raise

async def list_teams(workspace_id:str):
    logger.debug(f"list teams started | workspace_id:{workspace_id}")
    try:
        result= await db[CollectionNames.teams.value].find(
            {
                "workspace_id":workspace_id,
                "status":TeamStatus.ACTIVE.value
            },
            {"_id":1,"team_name":1}
        ).to_list()

        return [
            {"team_id":str(team["_id"]),"name":team["team_name"]}
            for team in result
        ]
    except Exception as e:
        logger.error(f"list teams failed | error: {e}")
        raise

async def list_teams_detailed(workspace_id: str, team_ids_filter: Optional[list[str]] = None) -> list[dict]:
    logger.debug(f"list teams detailed started | workspace_id:{workspace_id}")
    try:
        match_stage = {
            "workspace_id": workspace_id,
            "status": TeamStatus.ACTIVE.value
        }
        if team_ids_filter is not None:
            match_stage["_id"] = {"$in": [ObjectId(tid) for tid in team_ids_filter]}

        pipeline = [
            {
                "$match": match_stage
            },
            {
                "$lookup": {
                    "from": CollectionNames.workspace_members.value,
                    "localField": "team_manager_id",
                    "foreignField": "user_id",
                    "as": "manager_info"
                }
            },
            {
                "$unwind": {
                    "path": "$manager_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$lookup": {
                    "from": CollectionNames.workspace_members.value,
                    "let": {"member_ids": "$member_ids"},
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$user_id", "$$member_ids"]}}},
                        {"$project": {"_id": 0, "user_id": 1, "username": 1}}
                    ],
                    "as": "team_members"
                }
            },
            {
                "$lookup": {
                    "from": CollectionNames.tasks.value,
                    "let": {"team_project_ids": "$project_ids"},
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$project_id", "$$team_project_ids"]}}}
                    ],
                    "as": "team_tasks"
                }
            },
            {
                "$addFields": {
                    "team_members": {
                        "$map": {
                            "input": "$team_members",
                            "as": "member",
                            "in": {
                                "user_id": "$$member.user_id",
                                "username": "$$member.username",
                                "pending_count": {
                                    "$size": {
                                        "$filter": {
                                            "input": "$team_tasks",
                                            "cond": {
                                                "$and": [
                                                    {"$eq": ["$$this.assignee_id", "$$member.user_id"]},
                                                    {"$eq": ["$$this.status", TaskStatus.TODO.value]}
                                                ]
                                            }
                                        }
                                    }
                                },
                                "in_progress_count": {
                                    "$size": {
                                        "$filter": {
                                            "input": "$team_tasks",
                                            "cond": {
                                                "$and": [
                                                    {"$eq": ["$$this.assignee_id", "$$member.user_id"]},
                                                    {"$eq": ["$$this.status", TaskStatus.IN_PROGRESS.value]}
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "pending_count": {
                        "$size": {
                            "$filter": {
                                "input": "$team_tasks",
                                "cond": {"$eq": ["$$this.status", TaskStatus.TODO.value]}
                            }
                        }
                    },
                    "in_progress_count": {
                        "$size": {
                            "$filter": {
                                "input": "$team_tasks",
                                "cond": {"$eq": ["$$this.status", TaskStatus.IN_PROGRESS.value]}
                            }
                        }
                    },
                    "completed_count": {
                        "$size": {
                            "$filter": {
                                "input": "$team_tasks",
                                "cond": {"$eq": ["$$this.status", TaskStatus.DONE.value]}
                            }
                        }
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "team_id": {"$toString": "$_id"},
                    "team_name": 1,
                    "team_manager_id": 1,
                    "team_manager_name": "$manager_info.username",
                    "member_count": {"$size": "$member_ids"},
                    "members": "$team_members",
                    "pending_count": 1,
                    "in_progress_count": 1,
                    "completed_count": 1
                }
            }
        ]

        result = await db[CollectionNames.teams.value].aggregate(pipeline).to_list()

        return result
    except Exception as e:
        logger.error(f"list teams detailed failed | error: {e}")
        raise

async def remove_member_from_team(workspace_id:str,user_id:str,session=None):
    logger.debug(f"remove member from team started | workspace_id:{workspace_id} user_id:{user_id}")
    try:
        result=await db[CollectionNames.teams.value].update_many(
            {
                "workspace_id":workspace_id,
                "member_ids": user_id
            },
            {
                "$pull":{
                    "member_ids":user_id
                }
            },
            session=session
        )
    except Exception as e:
        logger.debug(f"remove member from team failed | error={e}")
        raise

async def get_my_team(workspace_id:str,user_id:str) -> Optional[dict]:
    logger.debug(f"get my team started | workspace_id:{workspace_id} user_id:{user_id}")
    try:
        member= await find_workspace_member(workspace_id=workspace_id,user_id=user_id)
        team_ids= member.get("team_ids",[]) if member else []
        if not team_ids:
            return None

        team= await db[CollectionNames.teams.value].find_one(
            {
                "workspace_id":workspace_id,
                "_id":ObjectId(team_ids[0])
            }
        )
        if team is None:
            return None

        members= await db[CollectionNames.workspace_members.value].find(
            {
                "workspace_id":workspace_id,
                "user_id":{"$in":team.get("member_ids",[])}
            },
            {"_id":0,"user_id":1,"username":1}
        ).to_list()

        return {
            "team_name":team["team_name"],
            "members":members
        }
    except Exception as e:
        logger.error(f"get my team failed | error={e}")
        raise

async def find_teams_by_manager(workspace_id:str,manager_id:str) -> list[dict]:
    logger.debug(f"find teams by manager started | workspace_id:{workspace_id} manager_id:{manager_id}")
    try:
        result= await db[CollectionNames.teams.value].find(
            {
                "workspace_id":workspace_id,
                "team_manager_id":manager_id,
                "status":TeamStatus.ACTIVE.value
            },
            {"project_ids":1}
        ).to_list()

        return result
    except Exception as e:
        logger.error(f"find teams by manager failed | error={e}")
        raise

async def find_teams_by_ids(workspace_id:str,team_ids:list[str]) -> list[dict]:
    logger.debug(f"find teams by ids started | workspace_id:{workspace_id} team_ids:{team_ids}")
    try:
        result= await db[CollectionNames.teams.value].find(
            {
                "workspace_id":workspace_id,
                "_id":{"$in":[ObjectId(team_id) for team_id in team_ids]}
            },
            {"member_ids":1}
        ).to_list()

        return result
    except Exception as e:
        logger.error(f"find teams by ids failed | error={e}")
        raise

async def remove_team_manager_from_project(workspace_id:str,user_id:str,session=None):
    logger.debug(f"remove team manager from project started | workspace_id:{workspace_id} user_id:{user_id}")
    try:
        await db[CollectionNames.teams.value].update_many(
            {
                "workspace_id":workspace_id,
                "team_manager_id":user_id
            },
            {
                "$set":{
                    "team_manager_id":None
                }
            },
            session=session
        )
    except Exception as e:
        logger.debug(f"remove team manager from project failed | error={e}")
        raise