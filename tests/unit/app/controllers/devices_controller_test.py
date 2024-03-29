import random

from src.app.controllers.devices_controller import DevicesController
from src.app.utils.http.request import Request
from src.domain.models.device import Device
from src.domain.models.measure import Measure
from src.domain.serializers.measure_serializer import MeasureSerializer
from tests.model_stubs.measure_stub import MeasureStub


def test_device_controller_instantiate_device_repository_when_instantiated():
    controller = DevicesController(None)
    assert controller.device_repository is not None


def test_device_controller_instantiate_measure_repository_when_instantiated():
    controller = DevicesController(None)
    assert controller.measure_repository is not None


def test_create_returns_error_response_when_device_is_not_valid():
    controller = DevicesController(Request.from_body({
        'name': None
    }))
    actual = controller.create()
    assert actual.status_code == 400
    assert actual.body['message'] == 'Device._name must not be None'


def test_create_returns_error_response_when_device_with_same_ble_id_exists_for_user():
    controller = DevicesController(
        Request.from_body({
            'name': 'test_device',
            'device_id': '5c7b5ffc-90e7-1b85-f041-0595c912c905'
        }))
    controller.device_repository.exists_for_user = lambda ble_id, user_id: True
    actual = controller.create()
    assert actual.status_code == 409
    assert actual.body['message'] == 'There is another device with the same device_id for logged user'


def test_create_returns_ok_response_when_device_was_created_successfully():
    controller = DevicesController(Request.from_body({
        'name': 'test_device'
    }))
    controller.device_repository.exists_for_user = lambda device_id, user_id: False
    controller.device_repository.create = lambda device, user_id: device.device_id
    actual = controller.create()
    assert actual.status_code == 201
    assert isinstance(actual.body['id'], str)


def test_add_measure_returns_error_response_when_measure_is_not_valid():
    measure = MeasureStub()
    controller = DevicesController(Request.from_body({
        'timestamp': measure.timestamp.isoformat(),
        'voltage': measure.voltage,
        'current': None
    }))
    actual = controller.add_measure('5c7b5ffc-90e7-1b85-f041-0595c912c905')
    assert actual.status_code == 400
    assert actual.body['message'] == 'Measure._current must not be None'


def test_add_measure_returns_error_response_when_device_is_not_valid_for_user():
    controller = DevicesController(Request.from_body(MeasureSerializer.serialize(MeasureStub())))
    controller.device_repository.exists_for_user = lambda ble_id, user_id: False
    actual = controller.add_measure('5c7b5ffc-90e7-1b85-f041-0595c912c905')
    assert actual.status_code == 400
    assert actual.body['message'] == 'Device identifier is not valid for logged user'


def test_add_measure_returns_ok_response_when_measure_was_registered():
    controller = DevicesController(Request.from_body(MeasureSerializer.serialize(MeasureStub())))
    controller.device_repository.exists_for_user = lambda device_id, user_id: True
    controller.measure_repository.create = lambda measure, device_id: None
    actual = controller.add_measure('5c7b5ffc-90e7-1b85-f041-0595c912c905')
    assert actual.status_code == 201
    assert actual.body == {}


def test_add_measures_returns_error_response_when_any_measure_is_not_valid():
    measure = MeasureStub()
    controller = DevicesController(Request.from_body([{
        'timestamp': measure.timestamp.isoformat(),
        'voltage': measure.voltage,
        'current': None
    }]))
    actual = controller.add_measures('5c7b5ffc-90e7-1b85-f041-0595c912c905')
    assert actual.status_code == 400
    assert actual.body['message'] == 'Measure._current must not be None'


def test_add_measures_returns_error_response_when_device_is_not_valid_for_user():
    controller = DevicesController(Request.from_body(MeasureSerializer.serialize_all(
        [MeasureStub() for x in range(random.randint(1, 10))]
    )))
    controller.device_repository.exists_for_user = lambda ble_id, user_id: False
    actual = controller.add_measures('5c7b5ffc-90e7-1b85-f041-0595c912c905')
    assert actual.status_code == 400
    assert actual.body['message'] == 'Device identifier is not valid for logged user'


def test_add_measures_returns_ok_response_when_the_measures_were_registered():
    controller = DevicesController(Request.from_body(MeasureSerializer.serialize_all(
        [MeasureStub() for x in range(random.randint(1, 10))]
    )))
    controller.device_repository.exists_for_user = lambda device_id, user_id: True
    controller.measure_repository.create_multiple = lambda measures, device_id: None
    actual = controller.add_measures('5c7b5ffc-90e7-1b85-f041-0595c912c905')
    assert actual.status_code == 201
    assert actual.body == {}


def test_measures_returns_error_response_when_device_is_not_valid_for_user():
    controller = DevicesController(None)
    controller.device_repository.exists_for_user = lambda ble_id, user_id: False
    actual = controller.get_measures('5c7b5ffc-90e7-1b85-f041-0595c912c905', 5)
    assert actual.status_code == 400
    assert actual.body['message'] == 'Device identifier is not valid for logged user'


