# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe import utils
import datetime
from frappe.utils import add_days
from frappe.desk.form import assign_to
#from frappe.utils import (cstr, validate_email_address, cint, comma_and, has_gravatar, now, getdate, nowdate)
#from frappe.model.mapper import get_mapped_doc
import requests
#from erpnext.controllers.selling_controller import SellingController
#from frappe.contacts.address_and_contact import load_address_and_contact
#from erpnext.accounts.party import set_taxes
#from frappe.email.inbox import link_communication_to_document

#sender_field = "email_id"
import json
class NewEnquiry(Document):
    pass

@frappe.whitelist()
def get_general_enquiry(mobile):
	if mobile:
		queries=frappe.db.sql('''select * from `tabEnquiry` where mobile_no=%(mob)s''',{"mob":mobile},as_dict=1)
		return queries

@frappe.whitelist(allow_guest=True)
def existing_lead(**kwargs):
	data=kwargs
	doc=json.loads(data['doc'])
	if doc['mobile_number']:
		lead = frappe.db.sql("""select * from `tabLead`
                                where name=%s """, (doc['mobile_number']),as_dict=1)
		#frappe.msgprint(str(lead))
		if not lead and doc['name'] is not None:
			form=frappe.new_doc("Lead")
			form.phone=doc['mobile_number']
			form.lead_name=doc['name1']
			form.mobile_number=doc['mobile_number']
			form.gender=doc['gender']
			form.blood_group=doc['blood_group']
			form.age=doc['age']
			form.diseases=doc['diseases']
			form.save()
			create_address(doc)
		else:
			if lead:
				pass
				#form=frappe.get_doc("Lead",doc.mobile_number)
				#child=form.append('realtions',{})
				#child.name1=doc.name
				#child.diseases=doc.diseases
				#child.insert()
		create_enquiry(doc)
		frappe.db.sql("""update `tabSingles` set value="" where doctype='New Enquiry' """)
		#frappe.msgprint("Update")
@frappe.whitelist()
def create_enquiry(doc):
	if doc:
		new_enquiry=frappe.new_doc("Enquiry")
		new_enquiry.mobile_no=doc['mobile_number']
		new_enquiry.query_category=doc['query_category']
		new_enquiry.query_type=doc['query_type']
		new_enquiry.query_description=doc['remarks']
		if doc['query_category']=="Product Purchase":
			create_sales_order(doc)
		elif doc['query_category']=="Appointment for Clinic":
			new_enquiry.schedule_date=doc['scheduled_date_time']
			create_appointment(doc)
		new_enquiry.submit()

@frappe.whitelist()
def create_address(doc):
	add_form=frappe.new_doc("Address")
	add_form.address_title = doc['name1']
	add_form.address_line1=doc['address']
	add_form.city=doc['city1']
	add_form.address_line2=doc['landmark']
	add_form.insert()
	customer = frappe.new_doc("Customer")
	customer.customer_name = doc['name1'] 
	customer.salutation = doc['salutation']
	customer.customer_type = "Individual"
	customer.customer_group = "Individual"
	customer.lead_name = doc['mobile_number']
	customer.save()
	child = add_form.append('links', {})
	child.link_doctype= "Lead"
	child.link_name=doc['mobile_number']
	child.link_title=doc['mobile_number']
	child.parent = add_form.name
	child.insert()
	cust_child = add_form.append('links', {})
	cust_child.link_doctype= "Customer"
	cust_child.link_name=customer.name
	cust_child.link_title=customer.name
	cust_child.parent = add_form.name
	cust_child.insert()
	frappe.msgprint("Successfully Added")
@frappe.whitelist()
def page_refresh():
	frappe.db.sql('''update `tabSingles` set value="" where doctype='New Enquiry' ''')
@frappe.whitelist()
def create_sales_order(doc):
	sales=frappe.new_doc("Sales Order")
	sales.customer=doc['name1']
	sales.order_type="Sales"
	sales.company="JEENA SIKHO LIFECARE PVT LTD"
	sales.transaction_date=datetime.date.today()
	sales.delivery_date=add_days(datetime.date.today(),3)
	for item in doc['items']:
		item_dict={}
		item_dict['item_code']=item['item_code']
		item_dict['item_name']=item['item_name']
		item_dict['qty']=item['qty']
		item_dict['rate']=item['total_amount']
		item_dict['price_list_rate']=item['price_list_rate']
		item_dict['amount']=item['amount']
		item_dict['warehouse']="JEENA SIKHO - JSLCP"
		sales.append("items",item_dict)
	sales.insert()
