from loguru import logger
from app.utils.role_checker import verify_role
from app.core.enum import Role
from app.database.repositories.project_repository import find_project_ids_by_manager,find_projects_by_manager
from app.database.repositories.team_repository import find_teams_by_manager,list_teams_detailed
from app.database.repositories.task_repository import count_tasks_by_status_for_projects,get_overdue_tasks_for_projects
from app.database.repositories.sprint_repository import get_active_sprints_for_projects

class ManagerDashboardService:
    def __init__(self):
        pass

    async def get_dashboard_stats(self,workspace_id:str,user_id:str) -> dict:
        logger.info(f"get dashboard stats function started | workspace_id:{workspace_id} user_id:{user_id}")
        try:
            await verify_role(
                workspace_id=workspace_id,
                user_id=user_id,
                min_role=Role.MANAGER.value
            )

            owned_project_ids= await find_project_ids_by_manager(workspace_id=workspace_id,manager_id=user_id)
            managed_teams= await find_teams_by_manager(workspace_id=workspace_id,manager_id=user_id)
            team_project_ids=[pid for team in managed_teams for pid in team.get("project_ids",[])]
            managed_project_ids= list(set(owned_project_ids) | set(team_project_ids))

            owned_team_ids=[str(team["_id"]) for team in managed_teams]
            managed_projects= await find_projects_by_manager(workspace_id=workspace_id,manager_id=user_id)
            project_team_ids=[tid for project in managed_projects for tid in project.get("team_ids",[])]
            managed_team_ids= list(set(owned_team_ids) | set(project_team_ids))

            task_stats= await count_tasks_by_status_for_projects(workspace_id=workspace_id,project_ids=managed_project_ids)
            overdue_tasks= await get_overdue_tasks_for_projects(workspace_id=workspace_id,project_ids=managed_project_ids)
            active_sprints= await get_active_sprints_for_projects(workspace_id=workspace_id,project_ids=managed_project_ids)
            teams_detailed= await list_teams_detailed(workspace_id=workspace_id,team_ids_filter=managed_team_ids)

            logger.info(f"get dashboard stats function completed | workspace_id:{workspace_id} user_id:{user_id}")

            return {
                "totalProjectsManaged":len(owned_project_ids),
                "totalTeamsManaged":len(teams_detailed),
                "taskStats":{
                    "todo":task_stats["todo"],
                    "inProgress":task_stats["in_progress"],
                    "inReview":task_stats["in_review"],
                    "completed":task_stats["completed"],
                    "cancelled":task_stats["cancelled"]
                },
                "activeSprints":active_sprints,
                "myTeams":[
                    {
                        "team_id":team["team_id"],
                        "team_name":team["team_name"],
                        "member_count":team["member_count"],
                        "pending_count":team["pending_count"],
                        "in_progress_count":team["in_progress_count"]
                    }
                    for team in teams_detailed
                ],
                "overdueTasks":overdue_tasks
            }
        except Exception as e:
            logger.error(f"get dashboard stats function failed | error={e}")
            raise
