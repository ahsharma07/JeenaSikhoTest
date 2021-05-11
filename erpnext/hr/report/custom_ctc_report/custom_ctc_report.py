# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	meta=frappe.db.get_all("Report",filters={"name":"my att"},fields=['*'])
	frappe.msgprint(str(meta))
	
	return columns, data
