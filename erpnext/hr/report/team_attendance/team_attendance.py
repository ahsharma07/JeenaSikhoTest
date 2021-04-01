
# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
import datetime
from datetime import time
def execute(filters):
	columns, data = [], []
#	frappe.msgprint(str(filters))
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	return columns ,data,None,chart
def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options":"Employee","width": 140},
		{"label":_("Employee-Name"),"fieldname":"employeename","fieldtype":"string","width":200},
		{"label": _("Date"), "fieldname": "date", "fieldtype":"Date","width": 100},
		{"label": _("Month"), "fieldname": "month","fieldtype":"Data","width": 200},
                {"label":_("Department"),"fieldname":"department","fieldtype":"Link","options":"Department","width":200},
		{"label": _("Shift"), "fieldname": "shift","fieldtype":"Data", "width": 100},
		{"label": _("In-Time"), "fieldname": "in_time", "fieldtype": "Time",  "width": 100},
		{"label": _("Out-Time"), "fieldname": "out_time", "fieldtype": "Time", "width": 120},
		{"label": _("Total-Hrs"), "fieldname": "hrs", "width": 100},
		{"label": _("Status"), "fieldname": "status",  "width": 100},
#		{"label":_("Department"),"fieldname":"department","width":200},
	#	{"label": _("OT-Hrs"), "fieldname": "OT",  "width": 100},
		]
def get_data(filters):
#	emp_code=frappe.get_value("User",frappe.session.user,"username")
#	sort_final_list=[]
#	frappe.msgprint(str(filters.month))
	dat =[]
	u_dat=[]
#	if filters.get('department'):
#		dept=filters.get('department') 
	all_data=frappe.db.sql('''SELECT employee as employee,employee_name as employeename,CAST(time as date) as date,MIN(CAST(time as time)) as in_time,
				log_type as log_type,shift as shift,max(CAST(time as time)) as out_time,monthname(time) as month
				 FROM `tabEmployee Checkin` where monthname(time)=%(month)s 
			        GROUP BY CAST(time as date),employee''',{"month":filters.get('month')},as_dict=1 )
#	frappe.msgprint(str(all_data))	
	for data in all_data:
		dat.append(data['date'])
		u_dat = list(set(dat))
		attendance_data=frappe.db.sql(''' SELECT employee as employee ,employee_name as employee_name,attendance_date as date,status as status,
						department as department
					FROM `tabAttendance` where employee = %(employee)s and attendance_date = %(attendance_date)s and docstatus = 1''',
					{"employee":data["employee"],"attendance_date":data["date"]},as_dict=1)
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
	att_dat = frappe.db.sql(''' SELECT employee as employee,employee_name as employeename,attendance_date as date,status as status,monthname(attendance_date) as month,
				department as department
				FROM `tabAttendance` where monthname(attendance_date)=%(month)s and docstatus = 1 ''',
				{"month":filters.get('month')},as_dict=1)
#	frappe.msgprint(str(att_dat))
	lis = []
	for data in att_dat:
	#	i = 0
#		if att_dat:
		if data['date'] not in u_dat:
			lis.append(data)
	#		i = i+1
#	frappe.msgprint(str(lis))
#	li = [data for data in att_dat if ((data['in_time']=="NaN") and (data['out_time']=="NaN"))]
	final_list = all_data + lis
	sort_final_list = (sorted(final_list, key = lambda k:k['date']))
#	frappe.msgprint(str(sort_final_list))
	return sort_final_list
def get_chart_data(att_dat):
	present =[]
	absent =[]
	on_leave = []
	half_day =[]
	employee =[]
	status = []
#	frappe.msgprint(str(all_data))
	for i in att_dat:
#		frappe.msgprint(str(i))
		employee.append(i['employee'])
		try :
			if i['status'] == 'Present':
				present.append(i['status'])
			elif i['status'] == 'On Leave':
				on_leave.append(i['status'])
			elif i['status'] == 'Absent':
				absent.append(i['status'])
			elif i['status'] == 'Half Day':
				half_day.append(i['status'])
			status.append(i['status'])
		except :
			pass
##	frappe.msgprint(str(status))
	chart = {
		"data": {
			'labels':['Present','On Leave','Absent','Half day'],
			'datasets':[
##				{"name" : "Present",'values': len(present)},
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
