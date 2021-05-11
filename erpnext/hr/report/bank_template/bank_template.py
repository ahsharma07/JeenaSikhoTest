# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data
def get_columns(filters):
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options":"Employee","width": 140},
		{"label":_("Employee-Name"),"fieldname":"employeename","fieldtype":"string","width":200},
		{"label":_("Old Employee Code"),"fieldname":"oldcode","fieldtype":"Data","width":100},
		{"label": _("Parent Department"), "fieldname": "parent_department", "fieldtype": "Link", "options":"Department","width": 140},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options":"Department","width": 140},
		{"label":_("Bank Name"),"fieldname":"bank_name","fieltype":"str","width":200},
		{"label":_("Account number"),"fieldname":"account_number","fieldtype":"Data","width":200},
		{"label":_("IFSC Code"),"fieldname":"ifsc_code","fieldtype":"Data","width":160},
		{"label":_("Net Pay"),"fieldname":"net_pay","fieldtype":"Currency","width":100},
		]
def get_data(filters):
	if filters.get("supplimentary") == 1:
#		frappe.throw(str("enter"))
		conditions = get_conditions(filters)
		query =  frappe.db.sql("""SELECT DISTINCT E.employee as employee ,E.employee_name as employeename,E.department as department,
					E.bank_name as bank_name,E.bank_ac_no as account_number,E.ifsc_code as ifsc_code,S.amount as net_pay
					FROM `tabEmployee` E , `tabAdditional Salary` S where {conditions} """ .format(conditions=conditions),as_list=1)
#		frappe.throw(str(query))
	else :
		conditions =  get_conditions(filters)
		query = frappe.db.sql("""SELECT DISTINCT E.employee as employee ,E.employee_name as employeename,
					E.department as department,
					E.bank_name as bank_name,E.bank_ac_no as account_number,E.ifsc_code as ifsc_code,S.net_pay as net_pay
					FROM `tabEmployee` E , `tabSalary Slip` S where {conditions} """ .format(conditions=conditions),as_list=1)
	return query
def get_conditions(filters):
	conditions = ""
	if filters.get("supplimentary") == 1 :
		conditions += " E.employee = S.employee and S.amount > 0"
		conditions += " and S.overwrite_salary_structure_amount = 0"
		if filters.get("company"): conditions += " and S.company= '%s' " % filters.get("company")
		if filters.get("month"): conditions += " and monthname(S.payroll_date)= '%s' "%filters.get("month")
		if filters.get("year"): conditions += " and year(S.payroll_date)= '%s' "%filters.get("year")
	else :
		conditions += " E.employee = S.employee and S.net_pay > 0"
		if filters.get("company"): conditions += " and S.company= '%s' " % filters.get("company") 
		if filters.get("month"): conditions += " and monthname(S.start_date)= '%s' "%filters.get("month")
		if filters.get("year"): conditions += " and year(S.start_date)= '%s' "%filters.get("year")
	if filters.get("parent_department"): conditions += " and E.parent_department= '%s' "%filters.get("parent_department")
	if filters.get("department"): conditions += " and E.department= '%s'"%filters.get("department")
	if filters.get("designation") : conditions += " and E.designation= '%s' "%filters.get("designation")
	if filters.get("branch"): conditions += " and E.branch= '%s' "%filters.get("branch")
	return conditions

