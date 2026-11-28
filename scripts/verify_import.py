"""Read the existing employee client; reconcile one product without any writes."""
from pathlib import Path
import argparse,importlib.util,json,os,re,sys,tomllib


def safe_error(error):
    match=re.search(r'\benterprise_(?:http|error)_\d+\b',str(error))
    return match.group(0) if match else type(error).__name__


def verify(client,product_id,supplier_id,sku,expected_code=None,max_pages=20):
    checks={};errors={}
    def read(name,args):
        try:return client.call(name,args)
        except Exception as error:errors[name]=safe_error(error);return None
    try:
        profile=client.api('GET','/system/auth/get-permission-info')
        identity={'userId':profile.get('user',{}).get('id'),'tenantId':client.tenant}
    except Exception as error:
        return {'verified':False,'classification':'employee_session_unavailable','error':safe_error(error),'writesPerformed':False}
    detail=read('enterprise_product_detail',{'product_id':product_id})
    snapshot=read('enterprise_product_edit_snapshot',{'product_id':product_id})
    links=read('enterprise_product_suppliers',{'product_id':product_id})
    def locate(name,args,predicate):
        for page in range(1,max_pages+1):
            result=read(name,args|{'page':page})
            if result is None:return {'found':False,'complete':False,'pages':page}
            rows=result.get('list',[])
            if any(predicate(row) for row in rows):return {'found':True,'complete':True,'pages':page}
            if not rows or page*result.get('pageSize',20)>=result.get('total',len(rows)):
                return {'found':False,'complete':True,'pages':page}
        return {'found':False,'complete':False,'pages':max_pages}
    reverse=locate('enterprise_supplier_products',{'supplier_id':supplier_id},lambda row:row.get('id')==product_id and row.get('supplier_sku')==sku)
    search=locate('enterprise_product_search',{'q':sku},lambda row:row.get('id')==product_id)
    record=snapshot or detail or {};fields=record.get('fields',{})
    matching=[row for row in links or [] if row.get('supplier_id')==supplier_id and row.get('supplier_sku')==sku]
    checks.update(productRead=detail is not None,editableSnapshot=snapshot is not None,
        productIdentity=record.get('id')==product_id and (expected_code is None or record.get('internal_code')==expected_code),
        productSku=fields.get('supplierSku')==sku,oneSkuLink=len(matching)==1,
        supplierReverse=reverse['found'],search=search['found'])
    if errors:classification='read_failed_or_permission_denied'
    elif all(checks.values()):classification='verified_for_current_employee'
    elif not checks['productIdentity']:classification='product_missing_or_identity_changed'
    elif not checks['oneSkuLink']:classification='supplier_sku_link_missing_or_ambiguous'
    elif not checks['productSku']:classification='product_sku_field_differs_from_link'
    elif not reverse['complete'] or not search['complete']:classification='pagination_incomplete'
    else:classification='record_exists_but_lookup_differs'
    return {'verified':all(checks.values()) and not errors,'classification':classification,
        'identity':identity,'productId':product_id,'internalCode':record.get('internal_code'),
        'supplierId':supplier_id,'sku':sku,'productSku':fields.get('supplierSku'),
        'linkIds':[row.get('id') for row in matching],'canShare':(detail or {}).get('canShare'),
        'checks':checks,'errors':errors,'supplierLookup':reverse,'searchLookup':search,
        'uiRoute':'/#/yona/product-library?productId='+str(product_id),
        'otherAccountAndBrowserVisibility':'not_verified','writesPerformed':False}


def load_client():
    codex=Path(os.environ.get('CODEX_HOME') or Path.home()/'.codex')
    entry=tomllib.loads((codex/'config.toml').read_text(encoding='utf8'))['mcp_servers']['yona_enterprise']
    args=entry['args'];programs=[Path(a) for a in args if str(a).replace('\\','/').endswith('/enterprise.py')]
    if len(programs)!=1 or args.count('--config')!=1:raise ValueError('existing_enterprise_client_not_found')
    program=programs[0].resolve(strict=True)
    config=json.loads(Path(args[args.index('--config')+1]).read_text(encoding='utf-8-sig'))
    sys.path.insert(0,str(program.parent))
    spec=importlib.util.spec_from_file_location('yona_existing_import_verifier',program)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.Enterprise(config)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--product-id',type=int,required=True);parser.add_argument('--supplier-id',type=int,required=True)
    parser.add_argument('--sku',required=True);parser.add_argument('--expected-code');parser.add_argument('--max-pages',type=int,default=20)
    args=parser.parse_args()
    if min(args.product_id,args.supplier_id)<1 or not 1<=args.max_pages<=100 or not 1<=len(args.sku)<=128:parser.error('invalid product, supplier, SKU or page bound')
    result=verify(load_client(),args.product_id,args.supplier_id,args.sku,args.expected_code,args.max_pages)
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['verified'] else 2


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'verified':False,'error':safe_error(error),'writesPerformed':False}));raise SystemExit(2)
