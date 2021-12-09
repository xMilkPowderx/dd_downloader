#from celery import Celery
from dd_scanner.celery import app
from dd_downloader.models import Scanner, Scan
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

"""
Iterates through all scanners, and queues a "process-scans" Celery task for each one.
"""
@app.task(name='process-all-scanners')
def process_all_scanners():
	scanner_list = Scanner.objects.all()
	for scanner_obj in scanner_list:
		process_scans.delay(scanner_obj.pk)

"""
Iterates through all scans under a scanner, and queues a "process-scan" Celery task for each one.
"""
@app.task(name='process-scans')
def process_scans(scanner_pk):
	scan_list = Scanner.objects.get(pk=scanner_pk).scan_set.all()
	for scan_obj in scan_list:
		process_scan.delay(scan_obj.pk)

"""
Automation task. Checks a scan's status, and depending on the status and whether it is eligible for automatic creation/starting/retrieval, it will call the corresponding action.
"""
@app.task(name='process-scan')
def process_scan(scan_pk):
	scan_obj = Scan.objects.get(pk=scan_pk)
	if scan_obj.status == Scan.NEW:
		if scan_obj.auto_create and scan_obj.can_create(auto=True):
			logger.info(f"Automatically creating {scan_obj}")
			scan_obj.create()
	elif scan_obj.status == Scan.CREATED:
		if scan_obj.auto_start and scan_obj.can_start(auto=True):
			logger.info(f"Automatically starting {scan_obj}")
			scan_obj.start()
	elif scan_obj.status == Scan.FINISHED:
		if scan_obj.auto_retrieve and scan_obj.can_retrieve(auto=True):
			logger.info(f"Automatically retrieving {scan_obj}")
			scan_obj.retrieve()
	elif scan_obj.status == Scan.IN_PROGRESS:
		scan_obj.poll()
#	elif scan_obj.status == Scan.ERRORS:
#		logger.warning(f"Error: {scan_obj}")

"""
Manual scan command tasks.
"""
@app.task(name='manual-create-scan')
def manual_create_scan(scan_pk):
	Scan.objects.get(pk=scan_pk).create()

@app.task(name='manual-start-scan')
def manual_start_scan(scan_pk):
	Scan.objects.get(pk=scan_pk).start()

@app.task(name='manual-pause-scan')
def manual_pause_scan(scan_pk):
	Scan.objects.get(pk=scan_pk).pause()

@app.task(name='manual-resume-scan')
def manual_resume_scan(scan_pk):
	Scan.objects.get(pk=scan_pk).resume()

@app.task(name='manual-stop-scan')
def manual_stop_scan(scan_pk):
	Scan.objects.get(pk=scan_pk).stop()

@app.task(name='manual-retrieve-scan')
def manual_retrieve_scan(scan_pk):
	Scan.objects.get(pk=scan_pk).retrieve()