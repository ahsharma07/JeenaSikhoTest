# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe.model.document import Document
from frappe.utils import flt,cint, cstr, getdate
from erpnext.accounts.utils import get_fiscal_year
#from erpnext.controllers.buying_controller import BuyingController
#from erpnext.controllers.stock_controller import make_sl_entries
from erpnext.stock.doctype.quality_inspection_template.quality_inspection_template \
	import get_template_details
from frappe.model.mapper import get_mapped_doc

class QualityInspection(Document):
	def validate(self):
		if not self.readings and self.item_code:
			self.get_item_specification_details()

	def get_item_specification_details(self):
		if not self.quality_inspection_template:
			self.quality_inspection_template = frappe.db.get_value('Item',
				self.item_code, 'quality_inspection_template')

		if not self.quality_inspection_template: return

		self.set('readings', [])
		parameters = get_template_details(self.quality_inspection_template)
		for d in parameters:
			child = self.append('readings', {})
			child.specification = d.specification
			child.value = d.value
			child.status = "Accepted"

	def get_quality_inspection_template(self):
		template = ''
		if self.bom_no:
			template = frappe.db.get_value('BOM', self.bom_no, 'quality_inspection_template')

		if not template:
			template = frappe.db.get_value('BOM', self.item_code, 'quality_inspection_template')

		self.quality_inspection_template = template
		self.get_item_specification_details()

	def on_submit(self):
#		self.update_qc_reference()
		if self.approved_qty > 0:
			if not self.accepted_warehouse:
				frappe.throw("Accepted Warehouse is mandatory")
			name = self.create_stock_entry(self.approved_qty,self.accepted_warehouse)
		if self.rej_qty > 0:
			if not self.rejected_warehouse:
				frappe.throw("Rejected Warehouse is mandatory")
			name = self.create_stock_entry(self.rej_qty,self.rejected_warehouse) 
