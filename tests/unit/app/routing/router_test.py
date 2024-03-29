import pytest

from src.app.routing.router import Router
from src.app.utils import global_variables
from src.app.routing import router, cors_solver
from src.app.utils.auth.device_token import DeviceToken
from src.app.utils.auth.permission_level import PermissionLevel
from src.app.utils.auth.user_token import UserToken
from src.app.utils.http.response import Response


class MockedRequest:
    def __init__(self, http_method: str, headers: dict = {}) -> None:
        self.method = http_method
        self.headers = headers
        self.path = None
        self.json = {}
        self.data = ''
        self.args = {}


class MockedResponse:
    def __init__(self, body, code) -> None:
        self.body = body
        self.code = code
        self.headers = {}


# Patch response jsonify
Response.jsonify = lambda self: MockedResponse(self.body, self.status_code)


class MockedController:

    def __init__(self, request=None, token=None):
        self.request = request
        self.token = token

    def mocked_http_endpoint(self):
        return Response(200, {'message': 'OK'})

    def mocked_http_endpoint_with_params(self, param1, param2):
        return Response(200, {'param1': param1, 'param2': param2})

    def mocked_http_endpoint_with_user_permission_level(self):
        return Response(200, {'message': 'OK'})

    def mocked_http_endpoint_with_device_permission_level(self):
        return Response(200, {'message': 'OK'})

    def mocked_http_endpoint_that_raises_exception(self):
        raise Exception("Mocked error")

    def on_request(self):
        pass

    def after_request(self):
        pass


def discover_controllers_mocked(router_instance):
    Router.register_http_method({
        'type': 'POST', 'alias': None, 'class_name': 'MockedController', 'method_name': 'mocked_http_endpoint',
        'min_permission_level': PermissionLevel.PUBLIC
    })
    Router.register_http_method({
        'type': 'GET', 'alias': None, 'class_name': 'MockedController',
        'method_name': 'mocked_http_endpoint_with_params', 'min_permission_level': PermissionLevel.PUBLIC
    })
    Router.register_http_method({
        'type': 'GET', 'alias': None, 'class_name': 'MockedController',
        'method_name': 'mocked_http_endpoint_with_user_permission_level', 'min_permission_level': PermissionLevel.USER
    })
    Router.register_http_method({
        'type': 'GET', 'alias': None, 'class_name': 'MockedController',
        'method_name': 'mocked_http_endpoint_with_device_permission_level',
        'min_permission_level': PermissionLevel.DEVICE
    })
    Router.register_http_method({
        'type': 'GET', 'alias': None, 'class_name': 'MockedController',
        'method_name': 'mocked_http_endpoint_that_raises_exception', 'min_permission_level': PermissionLevel.PUBLIC
    })
    return [MockedController]


def create_user_token(user_email: str) -> str:
    return 'Bearer ' + UserToken(user_email=user_email).encode()


def create_device_token(device_id: str, user_id: str) -> str:
    return 'Bearer ' + DeviceToken(device_id=device_id, user_id=user_id).encode()


# Mockeamos la funcion make_response importado desde flask
router.make_response = lambda message, code: MockedResponse(message, code)


@pytest.fixture
def router():
    Router._Router__discover_controllers = discover_controllers_mocked
    return Router()


def test_router_register_router_instance_in_global_variables_when_instantiated():
    router = Router()
    assert router == global_variables.ROUTER_INSTANCE


def test_router_map_rutes_when_instantiated():
    Router._discover_controllers = discover_controllers_mocked
    router = Router()
    assert 1 == len(router.routes)
    assert MockedController == router.routes[0].controller_class
    assert 'mocked_http_endpoint' == router.routes[0].methods[0].method_name
    assert 'POST' == router.routes[0].methods[0].http_type
    assert not router.routes[0].methods[0].alias
    assert router.routes[0].methods[0].min_permission_level == PermissionLevel.PUBLIC


def test_route_returns_error_response_when_controller_is_not_in_path(router):
    request = MockedRequest('POST', {})
    actual = router.route(request, '')
    assert actual.body['message'] == 'Not found'
    assert actual.code == 404


def test_route_returns_error_response_when_method_is_not_in_path(router):
    request = MockedRequest('POST')
    actual = router.route(request, 'mocked')
    assert actual.body['message'] == 'Not found'
    assert actual.code == 404


