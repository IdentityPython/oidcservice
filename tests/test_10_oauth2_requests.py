import pytest
from oiccli.exception import WrongContentType
from oiccli.grant import GrantDB
from oicmsg.oauth2 import AccessTokenRequest, Message, ASConfigurationResponse
from oicmsg.oauth2 import AccessTokenResponse
from oicmsg.oauth2 import AuthorizationRequest
from oicmsg.oauth2 import AuthorizationResponse
from oicmsg.oauth2 import ErrorResponse
from oiccli.oauth2.requests import factory
from oiccli.request import Request


class Response(object):
    def __init__(self, status_code, text, headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {"content-type": "text/plain"}


def test_request_factory():
    req = factory('Request', httplib=None, keyjar=None,
                  client_authn_method=None)
    assert isinstance(req, Request)


class TestAuthorizationRequest(object):
    @pytest.fixture(autouse=True)
    def create_request(self):
        self.req = factory('AuthorizationRequest')

    def test_construct(self):
        req_args = {'foo': 'bar'}
        cli_info = {'redirect_uris': ['https://example.com/cli/authz_cb'],
                    'client_id': 'client_id', 'client_secret': 'password'}
        _req = self.req.construct(cli_info, request_args=req_args)
        assert isinstance(_req, AuthorizationRequest)
        assert set(_req.keys()) == {'client_id', 'redirect_uri', 'foo'}

    def test_request_info(self):
        req_args = {'response_type': 'code'}
        cli_info = {'redirect_uris': ['https://example.com/cli/authz_cb'],
                    'client_id': 'client_id', 'client_secret': 'password'}
        self.req.endpoint = 'https://example.com/authorize'
        _info = self.req.request_info(cli_info, request_args=req_args)
        assert set(_info.keys()) == {'body', 'uri', 'cis', 'h_args'}
        assert _info['body'] is None
        assert _info['cis'].to_dict() == {
            'client_id': 'client_id',
            'redirect_uri': 'https://example.com/cli/authz_cb',
            'response_type': 'code'}
        assert _info['h_args'] == {}
        msg = AuthorizationRequest().from_urlencoded(
            self.req.get_urlinfo(_info['uri']))
        assert msg == _info['cis']

    def test_request_init(self):
        req_args = {'response_type': 'code'}
        cli_info = {'redirect_uris': ['https://example.com/cli/authz_cb'],
                    'client_id': 'client_id', 'client_secret': 'password'}
        self.req.endpoint = 'https://example.com/authorize'
        _info = self.req.do_request_init(cli_info, request_args=req_args)
        assert set(_info.keys()) == {'body', 'cis', 'http_args', 'uri', 'algs',
                                     'h_args'}
        assert _info['body'] is None
        assert _info['cis'].to_dict() == {
            'client_id': 'client_id',
            'redirect_uri': 'https://example.com/cli/authz_cb',
            'response_type': 'code'}
        assert _info['h_args'] == {}
        assert _info['http_args'] == {}
        msg = AuthorizationRequest().from_urlencoded(
            self.req.get_urlinfo(_info['uri']))
        assert msg == _info['cis']

    def test_parse_request_response_urlencoded(self):
        session_info = {'client_id': 'client_id',
                        'provider_info': {},
                        'issuer': 'https://www.example.org/as',
                        'grant_db': GrantDB()}

        req_resp = Response(
            200,
            AuthorizationResponse(code='access_code',
                                  state='state').to_urlencoded())
        resp = self.req.parse_request_response(req_resp, session_info)
        assert isinstance(resp, AuthorizationResponse)
        assert set(resp.keys()) == {'code', 'state'}

    def test_parse_request_response_200_error(self):
        session_info = {'client_id': 'client_id',
                        'provider_info': {},
                        'issuer': 'https://www.example.org/as',
                        'grant_db': GrantDB()}

        req_resp = Response(
            200, ErrorResponse(error='invalid_request').to_urlencoded())
        resp = self.req.parse_request_response(req_resp, session_info)
        assert isinstance(resp, ErrorResponse)
        assert set(resp.keys()) == {'error'}

    def test_parse_request_response_400_error(self):
        session_info = {'client_id': 'client_id',
                        'provider_info': {},
                        'issuer': 'https://www.example.org/as',
                        'grant_db': GrantDB()}

        req_resp = Response(
            400, ErrorResponse(error='invalid_request').to_urlencoded())
        resp = self.req.parse_request_response(req_resp, session_info)
        assert isinstance(resp, ErrorResponse)
        assert set(resp.keys()) == {'error'}

    def test_parse_request_response_json(self):
        session_info = {'client_id': 'client_id',
                        'provider_info': {},
                        'issuer': 'https://www.example.org/as',
                        'grant_db': GrantDB()}

        req_resp = Response(200, AuthorizationResponse(code='access_code',
                                                       state='state').to_json(),
                            headers={'content-type': 'application/json'})
        resp = self.req.parse_request_response(req_resp, session_info,
                                               body_type='json')
        assert isinstance(resp, AuthorizationResponse)
        assert set(resp.keys()) == {'code', 'state'}

    def test_parse_request_response_wrong_content_type(self):
        session_info = {'client_id': 'client_id',
                        'provider_info': {},
                        'issuer': 'https://www.example.org/as',
                        'grant_db': GrantDB()}

        req_resp = Response(200, AuthorizationResponse(code='access_code',
                                                       state='state').to_json(),
                            headers={'content-type': "text/plain"})
        with pytest.raises(WrongContentType):
            resp = self.req.parse_request_response(req_resp, session_info,
                                                   body_type='json')


class TestAccessTokenRequest(object):
    @pytest.fixture(autouse=True)
    def create_request(self):
        self.req = factory('AccessTokenRequest')

    def test_construct(self):
        req_args = {'foo': 'bar'}
        cli_info = {'redirect_uris': ['https://example.com/cli/authz_cb'],
                    'client_id': 'client_id', 'client_secret': 'password'}
        _req = self.req.construct(cli_info, request_args=req_args)
        assert isinstance(_req, AccessTokenRequest)
        assert set(_req.keys()) == {'client_id', 'foo', 'grant_type',
                                    'client_secret'}

    def test_request_info(self):
        req_args = {'redirect_uri': 'https://example.com/cli/authz_cb',
                    'code': 'access_code'}
        cli_info = {'redirect_uris': ['https://example.com/cli/authz_cb'],
                    'client_id': 'client_id', 'client_secret': 'password'}
        self.req.endpoint = 'https://example.com/authorize'
        _info = self.req.request_info(cli_info, request_args=req_args)
        assert set(_info.keys()) == {'body', 'uri', 'cis', 'h_args'}
        assert _info['body'] is None
        assert _info['cis'].to_dict() == {
            'client_id': 'client_id', 'client_secret': 'password',
            'code': 'access_code', 'grant_type': 'authorization_code',
            'redirect_uri': 'https://example.com/cli/authz_cb'}
        assert _info['h_args'] == {}
        msg = AccessTokenRequest().from_urlencoded(
            self.req.get_urlinfo(_info['uri']))
        assert msg == _info['cis']

    def test_request_init(self):
        req_args = {'redirect_uri': 'https://example.com/cli/authz_cb',
                    'code': 'access_code'}
        cli_info = {'redirect_uris': ['https://example.com/cli/authz_cb'],
                    'client_id': 'client_id', 'client_secret': 'password'}
        self.req.endpoint = 'https://example.com/authorize'
        _info = self.req.do_request_init(cli_info, request_args=req_args)
        assert set(_info.keys()) == {'body', 'cis', 'uri', 'http_args',
                                     'h_args'}
        assert _info['uri'] == 'https://example.com/authorize'
        assert _info['cis'].to_dict() == {
            'client_id': 'client_id', 'client_secret': 'password',
            'code': 'access_code', 'grant_type': 'authorization_code',
            'redirect_uri': 'https://example.com/cli/authz_cb'}
        assert _info['h_args'] == {
            'headers': {'Content-Type': 'application/x-www-form-urlencoded'}}
        msg = AccessTokenRequest().from_urlencoded(
            self.req.get_urlinfo(_info['body']))
        assert msg == _info['cis']

    def test_parse_request_response_urlencoded(self):
        session_info = {'client_id': 'client_id',
                        'provider_info': {},
                        'issuer': 'https://www.example.org/as',
                        'grant_db': GrantDB()}

        req_resp = Response(
            200,
            AccessTokenResponse(access_token='access_token',
                                state='state',
                                token_type='Bearer').to_json(),
            headers={'content-type': "application/json"}
        )
        resp = self.req.parse_request_response(req_resp, session_info,
                                               body_type='json')
        assert isinstance(resp, AccessTokenResponse)
        assert set(resp.keys()) == {'access_token', 'token_type', 'state'}

    def test_parse_request_response_200_error(self):
        session_info = {'client_id': 'client_id',
                        'provider_info': {},
                        'issuer': 'https://www.example.org/as',
                        'grant_db': GrantDB()}

        req_resp = Response(
            200, ErrorResponse(error='invalid_request').to_json(),
            headers={'content-type': "application/json"}
        )
        resp = self.req.parse_request_response(req_resp, session_info,
                                               body_type='json')
        assert isinstance(resp, ErrorResponse)
        assert set(resp.keys()) == {'error'}

    def test_parse_request_response_400_error(self):
        session_info = {'client_id': 'client_id',
                        'provider_info': {},
                        'issuer': 'https://www.example.org/as',
                        'grant_db': GrantDB()}

        req_resp = Response(
            400, ErrorResponse(error='invalid_request').to_json(),
            headers={'content-type': "application/json"}
        )
        resp = self.req.parse_request_response(req_resp, session_info,
                                               body_type='json')
        assert isinstance(resp, ErrorResponse)
        assert set(resp.keys()) == {'error'}

    def test_parse_request_response_wrong_content_type(self):
        session_info = {'client_id': 'client_id',
                        'provider_info': {},
                        'issuer': 'https://www.example.org/as',
                        'grant_db': GrantDB()}

        req_resp = Response(200, AccessTokenResponse(code='access_code',
                                                     state='state').to_json(),
                            headers={'content-type': "text/plain"})
        with pytest.raises(WrongContentType):
            resp = self.req.parse_request_response(req_resp, session_info,
                                                   body_type='json')


class TestProviderInfoRequest(object):
    @pytest.fixture(autouse=True)
    def create_request(self):
        self.req = factory('ProviderInfoDiscovery')

    def test_construct(self):
        cli_info = {'redirect_uris': ['https://example.com/cli/authz_cb'],
                    'client_id': 'client_id', 'client_secret': 'password',
                    'issuer': 'https://example.com/as'}
        _req = self.req.construct(cli_info)
        assert isinstance(_req, Message)
        assert len(_req) == 0

    def test_request_info(self):
        _iss = 'https://example.com/as'
        cli_info = {'redirect_uris': ['https://example.com/cli/authz_cb'],
                    'client_id': 'client_id', 'client_secret': 'password',
                    'issuer': _iss}
        _info = self.req.request_info(cli_info)
        assert set(_info.keys()) == {'uri'}
        assert _info['uri'] == '{}/.well-known/openid-configuration'.format(_iss)

    def test_parse_request_response(self):
        _iss = 'https://example.com/as'
        session_info = {'client_id': 'client_id', 'provider_info': {},
                        'issuer': _iss, 'grant_db': GrantDB()}

        req_resp = Response(
            200,
            ASConfigurationResponse(
                issuer=_iss, response_types_supported=['code'],
                grant_types_supported=['Bearer']
                ).to_json(),
            headers={'content-type': "application/json"}
        )
        resp = self.req.parse_request_response(req_resp, session_info,
                                               body_type='json')
        assert isinstance(resp, ASConfigurationResponse)
        assert set(resp.keys()) == {'issuer', 'response_types_supported',
                                    'version', 'grant_types_supported'}