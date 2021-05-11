// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bank Template"] = {
	"filters":[
		{
		"fieldname":"company",
		"label": __("Company"),
		"fieldtype": "Link",
		"options": "Company",
		"reqd":1,
		},
		{
		"fieldname":"month",
		"label": __("Month"),
		"fieldtype": "Select",
		"options":["January","February","March","April","May","June","July","August","September","October","November","December"],
		"reqd":1,
		},
		{
		"fieldname":"year",
		"label": __("Year"),
		"fieldtype": "Select",
		"options":["2020","2021","2022","2023","2024","2025","2026","2027","2028","2029","2030"],
		"reqd":1,
		},
           //     {
             //   "fieldname":"parent_department",
               // "label": __("Parent Department"),
               // "fieldtype": "Link",
           //     "options": "Department",
	//	//"reqd":1,
          //      "get_query": function() {
            //            return {
              ///                  filters: { 'is_group':1 }
                 //               }
                   //     }
               // },

                {
                "fieldname":"department",
                "label": __("Department"),
                "fieldtype": "Link",
                "options": "Department",
		//"default":"Clinic - OPD - JSLCPL",
                "get_query": function() {
                        const parent_department = frappe.query_report.get_filter_value('parent_department');
                        return {
                                filters: { 'parent_department':parent_department }
                                }
                        }

                },

                {
                "fieldname":"designation",
                "label": __("Designation"),
                "fieldtype": "Link",
                "options": "Designation",
		//"reqd":1,
                },
                {
                "fieldname":"branch",
                "label": __("Branch"),
                "fieldtype": "Link",
                "options": "Branch",
		//"reqd":1,
                },
		{
		"fieldname":"supplimentary",
		"label": __("Is Supplimentary"),
		"fieldtype":"Check",
		}

	]
}

