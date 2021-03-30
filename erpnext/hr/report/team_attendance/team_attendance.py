
# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
import datetime
from datetime import time
def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data()
	return columns, data
def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options":"Employee","width": 140},
		{"label":_("Employee-Name"),"fieldname":"employeename","fieldtype":"string","width":200},
		{"label": _("Date"), "fieldname": "date", "fieldtype":"Date","width": 100},
	#	{"label": _("Day"), "fieldname": "day","fieldtype":"Time","width": 200},
		{"label": _("Shift"), "fieldname": "shift","fieldtype":"Data", "width": 100},
		{"label": _("In-Time"), "fieldname": "in_time", "fieldtype": "Time",  "width": 100},
		{"label": _("Out-Time"), "fieldname": "out_time", "fieldtype": "Time", "width": 120},
		{"label": _("Total-Hrs"), "fieldname": "hrs", "width": 100},
		{"label": _("Status"), "fieldname": "status",  "width": 100},
	#	{"label": _("OT-Hrs"), "fieldname": "OT",  "width": 100},
		]
def get_data():
	all_data=frappe.db.sql('''SELECT employee as employee,employee_name as employeename,CAST(time as date) as date,MIN(CAST(time as time)) as in_time,
				 log_type as log_type,shift as shift,max(CAST(time as time)) as out_time 
				 FROM `tabEmployee Checkin`GROUP BY CAST(time as date),employee''',as_dict=1 )
	for data in all_data:
		attendance_data=frappe.db.sql(''' SELECT employee as employee ,employee_name as employee_name,attendance_date as date,status as status
						FROM `tabAttendance` where employee = %s and attendance_date = %s''',(data["employee"],data["date"]),as_dict=1)
		frappe.msgprint(str(attendance_data))
		if attendance_data:
			data['status'] = attendance_data[0]['status']
#		if data['employee']==attendance_data[0]['employee']:
#			if data['date']==attendance_data[0]['date']:
		if data['in_time'] == data['out_time']:
			data['hrs']=0
			if data['log_type'] =='IN':
				data['out_time']="NaN"
			elif data['log_type']=='OUT':
				data['in_time']="NaN"
		elif data['in_time'] != data['out_time'] :
			data['hrs'] = data['out_time'] - data['in_time']
	return all_data
