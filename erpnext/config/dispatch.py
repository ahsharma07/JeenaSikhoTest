from __future__ import unicode_literals
from frappe import _

def get_data():
        return [
                {
                        "label": _("Mapping"),
                        "items": [
                                {
                                        "type": "doctype",
                                        "name": "Delivery Mapping",
                                        "description":_("Mapping"),
                                        "onboard": 1,
                                }
                        ]
                }
		]
