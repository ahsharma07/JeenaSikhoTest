# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.utils import cstr, cint, get_fullname,getdate
from frappe import msgprint, _
from frappe.desk.form import assign_to
from frappe.model.mapper import get_mapped_doc
from erpnext.setup.utils import get_exchange_rate
from erpnext.utilities.transaction_base import TransactionBase
from erpnext.accounts.party import get_party_account_currency
from frappe.email.inbox import link_communication_to_document
from frappe.core.doctype.sms_settings.sms_settings import send_sms

subject_field = "title"
sender_field = "contact_email"

class Opportunity(TransactionBase):
	def after_insert(self):
		if self.opportunity_from == "Lead":
			frappe.get_doc("Lead", self.party_name).set_status(update=True)

	def validate(self):
		self._prev = frappe._dict({
			"contact_date": frappe.db.get_value("Opportunity", self.name, "contact_date") if \
				(not cint(self.get("__islocal"))) else None,
			"contact_by": frappe.db.get_value("Opportunity", self.name, "contact_by") if \
				(not cint(self.get("__islocal"))) else None,
		})

		self.make_new_lead_if_required()

		self.validate_item_details()
		self.validate_uom_is_integer("uom", "qty")
		self.validate_cust_name()

		if not self.title:
			self.title = self.customer_name

		if not self.with_items:
			self.items = []

		#if self.contact_by:
			#assign_to.add({
        	         #       "assign_to": self.contact_by,
                	  #      "doctype": self.doctype,
                        #	"name": self.name
			#	})

	def make_new_lead_if_required(self):
		"""Set lead against new opportunity"""
		if (not self.get("party_name")) and self.contact_email:
			# check if customer is already created agains the self.contact_email
			customer = frappe.db.sql("""select
				distinct `tabDynamic Link`.link_name as customer
				from
					`tabContact`,
					`tabDynamic Link`
				where `tabContact`.email_id='{0}'
				and
					`tabContact`.name=`tabDynamic Link`.parent
				and
					ifnull(`tabDynamic Link`.link_name, '')<>''
				and
					`tabDynamic Link`.link_doctype='Customer'
			""".format(self.contact_email), as_dict=True)
			if customer and customer[0].customer:
				self.party_name = customer[0].customer
				self.opportunity_from = "Customer"
				return

			lead_name = frappe.db.get_value("Lead", {"email_id": self.contact_email})
			if not lead_name:
				sender_name = get_fullname(self.contact_email)
				if sender_name == self.contact_email:
					sender_name = None

				if not sender_name and ('@' in self.contact_email):
					email_name = self.contact_email.split('@')[0]

					email_split = email_name.split('.')
					sender_name = ''
					for s in email_split:
						sender_name += s.capitalize() + ' '

				lead = frappe.get_doc({
					"doctype": "Lead",
					"email_id": self.contact_email,
					"lead_name": sender_name or 'Unknown'
				})

				lead.flags.ignore_email_validation = True
				lead.insert(ignore_permissions=True)
				lead_name = lead.name

			self.opportunity_from = "Lead"
			self.party_name = lead_name

	def declare_enquiry_lost(self, lost_reasons_list, detailed_reason=None):
		if not self.has_active_quotation():
			frappe.db.set(self, 'status', 'Lost')

			if detailed_reason:
				frappe.db.set(self, 'order_lost_reason', detailed_reason)

			for reason in lost_reasons_list:
				self.append('lost_reasons', reason)

			self.save()

		else:
			frappe.throw(_("Cannot declare as lost, because Quotation has been made."))

	def on_trash(self):
		self.delete_events()

	def has_active_quotation(self):
		if not self.with_items:
			return frappe.get_all('Quotation',
				{
					'opportunity': self.name,
					'status': ("not in", ['Lost', 'Closed']),
					'docstatus': 1
				}, 'name')
		else:
			return frappe.db.sql("""
				select q.name
				from `tabQuotation` q, `tabQuotation Item` qi
				where q.name = qi.parent and q.docstatus=1 and qi.prevdoc_docname =%s
				and q.status not in ('Lost', 'Closed')""", self.name)

	def has_ordered_quotation(self):
		return frappe.db.sql("""
			select q.name
			from `tabQuotation` q, `tabQuotation Item` qi
			where q.name = qi.parent and q.docstatus=1 and qi.prevdoc_docname =%s
			and q.status = 'Ordered'""", self.name)

	def has_lost_quotation(self):
		lost_quotation = frappe.db.sql("""
			select name
			from `tabQuotation`
			where  docstatus=1
				and opportunity =%s
				and status = 'Lost'
			""", self.name)
		if lost_quotation:
			if self.has_active_quotation():
				return False
			return True

	def validate_cust_name(self):
		if self.party_name and self.opportunity_from == 'Customer':
			self.customer_name = frappe.db.get_value("Customer", self.party_name, "customer_name")
		elif self.party_name and self.opportunity_from == 'Lead':
			lead_name, company_name = frappe.db.get_value("Lead", self.party_name, ["lead_name", "company_name"])
			self.customer_name = company_name or lead_name

	def on_update(self):
		self.add_calendar_event()
		if self.query_category=="Clinical Query":
			self.send_sms_for_appointment()

	def send_sms_for_appointment(self):
		receiver_list = []
		receiver_list.append(frappe.db.get_value("Lead",self.party_name,"phone"))
		if receiver_list:
			if self.schedule_date:
				address=self.clinic_address[12:]
				address=address.replace("</strong></h1>","")
				message=f"Your Appointment is booked {address} at {self.schedule_date}. For Navigation {self.clinic_map}  "
				self.create_appointment()
			else:
				 message=f"Clinic Address is  {address} . For Navigation {self.clinic_map}  "
			send_sms(receiver_list, cstr(message))
	def create_appointment(self):
		new_doc=frappe.new_doc("Appointment")
		new_doc.customer_name=self.party_name
		new_doc.customer_phone_number=frappe.db.get_value("Lead",self.party_name,"phone")
		new_doc.doctor = self.doctor_id
		new_doc.doctor_name = self.doctor_name
		new_doc.lead=self.party_name
		new_doc.status="Open"
                #new_doc.customer_details=self.diseases
		new_doc.scheduled_time=self.schedule_date
		new_doc.insert()
		assign_to.add({
                        "assign_to": self.doctor_id,
                        "doctype": "Appointment",
                        "name": new_doc.name
                        })
		frappe.db.set_value("Opportunity",self.name,"status", "Won")
		frappe.db.set_value("Lead",self.party_name,"status","Appointment Scheduled")

	def add_calendar_event(self, opts=None, force=False):
		if not opts:
			opts = frappe._dict()

		opts.description = ""
		opts.contact_date = self.contact_date

		if self.party_name and self.opportunity_from == 'Customer':
			if self.contact_person:
				opts.description = 'Contact '+cstr(self.contact_person)
			else:
				opts.description = 'Contact customer '+cstr(self.party_name)
		elif self.party_name and self.opportunity_from == 'Lead':
			if self.contact_display:
				opts.description = 'Contact '+cstr(self.contact_display)
			else:
				opts.description = 'Contact lead '+cstr(self.party_name)

		opts.subject = opts.description
		opts.description += '. By : ' + cstr(self.contact_by)

		if self.to_discuss:
			opts.description += ' To Discuss : ' + cstr(self.to_discuss)

		super(Opportunity, self).add_calendar_event(opts, force)

	def validate_item_details(self):
		if not self.get('items'):
			return

		# set missing values
		item_fields = ("item_name", "description", "item_group", "brand")

		for d in self.items:
			if not d.item_code:
				continue

			item = frappe.db.get_value("Item", d.item_code, item_fields, as_dict=True)
			for key in item_fields:
				if not d.get(key): d.set(key, item.get(key))


