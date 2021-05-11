# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
def execute(filters=None):
	columns, data = [], []
	columns=get_columns()
	data=get_data()
	frappe.msgprint(str(columns))
	return columns, data

def get_columns():
	return[
		{"label":_("Employee"),"fieldname":"employee","fieldtype":"Data","width":100},
		{"label":_("Employee Name"), "fieldname":"employee_name","width":100},
		{"label":_("Posting Date"), "fieldname":"from_date","fieldtype":"Date","width":100},
		{"label":_("Designation"), "fieldname":"designation","width":100},
		{"label":_("Company"), "fieldname":"company","width":100}
		]

def get_data():
	all_data= frappe.db.sql('''select ssa.employee,ssa.employee_name ,ssa.from_date,ssa.designation,ssa.company from `tabSalary Structure Assignment` ssa ''' , as_dict=1)
	frappe.msgprint(str(all_data[0]))
	return all_data
