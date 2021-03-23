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
		{"label": _("Date"), "fieldname": "date", "fieldtype":"Date","width": 100},
		{"label": _("Day"), "fieldname": "day","fieldtype":"Time","width": 200},
		{"label": _("Shift"), "fieldname": "shift","fieldtype":"Data", "width": 100},
		{"label": _("In-Time"), "fieldname": "in_time", "fieldtype": "Time",  "width": 100},
		{"label": _("Out-Time"), "fieldname": "out_time", "fieldtype": "Time", "width": 120},
		{"label": _("Total-Hrs"), "fieldname": "hrs", "width": 100},
		{"label": _("Portion"), "fieldname": "portion",  "width": 100},
		{"label": _("OT-Hrs"), "fieldname": "OT",  "width": 100},
		]
def get_data():
	datas = []
	all_data=frappe.db.sql('''select employee as employee,CAST(time AS date) as date,Dayname(time) as day,
				 time as in_time,shift as shift,log_type as log
				from `tabEmployee Checkin` 
				order by employee ASC''',as_dict=1 )
	employe =[]
	datde =[]

	frappe.msgprint(str(all_data))
	for data in all_data:
		employe.append(data.employee)
		datde.append(data.date)
	unique_employee = list(set(employe))
	unique_date = list(set(datde))
#	frappe.msgprint(str(employe))
#	frappe.msgprint(str(unique_employee))
#	frappe.msgprint(str(unique_date))
	log_in=[]
	log_out=[]
	dats = []
	employee = ""
	date=""
	for data in all_data:
#		for employee in unique_employee:
		if data.employee and not data.date == date:
			employee = data.employee
			date = data.date
			if data.date:
			#	date = data.date
				if data.log=="IN":
					log_in.append(data.in_time)
#			data.in_time = min(log_in)
					data.in_time = data.in_time
				elif data.log=="OUT":
					log_out.append(data.in_time)
#						data.out_time = max(log_out)
					data.out_time = data.in_time
					data.in_time = ''
				#data.hrs=data.in_time.seconds
				if data.in_time and data.out_time:
					data.hrs =(datetime.datetime.strftime(data.in_time, "%Y-%m-%d %H:%M:%S")) -( datetime.datetime.strftime(data.out_time, "%Y-%m-%d %H:%M:%S"))
#				data.hrs = 0
				if data.hrs:
					if data.hrs>=4.5:
						data.porton = 1
					elif data.hrs<4.5:
						data.portion = 0.5
					else:
						data.portion = 0
					if data.hrs>9:
						data.OT =  data.hrs - 9
					else:
						data.OT = 0
#			else:
#					dats = [{"employee" : data.employee ,"date" : data.date,"day" :data.day,"in_time" :data.in_time,"out_time":data.out_time, 
#						"shift" :data.shift,"hrs" : data.hrs , "portion" : data.portion ,"OT":data.OT}]
#			frappe.msgprint(str(dats))
				datas.append(data)
	return datas
 
"""		data["Total Hrs"] = datetime.strptime(log_in_time, "%H%M%S") - datetime.strptime(out_time, "%H%M%S")
		if data["Total Hrs"]  >=  4.5 :
			data["Porton"] = 1
		elif data["Total Hrs"] < 4.5 :
			data["Portion"] = 0.5
		else :
			data["portion"] = 0
		if data["Total Hrs"] > 9:
			data["OT Hrs"] =  data["Total Hrs"] - 9
		else :
			data["OT Hrs"] = 0"""

