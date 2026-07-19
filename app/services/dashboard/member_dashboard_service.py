from loguru import logger
from app.services.project_service import ProjectService
from app.database.repositories.task_repository import count_tasks_by_status_for_user,get_overdue_and_upcoming_tasks
from app.database.repositories.team_repository import get_my_team

class MemberDashboardService:
    def __init__(self):
        self.project_service=ProjectService()

    async def get_dashboard_stats(self,workspace_id:str,user_id:str) -> dict:
        logger.info(f"get dashboard stats function started | workspace_id:{workspace_id} user_id:{user_id}")
        try:
            task_stats= await count_tasks_by_status_for_user(workspace_id=workspace_id,user_id=user_id)
            task_due_dates= await get_overdue_and_upcoming_tasks(workspace_id=workspace_id,user_id=user_id)
            my_team= await get_my_team(workspace_id=workspace_id,user_id=user_id)
            projects= await self.project_service.list_projects(workspace_id=workspace_id,user_id=user_id)

            logger.info(f"get dashboard stats function completed | workspace_id:{workspace_id} user_id:{user_id}")

            return {
                "taskStats":{
                    "todo":task_stats["todo"],
                    "inProgress":task_stats["in_progress"],
                    "inReview":task_stats["in_review"],
                    "completed":task_stats["completed"],
                    "cancelled":task_stats["cancelled"]
                },
                "overdueTasks":task_due_dates["overdue"],
                "upcomingTasks":task_due_dates["upcoming"],
                "myTeam":my_team,
                "totalProjects":len(projects)
            }
        except Exception as e:
            logger.error(f"get dashboard stats function failed | error={e}")
            raise
