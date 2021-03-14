frappe.query_reports["My Attendance"] = {
        "filters": [
                {
                        "fieldname":"from_date",
                        "label": __("From Date"),
                        "fieldtype": "Date",
                        "width": "80",
                        "default": frappe.datetime.add_months(frappe.datetime.get_today(),-1)
                },
                {
                        "fieldname":"to_date",
                        "label": __("To Date"),
                        "fieldtype": "Date",
                        "width": "80",
                        "default": frappe.datetime.get_today()
                }
],
};

