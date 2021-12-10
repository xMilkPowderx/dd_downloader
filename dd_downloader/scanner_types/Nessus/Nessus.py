from django.db import models
from dd_downloader.models import Scanner, Scan
from django.utils import timezone
from dd_downloader.scanner_types.Nessus.NessusAPI import NessusAPI
from django import forms
from django.core.validators import MinValueValidator
import logging

logger = logging.getLogger('dd_downloader.scanner_types.Nessus')
class Nessus_Scanner(Scanner):
	@staticmethod
	def get_scanner_detail_template_path():
		return 'dd_downloader/scanner_types/Nessus/scanner_detail.html'
	@staticmethod
	def get_scan_detail_template_path():
		return 'dd_downloader/scanner_types/Nessus/scan_detail.html'
	@staticmethod
	def get_scanner_create_form_class():
		return Nessus_Scanner_Create_Form
	@staticmethod
	def get_scan_create_form_class():
		return Nessus_Scan_Create_Form

	#Address of the Nessus API
	api_url = models.CharField('API URL', max_length=200)
	
	#API Access key
	access_key = models.CharField('API Access Key', max_length=200)
	
	#API Secret key
	secret_key = models.CharField('API Secret Key', max_length=200)

	#The default policy that is to be used when creating new scans with this scanner.
	default_policy_id = models.IntegerField('Default policy ID for scans (optional)',blank=True,null=True,default=None)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.api_obj = NessusAPI(api_url=self.api_url, access_key=self.access_key, secret_key=self.secret_key, scan_policy_id=self.default_policy_id)


	def create_scan(self, endpoints, override_policy_id = None): #Returns a Nessus-specific scan ID.
		policy_id = None
		if override_policy_id is not None:
			policy_id = override_policy_id
		try:
			scan_id = self.api_obj.create_scan(scan_name = f"dd_downloader {self.pk}",targets=endpoints, override_policy_id=policy_id)
		except Exception as e:
			logger.exception('Create scan API for Nessus failed')
			return None
		else:
			return scan_id

	def start_scan(self, nessus_scan_id):
		try:
			self.api_obj.launch_scan(nessus_scan_id)
		except Exception as e:
			logger.exception('Start scan API for Nessus failed')
		else:
			return True

	def poll_scan(self, nessus_scan_id):
		try:
			poll = self.api_obj.scan_details(nessus_scan_id)
		except Exception as e:
			logger.exception('Poll scan API for Nessus failed')
			return None
		else:
			return poll

	def retrieve_scan(self, nessus_scan_id):
		try:
			file = self.api_obj.download_scan(nessus_scan_id)
		except Exception as e:
			logger.exception('Retrieve scan API for Nessus failed')
			return None
		else:
			return file

	def __str__(self):
		return f"{self.pk}, NS \"{self.scanner_name}\" at {self.api_url}, {str(self.create_date.time())}"
	class Meta:
		app_label='dd_downloader'


class Nessus_Scan(Scan):
	endpoints = models.TextField()
	override_policy_id = models.IntegerField(default=None,null=True,blank=True)
	scan_id = models.IntegerField(null=True,default=None,validators=[MinValueValidator(1)])
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
			logger.warning('Tried to create non-creatable scan')
			return
		self.status = Scan.CREATING
		self.save()
		created_scan_id = self.scanner.create_scan(self.endpoints, self.override_policy_id)
		if created_scan_id is None:
			logger.warning('Nessus creation ended with error')
			self.status = Scan.ERRORS
		else:
			self.scan_id = created_scan_id
			self.status = Scan.CREATED
		self.save()
	
	def start(self):
		if not self.can_start():
			logger.warning('Tried to start non-startable scan')
		self.status = Scan.STARTING
		self.save()
		start_result = self.scanner.start_scan(self.scan_id)
		if not start_result:
			logger.warning('Nessus start ended with error')
			self.status = Scan.ERRORS
		else:
			self.start_date = timezone.now()
			self.status = Scan.IN_PROGRESS
		self.save()

	def poll(self):
		if self.status != Scan.IN_PROGRESS:
			return
		poll = self.scanner.poll_scan(self.scan_id)
		if poll:
			logger.info('Nessus poll finished')
			self.status = Scan.FINISHED
			self.end_date = timezone.now()
			self.save()
		elif poll is None:
			logger.warning('Nessus poll ended with error')
			self.status = Scan.ERRORS
			self.save()
		else:
			logger.info('Nessus poll still in progress')
			

	def retrieve(self):
		if not self.can_retrieve():
			logger.warning('Tried to retrieve non-retrievable scan')
			return
		self.status = Scan.RETRIEVING
		self.save()
		file = self.scanner.retrieve_scan(self.scan_id)
		if file is None:
			logger.warning('File retrieval failed')
			self.status = Scan.ERRORS
		else:
			self.save_result(file)
			logger.info('Retrieval successful')
			self.status = Scan.RETRIEVED
		self.save()


	def __str__(self):
		return f"{self.pk}, NS \"{self.scan_name}\", {str(self.create_date.time())}"
	class Meta:
		app_label='dd_downloader'

"""
Classes for defining the creation forms. Ensure that the fields are in the order that you would like them to appear.
"""

class Nessus_Scanner_Create_Form(forms.ModelForm):
	class Meta:
		model = Nessus_Scanner
		fields = ['scanner_name', 'api_url', 'access_key', 'secret_key', 'default_policy_id', 'notes']


class Nessus_Scan_Create_Form(forms.ModelForm):
	class Meta:
		model = Nessus_Scan
		fields = ['scan_name', 'endpoints', 'override_policy_id', 'auto_create','auto_start','auto_retrieve','notes']
