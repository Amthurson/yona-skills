"""Lossless source-attribute planning. No API, writes to business data, or inference."""
from pathlib import Path
import argparse,json,re

PRODUCT_FIELDS={'name','category','supplierSku','brand','model','specification','attributes','oeNumbers','vehicleFitment','unit','aliases','historicalHandler'}
PRIVATE_LABEL=re.compile(r'联系方式|联系电话|手机号码|询盘客户|客户姓名|电子邮箱|supplier.?contact|customer|e-?mail|whatsapp|password|token|api.?key',re.I)

def length(value):return len(value.encode('utf-16-le'))//2

def prepare(document,capability='baseline'):
    if capability not in ('baseline','attributes-v1'):raise ValueError('unknown_server_capability')
    if document.get('schema')!=1 or not isinstance(document.get('products'),list)or not document['products']:raise ValueError('invalid_evidence_schema')
    plans=[];seen=set()
    for product in document['products']:
        key=product.get('record_key');source=product.get('source_locator')
        if not isinstance(key,str)or not key.strip()or key in seen:raise ValueError('missing_or_duplicate_record_key')
        seen.add(key)
        if not isinstance(source,str)or not source.strip():raise ValueError('source_required')
        fields=product.get('fields',{})
        if not isinstance(fields,dict)or set(fields)-PRODUCT_FIELDS or any(not isinstance(v,str)for v in fields.values()):raise ValueError('use_text_product_fields_only')
        fields={k:v.strip()for k,v in fields.items()if v.strip()}
        if not fields.get('name'):raise ValueError('product_name_required')
        inventory=product.get('attribute_inventory')
        count=product.get('source_attribute_count')
        if type(count)is not int or not isinstance(inventory,list)or count!=len(inventory):raise ValueError('attribute_inventory_incomplete')
        lines=[];unknown=[]
        for index,row in enumerate(inventory):
            if not isinstance(row,dict)or not isinstance(row.get('name'),str)or not row['name'].strip():raise ValueError('attribute_name_required')
            name=row['name'].strip()
            if PRIVATE_LABEL.search(name):raise ValueError('private_information_in_public_attributes')
            value=row.get('value');unit=row.get('unit','');locator=row.get('source_locator')
            if not isinstance(value,str)or not isinstance(unit,str)or not isinstance(locator,str)or not locator.strip():raise ValueError('attribute_text_and_source_required')
            if row.get('scope')not in ('sku','offer')or row.get('status')not in ('supplier_provided','pending_review'):raise ValueError('attribute_scope_and_status_required')
            if not value.strip():unknown.append({'row':index+1,'name':name,'source':locator});continue
            qualifiers=['商家声明']
            if row['scope']=='offer':qualifiers.append('商品链接共用，具体SKU适用性待核实')
            elif row['status']=='pending_review':qualifiers.append('待核实')
            lines.append(name+'：'+value.strip()+(' '+unit.strip()if unit.strip()else'')+'（'+'；'.join(qualifiers)+'）')
        # Never discard an existing independent attribute value on an old server.
        existing=fields.pop('attributes','')
        rendered='\n'.join(lines)
        if existing and existing!=rendered:rendered=existing+('\n'+rendered if rendered else'')
        field='attributes'if capability=='attributes-v1'else'specification'
        if rendered:
            if field=='specification':
                old=fields.get(field,'')
                fields[field]=old if rendered in old else (old+'\n'+rendered).strip()
            else:fields[field]=rendered
        for name,value in fields.items():
            limit=4000 if name=='attributes'else 2000 if name in ('specification','aliases','oeNumbers','vehicleFitment')else 255
            if length(value)>limit:raise ValueError('field_too_long_no_truncation:'+name)
        plans.append({'record_key':key,'source_locator':source,'capability':capability,'product_fields':fields,'attribute_coverage':{'source_rows':count,'rendered_rows':len(lines),'unknown_rows':unknown},'business_write_performed':False,'front_search_verified':False})
    return {'schema':1,'synthetic_example':document.get('synthetic_example')is True,'plans':plans}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('evidence',type=Path);parser.add_argument('--capability',choices=['baseline','attributes-v1'],default='baseline');parser.add_argument('--output',type=Path);a=parser.parse_args()
    result=prepare(json.loads(a.evidence.read_text(encoding='utf-8-sig')),a.capability)
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.output:a.output.write_text(text,encoding='utf8')
    else:print(text)

if __name__=='__main__':main()
