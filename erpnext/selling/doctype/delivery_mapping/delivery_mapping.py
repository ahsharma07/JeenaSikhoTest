# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class DeliveryMapping(Document):
	pass

@frappe.whitelist()
def get_all_item(service_provider_type,doc):
	all_attendance=frappe.db.get_all("Item",filters={"service_provider_type":service_provider_type,"disabled":0},fields=['item_code',"item_name",'item_group'])
	day_attend=[]
	for attendance in all_attendance:
		day_attend.append(attendance)
	return day_attend
