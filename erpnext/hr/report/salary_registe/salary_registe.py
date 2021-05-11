
from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
	if not filters: filters = {}
	salary_slips = get_salary_slips(filters)
	if not salary_slips: return [], []
	columns, earning_types, ded_types = get_columns(salary_slips)
	ss_earning_map = get_ss_earning_map(salary_slips)
	ss_ded_map = get_ss_ded_map(salary_slips)
	doj_map = get_employee_doj_map()
	parent_dep_map = get_employee_parent_department_map()
	old_id_map = get_employee_old_id_map()
	father_map = get_employee_father_name_map()
	dob_map = get_employee_dob_map()
	spouse_map = get_employee_spouse_map()
	data = []
	for ss in salary_slips:
		esic = frappe.db.get_value("Employee",ss.employee,"esic_number")
		uan = frappe.db.get_value("Employee",ss.employee,"uan_number")
		row = [ss.name, ss.employee, old_id_map.get(ss.employee),ss.employee_name,father_map.get(ss.employee), doj_map.get(ss.employee),dob_map.get(ss.employee),
			spouse_map.get(ss.employee), esic, uan,ss.company, ss.branch,
			parent_dep_map.get(ss.employee), ss.department, ss.designation,ss.total_working_days,ss.total_present_days,ss.payment_days,
			ss.manual_extra_days,ss.extra_days,ss.fixed_basic,ss.basic,ss.fixed_hra,ss.hra,ss.fixed_conveyance,ss.conveyance,ss.fixed_ta&da,ss.ta&da,
			ss.extra_days,ss.bonus,ss.incentive,ss.monthly_gross,ss.payable_salary,ss.ss,provident_fund,ss.esic,ss.ptax,ss.tds,ss.salary_advance,
			ss.loan,ss.security,ss.other_deduction,ss.total_deductions,ss.net_pay			ss.salary_structure,
			 ss.start_date, ss.end_date,ss.total_present_days,(ss.total_present_days - ss.payment_days),ss.leave_without_pay, ss.payment_days]
                if not ss.branch == None:columns[3] = columns[3].replace('-1','120')
                if not ss.department  == None: columns[4] = columns[4].replace('-1','120')
                if not ss.designation  == None: columns[5] = columns[5].replace('-1','120')
                if not ss.leave_without_pay  == None: columns[9] = columns[9].replace('-1','130')
                for e in earning_types:
                        row.append(ss_earning_map.get(ss.name, {}).get(e))
                row += [ss.gross_pay]
                for d in ded_types:
                        row.append(ss_ded_map.get(ss.name, {}).get(d))
                row.append(ss.total_loan_repayment)
                row += [ss.total_deduction, ss.net_pay,ss.base]
		data.append(row)
	return columns, data
def get_columns(salary_slips):
	columns = [
		_("Salary Slip ID") + ":Link/Salary Slip:150",_("Employee") + ":Link/Employee:120",_("Old Employee Id") + "::80", _("Employee Name") + "::140",
		_("Father's Name") + ":: 140",
		_("Date Joined") + "::80", _("Date of Birth"),_("Spouse Name"),_("ESIC No") + "::80",_("UAN No") + "::80", _("Grade") + ":Link/Salary Structure:100",
		_("Branch") + ":Link/Branch:-1",_("Parentt Department") +"::200",
		_("Department") + ":Link/Department:-1",
		_("Designation") + ":Link/Designation:-1",_("Total Days") + "::80",_("Days Present"),_("Days Paid"),_("Manual Extra Days"),
		_("Extra Days Calc") + "::80",_("Fixed Basic"),_("Basic"),_("Fixed HRA"),_("HRA"),_("Fixed Conveyance"),_("Conveyance"),
		_("Fixed TA & Other"),_("TA & Other"),_("Extra days Work"),_("Bouns"),_("Incentive"),_("Monthly Gross"),_("Payable Salary"),_("Provident Fund"),
		_("E.S.I.C"),_("P.Tax"),_("TDS"),_("Salary Advance"), _("Loan"),_("Security"),_("Other Deductions"),_("Total Deductions"),_("Net Pay")
		]
	return columns

def get_salary_slips(filters):
        filters.update({"from_date": filters.get("from_date"), "to_date":filters.get("to_date")})
        conditions, filters = get_conditions(filters)
        salary_slips = frappe.db.sql("""select * from `tabSalary Slip` where %s
                order by employee""" % conditions, filters, as_dict=1)

        return salary_slips or []

def get_conditions(filters):
        conditions = ""
        doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

        if filters.get("docstatus"):
                conditions += "docstatus = {0}".format(doc_status[filters.get("docstatus")])

        if filters.get("from_date"): conditions += " and start_date >= %(from_date)s"
        if filters.get("to_date"): conditions += " and end_date <= %(to_date)s"
        if filters.get("company"): conditions += " and company = %(company)s"
        if filters.get("employee"): conditions += " and employee = %(employee)s"

        return conditions, filters

def get_employee_doj_map():
        return  frappe._dict(frappe.db.sql("""
                                SELECT
                                        employee,
                                        date_of_joining
                                FROM `tabEmployee`
                                """))

def get_ss_earning_map(salary_slips):
        ss_earnings = frappe.db.sql("""select parent, salary_component, amount
                from `tabSalary Detail` where parent in (%s)""" %
                (', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

        ss_earning_map = {}
        for d in ss_earnings:
                ss_earning_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
                ss_earning_map[d.parent][d.salary_component] = flt(d.amount)

        return ss_earning_map

def get_ss_ded_map(salary_slips):
        ss_deductions = frappe.db.sql("""select parent, salary_component, amount
                from `tabSalary Detail` where parent in (%s)""" %
                (', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

        ss_ded_map = {}
        for d in ss_deductions:
                ss_ded_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
                ss_ded_map[d.parent][d.salary_component] = flt(d.amount)

        return ss_ded_map
def get_employee_parent_department_map():
        return  frappe._dict(frappe.db.sql("""
                                SELECT
                                        employee,
                                        parent_department
                                FROM `tabEmployee`
                                """))

def get_employee_old_id_map():
        return  frappe._dict(frappe.db.sql("""
                                SELECT
                                        employee,
                                        company_old_employee_id
                                FROM `tabEmployee`
                                """))
def get_employee_father_name_map():
        return  frappe._dict(frappe.db.sql("""
                                SELECT
					employee,
                                        person_to_be_contacted,
                                FROM `tabEmployee`
				"""))


def get_employee_dob_map():
        return  frappe._dict(frappe.db.sql("""
                                SELECT
                                        employee,
                                        date_of_birth
	                            FROM `tabEmployee`
                                """))

def get_employee_spouse_map():
	return frappe._dict(frappe.db.sql("""
				SELECT 
					employee,
					family_background
				FROM `tabEmployee`
			"""))
