
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
#	chart = get_chart_data(data)
	return columns ,data
def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options":"Employee","width": 140},
		{"label":_("Employee-Name"),"fieldname":"employeename","fieldtype":"string","width":200},
		{"label": _("Date"), "fieldname": "date", "fieldtype":"Date","width": 100},
		{"label": _("Month"), "fieldname": "month","fieldtype":"Data","width": 200},
		{"label": _("Company"),"fieldname":"company","fieldtype":"Data","width":100},
                {"label":_("Department"),"fieldname":"department","fieldtype":"Link","options":"Department","width":200},
		{"label": _("Shift"), "fieldname": "shift","fieldtype":"Data", "width": 100},
		{"label": _("In-Time"), "fieldname": "in_time", "fieldtype": "Time",  "width": 100},
		{"label": _("Out-Time"), "fieldname": "out_time", "fieldtype": "Time", "width": 120},
		{"label": _("Total-Hrs"), "fieldname": "hrs", "width": 100},
		{"label": _("Status"), "fieldname": "status",  "width": 100},
		]
def get_data(filters):
	all_data=frappe.db.sql('''SELECT E.employee as employee,E.employee_name as employeename,A.attendance_date as date,MIN(CAST(E.time as time)) as in_time,EE.department as department,
				EE.company as company,
				E.shift as shift,max(CAST(E.time as time)) as out_time,monthname(E.time) as month,A.status as status,timediff(max(cast(E.time as time)),min(cast(E.time as time))) as hrs
				FROM `tabEmployee Checkin` E ,`tabAttendance` A,`tabEmployee` EE  
				where monthname(E.time)=%(month)s  and CAST(E.time as date)=A.attendance_date and EE.company=%(company)s,EE.department=%(department)s
			        GROUP BY CAST(E.time as date),E.employee''', {"month":filters.get('month'),"company":filters.get('company'),"department":filters.get('department')},as_dict=1 )
	for data in all_data:
		paid_holiday=frappe.db.sql('''select holiday_date from `tabHoliday` where parent=%(calendar)s and holiday_date=%(date)s''',
				{"calendar":"Calendar of "+str(data['date'].year),"date":data['date']},as_dict=1)
		emp_holiday=frappe.db.get_value("Employee",data['employee'],'holiday_list')
		week_off=frappe.db.sql('''select holiday_date from `tabHoliday` where parent=%(calendar)s and holiday_date=%(date)s''',
				{"calendar":emp_holiday,"date":data['date']},as_dict=1)
		if paid_holiday:
			if data['status']=="Present":
				data['status']="Paid Holiday Present"
			elif all_data['status']=="Half Day":
				data['status']="Paid Holiday Half Day"
			else:
				data['status']="Paid Holiday"
		elif week_off:
			if data['status']=="Present":
				data['status']="Week Off Present"
			elif data['status']=="Half Day":
				data['status']="Week Off Half Day"
			else:
				data['status']="Week Off"
	return all_data
"""def get_chart_data(att_dat):
	present =[]
	absent =[]
	on_leave = []
	half_day =[]
	employee =[]
	status = []
	for i in att_dat:
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
"""