@frappe.whitelist()
def get_item_details(item_code):
	item = frappe.db.sql("""select item_name, stock_uom, image, description, item_group, brand
		from `tabItem` where name = %s""", item_code, as_dict=1)
	return {
		'item_name': item and item[0]['item_name'] or '',
		'uom': item and item[0]['stock_uom'] or '',
		'description': item and item[0]['description'] or '',
		'image': item and item[0]['image'] or '',
		'item_group': item and item[0]['item_group'] or '',
		'brand': item and item[0]['brand'] or ''
	}

@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	def set_missing_values(source, target):
		from erpnext.controllers.accounts_controller import get_default_taxes_and_charges
		quotation = frappe.get_doc(target)

		company_currency = frappe.get_cached_value('Company',  quotation.company,  "default_currency")

		if quotation.quotation_to == 'Customer' and quotation.party_name:
			party_account_currency = get_party_account_currency("Customer", quotation.party_name, quotation.company)
		else:
			party_account_currency = company_currency

		quotation.currency = party_account_currency or company_currency

		if company_currency == quotation.currency:
			exchange_rate = 1
		else:
			exchange_rate = get_exchange_rate(quotation.currency, company_currency,
				quotation.transaction_date, args="for_selling")

		quotation.conversion_rate = exchange_rate

		# get default taxes
		taxes = get_default_taxes_and_charges("Sales Taxes and Charges Template", company=quotation.company)
		if taxes.get('taxes'):
			quotation.update(taxes)

		quotation.run_method("set_missing_values")
		quotation.run_method("calculate_taxes_and_totals")
		if not source.with_items:
			quotation.opportunity = source.name

	doclist = get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Quotation",
			"field_map": {
				"opportunity_from": "quotation_to",
				"opportunity_type": "order_type",
				"name": "enq_no",
			}
		},
		"Opportunity Item": {
			"doctype": "Quotation Item",
			"field_map": {
				"parent": "prevdoc_docname",
				"parenttype": "prevdoc_doctype",
				"uom": "stock_uom"
			},
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)

	return doclist

