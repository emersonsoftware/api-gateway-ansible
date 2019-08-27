import library.apigw_model as apigw_model
from library.apigw_model import ApiGwModel
import mock
from mock import patch
import unittest
import boto
from botocore.exceptions import BotoCoreError, ClientError
from ansible.module_utils import basic

class TestApiGwModel(unittest.TestCase):
    def setUp(self):
        self.module = mock.MagicMock()

        self.model = ApiGwModel(self.module)
        self.model.client = mock.MagicMock()
        self.model.client.get_models = mock.MagicMock()

        basic.AnsibleModule = mock.MagicMock(return_value=self.module)

    def test_boto_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__

        def mock_import(name, *args):
            if name == 'boto': raise ImportError
            return real_import(name, *args)

        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(apigw_model)
            ApiGwModel(self.module)

        self.module.fail_json.assert_called_with(msg='boto and boto3 are required for this module')

    @patch.object(apigw_model, 'boto3')
    def test_boto3_client_properly_instantiated(self, mock_boto):
        ApiGwModel(self.module)
        mock_boto.client.assert_called_once_with('apigateway')

    def test_define_argument_spec(self):
        result = ApiGwModel._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertEqual(result, dict(
                     rest_api_id=dict(required=True, type=str),
                     models=dict(
                         type=list,
                         required=True,
                         default=[],
                         name=dict(require=True, type=str),
                         content_type=dict(required=True, type=str),
                         schema=dict(require=False, type=str),
                         description=dict(required=False, type=str)
                     )))


    @patch.object(apigw_model, 'AnsibleModule')
    @patch.object(apigw_model, 'ApiGwModel')
    def test_main(self, mockApiGwModel, mockAnsibleModule):
        argumentSpec = mock.MagicMock()
        apiGwModel = ApiGwModel(self.module)
        apiGwModel.process_request = mock.MagicMock()
        mockApiGwModel._define_module_argument_spec.return_value = argumentSpec
        mockApiGwModel.return_value = apiGwModel
        
        apigw_model.main()

        basic.AnsibleModule.assert_called_with(argument_spec=argumentSpec, supports_check_mode=True)
        mockApiGwModel.assert_called_once_with(self.module)
        self.assertEqual(1, apiGwModel.process_request.call_count)

    @patch.object(ApiGwModel, '_get_models')
    def test_process_request_calls_get_models(self, mockGetModels):
        self.model.process_request()

        mockGetModels.assert_called_once()

    def test_process_request_gets_models_from_apigateway(self):
        self.module.params = {
            'rest_api_id': 'rest_id'
        }
        self.model.process_request()

        self.model.client.get_models.assert_called_with(restApiId=self.module.params['rest_api_id'])
