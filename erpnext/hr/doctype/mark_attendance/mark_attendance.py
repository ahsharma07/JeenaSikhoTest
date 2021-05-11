# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class MarkAttendance(Document):
	pass
@frappe.whitelist()
def attendance(from_date,to_date):
	        return frappe.db.sql("""update `tabAttendance` JOIN 
					(SELECT *,TIMEDIFF(out_time,in_time),'Present' as new_status FROM 
					(SELECT employee as employee,employee_name as employeename,DATE(time) as attendance_date,MIN(TIME(time)) as in_time,
					log_type,shift as shift,max(TIME(time)) as out_time FROM `tabEmployee Checkin`  WHERE Date(time) 
					BETWEEN %s AND %s GROUP BY employee,DATE(time) ORDER BY employee) t1
					WHERE  TIMEDIFF(out_time,in_time)>'8:50:00' ) t2
					ON (`tabAttendance`.employee=t2.employee AND `tabAttendance`.attendance_date = t2.attendance_date)
					SET `tabAttendance`.status = t2.new_status""" ,(from_date,to_date))
