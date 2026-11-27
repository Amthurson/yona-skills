from pathlib import Path
import copy,importlib.util,json,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prepare',ROOT/'scripts/prepare_product.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ProductPlanTest(unittest.TestCase):
    def setUp(self):self.data=json.loads((ROOT/'assets/product-evidence-template.json').read_text(encoding='utf8'))
    def test_old_server_preserves_every_attribute_and_identifier(self):
        plan=m.prepare(self.data)['plans'][0];fields=plan['product_fields']
        self.assertEqual('000123',fields['oeNumbers']);self.assertEqual('DEMO-TYRE-0001',fields['supplierSku'])
        for value in ('90/90-12','合成示例橡胶','半热熔','2600 g','具体SKU适用性待核实'):self.assertIn(value,fields['specification'])
        self.assertNotIn('attributes',fields);self.assertEqual(3,plan['attribute_coverage']['rendered_rows']);self.assertFalse(plan['business_write_performed'])
    def test_independent_attribute_mode_keeps_original_specification(self):
        fields=m.prepare(self.data,'attributes-v1')['plans'][0]['product_fields']
        self.assertEqual('SYNTHETIC 90/90-12',fields['specification']);self.assertIn('半热熔',fields['attributes'])
    def test_missing_source_rows_are_rejected(self):
        self.data['products'][0]['attribute_inventory'].pop()
        with self.assertRaisesRegex(ValueError,'inventory_incomplete'):m.prepare(self.data)
    def test_oversize_is_not_truncated_and_private_labels_are_rejected(self):
        product=self.data['products'][0];product['attribute_inventory'][0]['value']='长'*2000
        with self.assertRaisesRegex(ValueError,'no_truncation'):m.prepare(self.data)
        product['attribute_inventory'][0].update(name='供方联系电话',value='SYNTHETIC')
        with self.assertRaisesRegex(ValueError,'private_information'):m.prepare(self.data)
    def test_unknown_is_reported_and_numeric_codes_require_text(self):
        self.data['products'][0]['attribute_inventory'][0]['value']=''
        plan=m.prepare(self.data)['plans'][0];self.assertEqual(1,len(plan['attribute_coverage']['unknown_rows']))
        self.data['products'][0]['fields']['oeNumbers']=123
        with self.assertRaisesRegex(ValueError,'text_product_fields'):m.prepare(self.data)

if __name__=='__main__':unittest.main()
