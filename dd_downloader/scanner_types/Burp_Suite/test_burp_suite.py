from django.test import TestCase, SimpleTestCase
from dd_downloader.models import Scanner, Scan
from dd_downloader.class_directory import get_scanner_types

class BurpSuiteTestCase(TestCase):
	def setUp(self):
		scanner_types = get_scanner_types()
		burp_suite_classes = scanner_types['Burp_Suite']

		b1 = burp_suite_classes['scanner'](scanner_name='Bs_test_1',api_url='https://burp_suite_test.com:1337',api_key='key1')
		b2 = burp_suite_classes['scanner'](scanner_name='Bs_test_2',api_url='https://burp_suite_test_2.com:1337',api_key='key2')
		b1.save()
		b2.save()
		self.b1_pk = b1.pk
		self.b2_pk = b2.pk

		bs1 = burp_suite_classes['scan'](scanner=b1,scan_name='BsScan1',endpoints='https://demo.testfire1.net')
		bs2 = burp_suite_classes['scan'](scanner=b1,scan_name='BsScan2',endpoints='https://demo.testfire2.net')
		bs3 = burp_suite_classes['scan'](scanner=b2,scan_name='BsScan3',endpoints='https://demo.testfire3.net')
		bs1.save()
		bs2.save()
		bs3.save()
		self.bs1_pk = bs1.pk
		self.bs2_pk = bs2.pk
		self.bs3_pk = bs3.pk

	def test_scanner_create_view(self):
		#Ensure the Burp Suite form page appears.
		resp = self.client.get(f"/dd_downloader/scanner/create/",{'dd_downloader_scanner_type':'Burp_Suite'})
		self.assertContains(resp, "Scanner Name")
		self.assertContains(resp, "API URL")
		self.assertContains(resp, "API Key")
		self.assertContains(resp, "Notes (optional)")
		
		resp = self.client.post(f"/dd_downloader/scanner/create/",{
			'dd_downloader_scanner_type':'Burp_Suite',
			'scanner_name':'create_test',
			'api_url':'https://creation_test.com:1337',
			'api_key':'key3'
		})
		#Ensure that after creation, the scanner appears in the DB
		created_scanner = Scanner.objects.get(scanner_name='create_test')
		self.assertEqual(created_scanner.scanner_name, 'create_test')

	def test_scanner_detail_view(self):
		#Check each created scanner, and ensure that their respective detail pages contain all of their details.
		for b_pk in [self.b1_pk, self.b2_pk]:
			b = Scanner.objects.get(pk=b_pk)
			resp = self.client.get(f"/dd_downloader/scanner/{b_pk}/")
			self.assertContains(resp, b.scanner_name)
			self.assertContains(resp, b.api_url)
			self.assertContains(resp, b.api_key)

	def test_scanner_edit_view(self):
		#Try editing scanner #2 and check if attribute changed.
		resp = self.client.post(f"/dd_downloader/scanner/{self.b2_pk}/edit",{
			'scanner_name':'edit_test',
			'api_url':'https://edit_test.com:1337',
			'api_key':'edit_api_key',
			'notes':'edit_note'
		})

		scanner_obj = Scanner.objects.get(pk=self.b2_pk)
		self.assertEquals(scanner_obj.scanner_name, 'edit_test')
		self.assertEquals(scanner_obj.api_url, 'https://edit_test.com:1337')
		self.assertEquals(scanner_obj.api_key, 'edit_api_key')
		self.assertEquals(scanner_obj.notes, 'edit_note')
	

	def test_scan_create_view(self):
		#Ensure the Burp Suite scan creation form appears.
		scanner_obj = Scanner.objects.get(pk=self.b1_pk)
		resp = self.client.get(f"/dd_downloader/scanner/{self.b1_pk}/create")
		self.assertContains(resp, f"Add a scan for {scanner_obj.scanner_name}")
		
		resp = self.client.post(f"/dd_downloader/scanner/{self.b1_pk}/create",{
			'scan_name':'scan_create_test',
			'endpoints':'https://demo.testfire4.net',
			'auto_create':False,
			'auto_start':True,
			'auto_retrieve':True,
			'notes':'test note'
		})
		#Ensure that after creation, the scan appears in the DB
		created_scan = Scan.objects.get(scan_name='scan_create_test')
		self.assertEqual(created_scan.scan_name, 'scan_create_test')
		self.assertEqual(created_scan.scanner.pk, self.b1_pk)

	def test_scan_detail_view(self):
		#Check each created scan, and ensure that their respective detail pages contain all of their details.
		for bs_pk in [self.bs1_pk, self.bs2_pk, self.bs3_pk]:
			bs = Scan.objects.get(pk=bs_pk)
			resp = self.client.get(f"/dd_downloader/scan/{bs_pk}/")
			self.assertIn(bs.scan_name, resp.content.decode())
			self.assertIn(bs.endpoints, resp.content.decode())
	
	def test_scan_edit_view(self):
		#Try editing scan #2 and check if attribute changed.
		resp = self.client.post(f"/dd_downloader/scan/{self.bs2_pk}/edit",{
			'scan_name':'edit_test_scan',
			'endpoints':'https://edit.testfire.net',
			'auto_create':True,
			'auto_start':True,
			'auto_retrieve':True,
			'notes':'edit_note'
		})

		scan_obj = Scan.objects.get(pk=self.bs2_pk)
		self.assertEquals(scan_obj.scan_name, 'edit_test_scan')
		self.assertEquals(scan_obj.endpoints, 'https://edit.testfire.net')
		self.assertEquals(scan_obj.auto_create, True)
		self.assertEquals(scan_obj.auto_start, True)
		self.assertEquals(scan_obj.auto_retrieve, True)
		self.assertEquals(scan_obj.notes, 'edit_note')