def test_get_measures_returns_ok_response_when_could_summarize_measures():
    controller = DevicesController(None)
    controller.device_repository.exists_for_user = lambda device_id, user_id: True
    controller.measure_repository.get_from_last_minutes = lambda device_id, time_interval: [
        Measure(timestamp=1626551296, voltage=220.571, current=5.432),
        Measure(timestamp=1626551301, voltage=220.424, current=5.555),
        Measure(timestamp=1626551306, voltage=219.4, current=5.512),
        Measure(timestamp=1626551311, voltage=218.93, current=5.628),
        Measure(timestamp=1626551316, voltage=219.157, current=5.579),
        Measure(timestamp=1626551321, voltage=222.171, current=5.656),
        Measure(timestamp=1626551326, voltage=219.634, current=5.696),
        Measure(timestamp=1626551331, voltage=217.96, current=5.449),
        Measure(timestamp=1626551336, voltage=219.442, current=5.239),
        Measure(timestamp=1626551362, voltage=218.562, current=5.639),
        Measure(timestamp=1626551367, voltage=221.682, current=5.699),
        Measure(timestamp=1626551372, voltage=221.005, current=5.18),
        Measure(timestamp=1626551377, voltage=217.802, current=5.614),
        Measure(timestamp=1626551382, voltage=219.584, current=5.385),
        Measure(timestamp=1626551633, voltage=219.111, current=5.502),
        Measure(timestamp=1626551729, voltage=221.923, current=5.411),
        Measure(timestamp=1626551750, voltage=218.024, current=5.443),
        Measure(timestamp=1626551755, voltage=220.784, current=5.18),
        Measure(timestamp=1626551760, voltage=217.849, current=5.373),
        Measure(timestamp=1626551765, voltage=219.831, current=5.362),
        Measure(timestamp=1626551881, voltage=221.5, current=5.245),
        Measure(timestamp=1626552004, voltage=220.465, current=5.685),
        Measure(timestamp=1626552205, voltage=221.847, current=5.287),
        Measure(timestamp=1626552281, voltage=221.918, current=5.602),
        Measure(timestamp=1626552286, voltage=219.383, current=5.404),
    ]
    expected = [
        {
            'current': 5.43,
            'power': 1197.7,
            'timestamp': '2021-07-17T19:48:16+00:00',
            'voltage': 220.57
        },
        {
            'current': 5.53,
            'power': 1216.1,
            'timestamp': '2021-07-17T19:48:28+00:00',
            'voltage': 219.91
        },
        {
            'current': 5.61,
            'power': 1228.87,
            'timestamp': '2021-07-17T19:48:40+00:00',
            'voltage': 219.05
        },
        {
            'current': 5.6,
            'power': 1231.55,
            'timestamp': '2021-07-17T19:48:52+00:00',
            'voltage': 219.92
        },
        {
            'current': 5.24,
            'power': 1149.87,
            'timestamp': '2021-07-17T19:49:04+00:00',
            'voltage': 219.44
        },
        {
            'current': 5.67,
            'power': 1248.08,
            'timestamp': '2021-07-17T19:49:28+00:00',
            'voltage': 220.12
        },
        {
            'current': 5.39,
            'power': 1182.57,
            'timestamp': '2021-07-17T19:49:40+00:00',
            'voltage': 219.4
        },
        {
            'current': 5.38,
            'power': 1181.34,
            'timestamp': '2021-07-17T19:49:52+00:00',
            'voltage': 219.58
        }
    ]
    actual = controller.get_measures('5c7b5ffc-90e7-1b85-f041-0595c912c905', 5)
    assert actual.status_code == 200
    assert actual.body == expected


def test_get_all_for_user_returns_ok_response_with_user_devices():
    controller = DevicesController(None)
    controller.device_repository.get_user_devices = lambda user_id: [
        Device(name='device_1', device_id='5c7b5ffc-90e7-1b85-f041-0595c912c905'),
        Device(name='device_2', device_id='5c7b5ffc-90e7-1b85-f041-0595c912c906'),
        Device(name='device_3', device_id='5c7b5ffc-90e7-1b85-f041-0595c912c907'),
    ]
    actual = controller.get_all_for_user()
    assert actual.status_code == 200
    assert actual.body == [
        {
            'active': False,
            'device_id': '5c7b5ffc-90e7-1b85-f041-0595c912c905',
            'measures': [],
            'name': 'device_1',
            'turned_on': False
        },
        {
            'active': False,
            'device_id': '5c7b5ffc-90e7-1b85-f041-0595c912c906',
            'measures': [],
            'name': 'device_2',
            'turned_on': False
        },
        {
            'active': False,
            'device_id': '5c7b5ffc-90e7-1b85-f041-0595c912c907',
            'measures': [],
            'name': 'device_3',
            'turned_on': False
        }
    ]


