import frappe
import requests
from frappe import _
import json

@frappe.whitelist()
def call(doc):
	doc=json.loads(doc)
	url=f"https://45.248.160.107:8475/CrmDial?exeUserName=test@jeenasikho&phoneNumber={doc['phone']}&skill=TESTSKL&listId=1"
	response = requests.request("GET", url,verify=False)
	data=json.loads(response.text.encode('utf8'))
	if data.get("response")=="Success":
		frappe.publish_realtime('lead_updates',message="Dialing",user="neha@extensioncrm.com")
	elif data.get("message").__contains__("not logged in."):
		frappe.publish_realtime('lead_updates',message="Agent Not logged in",user="neha@extensioncrm.com")

@frappe.whitelist()
def end_call(doc):
	doc=json.loads(doc)
	disposition="HANGUP"
	if disposition=="HANGUP":
		url=f"https://45.248.160.107:8475/CrmHangup?exeUserName=test@jeenasikho&disposition={disposition}:HU"
	else:
		url=f"https://45.248.160.107:8475/CrmHangup?exeUserName=test@jeenasikho&disposition={disposition}:CB  "
	response=requests.request("GET",url,verify=False)
	data=json.loads(response.text.encode('utf-8'))
	if data:
		if data.get("response")=="Success":
			frappe.publish_realtime('lead_updates',message="Call Ended",user="neha@extensioncrm.com")
		elif data.get("message").__contains__("not logged in."):
			frappe.publish_realtime('lead_updates',message="Agent Not Logged In",user="neha@extensioncrm.com")
	else:
		frappe.throw("Dialer is not working Properly")

@frappe.whitelist(allow_guest=True)
def incoming_call_handle(**kwargs):
	if kwargs:
		call_payload = kwargs
		if call_payload.get('callmode')=="IB":
			create_popup(call_payload.get('phone'))
			#lead_fields={"mobile_no":call_payload.get('phone'),'lead_name':call_payload.get('phone')}
			#popup_content = frappe.render_template("erpnext/templates/lead_info.html", lead_fields)
			#frappe.publish_realtime(event='msgprint',message=popup_content,user="Administrator")

		call_log = get_call_log(call_payload)
		if not call_log:
			call_log=create_call_log(call_payload)
		else:
			call_log=update_call_log(call_payload, call_log=call_log)
		if call_log:
			kwargs['success']=True
		return kwargs
	else:
		frappe.db.rollback()
		frappe.log_error(title=_('Error in Handling incoming call'))
		frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def handle_end_call(**kwargs):
	call_log=update_call_log(kwargs, 'Completed')
	if call_log:
		kwargs['success']=True
	return kwargs
@frappe.whitelist()
def get_call_log(call_payload):
	call_log = frappe.get_all('Call Log', {
		'id': call_payload.get('id'),
	}, limit=1)

	if call_log:
		return frappe.get_doc('Call Log', call_log[0].name)
from datetime import datetime
@frappe.whitelist()
def create_call_log(call_payload):
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
def create_outgoing_popup(data):
	pass
@frappe.whitelist()
def create_popup(mobile_no):
	lead_fields={}
	lead=frappe.db.sql('''select * from `tabLead` where phone=%(mobile)s''',{"mobile":mobile_no},as_dict=1)
	if lead:
		lead=lead[0]
		is_new_lead=0
		lead_fields['lead_status']=lead.status
	else:
		lead=frappe.new_doc("Lead")
		lead.phone=mobile_no
		lead.source="IVR"
		lead.insert(ignore_permissions=True,ignore_mandatory=True)
		frappe.log_error(lead.name,"lead")
		frappe.db.commit()
		is_new_lead=1
	lead_fields={'mobile_no':'9xxxxxxxxx','is_new_lead':is_new_lead,
			'call_timestamp':frappe.utils.datetime.datetime.strftime(frappe.utils.datetime.datetime.today(), '%d/%m/%Y %H:%M:%S'),
			'lead_name':lead.name}
	frappe.log_error(lead_fields,"lead")
	popup_content = frappe.render_template("erpnext/templates/lead_info.html", lead_fields)
	frappe.publish_realtime(event='msgprint',message=popup_content,user="anil@avissupport.com")