#		self.stock_entry = name
		"""doc = frappe.get_doc(self.reference_type,self.reference_name)
		qc = 1
		for i in doc.items:
			if i.item_code == self.item_code and i.name == self.row_name:
				if self.rejected_qty:
					i.rejected_qty = i.rejected_qty + self.rejected_qty
					i.qty = i.received_qty - i.rejected_qty
#					doc.total_rejected_qty = doc.total_rejected_qty + self.rejected_qty
			if not i.quality_inspection and qc == 1:
				qc = 0
		if qc ==0:
			doc.save()
		else:
			doc.submit()"""

	def create_stock_entry(doc,qty,warehouse):
		sales=frappe.new_doc("Stock Entry")
		sales.company= company=frappe.db.get_value("Purchase Receipt",doc.reference_name,"company")
		sales.stock_entry_type = "Material Transfer"
		sales.qulaity_inspection = doc.name
		sales.transaction_date=datetime.date.today()
		row = frappe.db.sql("""select * from `tabPurchase Receipt Item` where name = %s and parent = %s""",(doc.row_name,doc.reference_name),as_dict = 1)
		item = row[0]
		item_dict={}
		item_dict['item_code']=doc.item_code
		item_dict['item_name']=doc.item_name
		item_dict['qty']=qty
		item_dict['rate']=item['rate']
		item_dict['batch_no']:item['batch_no']
		item_dict['price_list_rate']=item['price_list_rate']
		item_dict['amount']=item['amount']
		item_dict['s_warehouse']=item['warehouse']
		item_dict['t_warehouse']=warehouse
		sales.append("items",item_dict)
		sales.insert()
		sales.submit()
		return sales.name

	def on_cancel(self):
		self.update_qc_reference()

	def update_qc_reference(self):
		quality_inspection = self.name if self.docstatus == 1 else ""
		doctype = self.reference_type + ' Item'
		if self.reference_type == 'Stock Entry':
			doctype = 'Stock Entry Detail'

		if self.reference_type and self.reference_name:
			frappe.db.sql("""update `tab{child_doc}` t1, `tab{parent_doc}` t2
				set t1.quality_inspection = %s, t2.modified = %s
				where t1.parent = %s and t1.item_code = %s and t1.parent = t2.name"""
				.format(parent_doc=self.reference_type, child_doc=doctype),
				(quality_inspection, self.modified, self.reference_name, self.item_code))

	def get_sl_entries(self, d, args):
		company=frappe.db.get_value("Purchase Receipt",self.reference_name,"company")
		sl_dict = frappe._dict({
			"item_code": d.get("item_code", None),
			"warehouse": d.get("warehouse", None),
			"posting_date": self.report_date,
			"posting_time": self.report_time,
			'fiscal_year': get_fiscal_year(self.report_date, company)[0],
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"voucher_detail_no": d.name,
			"actual_qty": (self.docstatus==1 and 1 or -1)*flt(d.get("stock_qty")),
			"stock_uom": frappe.db.get_value("Item", args.get("item_code") or d.get("item_code"), "stock_uom"),
			"incoming_rate": 0,
			"company": company,
			"batch_no": cstr(d.get("batch_no")).strip(),
			"serial_no": d.get("serial_no"),
			"project": d.get("project") or self.get('project'),
			"is_cancelled": 1 if self.docstatus==2 else 0
		})

		sl_dict.update(args)
		return sl_dict

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def item_query(doctype, txt, searchfield, start, page_len, filters):
	if filters.get("from"):
		from frappe.desk.reportview import get_match_cond
		mcond = get_match_cond(filters["from"])
		cond, qi_condition = "", "and (quality_inspection is null or quality_inspection = '')"

		if filters.get('from') in ['Purchase Invoice Item', 'Purchase Receipt Item']\
				and filters.get("inspection_type") != "In Process":
			cond = """and item_code in (select name from `tabItem` where
				inspection_required_before_purchase = 1)"""
		elif filters.get('from') in ['Sales Invoice Item', 'Delivery Note Item']\
				and filters.get("inspection_type") != "In Process":
			cond = """and item_code in (select name from `tabItem` where
				inspection_required_before_delivery = 1)"""
		elif filters.get('from') == 'Stock Entry Detail':
			cond = """and s_warehouse is null"""

		if filters.get('from') in ['Supplier Quotation Item']:
			qi_condition = ""

		return frappe.db.sql(""" select item_code from `tab{doc}`
			where parent=%(parent)s and docstatus < 2 and item_code like %(txt)s
			{qi_condition} {cond} {mcond}
			order by item_code limit {start}, {page_len}""".format(doc=filters.get('from'),
			parent=filters.get('parent'), cond = cond, mcond = mcond, start = start,
			page_len = page_len, qi_condition = qi_condition),
			{'parent': filters.get('parent'), 'txt': "%%%s%%" % txt})

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def quality_inspection_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.get_all('Quality Inspection',
		limit_start=start,
		limit_page_length=page_len,
		filters = {
			'docstatus': 1,
			'name': ('like', '%%%s%%' % txt),
			'item_code': filters.get("item_code"),
			'reference_name': ('in', [filters.get("reference_name", ''), ''])
		}, as_list=1)

@frappe.whitelist()
def make_quality_inspection(source_name, target_doc=None):
	def postprocess(source, doc):
		doc.inspected_by = frappe.session.user
		doc.get_quality_inspection_template()

	doc = get_mapped_doc("BOM", source_name, {
		'BOM': {
			"doctype": "Quality Inspection",
			"validation": {
				"docstatus": ["=", 1]
			},
			"field_map": {
				"name": "bom_no",
				"item": "item_code",
				"stock_uom": "uom",
				"stock_qty": "qty"
			},
		}
	}, target_doc, postprocess)

	return doc

@frappe.whitelist()
def get_batch(doc,item,batch):
	data= frappe.db.sql(""" select qty as qty,conversion_factor as conv, name as name from `tabPurchase Receipt Item`
                        where parent=%s and docstatus = 1 and item_code = %s and batch_no = %s""",
                        (doc,item,batch),as_dict = 1)
#	frappe.msgprint(str(data))
	return data

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def batch_query(doctype, txt, searchfield, start, page_len, filters):
	if filters.get("from"):
		from frappe.desk.reportview import get_match_cond
		mcond = get_match_cond(filters["from"])
#		cond, qi_condition = " ", "and (quality_inspection is null or quality_inspection = '')"
		return frappe.db.sql(""" select batch_no from `tab{doc}`
                        where parent=%(parent)s and docstatus = 1 and item_code = %(item_code)s
                        {mcond}
                        order by item_code limit {start}, {page_len}""".format(doc=filters.get('from'),
                        parent=filters.get('parent'), mcond = mcond, start = start,
                        page_len = page_len),
                        {'parent': filters.get('parent'), 'item_code': filters.get('item_code')})
