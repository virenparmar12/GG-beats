

import os
import yaml
import json
import logging
import requests
from app.main.util.util import *
from flask import request, make_response, Flask
from flask_restplus import Resource, Namespace
from app.main.beatsclasses.driverFunction import Driver
from app.main import config

# from api-code.log-ingestion.app.main import config.py


logging.basicConfig(level=logging.DEBUG)

api = Namespace('/', description='configuration related operation')


# need to import the base level configuration


@api.route('/FetchConfiguration')
class ConfigurationFile(Resource):

    @api.doc('generate docker image with configuration base on user input from UI')
    # @api.expect(type, validate=True)
    def post(self):
        """Creates a new User """
        try:
            request_data = request.get_json()
        except Exception as e:
            logging.error(
                "error in decoding data coming through request, the error message is {}".format(str(e)))
            return "error in parsing request data"
        # print(request_data)

        # herre is the separation logic
        # iterate
        configuration_setting = str()
        container_name = str()
        # configuration, type env, cloudsupport
        configuration, env_type, cloud_type = prepare_configuration(
            request_data, logging)
        logging.debug("Configuration return:{}".format(configuration[0]))
        logging.info("Total number of configuration {}".format(
            len(configuration)))
        # for log_type in request_data['type']:
        for i in range(len(configuration)):
            #logging.info("Inside loop:{}".format(configuration[i]))
            log_request = configuration[i]

            logging.info("Data {}".format(log_request))
            # logging.info("Conf:{}".format(type(log_request)))
            driver = Driver(log_request, env_type=env_type,
                            cloud_type=cloud_type)
            container_name_ret, configuration_setting_ret = driver.start()
            configuration_setting += configuration_setting_ret + '\n'
            container_name += container_name_ret

        # remove the last character
        container_name = container_name[:-1]
        setting = prepare_script(container_name, configuration_setting,
                                 logging, request_data, env_type=env_type, cloud_type=cloud_type)
        logging.debug("Containers Name:{}".format(container_name))
        logging.debug("Setting:{}".format(setting))
        response = make_response(setting, 200)
        response.mimetype = "text/plain"
        return response


@api.route('/SyslogConfiguration')
class SyslogConfiguration(Resource):

    @api.doc('generate docker image with configuration base on user input from UI')
    # @api.expect(type, validate=True)
    def get(self):
        """Creates a new User """
        setting = prepare_syslog_scipt()
        response = make_response(setting, 200)
        response.mimetype = "text/plain"
        return response

# @api.route('/create', methods=["GET"])
# class CreateUserConfiguration(Resource):
#     def get(self):
#         url = f"{os.environ['APIURL']}giggso/azure"
#         payload = "{ \"applicationId\": \"38770284-7f3d-435e-8a85-1ffc7bb52485\", \"applicationPW\": \"~_kX3-0RW_h8ji4P-nt6F~MCq0UMbYP1OM\", \"tenantID\": \"715779c6-7e22-4cbf-b67c-a118fd5c62f3\",\"subscriptionsId\":\"b3d399df-7a55-45c0-917e-1f47be01f5f9\"}"
#         headers = {
#             'X-Vault-Token': vault_token,
#             'Content-Type': 'application/json'
#         }

#         response = requests.request("POST", url, headers=headers, data=payload)
#         return "done"


@api.route('/get_cred_data', methods=["POST"])
class GetData(Resource):
    def post(self):
        json_credential = request.get_json()
        credential_name = json_credential['credentialname']
        url = f"{config.CREDENTIAL_BASE_URL}{credential_name}"

        payload = {}
        headers = {
            'X-Vault-Token': config.VAULT_TOKEN
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        json_data = json.loads(response.text)

        return json_data["data"]


def AccessToken():
    json_credential = request.get_json()
    credential_name = json_credential['credentialname']
    url1 = f"{config.CREDENTIAL_BASE_URL}{credential_name}"

    payload_vault = {}
    headers_vault = {
        'X-Vault-Token': config.VAULT_TOKEN
    }

    response1 = requests.request(
        "GET", url1, headers=headers_vault, data=payload_vault)

    json_data = json.loads(response1.text)

    url = f"https://login.microsoftonline.com/{json_data['data']['tenantID']}/oauth2/token"

    payload = f'grant_type=client_credentials&client_id={json_data["data"]["applicationId"]}&resource=https%3A%2F%2Fmanagement.core.windows.net%2F&client_secret={json_data["data"]["applicationPW"]}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'fpc=AqYyHkjQj-NBkH5wrAH9aP8PRTbPAQAAALtmJdgOAAAA'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    json_token = json.loads(response.text)
    return json_token["access_token"]


@api.route('/get_location', methods=["POST"])
class GetLocation(Resource):
    def post(self):
        try:
            json_credential = request.get_json()
            credential_name = json_credential['credentialname']
            token = AccessToken()
            url_base = f"{config.CREDENTIAL_BASE_URL}{credential_name}"

            payload_vault = {}
            headers_vault = {
                'X-Vault-Token': config.VAULT_TOKEN
            }

            response_vault = requests.request(
                "GET", url_base, headers=headers_vault, data=payload_vault)

            json_data_vault = json.loads(response_vault.text)

            url = f"https://management.azure.com/subscriptions/{json_data_vault['data']['subscriptionsId']}/locations?api-version=2020-01-01"

            payload = {}
            headers = {
                'Authorization': f'Bearer {token}'
            }

            response = requests.request(
                "GET", url, headers=headers, data=payload)

            json_data = json.loads(response.text)

            if "value" in json_data:
                Json_location = {"location": []}
                for i in json_data["value"]:
                    Json_location["location"].append(i["name"])
                return Json_location
            else:
                return json_data
        except:
            errormsg = {
                "errors": [
                    "error performing token check: failed to look up namespace from the token: no namespace"
                ]
            }
            return errormsg


@api.route('/get_resourcegroup', methods=["POST"])
class GetResource(Resource):
    def post(self):
        try:
            json_credential = request.get_json()
            credential_name = json_credential['credentialname']
            token = AccessToken()
            url_base = f"{config.CREDENTIAL_BASE_URL}{credential_name}"

            payload_vault = {}
            headers_vault = {
                'X-Vault-Token': config.VAULT_TOKEN
            }

            response_vault = requests.request(
                "GET", url_base, headers=headers_vault, data=payload_vault)

            json_data_vault = json.loads(response_vault.text)

            url = f"https://management.azure.com/subscriptions/{json_data_vault['data']['subscriptionsId']}/resourcegroups?api-version=2020-10-01"

            payload = {}
            headers = {
                'Authorization': f'Bearer {token}'
            }

            response = requests.request(
                "GET", url, headers=headers, data=payload)

            json_data = json.loads(response.text)

            if "value" in json_data:
                json_resourcegroup = {"resourcegroup": []}
                for i in json_data["value"]:
                    json_resourcegroup["resourcegroup"].append(i["name"])

                return json_resourcegroup
            else:
                return json_data
        except:
            errormsg = {
                "errors": [
                    "error performing token check: failed to look up namespace from the token: no namespace"
                ]
            }
            return errormsg
