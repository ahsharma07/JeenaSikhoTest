// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Team Attendance"] = {
	        "filters": [
                {
			"fieldname":"month",
			"label": __("Month"),
                        "fieldtype": "Select",
                        "options": ["January","February","March","April","May","June","July","August","September","October","November","December"],
			"reqd":1
        }
	]
};

