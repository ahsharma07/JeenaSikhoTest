# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe
from frappe import realtime
import json
from frappe.core.doctype.sms_settings.sms_settings import send_sms
from frappe import _
from frappe.utils import (cstr, validate_email_address, cint, comma_and, has_gravatar, now, getdate, nowdate)
from frappe.model.mapper import get_mapped_doc
import requests
import datetime
from erpnext.controllers.selling_controller import SellingController
from frappe.contacts.address_and_contact import load_address_and_contact
from erpnext.accounts.party import set_taxes
from frappe.email.inbox import link_communication_to_document
from frappe.desk.form import assign_to

sender_field = "email_id"

class Lead(SellingController):
	def get_feed(self):
		return '{0}: {1}'.format(_(self.status), self.lead_name)

	def onload(self):
		customer = frappe.db.get_value("Customer", {"lead_name": self.name})
		self.get("__onload").is_customer = customer
		load_address_and_contact(self)

	def validate(self):
		self.set_lead_name()
		self._prev = frappe._dict({
			"contact_date": frappe.db.get_value("Lead", self.name, "contact_date") if \
				(not cint(self.get("__islocal"))) else None,
			"ends_on": frappe.db.get_value("Lead", self.name, "ends_on") if \
				(not cint(self.get("__islocal"))) else None,
			"contact_by": frappe.db.get_value("Lead", self.name, "contact_by") if \
				(not cint(self.get("__islocal"))) else None,
		})

#		self.set_status()
		self.check_email_id_is_unique()

		if self.email_id:
			if not self.flags.ignore_email_validation:
				validate_email_address(self.email_id, True)

			if self.email_id == self.lead_owner:
				frappe.throw(_("Lead Owner cannot be same as the Lead"))

			if self.email_id == self.contact_by:
				frappe.throw(_("Next Contact By cannot be same as the Lead Email Address"))

			if self.is_new() or not self.image:
				self.image = has_gravatar(self.email_id)

		if self.contact_date and getdate(self.contact_date) < getdate(nowdate()):
			frappe.throw(_("Next Contact Date cannot be in the past"))

		if (self.ends_on and self.contact_date and
			(getdate(self.ends_on) < getdate(self.contact_date))):
			frappe.throw(_("Ends On date cannot be before Next Contact Date."))
		if self.contact_by:
			assign_to.add({
                                "assign_to": self.contact_by,
                                "doctype": self.doctype,
                                "name": self.name
				})

	def on_update(self):
		self.add_calendar_event()
		customer = frappe.db.sql("""select name from `tabCustomer`
			where lead_name=%s """, (self.name),as_dict=1)
		if not customer and self.lead_name:
			customer = frappe.new_doc("Customer")
			customer.customer_name = self.lead_name
#                       customer.salutation = self.
			customer.customer_type = "Individual"
			customer.customer_group = "Individual"
			customer.lead_name = self.name
			customer.mobile_no = self.phone
			customer.email_id = self.email_id
			customer.save()

		if self.query_category=="Appointment For Clinic":
			self.create_appointment()
			self.send_sms_for_appointment()
			frappe.db.set_value("Lead",self.name,"query_category","")
	def send_sms_for_appointment(self):
		receiver_list = []
		receiver_list.append(self.phone)
		if receiver_list:
			message=f"Your Appointment is booked {self.clinic_address} at {getdate(self.schedule_date).strftime('%d-%m-%Y %H:%M:%S')}. For Navigation {self.clinic_map}  "
			send_sms(receiver_list, cstr(message))
			create_communication(self)

	def create_communication(self):
		communication = frappe.new_doc("Communication")
		communication.update({
			"communication_type": "Communication",
			"communication_medium": "Email",
			"sent_or_received": "Received",
			"email_status": "Open",
			"subject": self.subject,
			"sender": self.raised_by,
			"content": self.description,
			"status": "Linked",
			"reference_doctype": "Issue",
			"reference_name": self.name
		})
		communication.ignore_permissions = True
		communication.ignore_mandatory = True
		communication.save()
	def create_appointment(self):
		new_doc=frappe.new_doc("Appointment")
		new_doc.customer_name=self.lead_name
		new_doc.customer_phone_number=self.phone
		new_doc.doctor = self.doctor_id
		new_doc.doctor_name = self.doctor_name
		new_doc.lead=self.name
		new_doc.status="Open"
		#new_doc.customer_details=self.diseases
		new_doc.scheduled_time=self.schedule_date
		new_doc.insert()
		assign_to.add({
			"assign_to": self.doctor_id,
			"doctype": "Appointment",
			"name": new_doc.name
			})
		frappe.db.set_value("Lead",self.name,"status", "Appointment Scheduled")
	def add_calendar_event(self, opts=None, force=False):
		super(Lead, self).add_calendar_event({
			"owner": self.lead_owner,
			"starts_on": self.contact_date,
			"ends_on": self.ends_on or "",
			"subject": ('Contact ' + cstr(self.lead_name)),
			"description": ('Contact ' + cstr(self.lead_name)) + \
				(self.contact_by and ('. By : ' + cstr(self.contact_by)) or '')
		}, force)

	def check_email_id_is_unique(self):
		if self.email_id:
			# validate email is unique
			duplicate_leads = frappe.db.sql_list("""select name from tabLead
				where email_id=%s and name!=%s""", (self.email_id, self.name))

			if duplicate_leads:
				frappe.throw(_("Email Address must be unique, already exists for {0}")
					.format(comma_and(duplicate_leads)), frappe.DuplicateEntryError)

	def on_trash(self):
		frappe.db.sql("""update `tabIssue` set lead='' where lead=%s""",
			self.name)

		self.delete_events()

	def has_customer(self):
		return frappe.db.get_value("Customer", {"lead_name": self.name})

	def has_opportunity(self):
		return frappe.db.get_value("Opportunity", {"party_name": self.name, "status": ["!=", "Lost"]})

	def has_quotation(self):
		return frappe.db.get_value("Quotation", {
			"party_name": self.name,
			"docstatus": 1,
			"status": ["!=", "Lost"]

		})

	def has_lost_quotation(self):
		return frappe.db.get_value("Quotation", {
			"party_name": self.name,
			"docstatus": 1,
			"status": "Lost"
		})

	def set_lead_name(self):
		if not self.lead_name:
			# Check for leads being created through data import
			if not self.company_name and not self.flags.ignore_mandatory:
				frappe.throw(_("A Lead requires either a person's name or an organization's name"))

			self.lead_name = self.company_name

