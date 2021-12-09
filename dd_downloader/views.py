from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, FileResponse
from django.urls import reverse
from .celery_tasks import manual_create_scan,manual_start_scan,manual_pause_scan,manual_resume_scan,manual_stop_scan,manual_retrieve_scan
from .models import Scanner, Scan

#Common error messages
SCANNER_FETCH_ERROR = "An error occured while fetching scanner {pk} from the database."
SCAN_FETCH_ERROR = "An error occured while fetching scan {item} from the database."
INVALID_PARAMETERS_ERROR = "The necessary parameter(s) in a request ({params}) were missing or invalid."
GENERIC_ERROR = "An unknown error occured."

import logging
logger = logging.getLogger(__name__)

"""
Return the scan list page, listing all scans in the application in a DataTable.
"""
def scan_list_endpoint(request):
	try:
		scan_list = Scan.objects.all()
	except Exception as e:
		logger.exception('Unknown error occured while retrieving scan list')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})
	return render(request, 'dd_downloader/scan_list.html', {'scan_list': scan_list})

"""
Return the scanner list page, listing all scanners in the application in a DataTable.
"""
def scanner_list_endpoint(request):
	try:
		scanner_list = Scanner.objects.all()
	except Exception as e:
		logger.exception('Unknown error occured while retrieving scanner list')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})
	return render(request, 'dd_downloader/scanner_list.html', {'scanner_list': scanner_list})

"""
Return the scanner creation page. Form class is provided by the static get_scanner_create_form_class method in the Scanner class. On GET without any parameters, this simply returns a radio button list of all the different scanner types that were found in the scanner_types directory.
On submission of the radio button list, the parameter "dd_downloader_scanner_type" is sent to the same endpoint as a GET request, and the corresponding scanner type's scanner creation form is returned.
On submission of this form by POST, the form is validated and the scanner is created.
"""
def scanner_create_endpoint(request):
	from . import class_directory
	scanner_type_dict = class_directory.get_scanner_types()
	if request.method == 'POST':
		try:
			scanner_type = request.POST['dd_downloader_scanner_type']
			scanner_class = scanner_type_dict[scanner_type]['scanner']
		except KeyError as e:
			logger.error('Invalid type found while creating scan!')
			error_msg = INVALID_PARAMETERS_ERROR.format(params='dd_downloader_scanner_type')
			return render(request, 'dd_downloader/error.html', {'error_msg': error_msg})
		except Exception as e:
			logger.exception('Unknown error occured while determining scanner type for creation')
			return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})
		
		form_class = scanner_class.get_scanner_create_form_class()
		f = form_class(request.POST)
		if f.is_valid():
			f.save()
			return HttpResponseRedirect(reverse('dd_downloader:scanner list page'))
		else:
			logger.error('Scanner creation unsuccessful')
			return render(request, 'dd_downloader/error.html', {'error_msg': 'Scanner creation parameters were not valid'})

	elif request.method == 'GET':
		try:
			scanner_type = request.GET['dd_downloader_scanner_type']
			scanner_class = scanner_type_dict[scanner_type]['scanner']
		except KeyError as e:
			logger.debug('No type/invalid type found, returning default page')
			return render(request, 'dd_downloader/scanner_create.html', {'scanner_type_list':scanner_type_dict.keys()})

		form_class = scanner_class.get_scanner_create_form_class()
		return render(request, 'dd_downloader/scanner_create.html', {'scanner_type_list':scanner_type_dict.keys(),'dd_downloader_scanner_type':scanner_type, 'form':form_class().as_p()})