@frappe.whitelist()
def create_appointment(doc):
	new_doc=frappe.new_doc("Appointment")
	new_doc.customer_name=doc['name1']
	new_doc.customer_phone_number=doc['mobile_number']
	new_doc.doctor = doc['doctor_id']
	new_doc.doctor_name = doc['doctor_name']
	new_doc.lead=doc['mobile_number']
	new_doc.status="Open"
	new_doc.customer_details=doc['diseases']
	new_doc.scheduled_time=doc['scheduled_date_time']
	new_doc.insert()
	assign_to.add({
		"assign_to": doc['doctor_id'],
		"doctype": "Appointment",
		"name": new_doc.name
	})
@frappe.whitelist()
def exist_lead(mobile):
	if mobile:
		lead=frappe.db.sql("""select * from `tabLead` where name=%s""",(mobile),as_dict=1)
		if lead:
			return lead

@frappe.whitelist()
def search(state):
	if state:
		data=frappe.db.sql_list("""select distinct district_name from `tabPincode Master` where state_name=%s """,(state))
		return data
@frappe.whitelist()
def search_tehsil(district):
	if district:
		tehsils=frappe.db.sql_list("""select distinct related_headoffice from `tabPincode Master` where  related_headoffice=%s""",(district))
		return tehsils
@frappe.whitelist()
def search_city(tehsil):
	if tehsil:
		cities=frappe.db.sql_list("""select distinct related_suboffice from `tabPincode Master` where related_headoffice=%s""",(tehsil))
		return cities
@frappe.whitelist()
def search_pincode(city):
	if city:
		pincode=frappe.db.sql_list("""select pincode from `tabPincode Master` where related_suboffice=%s""",(city))
		return pincode[0]

@frappe.whitelist()
def clinic_state(country):
        if country:
                data=frappe.db.sql_list("""select state from `tabClinics` where country=%s """,(country))
                return data

@frappe.whitelist()
def clinic_district(state):
        if state:
                data=frappe.db.sql_list("""select district from `tabClinics` where state=%s """,(state))
                return data

@frappe.whitelist()
def clinic_address(state,district,country):
	if state:
		data=frappe.db.sql("""select name,clinic_name,address,map,doctor,doctor_name from `tabClinics` where state=%s and district = %s and country = %s""",(state,district,country),as_dict = 1)
		return data


@frappe.whitelist()
def fetch_pincode():
	import requests
	url = "https://clbeta.ecomexpress.in/apiv2/pincodes/"

	payload={'username': 'jeenasikholifecare46901_temp',
	'password': 'W4sEMCUYwcFnyAKv'}

	files=[

	]
	headers = {
	'Cookie': 'AWSALB=mUnn16QC3hEtwGrbdwPJFM5A2TrX0c3QZJBzWQLLXwc7L9TK+NhxnI+EkhN6h/z9BG+Rkkv2KHdGvCsfVv7o1V2dn6Rh/ez+6NQN6UpcsMz6mwhjJhezNjYxsH00; AWSALBCORS=mUnn16QC3hEtwGrbdwPJFM5A2TrX0c3QZJBzWQLLXwc7L9TK+NhxnI+EkhN6h/z9BG+Rkkv2KHdGvCsfVv7o1V2dn6Rh/ez+6NQN6UpcsMz6mwhjJhezNjYxsH00'
	}
	response = requests.request("POST", url, headers=headers, data=payload, files=files)
	print(response.text)


@frappe.whitelist()
def get_item_price(item):
	if item:
		date=utils.today()
		price=frappe.db.sql("""select price_list_rate from `tabItem Price` where item_code=%s and selling=1 and valid_from<%s""",(item,date))
		return price

@frappe.whitelist()
def get_standard_item():
	all_attendance=frappe.db.get_all("Item",filters={"product_purchase":1},fields=['item_code','item_name'])
	day_attend=[]
        #frappe.msgprint(str(all_attendance))
	for attendance in all_attendance:
		item =  attendance['item_code']
		date=utils.today()
		price=frappe.db.sql("""select price_list_rate from `tabItem Price` where item_code=%s and selling=1 and valid_from<%s""",(item,date))
		attendance['price_list'] = price[0][0]
		day_attend.append(attendance)
	return day_attend
