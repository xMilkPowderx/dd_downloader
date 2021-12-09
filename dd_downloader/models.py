from django.db import models
from polymorphic.models import PolymorphicModel
from django.core.files.storage import FileSystemStorage
from django.core.validators import RegexValidator

"""
Base Scanner/Scan classes
"""
class Scanner(PolymorphicModel):
	#Custom name for this scanner.
	scanner_name = models.CharField('Scanner Name',max_length=200, unique=True)
	#Date when the scanner was initially created.
	create_date = models.DateTimeField('Date Created', auto_now_add=True)
	#Any notes that the user may wish to add
	notes = models.TextField('Notes (optional)',blank=True)
	
	"""
	Should return the filepath to the template HTML file for the scanner's detail page. The root of the path is "<root directory>/dd_downloader/templates/"
	"""
	@staticmethod
	def get_scanner_detail_template_path():
		raise NotImplementedError
	"""
	Should return the filepath to the template HTML file for the scan's detail page. The root of the path is "<root directory>/dd_downloader/templates/"
	"""
	@staticmethod
	def get_scan_detail_template_path():
		raise NotImplementedError
	"""
	Should return a reference to the ModelForm class for creating a scanner.
	"""
	@staticmethod
	def get_scanner_create_form_class():
		raise NotImplementedError
	"""
	Should return a reference to the ModelForm class for creating a scan under this scanner.
	"""
	@staticmethod
	def get_scan_create_form_class():
		raise NotImplementedError
	"""
	For debugging purposes.
	"""
	def __str__(self):
		return f"{self.id}, \"{self.scanner_name}\""


fs = FileSystemStorage()

class Scan(PolymorphicModel):
	#Reference to the parent scanner of this scan.
	scanner = models.ForeignKey(
		Scanner,
		on_delete=models.CASCADE
	)
	#Custom name for this scan.
	scan_name = models.CharField('Scan Name',max_length=200,unique=True)
	#Date when the scan was initially created.
	create_date = models.DateTimeField('Date Created', auto_now_add=True)
	#Date when the scan was last started.
	start_date = models.DateTimeField('Date Started', null=True)
	#Date when the scan was last finished.
	end_date = models.DateTimeField('Date Ended', null=True)
	#Any notes that the user may wish to add
	notes = models.TextField('Notes (optional)', blank=True)
	#The results of the scan can be stored here.
	result = models.FileField('Scan Result',storage=fs)

	#Flags that determine whether this scan can be automatically created, started, or retrieved by Celery.
	auto_create = models.BooleanField('Automatically create scan',default=False)
	auto_start = models.BooleanField('Automatically start scan',default=False)
	auto_retrieve = models.BooleanField('Automatically retrieve scan',default=False)

	"""
	Condition for whether a scan be created. Can be overridden in the extension class.
	"""
	def can_create(self, auto=False):
		return self.status == Scan.NEW
	def create(self):
		raise NotImplementedError
	"""
	Condition for whether a scan be started. Can be overridden in the extension class.
	"""
	def can_start(self, auto=False):
		return self.status == Scan.CREATED
	def start(self):
		raise NotImplementedError
	"""
	Function that will be run periodically while the scan is in the IN_PROGRESS stage. If you would like the scan to have an IN_PROGRESS stage but not do anything, this can be overridden to do nothing.
	"""
	def poll(self):
		raise NotImplementedError
	"""
	Condition for whether a scan be paused. Can be overridden in the extension class.
	"""
	def can_pause(self):
		return self.status == Scan.IN_PROGRESS
	def pause(self):
		raise NotImplementedError
	"""
	Condition for whether a scan be resumed. Can be overridden in the extension class.
	"""
	def can_resume(self):
		return self.status == Scan.PAUSED
	def resume(self):
		raise NotImplementedError
	"""
	Condition for whether a scan be stopped. Can be overridden in the extension class.
	"""
	def can_stop(self):
		return self.status == Scan.IN_PROGRESS
	def stop(self):
		raise NotImplementedError
	"""
	Condition for whether a scan be retrieved. Can be overridden in the extension class.
	"""
	def can_retrieve(self, auto=False):
		return self.status == Scan.FINISHED
	def retrieve(self):
		raise NotImplementedError

	NEW			= 'NW' #Nothing has happened on the scanning tool.
	CREATING	= 'CR' #Mutex stage prior to CREATED.
	CREATED		= 'CD' #Scan has been 'created' on the scanning tool, but not 'started' yet.
	STARTING	= 'ST' #Mutex stage prior to IN_PROGRESS.
	IN_PROGRESS	= 'IP' #Scan is 'in progress' and poll() will be called periodically until the function changes the scan's state to something else.
	PAUSED		= 'PD' #Scan is temporarily paused, and can be restored to IN_PROGRESS by resuming
	STOPPED		= 'ST' #Scan is terminated, with no intention of being resumed in the future.	
	FINISHED	= 'FI' #Scan completed, but results not retrieved yet.
	RETRIEVING	= 'RG' #Mutex stage prior to RETRIEVED.
	RETRIEVED	= 'RD' #Result successfully retrieved from the scanning tool, and stored in the "result" attribute.
	ERRORS		= 'ER' #Generic error stage for any errors that might have occurred in any stages.
	#Choices for scan's status.
	SCAN_STATUS_CHOICES = [
		(NEW, 'New'),
		(CREATING, 'Creating'),
		(CREATED, 'Created'),
		(STARTING, 'Starting'),
		(IN_PROGRESS, 'In progress'),
		(PAUSED, 'Paused'),
		(STOPPED, 'Stopped'),
		(FINISHED, 'Finished'),
		(RETRIEVING, 'Retrieving'),
		(RETRIEVED, 'Retrieved'),
		(ERRORS, 'Error occurred')
	]

	#The current status of the scan.
	status = models.CharField(
		max_length=2,
		choices=SCAN_STATUS_CHOICES,
		default=NEW
	)

	"""
	Helper function for creating a ContentFile and saving it to the "result" attribute.
	"""
	def save_result(self,file):
		from os.path import join
		self.delete_result()
		from django.core.files.base import ContentFile
		from django.utils.text import slugify
		cf = ContentFile(file)
		
		fp = join(slugify(self.scanner.scanner_name),slugify(self.scan_name))
		print(fp)
		self.result.save(fp, cf, save=True)
	"""
	Helper function for deleting the file in the "result" attribute.
	"""
	def delete_result(self):
		if self.result:
			self.result.delete()

	"""
	For debugging purposes.
	"""
	def __str__(self):
		return f"{self.pk}, {self.status}, \"{self.scan_name}\""

#Loads all scanner modules from scanner_types.
from . import class_directory
class_directory.load()