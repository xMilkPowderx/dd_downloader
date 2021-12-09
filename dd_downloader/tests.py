from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from dd_downloader.models import Scan, Scanner
from dd_downloader.class_directory import get_scanner_types
# Create your tests here.

class ViewsSimpleTestCase(SimpleTestCase):
	#For each test method, we check whether the status code is 200, whether the correct page is returned, and whether the correct template is used to build the page.
	def test_scan_list_page(self):
		resp = self.client.get(reverse('dd_downloader:index'))
		self.assertEquals(resp.status_code, 200)
		self.assertContains(resp, "<title>All Scans</title>")
		self.assertTemplateUsed(resp,'dd_downloader/scan_list.html')

	def test_scanner_list_page(self):
		resp = self.client.get(reverse('dd_downloader:scanner list page'))
		self.assertEquals(resp.status_code, 200)
		self.assertContains(resp, "<title>All Scanners</title>")
		self.assertTemplateUsed(resp,'dd_downloader/scanner_list.html')
		
	def test_scanner_create_page(self):
		resp = self.client.get(reverse('dd_downloader:scanner create page'))
		self.assertEquals(resp.status_code, 200)
		self.assertContains(resp, "<title>Add a scanner</title>")
		self.assertTemplateUsed(resp,'dd_downloader/scanner_create.html')

		
class ViewsTestCase(TestCase):
	#Setup some scanners and scans
	def setUp(self):
		#We use the currently built-in scanner types (Burp and Nessus) only. The tests can be expanded for other scanner types if desired.
		scanner_types = get_scanner_types()
		self.scanner_pks = {'Nessus':[],'Burp_Suite':[]}
		self.scan_pks = {'Nessus':[],'Burp_Suite':[]}
		nessus_classes = scanner_types['Nessus']
		n1 = nessus_classes['scanner'](scanner_name='Ns_test_1',api_url='https://nessus_test.com:8834',access_key='access1',secret_key='secret1')
		n2 = nessus_classes['scanner'](scanner_name='Ns_test_2',api_url='https://nessus_test_2.com:8834',access_key='access2',secret_key='secret2',default_policy_id=123)
		n1.save()
		n2.save()
		self.scanner_pks['Nessus'].append(n1.pk)
		self.scanner_pks['Nessus'].append(n2.pk)

		ns1 = nessus_classes['scan'](scanner=n1,scan_name='NsScan1',endpoints='https://demo.testfire1.net')
		ns2 = nessus_classes['scan'](scanner=n1,scan_name='NsScan2',endpoints='https://demo.testfire2.net')
		ns3 = nessus_classes['scan'](scanner=n2,scan_name='NsScan3',endpoints='https://demo.testfire3.net')
		ns1.save()
		ns2.save()
		ns3.save()
		self.scan_pks['Nessus'].append(ns1.pk)
		self.scan_pks['Nessus'].append(ns2.pk)
		self.scan_pks['Nessus'].append(ns3.pk)

		burp_suite_classes = scanner_types['Burp_Suite']
		b1 = burp_suite_classes['scanner'](scanner_name='Bs_test_1',api_url='https://burp_test.com:1337',api_key='apikey1')
		b2 = burp_suite_classes['scanner'](scanner_name='Bs_test_2',api_url='https://burp_test_2.com:1337',api_key='apikey2')
		b1.save()
		b2.save()
		self.scanner_pks['Burp_Suite'].append(b1.pk)
		self.scanner_pks['Burp_Suite'].append(b2.pk)

		bs1 = burp_suite_classes['scan'](scanner=b1,scan_name='BsScan1',endpoints='https://demo.testfire1.net')
		bs2 = burp_suite_classes['scan'](scanner=b1,scan_name='BsScan2',endpoints='https://demo.testfire2.net')
		bs3 = burp_suite_classes['scan'](scanner=b2,scan_name='BsScan3',endpoints='https://demo.testfire3.net')
		bs1.save()
		bs2.save()
		bs3.save()
		self.scan_pks['Burp_Suite'].append(bs1.pk)
		self.scan_pks['Burp_Suite'].append(bs2.pk)
		self.scan_pks['Burp_Suite'].append(bs3.pk)


	#Testing of the Ajax endpoints.
	def test_scan_list_ajax(self):
		resp = self.client.get(reverse('dd_downloader:scan list ajax'))
		self.assertEquals(resp.status_code, 200)
		for scanner_type, scanner_type_scan_list in self.scan_pks.items():
			for scan_pk in scanner_type_scan_list:
				scan_obj = Scan.objects.get(pk=scan_pk)
				self.assertContains(resp, scan_obj.scan_name)

	def test_scanner_list_ajax(self):
		resp = self.client.get(reverse('dd_downloader:scanner list ajax'))
		self.assertEquals(resp.status_code, 200)
		for scanner_type, scanner_type_scanner_list in self.scanner_pks.items():
			for scanner_pk in scanner_type_scanner_list:
				scanner_obj = Scanner.objects.get(pk=scanner_pk)
				self.assertContains(resp, scanner_obj.scanner_name)
	
	def test_child_scan_list(self):
		#go through every scanner_type
		for scanner_type, scanner_type_scanner_list in self.scanner_pks.items():
			#go through all the scanners of that scanner type
			for scanner_pk in scanner_type_scanner_list:
				#check the child scan ajax endpoint for that scanner_pk and ensure that all the child scans inside that scanner are contained in the response
				resp = self.client.get(reverse('dd_downloader:child scan list ajax', args=[scanner_pk]))
				self.assertEquals(resp.status_code, 200)
				child_scan_objs = Scanner.objects.get(pk=scanner_pk).scan_set.all()
				for child_scan_obj in child_scan_objs:
					self.assertContains(resp, child_scan_obj.scan_name)
