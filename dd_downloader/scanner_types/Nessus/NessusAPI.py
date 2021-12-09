import requests, json, time, urllib
import urllib3
urllib3.disable_warnings() #Disable insecurerequestwarnings caused from Nessus web portal not having a valid SSL cert

#Helper class for interacting with the Nessus API.
import logging
logger = logging.getLogger(__name__)

class NessusAPI:
	"""The Nessus API requires that you authenticate with an access key and a secret key."""
	"""No wrapper library exists for Nessus Professional, so this will need to be updated whenever Nessus's API changes"""
	def __init__(self, api_url: str, access_key: str = None, secret_key: str = None, username: str = None, password: str = None, scan_completion_interval: int = 10, scan_policy_id: int = None, verify = False, timeout = 5):
		self.api_url = api_url
		self.session_token = ''
		self.verify = verify

		self.access_key = access_key
		self.secret_key = secret_key

		self.username = username
		self.password = password
		
		self.SCAN_COMPLETION_INTERVAL = scan_completion_interval
		self.POLICY_ID = scan_policy_id
		self.TIMEOUT = timeout

	#API urls
	scans_api = '/scans'
	scans_launch_api = '/scans/{scan_id}/launch'
	scans_details_api = '/scans/{scan_id}'
	export_request_api = '/scans/{scan_id}/export'
	token_status_api = '/tokens/{token}/status'
	download_token_api = '/tokens/{token}/download'
	session_api = '/session'

	#Nessus blocks certain API calls for users who are not using Nessus Manager.
	#To allow the web application to use the API calls, however, the web application includes a secret hard-coded API token into its requests.
	#To bypass this requirement, add a 'X-Api-Token' header, with this token as the contents, to any API calls which require "Nessus Manager".
	#This API token is hardcoded into the nessus.js file that is retrieved every time the Nessus login page is reloaded. (search for getApiToken)
	BYPASS_TOKEN = '7A2C4A96-4AEE-4706-9617-2EF643532628'
	
	def auth_header(self):
		if self.access_key is not None and self.secret_key is not None:
			return {'X-ApiKeys':f'accessKey={self.access_key}; secretKey={self.secret_key};'}
		elif (self.username is not None and self.password is not None):
			if not self.session_token:
				token_response = self.get_session_token(self.username, self.password)
				try:
					self.token = json.loads(token_response.content)['token']
				except Exception as e:
					print('Trouble retrieving token from session creation!')
					raise e

			return {'X-Cookie':f'token={self.token};'}
		else:
			raise Exception('Incomplete authentication information provided!')

	def get_session_token(self, username: str, password: str):
		response = requests.post(
			timeout = self.TIMEOUT,
			url = self.api_url+self.session_api,
			json = {
				'username': username,
				'password': password
			},
			verify = self.verify
		)
		logger.debug(f"{self.api_url+self.session_api}, {response.status_code}")
		return response

	def scans_list(self):
		response = requests.get(
			timeout = self.TIMEOUT,
			url = self.api_url+self.scans_api,
			headers = self.auth_header(),
			verify = self.verify
		)
		logger.debug(f"{self.api_url+self.scans_api}, {response.status_code}")
		return response

	#Return ID of scan
	def create_scan(self, targets: str, scan_name: str, override_policy_id = None):
		bypass_header = self.auth_header()
		bypass_header['X-Api-Token'] = self.BYPASS_TOKEN
		bypass_header['content-type'] = 'application/json'
		#Any random uuid + 16 chars is allowed.
		RANDOM_UUID = 'ad629e16-03b6-8c1d-cef6-ef8c9dd3c658d24bd260ef5f9e66'
		if override_policy_id is not None :
			data = {
				'uuid':RANDOM_UUID,
				'settings':{
					'name': scan_name,
					'policy_id': override_policy_id,
					'text_targets': targets
				}
			}
		elif self.POLICY_ID is not None :
			data = {
				'uuid':RANDOM_UUID,
				'settings':{
					'name': scan_name,
					'policy_id': self.POLICY_ID,
					'text_targets': targets
				}
			}
		else:
			data = {
				'uuid':RANDOM_UUID,
				'settings':{
					'name': scan_name,
					'text_targets': targets
				}
			}
		response = requests.post(
			timeout = self.TIMEOUT,
			url = self.api_url+self.scans_api,
			data = json.dumps(data),
			headers = bypass_header,
			verify = self.verify
		)
		logger.debug(f"{self.api_url+self.scans_api}, {response.status_code}")
		if (response.status_code != 200):
			logger.error('Nessus scan creation failed')
			return None

		try:
			return json.loads(response.content)['scan']['id']
		except Exception as e:
			logger.error('Retrieving Nessus scan ID after creation failed')
			return None

		
	def launch_scan(self, scan_id: int):
		bypass_header = self.auth_header()
		bypass_header['X-Api-Token'] = self.BYPASS_TOKEN
		response = requests.post(
			timeout = self.TIMEOUT,
			url = self.api_url+self.scans_launch_api.format(scan_id = scan_id),
			headers = bypass_header,
			verify = self.verify
		)
		logger.debug(f"{self.api_url+self.scans_launch_api.format(scan_id = scan_id)}, {response.status_code}")
		return (response.status_code == 200)

	def scan_details(self, scan_id: int):
		response = requests.get(
			timeout = self.TIMEOUT,
			url = self.api_url+self.scans_details_api.format(scan_id = scan_id),
			headers = self.auth_header(),
			verify = self.verify
		)
		logger.debug(f"{self.api_url+self.scans_details_api.format(scan_id = scan_id)}, {response.status_code}")
		return (json.loads(response.content)['info']['status'] == 'completed')

	def export_scan(self, scan_id: str):
		response = requests.post(
			timeout = self.TIMEOUT,
			url = self.api_url+self.export_request_api.format(scan_id = scan_id),
			data = {'format':'csv'},
			headers = self.auth_header(),
			verify = self.verify
		)
		logger.debug(f"{self.api_url+self.export_request_api.format(scan_id = scan_id)}, {response.status_code}")
		return json.loads(response.content)['token']

	def export_status(self, token: str):
		response = requests.get(
			timeout = self.TIMEOUT,
			url = self.api_url+self.token_status_api.format(token = token),
			headers = self.auth_header(),
			verify = self.verify
		)
		logger.debug(f"{self.api_url+self.token_status_api.format(token = token),}, {response.status_code}")
		return response

	def download_export_request(self, token: str):
		response = requests.get(
			timeout = self.TIMEOUT,
			url = self.api_url+self.download_token_api.format(token = token),
			headers = self.auth_header(),
			verify = self.verify
		)
		logger.debug(f"{self.api_url+self.download_token_api.format(token = token)}, {response.status_code}")
		return response


	def download_scan(self, scan_id: str):
		download_token = self.export_scan(scan_id)
		status = ''
		attempts = 1
		while (status != 'ready'):
			time.sleep(10)
			logger.debug(f"Export progress: poll attempt {attempts}")
			status_response = self.export_status(download_token)
			if (status_response.status_code == 200):
				status = json.loads(status_response.content)['status']

			attempts += 1

		#Download scan
		download_response = self.download_export_request(download_token)
		if (download_response.status_code != 200):
			logger.error('download_response ! 200')
			raise Exception('Download unsuccessful')

		csv = download_response.content.decode().replace('\r','')
		return csv
