from __future__ import unicode_literals
from frappe import utils
import frappe
from frappe.utils import date_diff


def execute(filters=None):
#	   columns, data = [], []
		date = utils.nowdate()
#	   frappe.msgprint(str(date))
		columns = get_columns(filters)
		data = get_data()
		return columns,data




def get_data():
		emp_data = map_data()
		res = []
		for emp in emp_data:
			for i in emp_data[emp]:
				if i['streak']>2:
					res.append([emp,i['name'],i['from'],i['to'],i['streak']])
		
		return res


def get_columns(filters):
		"""return columns based on filters"""
		columns = [
				{"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options":"Employee", "width": 150},
				{"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
				{"label": "From Date", "fieldname": "from_date","fieldtype": "Date", "width": 100},
				{"label": "To Date", "fieldname": "to_date","fieldtype": "Date", "width": 100},
				{"label": "Streak", "fieldname": "streak","fieldtype": "Data", "width": 100}
				]
		return columns

def map_data():
	x = frappe.db.sql("""select employee, attendance_date, employee_name from `tabAttendance` where status= 'Absent' order by attendance_date desc""")
	emp_map = {}

	for i in range(len(x)):
		emp_map[x[i][0]]=[frappe._dict({ "name":x[i][2], "from" : " ", "to": " ", "streak": 1,'c':0 })]
		
	for i in range(len(x)):
		c = emp_map[x[i][0]][0]['c'] 
		if emp_map[x[i][0]][c]['streak'] < 3 :
			if emp_map[x[i][0]][c]['to'] == ' ':
				emp_map[x[i][0]][c]['to'] = x[i][1]
				emp_map[x[i][0]][c]['from'] = x[i][1]
			if date_diff(emp_map[x[i][0]][c]['from'],x[i][1]) == 1: 
				emp_map[x[i][0]][c]['from'] = x[i][1]
				emp_map[x[i][0]][c]['streak'] += 1
			else:
				emp_map[x[i][0]][c]['streak'] = 1
		elif date_diff(emp_map[x[i][0]][c]['from'],x[i][1]) == 1:
			emp_map[x[i][0]][c]['from'] = x[i][1]
			emp_map[x[i][0]][c]['streak'] += 1
		else:
			c += 1
			emp_map[x[i][0]][0]['c'] += 1
			emp_map[x[i][0]].append(frappe._dict({"name":x[i][2], "from" : ' ', 'to': ' ', 'streak': 1}))
			if emp_map[x[i][0]][c]['to'] == ' ':
				emp_map[x[i][0]][c]['to'] = x[i][1]
				emp_map[x[i][0]][c]['from'] = x[i][1]
			if date_diff(emp_map[x[i][0]][c]['from'],x[i][1]) == 1: 
				emp_map[x[i][0]][c]['from'] = x[i][1]
				emp_map[x[i][0]][c]['streak'] += 1
			else:
				emp_map[x[i][0]][c]['streak'] = 1
				
	return emp_map
			



