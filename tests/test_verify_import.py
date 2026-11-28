from pathlib import Path
import importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('verify_import',ROOT/'scripts/verify_import.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Client:
    tenant=7
    def __init__(self):self.calls=[];self.denied=False;self.links=[{'id':8,'supplier_id':9,'supplier_sku':'000123'}]
    def api(self,method,path):
        assert method=='GET';return {'user':{'id':5}}
    def call(self,name,args):
        self.calls.append((name,args))
        if self.denied and name.startswith('enterprise_product_'):raise ValueError('enterprise_http_403 PRIVATE-TOKEN')
        if name in ('enterprise_product_detail','enterprise_product_edit_snapshot'):return {'id':4,'internal_code':'PL-SYNTHETIC','fields':{'supplierSku':'000123'},'canShare':True}
        if name=='enterprise_product_suppliers':return self.links
        if name=='enterprise_supplier_products':return {'list':[{'id':99}]*20 if args['page']==1 else [{'id':4,'supplier_sku':'000123'}],'total':21,'pageSize':20}
        if name=='enterprise_product_search':return {'list':[{'id':4}],'total':1}
        raise AssertionError('write or unknown operation: '+name)

class VerificationTests(unittest.TestCase):
    def test_all_reads_and_second_page_are_required_before_employee_verified(self):
        client=Client();r=m.verify(client,4,9,'000123','PL-SYNTHETIC')
        self.assertTrue(r['verified']);self.assertEqual(2,r['supplierLookup']['pages']);self.assertEqual([8],r['linkIds']);self.assertFalse(r['writesPerformed']);self.assertEqual('not_verified',r['otherAccountAndBrowserVisibility'])
    def test_missing_link_is_not_hidden_by_search_success(self):
        client=Client();client.links=[];r=m.verify(client,4,9,'000123')
        self.assertFalse(r['verified']);self.assertEqual('supplier_sku_link_missing_or_ambiguous',r['classification'])
    def test_permission_error_is_redacted_and_does_not_trigger_writes(self):
        client=Client();client.denied=True;r=m.verify(client,4,9,'000123')
        self.assertFalse(r['verified']);self.assertEqual('read_failed_or_permission_denied',r['classification']);self.assertNotIn('PRIVATE',str(r))
    def test_identity_mismatch_and_page_limit_cannot_pass(self):
        r=m.verify(Client(),4,9,'000123','PL-DIFFERENT');self.assertFalse(r['verified'])
        r=m.verify(Client(),4,9,'000123',max_pages=1);self.assertFalse(r['verified']);self.assertEqual('pagination_incomplete',r['classification'])

if __name__=='__main__':unittest.main()
