from django.db import models
from dd_downloader.models import Scanner, Scan
from django.utils import timezone
import burpsuite
from django import forms
from django.core.validators import MinValueValidator
import logging
logger = logging.getLogger('dd_downloader.scanner_types.Burp_Suite')
class Burp_Suite_Scanner(Scanner):
	@staticmethod
	def get_scanner_detail_template_path():
		return 'dd_downloader/scanner_types/Burp_Suite/scanner_detail.html'
	@staticmethod
	def get_scan_detail_template_path():
		return 'dd_downloader/scanner_types/Burp_Suite/scan_detail.html'
	@staticmethod
	def get_scanner_create_form_class():
		return Burp_Suite_Scanner_Create_Form
	@staticmethod
	def get_scan_create_form_class():
		return Burp_Suite_Scan_Create_Form

	#Address of the Burp Suite API
	api_url = models.CharField('API URL', max_length=200)
	#API key for the API
	api_key = models.CharField('API Key', max_length=200)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.api_obj = burpsuite.BurpSuiteApi(server_url=self.api_url,api_key=self.api_key)

	def create_scan(self, endpoints): #Returns a Burp-specific scan ID.
		try:
			scan_id = self.api_obj.initiate_scan({'urls': endpoints})
		except Exception as e:
			logger.warning('Create scan API for Burp failed')
			return None
		else:
			return scan_id

	def poll_scan(self, burp_scan_id):
		try:
			status_response = self.api_obj.get_scan(burp_scan_id)
			status = status_response['scan_status']
		except Exception as e:
			logger.warning('Poll scan API for Burp failed')
			return None
		else:
			if status == 'failed':
				return None
			else:
				return (status == 'succeeded')

	def retrieve_scan(self, burp_scan_id):
		try:
			file = self.api_obj.get_scan(burp_scan_id, raw=True).content.decode()
		except Exception as e:
			logger.warning('Retrieve scan API for Burp failed')
			return None
		else:
			return file
	
	def __str__(self):
		return f"{self.pk}, BS \"{self.scanner_name}\" at {self.api_url}, {str(self.create_date)}"
	class Meta:
		app_label='dd_downloader'


class Burp_Suite_Scan(Scan):
	endpoints = models.TextField()
	scan_id = models.IntegerField(default=None,null=True,validators=[MinValueValidator(1)])
	def can_create(self, auto=False):
		if auto:
			return self.status == Scan.NEW
		else:
			return self.status == Scan.NEW or self.status == Scan.ERRORS or self.status == Scan.FINISHED
	def can_retrieve(self, auto=False):
		if auto:
			return self.status == Scan.FINISHED
		else:
			return self.status == Scan.FINISHED or self.status == Scan.RETRIEVED
	def can_pause(self):
		return False
	def can_resume(self):
		return False
	def can_stop(self):
		return False

	def create(self):
		if not self.can_create():
			logger.warning('Tried to create non-creatable Burp scan')
			return
		self.status = Scan.CREATING
		self.save()
		scan_id = self.scanner.create_scan(self.endpoints.split(','))
		if scan_id is None:
			self.status = Scan.ERRORS
			logger.warning('Burp start failed')
		else:
			self.scan_id = scan_id
			self.start_date = timezone.now()
			self.status = Scan.IN_PROGRESS
		self.save()

	def poll(self):
		poll = self.scanner.poll_scan(self.scan_id)
		if poll:
			logger.info('Burp poll finished')
			self.status = Scan.FINISHED
			self.end_date = timezone.now()
			self.save()
		elif poll is None:
			logger.warning('Burp poll ended with error')
			self.status = Scan.ERRORS
			self.save()
		else:
			logger.info('Burp poll still in progress')

	def retrieve(self):
		if not self.can_retrieve():
			logger.warning('Tried to retrieve non-retrievable Burp scan')
			return
		self.status = Scan.RETRIEVING
		self.save()
		file = self.scanner.retrieve_scan(self.scan_id)
		if file is None:
			logger.warning('File retrieval failed')
			self.status = Scan.ERRORS
		else:
			self.save_result(file)
			logger.info('Retrieval success')
			self.end_date = timezone.now()
			self.status = Scan.RETRIEVED
		self.save()

	class Meta:
		app_label='dd_downloader'

class Burp_Suite_Scanner_Create_Form(forms.ModelForm):
	class Meta:
		model = Burp_Suite_Scanner
		fields = ['scanner_name', 'api_url', 'api_key', 'notes']

class Burp_Suite_Scan_Create_Form(forms.ModelForm):
	class Meta:
		model = Burp_Suite_Scan
		fields = ['scan_name', 'endpoints', 'auto_create','auto_retrieve','notes']