@frappe.whitelist()
def make_customer(source_name, target_doc=None):
	return _make_customer(source_name, target_doc)

def _make_customer(source_name, target_doc=None, ignore_permissions=False):
	def set_missing_values(source, target):
		if source.company_name:
			target.customer_type = "Company"
			target.customer_name = source.company_name
		else:
			target.customer_type = "Individual"
			target.customer_name = source.lead_name

		target.customer_group = frappe.db.get_default("Customer Group")

	doclist = get_mapped_doc("Lead", source_name,
		{"Lead": {
			"doctype": "Customer",
			"field_map": {
				"name": "lead_name",
				"company_name": "customer_name",
				"contact_no": "phone_1",
				"fax": "fax_1"
			}
		}}, target_doc, set_missing_values, ignore_permissions=ignore_permissions)

	return doclist

@frappe.whitelist()
def make_opportunity(source_name, target_doc=None):
	def set_missing_values(source, target):
		_set_missing_values(source, target)

	target_doc = get_mapped_doc("Lead", source_name,
		{"Lead": {
			"doctype": "Opportunity",
			"field_map": {
				"campaign_name": "campaign",
				"doctype": "opportunity_from",
				"name": "party_name",
				"lead_name": "contact_display",
				"company_name": "customer_name",
				"email_id": "contact_email",
				"mobile_no": "contact_mobile"
			}
		}}, target_doc, set_missing_values)

	return target_doc

@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	def set_missing_values(source, target):
		_set_missing_values(source, target)

	target_doc = get_mapped_doc("Lead", source_name,
		{"Lead": {
			"doctype": "Quotation",
			"field_map": {
				"name": "party_name"
			}
		}}, target_doc, set_missing_values)

	target_doc.quotation_to = "Lead"
	target_doc.run_method("set_missing_values")
	target_doc.run_method("set_other_charges")
	target_doc.run_method("calculate_taxes_and_totals")

	return target_doc

def _set_missing_values(source, target):
	address = frappe.get_all('Dynamic Link', {
			'link_doctype': source.doctype,
			'link_name': source.name,
			'parenttype': 'Address',
		}, ['parent'], limit=1)

	contact = frappe.get_all('Dynamic Link', {
			'link_doctype': source.doctype,
			'link_name': source.name,
			'parenttype': 'Contact',
		}, ['parent'], limit=1)

	if address:
		target.customer_address = address[0].parent

	if contact:
		target.contact_person = contact[0].parent

@frappe.whitelist()
def get_lead_details(lead, posting_date=None, company=None):
	if not lead: return {}

	from erpnext.accounts.party import set_address_details
	out = frappe._dict()

	lead_doc = frappe.get_doc("Lead", lead)
	lead = lead_doc

	out.update({
		"territory": lead.territory,
		"customer_name": lead.company_name or lead.lead_name,
		"contact_display": " ".join(filter(None, [lead.salutation, lead.lead_name])),
		"contact_email": lead.email_id,
		"contact_mobile": lead.mobile_no,
		"contact_phone": lead.phone,
	})

	set_address_details(out, lead, "Lead")

	taxes_and_charges = set_taxes(None, 'Lead', posting_date, company,
		billing_address=out.get('customer_address'), shipping_address=out.get('shipping_address_name'))
	if taxes_and_charges:
		out['taxes_and_charges'] = taxes_and_charges

	return out

