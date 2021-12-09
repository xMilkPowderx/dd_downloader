from django.test import TestCase, SimpleTestCase
from dd_downloader.models import Scanner, Scan
from dd_downloader.class_directory import get_scanner_types

class NessusTestCase(TestCase):
	def setUp(self):
		scanner_types = get_scanner_types()
		nessus_classes = scanner_types['Nessus']

		n1 = nessus_classes['scanner'](scanner_name='Ns_test_1',api_url='https://nessus_test.com:8834',access_key='access1',secret_key='secret1')
		n2 = nessus_classes['scanner'](scanner_name='Ns_test_2',api_url='https://nessus_test_2.com:8834',access_key='access2',secret_key='secret2',default_policy_id=123)
		n1.save()
		n2.save()
		self.n1_pk = n1.pk
		self.n2_pk = n2.pk

		ns1 = nessus_classes['scan'](scanner=n1,scan_name='NsScan1',endpoints='https://demo.testfire1.net')
		ns2 = nessus_classes['scan'](scanner=n1,scan_name='NsScan2',endpoints='https://demo.testfire2.net',override_policy_id=122)
		ns3 = nessus_classes['scan'](scanner=n2,scan_name='NsScan3',endpoints='https://demo.testfire3.net')
		ns1.save()
		ns2.save()
		ns3.save()
		self.ns1_pk = ns1.pk
		self.ns2_pk = ns2.pk
		self.ns3_pk = ns3.pk

	def test_scanner_create_view(self):
		#Ensure the Nessus form page appears.
		resp = self.client.get(f"/dd_downloader/scanner/create/",{'dd_downloader_scanner_type':'Nessus'})
		self.assertContains(resp, "Scanner Name")
		self.assertContains(resp, "API URL")
		self.assertContains(resp, "API Access Key")
		self.assertContains(resp, "API Secret Key")
		self.assertContains(resp, "Default policy ID for scans (optional)")
		self.assertContains(resp, "Notes (optional)")
		
		resp = self.client.post(f"/dd_downloader/scanner/create/",{
			'dd_downloader_scanner_type':'Nessus',
			'scanner_name':'create_test',
			'api_url':'https://creation_test.com:8834',
			'access_key':'access3',
			'secret_key':'secret3'
		})
		#Ensure that after creation, the scanner appears in the DB
		created_scanner = Scanner.objects.get(scanner_name='create_test')
		self.assertEqual(created_scanner.scanner_name, 'create_test')

	def test_scanner_detail_view(self):
		#Check each created scanner, and ensure that their respective detail pages contain all of their details.
		for n_pk in [self.n1_pk, self.n2_pk]:
			n = Scanner.objects.get(pk=n_pk)
			resp = self.client.get(f"/dd_downloader/scanner/{n_pk}/")
			self.assertContains(resp, n.scanner_name)
			self.assertContains(resp, n.api_url)
			self.assertContains(resp, n.access_key)
			self.assertContains(resp, n.secret_key)
			if n.default_policy_id is None:
				self.assertContains(resp, 'None')
			else:
				self.assertContains(resp, str(n.default_policy_id))

	def test_scanner_edit_view(self):
		#Try editing scanner #2 and check if attribute changed.
		resp = self.client.post(f"/dd_downloader/scanner/{self.n2_pk}/edit",{
			'scanner_name':'edit_test',
			'api_url':'https://edit_test.com:8834',
			'access_key':'edit_access',
			'secret_key':'edit_secret',
			'default_policy_id':456,
			'notes':'edit_note'
		})

		scanner_obj = Scanner.objects.get(pk=self.n2_pk)
		self.assertEquals(scanner_obj.scanner_name, 'edit_test')
		self.assertEquals(scanner_obj.api_url, 'https://edit_test.com:8834')
		self.assertEquals(scanner_obj.access_key, 'edit_access')
		self.assertEquals(scanner_obj.secret_key, 'edit_secret')
		self.assertEquals(scanner_obj.default_policy_id, 456)
		self.assertEquals(scanner_obj.notes, 'edit_note')

	def test_scan_create_view(self):
		#Ensure the Nessus scan creation form appears.
		scanner_obj = Scanner.objects.get(pk=self.n1_pk)
		resp = self.client.get(f"/dd_downloader/scanner/{self.n1_pk}/create")
		self.assertContains(resp, f"Add a scan for {scanner_obj.scanner_name}")
		
		resp = self.client.post(f"/dd_downloader/scanner/{self.n1_pk}/create",{
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
		self.assertEqual(created_scan.scanner.pk, self.n1_pk)

	def test_scan_detail_view(self):
		#Check each created scan, and ensure that their respective detail pages contain all of their details.
		for ns_pk in [self.ns1_pk, self.ns2_pk, self.ns3_pk]:
			ns = Scan.objects.get(pk=ns_pk)
			resp = self.client.get(f"/dd_downloader/scan/{ns_pk}/")
			self.assertIn(ns.scan_name, resp.content.decode())
			self.assertIn(ns.endpoints, resp.content.decode())
			if ns.override_policy_id is None:
				self.assertIn('None', resp.content.decode())
			else:
				self.assertIn(str(ns.override_policy_id), resp.content.decode())
	
	def test_scan_edit_view(self):
		#Try editing scan #2 and check if attribute changed.
		resp = self.client.post(f"/dd_downloader/scan/{self.ns2_pk}/edit",{
			'scan_name':'edit_test_scan',
			'endpoints':'https://edit.testfire.net',
			'auto_create':True,
			'auto_start':True,
			'auto_retrieve':True,
			'override_policy_id':233,
			'notes':'edit_note'
		})

		scan_obj = Scan.objects.get(pk=self.ns2_pk)
		self.assertEquals(scan_obj.scan_name, 'edit_test_scan')
		self.assertEquals(scan_obj.endpoints, 'https://edit.testfire.net')
		self.assertEquals(scan_obj.auto_create, True)
		self.assertEquals(scan_obj.auto_start, True)
		self.assertEquals(scan_obj.auto_retrieve, True)
		self.assertEquals(scan_obj.override_policy_id, 233)
		self.assertEquals(scan_obj.notes, 'edit_note')