def test_get_measures_for_all_devices_returns_summarized_measures_for_all_devices():
    controller = DevicesController(None)
    controller.measure_repository.get_all_for_user_from_last_minutes = lambda user_id, time_interval: [
        Measure(timestamp=1626551296, voltage=220.571, current=5.432),
        Measure(timestamp=1626551301, voltage=220.424, current=5.555),
        Measure(timestamp=1626551306, voltage=219.4, current=5.512),
        Measure(timestamp=1626551311, voltage=218.93, current=5.628),
        Measure(timestamp=1626551316, voltage=219.157, current=5.579),
        Measure(timestamp=1626551321, voltage=222.171, current=5.656),
        Measure(timestamp=1626551326, voltage=219.634, current=5.696),
        Measure(timestamp=1626551331, voltage=217.96, current=5.449),
        Measure(timestamp=1626551336, voltage=219.442, current=5.239),
        Measure(timestamp=1626551362, voltage=218.562, current=5.639),
        Measure(timestamp=1626551367, voltage=221.682, current=5.699),
        Measure(timestamp=1626551372, voltage=221.005, current=5.18),
        Measure(timestamp=1626551377, voltage=217.802, current=5.614),
        Measure(timestamp=1626551382, voltage=219.584, current=5.385),
        Measure(timestamp=1626551633, voltage=219.111, current=5.502),
        Measure(timestamp=1626551729, voltage=221.923, current=5.411),
        Measure(timestamp=1626551750, voltage=218.024, current=5.443),
        Measure(timestamp=1626551755, voltage=220.784, current=5.18),
        Measure(timestamp=1626551760, voltage=217.849, current=5.373),
        Measure(timestamp=1626551765, voltage=219.831, current=5.362),
        Measure(timestamp=1626551881, voltage=221.5, current=5.245),
        Measure(timestamp=1626552004, voltage=220.465, current=5.685),
        Measure(timestamp=1626552205, voltage=221.847, current=5.287),
        Measure(timestamp=1626552281, voltage=221.918, current=5.602),
        Measure(timestamp=1626552286, voltage=219.383, current=5.404),
    ]
    expected = [
        {
            'current': 5.43,
            'power': 1197.7,
            'timestamp': '2021-07-17T19:48:16+00:00',
            'voltage': 220.57
        },
        {
            'current': 5.53,
            'power': 1216.1,
            'timestamp': '2021-07-17T19:48:28+00:00',
            'voltage': 219.91
        },
        {
            'current': 5.61,
            'power': 1228.87,
            'timestamp': '2021-07-17T19:48:40+00:00',
            'voltage': 219.05
        },
        {
            'current': 5.6,
            'power': 1231.55,
            'timestamp': '2021-07-17T19:48:52+00:00',
            'voltage': 219.92
        },
        {
            'current': 5.24,
            'power': 1149.87,
            'timestamp': '2021-07-17T19:49:04+00:00',
            'voltage': 219.44
        },
        {
            'current': 5.67,
            'power': 1248.08,
            'timestamp': '2021-07-17T19:49:28+00:00',
            'voltage': 220.12
        },
        {
            'current': 5.39,
            'power': 1182.57,
            'timestamp': '2021-07-17T19:49:40+00:00',
            'voltage': 219.4
        },
        {
            'current': 5.38,
            'power': 1181.34,
            'timestamp': '2021-07-17T19:49:52+00:00',
            'voltage': 219.58
        }
    ]
    actual = controller.get_measures_for_all_devices(5)
    assert actual.status_code == 200
    assert actual.body == expected


def test_update_state_returns_ok_response_when_device_state_is_valid():
    controller = DevicesController(Request.from_body({'turned_on': True}))
    controller.device_repository.exists_for_user = lambda device_id, user_id: True
    controller.device_repository.update_state = lambda device_id, user_id, turned_on, last_status_update: None
    actual = controller.update_state('test_device_id')
    assert actual.status_code == 200


def test_update_state_returns_error_response_when_device_state_is_not_valid():
    controller = DevicesController(Request.from_body({'turned_on': None}))
    controller.device_repository.exists_for_user = lambda device_id, user_id: True
    controller.device_repository.update_state = lambda device_id, user_id, turned_on, last_status_update: None
    actual = controller.update_state('test_device_id')
    assert actual.status_code == 400
    assert actual.body == {'message': 'turned_on must be a valid boolean'}


def test_update_state_returns_error_response_when_device_is_not_valid_for_provided_user():
    controller = DevicesController(Request.from_body({'turned_on': True}))
    controller.device_repository.exists_for_user = lambda device_id, user_id: False
    actual = controller.update_state('test_device_id')
    assert actual.status_code == 400
    assert actual.body == {'message': 'Device identifier is not valid for logged user'}


def test_get_state_returns_device_turned_on_state_when_device_is_valid():
    controller = DevicesController(Request.from_body({}))
    controller.device_repository.exists_for_user = lambda device_id, user_id: True
    controller.device_repository.get_state = lambda device_id, user_id: True
    actual = controller.get_state('test_device_id')
    assert actual.status_code == 200
    assert actual.body == {'turned_on': True}


def test_get_state_returns_error_response_when_device_is_not_valid_for_provided_user():
    controller = DevicesController(Request.from_body({}))
    controller.device_repository.exists_for_user = lambda device_id, user_id: False
    actual = controller.get_state('test_device_id')
    assert actual.status_code == 400
    assert actual.body == {'message': 'Device identifier is not valid for logged user'}