def test_route_returns_error_response_when_method_is_valid_but_http_method_type_does_not_match(router):
    request = MockedRequest('GET')
    actual = router.route(request, 'mocked')
    assert actual.body['message'] == 'Not found'
    assert actual.code == 404


def test_route_executes_controller_method_when_route_is_valid(router):
    param1 = 'text_param'
    param2 = 10
    request = MockedRequest('GET')
    actual = router.route(request, f'mocked/mocked_http_endpoint_with_params/{param1}/{param2}')
    assert actual.body['param1'] == param1
    assert actual.body['param2'] == str(param2)
    assert actual.code == 200


def test_route_returns_error_response_when_endpoint_is_valid_but_params_are_invalid(router):
    request = MockedRequest('GET')
    actual = router.route(request, 'mocked/mocked_http_endpoint_with_params')
    assert actual.body['message'] == 'Bad method arguments'
    assert actual.code == 400


def test_route_returns_error_response_when_mapped_method_raises_exception(router):
    request = MockedRequest('GET')
    actual = router.route(request, 'mocked/mocked_http_endpoint_that_raises_exception')
    assert actual.body['message'] == 'Internal server error'
    assert actual.code == 500


def test_route_returns_error_response_when_cors_wanted_method_is_not_valid(router):
    request = MockedRequest('OPTIONS', {
        'Origin': 'local',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': None
    })
    actual = router.route(request, 'mocked/invalid_http_endpoint')
    assert actual.body['message'] == 'Not found'
    assert actual.code == 404


def test_route_returns_cors_response_when_cors_requested_in_valid_endpoint(router):
    # Mockeamos el jsonify importado en cors_solver
    cors_solver.jsonify = lambda ssuccess=True: MockedResponse({}, 200)
    request = MockedRequest('OPTIONS', {
        'Origin': 'local',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': None
    })
    actual = router.route(request, 'mocked/mocked_http_endpoint')
    assert actual.headers['Access-Control-Allow-Methods'] == 'POST'
    assert actual.code == 200


def test_route_returns_error_response_when_user_token_is_required_and_not_provided(router):
    request = MockedRequest('GET')
    actual = router.route(request, 'mocked/mocked_http_endpoint_with_user_permission_level')
    assert actual.body['message'] == 'Unauthorized'
    assert actual.code == 401


def test_route_returns_error_response_when_user_token_is_required_and_a_device_one_is_used_instead(router):
    request = MockedRequest('GET', {'Authorization': create_device_token('device_012345', 'user_012345')})
    actual = router.route(request, 'mocked/mocked_http_endpoint_with_user_permission_level')
    assert actual.body['message'] == 'Unauthorized'
    assert actual.code == 401


def test_route_returns_ok_response_when_user_token_is_required_and_provided(router):
    request = MockedRequest('GET', {'Authorization': create_user_token('test_user@test.com')})
    actual = router.route(request, 'mocked/mocked_http_endpoint_with_user_permission_level')
    assert actual.body['message'] == 'OK'
    assert actual.code == 200


def test_route_returns_error_response_when_device_token_is_required_and_not_provided(router):
    request = MockedRequest('GET')
    actual = router.route(request, 'mocked/mocked_http_endpoint_with_device_permission_level')
    assert actual.body['message'] == 'Unauthorized'
    assert actual.code == 401


def test_route_returns_ok_response_when_device_token_is_required_and_an_user_one_is_used_instead(router):
    request = MockedRequest('GET', {'Authorization': create_user_token('test_user@test.com')})
    actual = router.route(request, 'mocked/mocked_http_endpoint_with_device_permission_level')
    assert actual.body['message'] == 'OK'
    assert actual.code == 200


def test_route_returns_ok_response_when_device_token_is_required_and_provided(router):
    request = MockedRequest('GET', {'Authorization': create_device_token('device_012345', 'user_012345')})
    actual = router.route(request, 'mocked/mocked_http_endpoint_with_device_permission_level')
    assert actual.body['message'] == 'OK'
    assert actual.code == 200


def test_get_base_url_returns_base_api_url_when_called():
    actual = Router.get_base_url()
    assert 'api' == actual
