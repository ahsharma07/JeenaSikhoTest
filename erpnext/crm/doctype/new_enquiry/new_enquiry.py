# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe import utils

#from frappe.utils import (cstr, validate_email_address, cint, comma_and, has_gravatar, now, getdate, nowdate)
#from frappe.model.mapper import get_mapped_doc
import requests
#from erpnext.controllers.selling_controller import SellingController
#from frappe.contacts.address_and_contact import load_address_and_contact
#from erpnext.accounts.party import set_taxes
#from frappe.email.inbox import link_communication_to_document

#sender_field = "email_id"

class NewEnquiry(Document):
    pass


@frappe.whitelist(allow_guest=True)
def existing_lead(mobile_number,name=None,gender=None,blood_group=None,age=None,diseases=None,address=None,city=None,landmark=None,salutation=None):
	if mobile_number:
		lead = frappe.db.sql("""select * from `tabLead`
                                where name=%s """, (mobile_number),as_dict=1)
		#frappe.msgprint(str(lead))
		if not lead and name is not None:
			form=frappe.new_doc("Lead")
			form.phone=mobile_number
			form.lead_name=name
			form.mobile_number=mobile_number
			form.gender=gender
			form.blood_group=blood_group
			form.age=age
			form.diseases=diseases
			form.save()
			add_form=frappe.new_doc("Address")
			add_form.address_title = name
			add_form.address_line1=address
			add_form.city=city
			add_form.address_line2=landmark
			add_form.insert()
			customer = frappe.new_doc("Customer")
			customer.customer_name = name 
			customer.salutation = salutation
			customer.customer_type = "Individual"
			customer.customer_group = "Individual"
			customer.lead_name = mobile_number
			customer.save()
			child = add_form.append('links', {})
			child.link_doctype= "Lead"
			child.link_name=mobile_number
			child.link_title=mobile_number
			child.parent = add_form.name
			child.insert()
			cust_child = add_form.append('links', {})
			cust_child.link_doctype= "Customer"
			cust_child.link_name=customer.name
			cust_child.link_title=customer.name
			cust_child.parent = add_form.name
			frappe.msgprint(str(child))
			cust_child.insert()
			#add_form.save()
			frappe.msgprint("Successfully Added")
		else:
			if lead:
				form=frappe.get_doc("Lead",mobile_number)
				child=form.append('realtions',{})
				child.name1=name
				child.diseases=diseases
				frappe.msgprint(str(child))
				child.insert()
				frappe.msgprint("Add")
			#return lead
#		enquiry = frappe.new_doc("Enquiry")
#		enquiry.mobile_no = mobile_no
#		enquiry.query_category = doc.query_category
#		enquiry.query_type= doc.query_type
#		enquiry.query_description = doc.query_description
		frappe.db.sql("""update `tabSingles` set value="" where doctype='New Enquiry' """)
		#if update:
		frappe.msgprint("Update")
@frappe.whitelist()
def exist_lead(mobile):
	if mobile:
		lead=frappe.db.sql("""select * from `tabLead` where name=%s""",(mobile),as_dict=1)
		#frappe.msgprint(str(lead))
		if lead:
			return lead

@frappe.whitelist()
def search(state):
	if state:
		data=frappe.db.sql_list("""select distinct district_name from `tabPincode Master` where state_name=%s """,(state))
		#frappe.msgprint(str(data))
		return data
@frappe.whitelist()
def search_tehsil(district):
	if district:
		tehsils=frappe.db.sql_list("""select distinct related_headoffice from `tabPincode Master` where  related_headoffice=%s""",(district))
		#frappe.msgprint(str(tehsils))
		return tehsils
@frappe.whitelist()
def search_city(tehsil):
	if tehsil:
		cities=frappe.db.sql_list("""select distinct related_suboffice from `tabPincode Master` where related_headoffice=%s""",(tehsil))
		#frappe.msgprint(str(cities))
		return cities
@frappe.whitelist()
def search_pincode(city):
	if city:
		frappe.msgprint(city)
		pincode=frappe.db.sql("""select pincode from `tabPincode Master` where related_suboffice=%s""",(city))
		frappe.msgprint(str(pincode))
		return pincode

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

@frappe.whitelist(allow_guest=True)
def handle_incoming_call(**kwargs):
	frappe.log_error(kwargs,"IVR")

@frappe.whitelist()
def get_item_price(item):
	if item:
		date=utils.today()
		price=frappe.db.sql("""select price_list_rate from `tabItem Price` where item_code=%s and selling=1 and valid_from<%s""",(item,date))
		#frappe.msgprint(str(price))
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
