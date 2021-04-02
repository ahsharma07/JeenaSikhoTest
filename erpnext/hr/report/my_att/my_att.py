# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime
from datetime import time
from datetime import date, timedelta
def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	data=sorted(data, key=lambda k: k['date'])
	return columns, data
def get_columns():
        return [
		{"label": _("Employee Attendance"), "fieldname": "attendance", "fieldtype": "Link", "options":"Attendance","width": 140},
		{"label": _("Employee Checkin"), "fieldname": "checkin", "fieldtype": "Link", "options":"Employee Checkin","width": 140},
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
	res=[]
	all_att_data=frappe.db.sql('''select name,attendance_date,status,employee,employee_name,shift from `tabAttendance` where employee=%s''',"HR-EMP-00053",as_dict=1)
	for att_data in all_att_data:
		paid_holiday=frappe.db.sql('''select holiday_date from `tabHoliday` where parent=%(calendar)s and holiday_date=%(date)s''',
			{"calendar":"Calendar of "+str(att_data['attendance_date'].year),"date":att_data['attendance_date']},as_dict=1)
		emp_holiday=frappe.db.get_value("Employee",att_data['employee'],'holiday_list')
		week_off=frappe.db.sql('''select holiday_date from `tabHoliday` where parent=%(calendar)s and holiday_date=%(date)s''',
				{"calendar":emp_holiday,"date":att_data['attendance_date']},as_dict=1)
		employee_checkin=frappe.db.sql('''SELECT name as checkin,employee as employee,employee_name as employee_name,CAST(time as date) as date,MIN(CAST(time as time)) as in_time,
                                     log_type as log_type,shift as shift,max(CAST(time as time)) as out_time,monthname(time) as month
                                      FROM `tabEmployee Checkin` where DATE(time)=%(date)s and employee=%(employee)s''',
					{"date":att_data['attendance_date'],"employee":att_data["employee"]},as_dict=1)
		if paid_holiday:
			if att_data['status']=="Present":
				att_data['status']="Paid Holiday Present"
			elif att_data['status']=="Half Day":
				att_data['status']="Paid Holiday Half Day"
			else:
				att_data['status']="Paid Holiday"
		elif week_off:
			if att_data['status']=="Present":
				att_data['status']="Week Off Present"
			elif att_data['status']=="Half Day":
                                att_data['status']="Week Off Half Day"
			else:
				att_data['status']="Week Off"
		if employee_checkin[0]['employee'] is not None:
			employee_checkin[0]['status']=att_data['status']
			employee_checkin[0]['attendance']=att_data['name']
			res.append(employee_checkin[0])
		else:
			res.append({'attendance':att_data['name'],'employee':att_data['employee'],'employee_name':att_data['employee_name'],'date':att_data['attendance_date'],'shift':att_data['shift'],
			'status':att_data['status']})
	frappe.msgprint(str(res))
	return res