@frappe.whitelist()
def make_request_for_quotation(source_name, target_doc=None):
	doclist = get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Request for Quotation"
		},
		"Opportunity Item": {
			"doctype": "Request for Quotation Item",
			"field_map": [
				["name", "opportunity_item"],
				["parent", "opportunity"],
				["uom", "uom"]
			]
		}
	}, target_doc)

	return doclist

@frappe.whitelist()
def make_supplier_quotation(source_name, target_doc=None):
	doclist = get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Supplier Quotation",
			"field_map": {
				"name": "opportunity"
			}
		},
		"Opportunity Item": {
			"doctype": "Supplier Quotation Item",
			"field_map": {
				"uom": "stock_uom"
			}
		}
	}, target_doc)

	return doclist

@frappe.whitelist()
def set_multiple_status(names, status):
	names = json.loads(names)
	for name in names:
		opp = frappe.get_doc("Opportunity", name)
		opp.status = status
		opp.save()

def auto_close_opportunity():
	""" auto close the `Replied` Opportunities after 7 days """
	auto_close_after_days = frappe.db.get_single_value("Selling Settings", "close_opportunity_after_days") or 15

	opportunities = frappe.db.sql(""" select name from tabOpportunity where status='Replied' and
		modified<DATE_SUB(CURDATE(), INTERVAL %s DAY) """, (auto_close_after_days), as_dict=True)

	for opportunity in opportunities:
		doc = frappe.get_doc("Opportunity", opportunity.get("name"))
		doc.status = "Closed"
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.save()

@frappe.whitelist()
def make_opportunity_from_communication(communication, company, ignore_communication_links=False):
	from erpnext.crm.doctype.lead.lead import make_lead_from_communication
	doc = frappe.get_doc("Communication", communication)

	lead = doc.reference_name if doc.reference_doctype == "Lead" else None
	if not lead:
		lead = make_lead_from_communication(communication, ignore_communication_links=True)

	opportunity_from = "Lead"

	opportunity = frappe.get_doc({
		"doctype": "Opportunity",
		"company": company,
		"opportunity_from": opportunity_from,
		"party_name": lead
	}).insert(ignore_permissions=True)

	link_communication_to_document(doc, "Opportunity", opportunity.name, ignore_communication_links)

	return opportunity.name

@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	doclist = get_mapped_doc("Opportunity", source_name, {
			"Opportunity": {
				"doctype": "Sales Order",
				"field_map":{
					"customer_name":"customer",
					"party_name":"lead"
					}
			},
			"Opportunity Item": {
				"doctype": "Sales Order Item",
				"field_map": {
					"parent": "prevdoc_docname"
				},
			},
			"Sales Taxes and Charges": {
				"doctype": "Sales Taxes and Charges",
				"add_if_empty": True
			},
			"Sales Team": {
				"doctype": "Sales Team",
				"add_if_empty": True
			},
			"Payment Schedule": {
				"doctype": "Payment Schedule",
				"add_if_empty": True
			}
		}, target_doc)

	return doclist
