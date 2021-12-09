from django.urls import path

from . import views

app_name='dd_downloader'
urlpatterns = [
	#list views
	path('', views.scan_list_endpoint, name='index'), #ViewsSimpleTestCase
	path('scanner/', views.scanner_list_endpoint, name='scanner list page'), #ViewsSimpleTestCase
	
	#scanners
	path('scanner/create/', views.scanner_create_endpoint, name='scanner create page'), #ViewsSimpleTestCase
	path('scanner/<int:scanner_pk>/', views.scanner_detail_endpoint, name='scanner detail page'), #scanner-specific
	path('scanner/<int:scanner_pk>/edit', views.scanner_edit_endpoint, name='scanner edit page'), #scanner-specific
	path('scanner/<int:scanner_pk>/delete', views.scanner_delete_endpoint, name='scanner delete page'), #ViewsTestCase
	path('scanner/<int:scanner_pk>/create', views.scan_create_endpoint, name='scan create page'), #scanner-specific

	#scans
	path('scan/<int:scan_pk>/', views.scan_detail_endpoint, name='scan detail page'), #scanner-specific
	path('scan/<int:scan_pk>/edit', views.scan_edit_endpoint, name='scan edit page'), #scanner-specific
	path('scan/<int:scan_pk>/result', views.scan_result_endpoint, name='scan result endpoint'), #scanner-specific
	path('scan/<int:scan_pk>/delete', views.scan_delete_endpoint, name='scan delete page'), #ViewsTestCase

	path('scan/<int:scan_pk>/create', views.scan_manual_create_endpoint, name='scan manual create endpoint'),
	path('scan/<int:scan_pk>/start', views.scan_manual_start_endpoint, name='scan manual start endpoint'),
	path('scan/<int:scan_pk>/pause', views.scan_manual_pause_endpoint, name='scan manual pause endpoint'),
	path('scan/<int:scan_pk>/resume', views.scan_manual_resume_endpoint, name='scan manual resume endpoint'),
	path('scan/<int:scan_pk>/stop', views.scan_manual_stop_endpoint, name='scan manual stop endpoint'),
	path('scan/<int:scan_pk>/retrieve', views.scan_manual_retrieve_endpoint, name='scan manual retrieve endpoint'),

	#ajax endpoint
	path('api/scan/', views.scan_list_ajax_endpoint, name='scan list ajax'), #ViewsTestCase
	path('api/scanner/', views.scanner_list_ajax_endpoint, name='scanner list ajax'), #ViewsTestCase
	path('api/scanner/<int:scanner_pk>/scan', views.child_scan_list_ajax_endpoint, name='child scan list ajax'), #ViewsTestCase
	path('api/batch/', views.batch_control_endpoint, name='batch control ajax'),

	#batch downloading
	path('api/download/', views.batch_download_endpoint, name='batch download endpoint'),
]
