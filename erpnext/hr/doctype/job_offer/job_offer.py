# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe import _
from frappe.utils.data import get_link_to_form

class JobOffer(Document):
	def onload(self):
		employee = frappe.db.get_value("Employee", {"job_applicant": self.job_applicant}, "name") or ""
		self.set_onload("employee", employee)

	def validate(self):
		self.validate_vacancies()

	def validate_vacancies(self):
		staffing_plan = get_staffing_plan_detail(self.designation, self.company, self.offer_date)
		check_vacancies = frappe.get_single("HR Settings").check_vacancies
		if staffing_plan and check_vacancies:
			job_offers = self.get_job_offer(staffing_plan.from_date, staffing_plan.to_date)
			if not staffing_plan.get("vacancies") or cint(staffing_plan.vacancies) - len(job_offers) <= 0:
				error_variable = 'for ' + frappe.bold(self.designation)
				if staffing_plan.get("parent"):
					error_variable = frappe.bold(get_link_to_form("Staffing Plan", staffing_plan.parent))

				frappe.throw(_("There are no vacancies under staffing plan {0}").format(error_variable))

	def on_change(self):
		update_job_applicant(self.status, self.job_applicant)

	def get_job_offer(self, from_date, to_date):
		''' Returns job offer created during a time period '''
		return frappe.get_all("Job Offer", filters={
				"offer_date": ['between', (from_date, to_date)],
				"designation": self.designation,
				"company": self.company
			}, fields=['name'])

	def get_employee_grade_slab(self):
		self.set('employee_grade_slab', [])
#            parameters = get_template_details(self.quality_inspection_template)
		parameters = frappe.get_all('Employee Grade Slab', fields=["components","yearly","monthly"],
                                filters={'parenttype': 'Employee Grade', 'parent': self.employee_grade}, order_by="idx")
		for d in parameters:
			child = self.append('employee_grade_slab', {})
			child.components = d.components
			child.monthly = d.monthly
			child.yearly = d.yearly
	def on_submit(self):
		selected_applicant = frappe.db.get_value("Job Requisition Form", self.job_requisition_form, "total_selected_applicant")
		required_employee = frappe.db.get_value("Job Requisition Form", self.job_requisition_form, "no_of_required_emp")
		if self.status == "Accepted":
			selected_applicant += 1
			frappe.set_value("Job Requisition Form", self.job_requisition_form, "total_selected_applicant", selected_applicant)
		elif self.status == "Rejected" and not selected_applicant == 0:
			selected_applicant -= 1
			frappe.set_value("Job Requisition Form", self.job_requisition_form, "total_selected_applicant", selected_applicant)

		if selected_applicant == required_employee:
			frappe.set_value("Job Requisition Form", self.job_requisition_form, "status", "Completed")
		elif selected_applicant > 0 :
			frappe.set_value("Job Requisition Form", self.job_requisition_form, "status", "In - Progress")
		else:
			frappe.set_value("Job Requisition Form", self.job_requisition_form, "status", "Open")

		selected_applicant = frappe.db.get_value("Training Batch", self.training_batch, "enrolled_applicants")
		if self.status == "Accepted":
			selected_applicant += 1
			frappe.set_value("Training Batch", self.training_batch, "enrolled_applicants", selected_applicant)
		elif self.status == "Rejected" and not selected_applicant == 0:
			selected_applicant -= 1
			frappe.set_value("Training Batch", self.training_batch, "enrolled_applicants", selected_applicant)

	def on_update_after_submit(self):
		selected_applicant = frappe.db.get_value("Job Requisition Form", self.job_requisition_form, "total_selected_applicant")
		if self.status == "Accepted":
			selected_applicant += 1
			frappe.set_value("Job Requisition Form", self.job_requisition_form, "total_selected_applicant", selected_applicant)
		elif self.status == "Rejected" and not selected_applicant == 0:
			selected_applicant -= 1
			frappe.set_value("Job Requisition Form", self.job_requisition_form, "total_selected_applicant", selected_applicant)

		selected_applicant = frappe.db.get_value("Training Batch", self.training_batch, "enrolled_applicants")
		if self.status == "Accepted":
			selected_applicant += 1
			frappe.set_value("Training Batch", self.training_batch, "enrolled_applicants", selected_applicant)
		elif self.status == "Rejected" and not selected_applicant == 0:
			selected_applicant -= 1
			frappe.set_value("Training Batch", self.training_batch, "enrolled_applicants", selected_applicant)

def update_job_applicant(status, job_applicant):
	if status in ("Selected", "Rejected"):
		frappe.set_value("Job Applicant", job_applicant, "status", status)

def get_staffing_plan_detail(designation, company, offer_date):
	detail = frappe.db.sql("""
		SELECT DISTINCT spd.parent,
			sp.from_date as from_date,
			sp.to_date as to_date,
			sp.name,
			sum(spd.vacancies) as vacancies,
			spd.designation
		FROM `tabStaffing Plan Detail` spd, `tabStaffing Plan` sp
		WHERE
			sp.docstatus=1
			AND spd.designation=%s
			AND sp.company=%s
			AND spd.parent = sp.name
			AND %s between sp.from_date and sp.to_date
	""", (designation, company, offer_date), as_dict=1)

	return frappe._dict(detail[0]) if (detail and detail[0].parent) else None

@frappe.whitelist()
def make_employee(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.personal_email = frappe.db.get_value("Job Applicant", source.job_applicant, "email_id")
	doc = get_mapped_doc("Job Offer", source_name, {
			"Job Offer": {
				"doctype": "Employee",
				"field_map": {
					"applicant_name": "employee_name",
					"applicant_name": "first_name",
					"offer_date": "date_of_joining",
					"gender":"gender",
					"date_of_birth":"date_of_birth",
					"training_batch":"training_batch"
				}}
		}, target_doc, set_missing_values)
	return doc

@frappe.whitelist()
def get_employee_grade_slab(self):
	self.set('employee_grade_slab', [])
#            parameters = get_template_details(self.quality_inspection_template)
	parameters = frappe.get_all('Employee Grade Slab', fields=["componets","yearly","monthly"],
                                filters={'parenttype': 'Employee Grade', 'parent': self.employee_grade}, order_by="idx")
	for d in parameters:
		child = self.append('employee_grade_slab', {})
		child.components = d.components
		child.monthly = d.monthly
		child.yearly = d.yearly
