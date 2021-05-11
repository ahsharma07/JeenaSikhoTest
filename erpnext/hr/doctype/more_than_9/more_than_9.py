# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class MoreThan9(Document):
	pass
@frappe.whitelist()
def call(from_date,to_date):
	at = frappe.db.sql('''UPDATE tabAttendance JOIN (
				SELECT *,TIMEDIFF(out_time,in_time),'Present' as new_status FROM 
				(SELECT employee as employee,employee_name as employeename,DATE(time) as attendance_date,MIN(TIME(time)) as in_time,
				log_type,shift as shift,max(TIME(time)) as out_time FROM tabEmployee Checkin  WHERE Date(time) 
				BETWEEN from_date AND to_date  GROUP BY employee,DATE(time) ORDER BY employee) t1
				WHERE  TIMEDIFF(out_time,in_time)>'8:50:00' ) t2
				ON (tabAttendance.employee=t2.employee AND tabAttendance.attendance_date = t2.attendance_date)
				SET tabAttendance.status = t2.new_status
				SELECT employee,employeename,status,count(*)
				FROM (
				SELECT t1.*,TIMEDIFF(out_time,in_time) as working_hrs,
				CASE WHEN TIMEDIFF(out_time,in_time)>'8:50' OR t3.approved_request=TRUE THEN 'Present' ELSE 
				CASE WHEN TIMEDIFF(out_time,in_time)<'8:50' AND TIMEDIFF(out_time,in_time)>'5:00' THEN 'Half Day' ELSE 'Absent' END
				END as status ,t3.approved_request
				FROM 
				(SELECT employee as employee,employee_name as employeename,shift as shift,DATE(time) as attendance_date,
				MIN(CASE WHEN log_type='IN' THEN TIME(time) ELSE Null END ) as in_time,
				max(CASE WHEN log_type='OUT' THEN TIME(time) ELSE NULL END) as out_time FROM tabEmployee Checkin  WHERE Date(time) 
				BETWEEN from_date AND to_date  GROUP BY employee,DATE(time)) t1
				LEFT JOIN 
				(SELECT employee,from_date,TRUE as approved_request FROM tabAttendance Request tar  
				WHERE from_date BETWEEN '2021-03-15' AND '2021-03-31'
				AND workflow_state like 'Approved') t3
				ON t1.employee=t3.employee and t1.attendance_date=t3.from_date) t4
				GROUP BY employee,status'''

