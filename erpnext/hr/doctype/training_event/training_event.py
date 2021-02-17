# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import time_diff_in_seconds
from erpnext.hr.doctype.employee.employee import get_employee_emails

class TrainingEvent(Document):
	def validate(self):
		self.set_employee_emails()
		self.validate_period()

	def set_employee_emails(self):
		self.employee_emails = ', '.join(get_employee_emails([d.employee
			for d in self.employees]))

	def validate_period(self):
		if time_diff_in_seconds(self.end_time, self.start_time) <= 0:
			frappe.throw(_('End time cannot be before start time'))

	def get_attendence(self):
		self.set('employees', [])
#               parameters = get_template_details(self.quality_inspection_template)
		parameters = frappe.get_all('Training Event Employee', fields=["employee",'employee_name','status','attendance'],
                                filters={'parenttype': 'Training Batch', 'parent': self.training_batch}, order_by="idx")
		for d in parameters:
			child = self.append('employees', {})
			child.employee = d.employee
			child.employee_name = d.employee_name
			child.status = d.status
			child.attendance = d.attendance
