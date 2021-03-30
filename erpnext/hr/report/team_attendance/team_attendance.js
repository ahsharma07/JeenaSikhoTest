// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Team Attendance"] = {
		"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "in_time") {
			value = "<span style='color:green'>" + value + "</span>";
		}
		if (column.fieldname == "out_time") {
			value = "<span style='color:red'>" + value + "</span>";
		}
		return value
		}

};
