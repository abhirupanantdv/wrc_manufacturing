app_name = "manufacturing_adv"
app_title = "manufacturing_adv"
app_publisher = "manufacturing_adv"
app_description = "manufacturing_adv"
app_email = "Abhirup.s@anantdv.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "manufacturing_adv",
# 		"logo": "/assets/manufacturing_adv/logo.png",
# 		"title": "manufacturing_adv",
# 		"route": "/manufacturing_adv",
# 		"has_permission": "manufacturing_adv.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/manufacturing_adv/css/manufacturing_adv.css"
app_include_js = "/assets/manufacturing_adv/js/work_order.js"

# include js, css files in header of web template
# web_include_css = "/assets/manufacturing_adv/css/manufacturing_adv.css"
# web_include_js = "/assets/manufacturing_adv/js/manufacturing_adv.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "manufacturing_adv/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Work Order": "public/js/work_order.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "manufacturing_adv/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "manufacturing_adv.utils.jinja_methods",
# 	"filters": "manufacturing_adv.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "manufacturing_adv.install.before_install"
# after_install = "manufacturing_adv.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "manufacturing_adv.uninstall.before_uninstall"
# after_uninstall = "manufacturing_adv.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "manufacturing_adv.utils.before_app_install"
# after_app_install = "manufacturing_adv.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "manufacturing_adv.utils.before_app_uninstall"
# after_app_uninstall = "manufacturing_adv.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "manufacturing_adv.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"manufacturing_adv.tasks.all"
# 	],
# 	"daily": [
# 		"manufacturing_adv.tasks.daily"
# 	],
# 	"hourly": [
# 		"manufacturing_adv.tasks.hourly"
# 	],
# 	"weekly": [
# 		"manufacturing_adv.tasks.weekly"
# 	],
# 	"monthly": [
# 		"manufacturing_adv.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "manufacturing_adv.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "manufacturing_adv.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "manufacturing_adv.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["manufacturing_adv.utils.before_request"]
# after_request = ["manufacturing_adv.utils.after_request"]

# Job Events
# ----------
# before_job = ["manufacturing_adv.utils.before_job"]
# after_job = ["manufacturing_adv.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"manufacturing_adv.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
doc_events = {
    "Work Order": {
        "on_submit": "manufacturing_adv.work_order_workflow.process_work_order_workflow",
        "on_update_after_submit": "manufacturing_adv.work_order_workflow.process_work_order_workflow",
        "on_change": "manufacturing_adv.work_order_workflow.process_work_order_workflow",
    }
}
fixtures = [
    {
        "dt": "Workflow State",
        "filters": [
            [
                "name",
                "in",
                [
                    "Draft",
                    "Material Transfer Approved",
                    "Production Approved",
                    "Completed",
                ],
            ]
        ],
    },
    {
        "dt": "Workflow Action",
        "filters": [
            [
                "name",
                "in",
                [
                    "Approve and Transfer Material",
                    "Approve Production",
                    "Approve and Manufacture",
                ],
            ]
        ],
    },
    {
        "dt": "Workflow",
        "filters": [
            ["name", "=", "Work Order Approval"]
        ],
    },
]