"""
Return a scanner's detail page. Template is provided by the static get_scanner_detail_template_path method in the Scanner class.
"""
def scanner_detail_endpoint(request, scanner_pk):
	try:
		scanner_obj = Scanner.objects.get(pk=scanner_pk)
	except Scanner.DoesNotExist as e:
		logger.error('Nonexistent scanner')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCANNER_FETCH_ERROR.format(pk=scanner_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scanner details')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})
	
	return render(request,scanner_obj.get_scanner_detail_template_path(), {'scanner':scanner_obj,'child_scan_list':scanner_obj.scan_set.all()})

"""
Return the scanner edit page. Form class is provided by the static get_scanner_create_form_class method in the Scanner class. On GET without any parameters, this simply returns the form.
On POST, this validates the form and updates the scanner object with the given parameters.
"""
def scanner_edit_endpoint(request, scanner_pk):
	try:
		scanner_obj = Scanner.objects.get(pk=scanner_pk)
	except Scanner.DoesNotExist as e:
		logger.error('Nonexistent scanner')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCANNER_FETCH_ERROR.format(pk=scanner_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scanner for editing')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if request.method == 'POST':
		form_class = scanner_obj.get_scanner_create_form_class()
		f = form_class(request.POST, instance=scanner_obj)
		if f.is_valid():
			f.save()
			return HttpResponseRedirect(reverse('dd_downloader:index'))
		else:
			logger.error('Scanner edit unsuccessful')
			return render(request, 'dd_downloader/error.html', {'error_msg': 'Scanner edit parameters were not valid'})
	else:
		form_class = scanner_obj.get_scanner_create_form_class()
		form = form_class(instance=scanner_obj)
		return render(request, 'dd_downloader/scanner_edit.html', {'form': form.as_p(), 'scanner': scanner_obj})

"""
Return the scanner delete page. On GET, this returns a confirmation page warning the user about deleting a scanner.
On POST, this deletes the scanner.
"""
def scanner_delete_endpoint(request, scanner_pk):
	try:
		scanner_obj = Scanner.objects.get(pk=scanner_pk)
	except Scanner.DoesNotExist as e:
		logger.error('Nonexistent scanner')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCANNER_FETCH_ERROR.format(pk=scanner_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scanner for deletion')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if request.method == 'GET':
		return render(request,'dd_downloader/scanner_delete.html', {'scanner': scanner_obj})
	elif (request.method == 'POST'):
		logger.debug(f"Deleting {scanner_obj}")
		scanner_obj.delete()
		return HttpResponseRedirect(reverse('dd_downloader:scanner list page'))

#Scans


"""
Return the scan creation page for a given scanner. Form class is provided by the static get_scan_create_form_class method in the Scanner class. On GET without any parameters, this simply returns the form.
On submission of this form by POST, the form is validated and the scan is created under the given scanner.
"""
def scan_create_endpoint(request, scanner_pk):
	try:
		scanner_obj = Scanner.objects.get(pk=scanner_pk)
	except Scanner.DoesNotExist as e:
		logger.error('Nonexistent scanner')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCANNER_FETCH_ERROR.format(pk=scanner_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scanner for scan creation')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})
	if request.method == 'POST':
		form_class = scanner_obj.get_scan_create_form_class()
		f = form_class(request.POST)
		if f.is_valid():
			#this just takes care of the scanner ForeignKey field
			s = f.save(commit=False)
			s.scanner = scanner_obj
			s.save()
			return HttpResponseRedirect(reverse('dd_downloader:index'))
		else:
			logger.error('Scan creation unsuccessful')
			return render(request, 'dd_downloader/error.html', {'error_msg': 'Scan creation parameters were not valid'})
	else:
		form_class = scanner_obj.get_scan_create_form_class()
		return render(request, 'dd_downloader/scan_create.html',{'form':form_class().as_p(),'scanner':scanner_obj})

"""
Return a scan's detail page. Template is provided by the static get_scan_detail_template_path method in the Scanner class.
"""
def scan_detail_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan details')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	return render(request, scan_obj.scanner.get_scan_detail_template_path(), {'scan':scan_obj})


"""
Return the scan edit page. Form class is provided by the static get_scan_create_form_class method in the Scanner class. On GET without any parameters, this simply returns the form.
On POST, this validates the form and updates the scan object with the given parameters.
"""
def scan_edit_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan for editing')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if request.method == 'POST':
		form_class = scan_obj.scanner.get_scan_create_form_class()
		f = form_class(request.POST, instance=scan_obj)
		if f.is_valid():
			f.save()
			return HttpResponseRedirect(reverse('dd_downloader:index'))
		else:
			logger.error('Scan edit unsuccessful')
			return render(request, 'dd_downloader/error.html', {'error_msg': 'Scan edit parameters were not valid'})
	else:
		form_class = scan_obj.scanner.get_scan_create_form_class()
		form = form_class(instance=scan_obj)
		return render(request, 'dd_downloader/scan_edit.html', {'form': form.as_p(), 'scan': scan_obj})

"""
Return the scan delete page. On GET, this returns a confirmation page warning the user about deleting a scan.
On POST, this deletes the scan.
"""
def scan_delete_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan for deletion')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if request.method == 'GET':
		return render(request,'dd_downloader/scan_delete.html', {'scan': scan_obj})
	elif request.method == 'POST':
		logger.debug(f"Deleting scan {scan_obj}")
		scan_obj.delete()
		return HttpResponseRedirect(reverse('dd_downloader:index'))

"""
Return the scan's result as a file download.
"""
def scan_result_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan result')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	return FileResponse(scan_obj.result.file,filename='results')

#Manual scan control endpoints
"""
Each manual scan control endpoint checks if the scan object is eligible to have the command run on them. If they are not eligible, an error page is returned.
"""
def scan_manual_create_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan for manual creation')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if not scan_obj.can_create():
		error_msg = "Scan could not be created."
		logger.warning(error_msg)
		return render(request, 'dd_downloader/error.html', {'error_msg': error_msg})
	manual_create_scan.delay(scan_obj.pk)
	return HttpResponseRedirect(reverse('dd_downloader:index'))

def scan_manual_start_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan for manual start')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if not scan_obj.can_start():
		error_msg = "Scan could not be started."
		return render(request, 'dd_downloader/error.html', {'error_msg': error_msg})
	manual_start_scan.delay(scan_obj.pk)
	return HttpResponseRedirect(reverse('dd_downloader:index'))

def scan_manual_pause_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan for manual pause')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if not scan_obj.can_pause():
		error_msg = "Scan could not be paused."
		logger.warning(error_msg)
		return render(request, 'dd_downloader/error.html', {'error_msg': error_msg})
	manual_pause_scan.delay(scan_obj.pk)
	return HttpResponseRedirect(reverse('dd_downloader:index'))

def scan_manual_resume_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan for manual resume')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if not scan_obj.can_resume():
		error_msg = "Scan could not be resumed."
		logger.warning(error_msg)
		return render(request, 'dd_downloader/error.html', {'error_msg': error_msg})
	manual_resume_scan.delay(scan_obj.pk)
	return HttpResponseRedirect(reverse('dd_downloader:index'))

def scan_manual_stop_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan for manual stop')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if not scan_obj.can_stop():
		error_msg = "Scan could not be stopped."
		logger.warning(error_msg)
		return render(request, 'dd_downloader/error.html', {'error_msg': error_msg})
	manual_stop_scan.delay(scan_obj.pk)
	return HttpResponseRedirect(reverse('dd_downloader:index'))

def scan_manual_retrieve_endpoint(request, scan_pk):
	try:
		scan_obj = Scan.objects.get(pk=scan_pk)
	except Scan.DoesNotExist as e:
		logger.error('Nonexistent scan')
		return render(request, 'dd_downloader/error.html', {'error_msg': SCAN_FETCH_ERROR.format(pk=scan_pk)})
	except Exception as e:
		logger.exception('Unknown error while fetching scan for manual retrieval')
		return render(request, 'dd_downloader/error.html', {'error_msg': GENERIC_ERROR})

	if not scan_obj.can_retrieve():
		error_msg = "Scan could not be retrieved."
		logger.warning(error_msg)
		return render(request, 'dd_downloader/error.html', {'error_msg': error_msg})
	manual_retrieve_scan.delay(scan_obj.pk)
	return HttpResponseRedirect(reverse('dd_downloader:index'))

#Batch control endpoints
"""
Accepts a JSON object containing a list of scan PKs. If the result attribute of each scan object contains a file, they are zipped and the zipped result is returned as a file download.
"""
def batch_download_endpoint(request):
	if request.method == 'POST':
		try:
			pk_list = request.POST.getlist('pk_list[]')
		except Exception as e:
			logger.exception('Could not retrieve list of scan PKs for batch download')
			return render(request, 'dd_downloader/error.html', {'error_msg': "Could not retrieve list of scan PKs for batch download"})
		
		results = []
		for pk in pk_list:
			try:
				scan_obj = Scan.objects.get(pk=pk)
			except Exception as e:
				logger.exception('Scan could not be found for batch download')
				return render(request, 'dd_downloader/error.html', {'error_msg': "Nonexistent scan in batch download"})
			else:
				if not scan_obj.result:
					return render(request, 'dd_downloader/error.html', {'error_msg': "Scan with no results discovered while batch downloading"})
				else:
					results.append(scan_obj)
		import zipfile
		import io
		temp_zip = io.BytesIO()
		try:
			with zipfile.ZipFile(temp_zip, "w") as z:
				for scan_obj in results:
					z.write(scan_obj.result.path, arcname=scan_obj.result.name)
		except Exception as e:
			logger.exception('Zipping failed')
			return render(request, 'dd_downloader/error.html', {'error_msg': "An error occurred while archiving the scan results"})
		resp = HttpResponse(temp_zip.getvalue(), content_type="application/zip")
		resp['Content-Disposition'] = 'filename=result.zip'
		return resp
	else:
		return render(request, 'dd_downloader/error.html', {'error_msg': "Invalid method for this endpoint"})


"""
Accepts a JSON object containing a list of scan PKs, and a command. All scan objects that are eligible for the command will have the command run on them. Any scan objects that were not eligible or were missing will not have any command run on them, and will be placed in a list that is returned to the user as JSON object.
"""
def batch_control_endpoint(request):
	if request.method == 'POST':
		try:
			command = request.POST['command']
			target_type = request.POST['type']
			pk_list = request.POST.getlist('pk_list[]')
		except Exception as e:
			logger.error('Command, type, and/or pk_list not found')
			return JsonResponse({'status': 'invalid params'})
		if command not in ['CR','ST','PS','RS','SP','RT','DL'] and target_type not in ['scanner','scan']:
			logger.error('Invalid command and/or type')
			return JsonResponse({'status': 'invalid command and/or type'})

		if (target_type == 'scan'):
			missing_scan_pks = []
			unsuccessful_scans = []
			for pk in pk_list:
				try:
					scan_obj = Scan.objects.get(pk=pk)
				except Exception as e:
					logger.error('Nonexistent scan in batch command')
					missing_scan_pks.append(pk)
				else:
					if command == 'CR' and scan_obj.can_create():
						manual_create_scan.delay(scan_obj.pk)
					elif command == 'ST' and scan_obj.can_start():
						manual_start_scan.delay(scan_obj.pk)
					elif command == 'PS' and scan_obj.can_pause():
						manual_pause_scan.delay(scan_obj.pk)
					elif command == 'RS' and scan_obj.can_resume():
						manual_resume_scan.delay(scan_obj.pk)
					elif command == 'SP' and scan_obj.can_stop():
						manual_stop_scan.delay(scan_obj.pk)
					elif command == 'RT' and scan_obj.can_retrieve():
						manual_retrieve_scan.delay(scan_obj.pk)
					elif command == 'DL':
						scan_obj.delete()
					else:
						unsuccessful_scans.append(scan_obj)
			resp = {}
			if unsuccessful_scans:
				unsuccessful_names = []
				logger.info(f"These scans failed to {command}: {unsuccessful_scans}")
				for scan_obj in unsuccessful_scans:
					unsuccessful_names.append(scan_obj.scan_name)
				resp['unsuccessful'] = unsuccessful_names
			if missing_scan_pks:
				resp['missing'] = missing_scan_pks

			resp['status'] = 'failure' if (unsuccessful_scans or missing_scan_pks) else 'success'
			return JsonResponse(resp)

		elif (target_type == 'scanner'):
			missing_scanner_pks = []
			for pk in pk_list:
				try:
					scanner_obj = Scanner.objects.get(pk=pk)
				except Exception as e:
					logger.error('Nonexistent scanner in batch command')
					missing_scanner_pks.append(pk)
				else:
					if command == 'DL':			
						logger.info(f"delete {pk}")
						scanner_obj.delete()
			resp = {}
			if missing_scanner_pks:
				resp['missing'] = missing_scanner_pks
			resp['status'] = 'failure' if (missing_scanner_pks) else 'success'
			return JsonResponse(resp)
	else:
		return JsonResponse({'status': 'invalid method'})

"""
Helper functions for serializing scan/scanner lists
"""
def scan_list_to_json(request, scan_list):
	from django.utils.html import escape
	scan_json = {'data':[]}
	for scan in scan_list:
		scan_json['data'].append ({
			'PK':scan.pk,
			'Scan Name': {
				'URL': request.build_absolute_uri(reverse('dd_downloader:scan detail page',args=[scan.pk])),
				'Name': escape(scan.scan_name)
			},
			'Status':escape(scan.get_status_display()),
			'Automation': {
				'Auto Create': scan.auto_create,
				'Auto Start': scan.auto_start,
				'Auto Retrieve': scan.auto_retrieve,
			},
			'Parent Scanner': {
				'URL': request.build_absolute_uri(reverse('dd_downloader:scanner detail page',args=[scan.scanner.pk])),
				'Name': escape(scan.scanner.scanner_name)
			},
			'Created On':scan.create_date,
			'Started On':scan.start_date,
			'Ended On':scan.end_date
		})
	return scan_json

def scanner_list_to_json(request, scanner_list):
	from django.utils.html import escape
	scanner_json = {'data':[]}
	for scanner in scanner_list:
		scanner_json['data'].append ({
			'PK':scanner.pk,
			'Scanner Name': {
				'URL':request.build_absolute_uri(reverse('dd_downloader:scanner detail page',args=[scanner.pk])),
				'Name':escape(scanner.scanner_name)
			},
			'# of Child Scans': len(scanner.scan_set.all()),
			'Created On':scanner.create_date
		})
	return scanner_json

#AJAX endpoints
"""
Returns a JSON object with details of all scan objects in the web application.
"""
def scan_list_ajax_endpoint(request):
	scan_list = Scan.objects.all()
	return JsonResponse(scan_list_to_json(request,scan_list))

"""
Returns a JSON object with details of all scan objects under a scanner.
"""
def child_scan_list_ajax_endpoint(request, scanner_pk):
	scanner_obj = Scanner.objects.get(pk=scanner_pk)
	scan_list = scanner_obj.scan_set.all()
	return JsonResponse(scan_list_to_json(request,scan_list))

"""
Returns a JSON object with details of all scanner objects in the web application.
"""
def scanner_list_ajax_endpoint(request):
	scanner_list = Scanner.objects.all()		
	return JsonResponse(scanner_list_to_json(request,scanner_list))
