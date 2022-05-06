from datetime import timedelta
from pytest_bdd import given, then, when, parsers

from src.app.controllers.devices_controller import DevicesController
from src.app.utils.http.request import Request
from src.common import dates
from src.domain.models.device import Device
from src.domain.models.user import User
from src.infrastructure.repositories.device_pg_repository import DevicePGRepository
from src.infrastructure.repositories.measure_pg_repository import MeasurePGRepository
from tests.integration.utils import shared_variables
from tests.model_stubs.measure_stub import MeasureStub


@given(parsers.cfparse('device with id \'{device_id}\' exists for logged user'))
def device_exists_for_logged_user(device_id: str):
    device_repository = DevicePGRepository()
    device = Device(name=device_id, device_id=device_id)
    user_id = User.email_to_id(shared_variables.logged_auth_info.user_email)
    if not device_repository.exists_for_user(device_id, user_id):
        device_repository.create(device, user_id)


@given(parsers.cfparse('device with id \'{device_id}\' has recent measures'))
def device_has_recent_measures(device_id: str):
    measure_repository = MeasurePGRepository()
    minutes_interval = 0.0
    while minutes_interval <= 10:  # Until 10 minutes
        measure = MeasureStub(timestamp=dates.now() - timedelta(minutes=minutes_interval))
        measure_repository.create(measure, device_id)
        minutes_interval += 0.5


@when(parsers.cfparse('user tries to create device with name \'{device_name}\''))
def try_user_login(device_name: str):
    controller = DevicesController(request=Request.from_body({
        'name': device_name
    }),
        auth_info=shared_variables.logged_auth_info)
    shared_variables.last_response = controller.create()


@when(parsers.cfparse('user tries to add a measure for device with id \'{device_id}\''))
def try_add_valid_measure(device_id: str):
    controller = DevicesController(request=Request.from_body(MeasureStub().to_dict()),
                                   auth_info=shared_variables.logged_auth_info)
    shared_variables.last_response = controller.add_measure(device_id)


@when(parsers.cfparse('user tries to add an invalid measure for device with id \'{device_id}\''))
def try_add_invalid_measure(device_id: str):
    measure_dict = {
        **MeasureStub().to_dict(), **{
            'voltage': -200.0,
            'current': -5.0
        }
    }
    controller = DevicesController(request=Request.from_body(measure_dict), auth_info=shared_variables.logged_auth_info)
    shared_variables.last_response = controller.add_measure(device_id)


@when(parsers.cfparse('user tries to get measures for device with id \'{device_id}\''))
def try_get_measures_for_device(device_id: str):
    controller = DevicesController(request=None, auth_info=shared_variables.logged_auth_info)
    minutes_interval = 10
    shared_variables.last_response = controller.get_measures(device_id, minutes_interval)


@then('device is created successfully')
def device_created_successfully():
    assert shared_variables.last_response.status_code == 201


@then('measure is added successfully')
def measure_added_successfully():
    assert shared_variables.last_response.status_code == 201


@then('measure addition fails')
def measure_addition_fails():
    assert shared_variables.last_response.status_code == 400


@then('summarized measures are returned successfully')
def summarized_measures_returned_successfully():
    assert shared_variables.last_response.status_code == 200
    assert len(shared_variables.last_response.body) > 0
    for measure in shared_variables.last_response.body:
        assert 'current' in measure
        assert 'voltage' in measure
        assert 'power' in measure
        assert 'timestamp' in measure
