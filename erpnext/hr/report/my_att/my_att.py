# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import datetime
from datetime import time
from datetime import date, timedelta
start_date = date(2021, 3, 1)
end_date = date(2021, 3, 31)
dates = []
delta = timedelta(days=1)
while start_date <= end_date:
    dates.append(start_date.strftime("%Y-%m-%d"))
    start_date += delta
def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data
def get_columns():
        return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options":"Employee","width": 140},
		{"label":_("Employee-Name"),"fieldname":"employee_name","fieldtype":"string","width":200},
		{"label": _("Date"), "fieldname": "date", "fieldtype":"Date","width": 100},
		{"label": _("Shift"), "fieldname": "shift","fieldtype":"Data", "width": 100},
		{"label": _("In-Time"), "fieldname": "in_time", "fieldtype": "Time",  "width": 100},
		{"label": _("Out-Time"), "fieldname": "out_time", "fieldtype": "Time", "width": 120},
		{"label": _("Total-Hrs"), "fieldname": "hrs", "width": 100},
		{"label": _("Status"), "fieldname": "status",  "width": 100},
		]
def get_data(filters=None):
	emp_code=frappe.get_value("User",frappe.session.user,"username")
	frappe.msgprint(str(dates))
	for date in dates :
		data=frappe.db.sql('''SELECT ec.employee as employee,ec.employee_name as employeename,CAST(ec.time as date) as date,
					MIN(CAST(ec.time as time)) as in_time,ec.log_type as log_type,ec.shift as shift,
					max(CAST(time as time)) as out_time,att.status as status
					FROM `tabEmployee Checkin` ec, `tabAttendance` att where ec.attendance=att.name and ec.employee ="HR-EMP-00049" 
					GROUP BY CAST(time as date)''',as_dict=1 )
		frappe.msgprint(data)
		return data
