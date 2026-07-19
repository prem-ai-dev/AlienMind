from loguru import logger
from app.utils.role_checker import verify_role
from app.core.enum import Role,WorkspaceMemberStatus,CollectionNames
from app.schemas.workspace_member import MemberListResponse
from app.database.repositories.workspace_member_repository import count_workspace_stats,get_all_member_list
from app.database.repositories.project_repository import count_total_projects
from app.database.repositories.task_repository import count_tasks_by_status
from app.database.repositories.sprint_repository import get_active_sprints_summary
from app.database.repositories.base_repository import count_any_doc

class AdminDashboardService:
    def __init__(self):
        pass

    async def get_dashboard_stats(self,workspace_id:str) -> dict:
        logger.info(f"get dashboard stats function started | workspace_id:{workspace_id}")
        try:
            member_stats= await count_workspace_stats(workspace_id=workspace_id)
            total_projects= await count_total_projects(workspace_id=workspace_id)
            task_stats= await count_tasks_by_status(workspace_id=workspace_id)
            active_sprints= await get_active_sprints_summary(workspace_id=workspace_id)

            logger.info(f"get dashboard stats function completed | workspace_id:{workspace_id}")

            return {
                "totalMembers":member_stats["total_members"],
                "totalProjects":total_projects,
                "pendingInvites":member_stats["pending_invites"],
                "adminSeatsUsed":member_stats["admin_seats_used"],
                "adminSeatsMax":member_stats["admin_seats_max"],
                "inProgressTasks":task_stats["in_progress"],
                "reviewTasks":task_stats["in_review"],
                "completedTasks":task_stats["completed"],
                "cancelledTasks":task_stats["cancelled"],
                "activeSprints":active_sprints,
                "recentActivity":[]
            }
        except Exception as e:
            logger.error(f"get dashboard stats function failed | error={e}")
            raise

async def list_of_member(workspace_id:str,user_id:str,**search):
    logger.info(f"list of member func started | ")
    try:
        await verify_role(
            workspace_id=workspace_id,
            user_id=user_id,
            min_role=Role.MANAGER.value
        )
        query_filter={"workspace_id": workspace_id,**{k:v for k,v in search.items() if v is not None},"status":WorkspaceMemberStatus.ACTIVE.value}

        result=await get_all_member_list(
            query_filter=query_filter
        )
        count_result= await count_any_doc(
            collection_name=CollectionNames.workspace_members.value,
            query_filter=query_filter
        )
        return MemberListResponse(
            members=[
                {
                    "user_id":res["user_id"],
                    "username":res["username"],
                    "role":res["role"],
                    "joined_at":res["joined_at"]
                } for res in result
            ],
            count=count_result
        )

    except Exception as e:
        logger.error(f"list of member func failed | error={e}")
        raise
