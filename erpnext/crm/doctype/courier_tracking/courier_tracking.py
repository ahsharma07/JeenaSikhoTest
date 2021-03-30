# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import requests
import json
import xmltodict
from frappe.model.document import Document

class CourierTracking(Document):
	pass

@frappe.whitelist()
def get_details_bluedart(awb):
	url = f'''https://api.bluedart.com/servlet/RoutingServlet?handler=tnt&action=custawbquery&loginid=ZK447834&awb=awb&numbers={awb}&format=json
		&lickey=a69f9fe8f08d0f9d84b531a0b3efd4ae&verno=1.3&scan=1'''
	headers = {'Cookie': 'BD_Web_LF=ffffffff0d8663c345525d5f4f58455e445a4a423660'}
	response = requests.request("GET", url, headers=headers)
	response2=xmltodict.parse(response.text)
	response2=json.dumps(response2)
	response2=json.loads(response2)
	return response2
