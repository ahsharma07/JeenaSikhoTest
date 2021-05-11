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
        },
                {
                "fieldname":"company",
                "label": __("Company"),
                "fieldtype": "Link",
                "options": "Company",
                "reqd":1,
                },
                {
                "fieldname":"department",
                "label": __("Department"),
                "fieldtype": "Link",
                "options": "Department",
                "default":"Clinic - OPD - JSLCPL",
                "get_query": function() {
                        const parent_department = frappe.query_report.get_filter_value('parent_department');
                        return {
                                filters: { 'parent_department':parent_department }
                                }
                        }

                }


	]
};

