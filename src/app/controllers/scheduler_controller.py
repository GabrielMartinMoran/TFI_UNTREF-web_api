from src.app.utils.auth_info import AuthInfo
from src.app.utils.http.request import Request
from src.domain.exceptions.device_not_found_exception import DeviceNotFoundException
from pymodelio.exceptions.model_validation_exception import ModelValidationException
from src.domain.mappers.scheduling.tasks.task_mapper import TaskMapper
from src.domain.serializers.scheduling.scheduler_action_serializer import SchedulerActionSerializer
from src.domain.serializers.scheduling.tasks.task_serializer import TaskSerializer
from src.domain.services.device_scheduler.device_scheduler_retriever import DeviceSchedulerRetriever
from src.domain.services.device_scheduler.device_scheduler_updater import DeviceSchedulerUpdater
from src.app.utils.http.response import Response
from src.app.utils.http.route import route
from src.app.utils.logging.logger import Logger
from src.app.controllers.base_controller import BaseController
from src.app.utils.http import http_methods
from src.infrastructure.repositories.device_pg_repository import DevicePGRepository
from src.infrastructure.repositories.device_scheduler_pg_repository import DeviceSchedulerPGRepository


class SchedulerController(BaseController):

    def __init__(self, request: Request, auth_info: AuthInfo = None) -> None:
        super().__init__(request, auth_info)
        self.device_repository = DevicePGRepository()
        self.device_scheduler_repository = DeviceSchedulerPGRepository()

    @route(http_methods.POST)
    def set_scheduling_tasks(self, device_id: str) -> Response:
        try:
            tasks = TaskMapper.map_all(self.get_json_body())
            updater = DeviceSchedulerUpdater(self.device_repository, self.device_scheduler_repository)
            updater.set_scheduling_tasks(device_id, self.get_authenticated_user_id(), tasks)
            return Response.success()
        except ModelValidationException as e:
            Logger.error(e)
            return Response.bad_request(message=str(e))
        except DeviceNotFoundException as e:
            Logger.error(e)
            return Response.bad_request('Provided device_id does not match any of the user devices')
        except Exception as e:
            Logger.error(e)
            return Response.server_error('An error has occurred while updating device scheduling')

    @route(http_methods.GET)
    def get_scheduling_tasks(self, device_id: str) -> Response:
        try:
            retriever = DeviceSchedulerRetriever(self.device_repository, self.device_scheduler_repository)
            tasks = retriever.get_scheduling_tasks(device_id, self.get_authenticated_user_id())
            return Response.success(TaskSerializer.serialize_all(tasks))
        except ModelValidationException as e:
            Logger.error(e)
            return Response.bad_request(validation_errors=e.validation_errors)
        except DeviceNotFoundException as e:
            Logger.error(e)
            return Response.bad_request('Provided device_id does not match any of the user devices')
        except Exception as e:
            Logger.error(e)
            return Response.server_error('An error has occurred while getting device scheduling')

    @route(http_methods.GET)
    def get_next_scheduling_action(self, device_id: str) -> Response:
        try:
            retriever = DeviceSchedulerRetriever(self.device_repository, self.device_scheduler_repository)
            scheduler_action = retriever.get_next_scheduling_action(device_id, self.get_authenticated_user_id())
            return Response.success(
                SchedulerActionSerializer.serialize(scheduler_action) if scheduler_action is not None else {}
            )
        except ModelValidationException as e:
            Logger.error(e)
            return Response.bad_request(validation_errors=e.validation_errors)
        except DeviceNotFoundException as e:
            Logger.error(e)
            return Response.bad_request('Provided device_id does not match any of the user devices')
        except Exception as e:
            Logger.error(e)
            return Response.server_error('An error has occurred while getting device next scheduling action')