@frappe.whitelist()
def make_lead_from_communication(communication, ignore_communication_links=False):
	""" raise a issue from email """

	doc = frappe.get_doc("Communication", communication)
	lead_name = None
	if doc.sender:
		lead_name = frappe.db.get_value("Lead", {"email_id": doc.sender})
	if not lead_name and doc.phone_no:
		lead_name = frappe.db.get_value("Lead", {"mobile_no": doc.phone_no})
	if not lead_name:
		lead = frappe.get_doc({
			"doctype": "Lead",
			"lead_name": doc.sender_full_name,
			"email_id": doc.sender,
			"mobile_no": doc.phone_no
		})
		lead.flags.ignore_mandatory = True
		lead.flags.ignore_permissions = True
		lead.insert()

		lead_name = lead.name

	link_communication_to_document(doc, "Lead", lead_name, ignore_communication_links)
	return lead_name

def get_lead_with_phone_number(number):
	if not number: return

	leads = frappe.get_all('Lead', or_filters={
		'phone': ['like', '%{}'.format(number)],
		'mobile_no': ['like', '%{}'.format(number)]
	}, limit=1)

	lead = leads[0].name if leads else None

	return lead

@frappe.whitelist()
def call(phone,agent_id):
	url=f"https://45.248.160.107:8475/CrmDial?exeUserName={agent_id}@jeenasikho&phoneNumber={phone}&skill=TESTSKL&listId=1"
	response = requests.request("GET", url,verify=False)
	data=json.loads(response.text.encode('utf8'))
	if data.get("response")=="Success":
		return "Outgoing"
	elif data.get("message").__contains__("not logged in."):
		return "Agent not logged in"

@frappe.whitelist()
def end_call(agent_id,disposition,time=None):
	if disposition=="HANGUP":
		url=f"https://45.248.160.107:8475/CrmHangup?exeUserName={agent_id}@jeenasikho&disposition={disposition}:HU"
	else:
		url=f"https://45.248.160.107:8475/CrmHangup?exeUserName={agent_id}@jeenasikho&disposition={disposition}:CB &callbackDate={time} "
	response=requests.request("GET",url,verify=False)
	data=json.loads(response.text.encode('utf-8'))
	frappe.publish_realtime('realtime_updates',message="Yes",room='my_room',user=frappe.session.user)
	if data:
		if data.get("response")=="Success":
			return "Call Ended"
		elif data.get("message").__contains__("not logged in."):
			return "Agent not logged in"
	else:
		frappe.throw("Dialer is not working Properly")


@frappe.whitelist(allow_guest=True)
def incoming_call_handle(**kwargs):
	lead_fields={"mobile_no":"8360608030",'lead_name':"8360608030"}
	popup_content = frappe.render_template("erpnext/templates/lead_info.html", lead_fields)
	frappe.publish_realtime(event='msgprint',message=popup_content,user="Administrator")

	try:
		frappe.log_error(kwargs,"IVR")
		call_payload = kwargs
		#lead_fields={"mobile_no":call_payload.get('phone'),'lead_name':call_payload.get('phone')}
		#popup_content = frappe.render_template("erpnext/templates/lead_info.html", lead_fields)
		#frappe.publish_realtime(event='msgprint',message=popup_content,user="Administrator")
		call_log = get_call_log(call_payload)
		if not call_log:
			create_call_log(call_payload)
		else:
			update_call_log(call_payload, call_log=call_log)
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(title=_('Error in Handling incoming call'))

		frappe.db.commit()
@frappe.whitelist(allow_guest=True)
def handle_end_call(**kwargs):
	frappe.log_error(kwargs,"End IVR")
	update_call_log(kwargs, 'Completed')
@frappe.whitelist()
def get_call_log(call_payload):
	call_log = frappe.get_all('Call Log', {
		'id': call_payload.get('id'),
	}, limit=1)

	if call_log:
		return frappe.get_doc('Call Log', call_log[0].name)
@frappe.whitelist()
def create_call_log(call_payload):
	#frappe.throw('show_call_popup')
	call_log = frappe.new_doc('Call Log')
	call_log.id = call_payload.get('id')
	call_log.to = call_payload.get('DialWhomNumber')
	if call_payload.get('callmode')=="IB":
		call_log.medium = "Incoming"
	elif call_payload.get('callmode')=="MB":
		call_log.medium="Missed Call"
	else:
		call_log.medium="Outgoing"
	call_log.status = 'Ringing'
	setattr(call_log, 'from', call_payload.get('phone'))
	call_log.save(ignore_permissions=True)
	frappe.db.commit()
	create_popup()
	return call_log
@frappe.whitelist()
def update_call_log(call_payload, status='Ringing', call_log=None):
	call_log = call_log or get_call_log(call_payload)
	if call_log:
		call_log.status = status
		call_log.to = call_payload.get('DialWhomNumber')
		#call_log.duration = call_payload.get('DialCallDuration') or 0
		call_log.recording_url = call_payload.get('RecordingUrl')
		call_log.save(ignore_permissions=True)
		frappe.db.commit()
		return call_log
@frappe.whitelist()
def create_popup():
	lead_fields={"mobile":"8360608030"}
	frappe.msgprint("hello")
	popup_content = frappe.render_template("erpnext/templates/lead_info.html", lead_fields)
	frappe.publish_realtime(event="msgprint",message=popup_content, user="neha@extensioncrm.com")

