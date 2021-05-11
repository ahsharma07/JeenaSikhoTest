# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	return columns, data

def get_data(filters):
	datalist=[]
	all_data=frappe.db.sql('''select a.employee, a.employee_name, a.status, a.attendance_date from `tabAttendance` a 
			where a.status="Absent" order by employee asc,a.attendance_date asc''')
	frappe.msgprint(str(all_data))
	for i in range(0,len(all_data)-2):
		if (not i==0) and all_data[i]['employee']==all_data[i-1]['employee']==all_data[i+1]['employee']:
			if all_data[i-1]['attendance_date']==all_data[i]['attendance_date']-1==all_data[i+1]['attendance_date']-2:
				datalist.append([all_data[i]['employee'],all_data[i]['status'],all_data[i-1]['attendance_date',
					all_data[i]['attendance_date'],all_data[i+1]['attendance_date']]])
	frappe.msgprint(str(datalist))
