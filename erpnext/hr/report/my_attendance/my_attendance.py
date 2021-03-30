
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
	data = get_data(filters)
	chart = get_chart_data(data)
	return columns, data,None, chart
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
def get_data(filters=None):
	emp_code=frappe.get_value("User",frappe.session.user,"username")
	all_data=frappe.db.sql('''SELECT employee as employee,employee_name as employeename,CAST(time as date) as date,MIN(CAST(time as time)) as in_time,
				 log_type as log_type,shift as shift,max(CAST(time as time)) as out_time 
				 FROM `tabEmployee Checkin` where employee = %s GROUP BY CAST(time as date),employee''',emp_code,as_dict=1 )
#	frappe.msgprint(str(all_data))
	for data in all_data:
		attendance_data=frappe.db.sql(''' SELECT employee as employee ,employee_name as employee_name,attendance_date as date,status as status
						FROM `tabAttendance` where employee = %s and attendance_date = %s''',(data["employee"],data["date"]),as_dict=1)
#		frappe.msgprint(str(attendance_data))
		if attendance_data:
			data['status'] = attendance_data[0]['status']
		if data['in_time'] == data['out_time']:
			data['hrs']=0
			if data['log_type'] =='IN':
				data['out_time']="NaN"
			elif data['log_type']=='OUT':
				data['in_time']="NaN"
		else :
			data['hrs'] = data['out_time'] - data['in_time']
	return all_data
def get_chart_data(all_data):
	present =[]
	absent =[]
	on_leave = []
	half_day =[]
	employee =[]
	status = []
	frappe.msgprint(str(all_data))
	for i in all_data:
#		frappe.msgprint(str(i))
		employee.append(i['employee'])
		if i['status'] == 'Present':
			present.append(i['status'])
		elif i['status'] == 'On Leave':
			on_leave.append(i['status'])
		elif i['status'] == 'Absent':
			absent.append(i['status'])
		elif i['status'] == 'Half Day':
			half_day.append(i['status'])
#		status.append(i['status'])
#	frappe.msgprint(str(status))
	chart = {
		"data": {
			'labels':['Present','On Leave','Absent','Half day'],
			'datasets':[
#				{"name" : "Present",'values': len(present)},
				{"values": [len(present),len(on_leave),len(absent),len(half_day)]}
#				{"name" : "Absent",'values': len(absent)},
#				{"name" : "Half day",'values':len(half_day)}
				]
		}
	}
	chart["type"] = "bar"
#	chart[0]["colors"] = ["#6495ED"]
#	chart[1]["colors"]=["#FF0000","#FF7F00","#D2691E"]
#	data = {
#		"labels": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
#		"datasets": [
#				{"values": [18, 40, 30, 35, 8, 52, 17, -4] }
#			]
#		}
	return chart
