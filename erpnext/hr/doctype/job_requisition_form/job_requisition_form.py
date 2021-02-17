# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.desk.form import assign_to

class JobRequisitionForm(Document):
	def on_submit(self):
		assign_to.add({
			"assign_to":"ashish@extensioncrm.com",
			"doctype": "Job Requisition Form",
			"name": self.name,
			"description": "Job Requisition raised"})

