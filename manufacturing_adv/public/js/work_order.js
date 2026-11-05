// Custom Work Order Form Script for manufacturing_adv
// Suppresses default ERPNext custom buttons (Status, Finish, Create, Start, Material Consumption, etc.)
// to enforce the Work Order Approval workflow without adding any Client Script directly in Frappe.

frappe.provide("erpnext.work_order");

// 1. Monkey-patch ERPNext Work Order custom button builder
erpnext.work_order.set_custom_buttons = function (_frm) {
	// Intentionally suppressed: Close, Stop, Re-open (Status), Start, Finish, Create Pick List, Material Consumption
};

// 2. Inject CSS rules globally to ensure buttons are hidden immediately even before JS execution
frappe.dom.set_style(`
	div[id="page-Work Order"] .page-actions .custom-actions,
	div[data-page-route="Work Order"] .page-actions .custom-actions,
	div[id="page-Work Order"] .custom-actions,
	div[data-page-route="Work Order"] .custom-actions,
	div[id="page-Work Order"] .inner-group-button[data-label="Status"],
	div[data-page-route="Work Order"] .inner-group-button[data-label="Status"],
	div[id="page-Work Order"] .inner-group-button[data-label="Create"],
	div[data-page-route="Work Order"] .inner-group-button[data-label="Create"],
	div[id="page-Work Order"] button[data-label="Material%20Consumption"],
	div[data-page-route="Work Order"] button[data-label="Material%20Consumption"],
	div[id="page-Work Order"] button[data-label="Finish"],
	div[data-page-route="Work Order"] button[data-label="Finish"],
	div[id="page-Work Order"] button[data-label="Start"],
	div[data-page-route="Work Order"] button[data-label="Start"],
	div[id="page-Work Order"] button[data-label="Create%20Pick%20List"],
	div[data-page-route="Work Order"] button[data-label="Create%20Pick%20List"],
	div[id="page-Work Order"] button[data-label="Create%20Job%20Card"],
	div[data-page-route="Work Order"] button[data-label="Create%20Job%20Card"] {
		display: none !important;
	}
`, "manufacturing_adv_hide_wo_buttons");

function hide_all_default_buttons(frm) {
	if (!frm || !frm.page) return;

	// Reset ERPNext button flags and custom make mapping
	frm.has_start_btn = false;
	frm.has_finish_btn = false;
	frm.custom_make_buttons = {};

	// Remove standalone custom buttons
	const standalone_buttons = [
		"Start",
		"Finish",
		"Create Pick List",
		"Create Job Card",
		"Material Consumption",
		"Return Components",
		"Alternate Item",
	];
	standalone_buttons.forEach((label) => {
		try {
			frm.remove_custom_button(__(label));
			frm.remove_custom_button(label);
		} catch (e) {}
	});

	// Remove buttons under "Status" group
	const status_buttons = ["Close", "Stop", "Re-open"];
	status_buttons.forEach((label) => {
		try {
			frm.remove_custom_button(__(label), __("Status"));
			frm.remove_custom_button(label, "Status");
			frm.remove_custom_button(__(label), "Status");
			frm.remove_custom_button(label, __("Status"));
		} catch (e) {}
	});

	// Remove buttons under "Create" group
	const create_buttons = ["BOM", "Disassemble Order"];
	create_buttons.forEach((label) => {
		try {
			frm.remove_custom_button(__(label), __("Create"));
			frm.remove_custom_button(label, "Create");
			frm.remove_custom_button(__(label), "Create");
			frm.remove_custom_button(label, __("Create"));
		} catch (e) {}
	});

	// Clear inner toolbar completely
	// Note: Workflow Actions live in frm.page.actions (.actions-btn-group) and remain intact
	try {
		frm.clear_custom_buttons();
	} catch (e) {}

	if (frm.page.inner_toolbar) {
		frm.page.inner_toolbar.empty().addClass("hide").hide();
	}
}

function observe_inner_toolbar(frm) {
	if (!frm || !frm.page || !frm.page.inner_toolbar) return;
	const toolbar = frm.page.inner_toolbar[0];
	if (!toolbar || toolbar._mo_attached) return;
	toolbar._mo_attached = true;

	const observer = new MutationObserver(() => {
		if (frm.doctype === "Work Order" && toolbar.children.length > 0) {
			$(toolbar).empty().addClass("hide").hide();
		}
	});

	observer.observe(toolbar, { childList: true, subtree: true });
}

frappe.ui.form.on("Work Order", {
	setup: function (frm) {
		erpnext.work_order.set_custom_buttons = function (_frm) {};
		frm.custom_make_buttons = {};
		hide_all_default_buttons(frm);
		observe_inner_toolbar(frm);
	},

	onload: function (frm) {
		erpnext.work_order.set_custom_buttons = function (_frm) {};
		frm.custom_make_buttons = {};
		hide_all_default_buttons(frm);
		observe_inner_toolbar(frm);
	},

	refresh: function (frm) {
		erpnext.work_order.set_custom_buttons = function (_frm) {};
		frm.custom_make_buttons = {};
		hide_all_default_buttons(frm);
		observe_inner_toolbar(frm);

		setTimeout(() => {
			hide_all_default_buttons(frm);
		}, 0);

		setTimeout(() => {
			hide_all_default_buttons(frm);
		}, 100);
	},

	allow_alternative_item: function (frm) {
		frm.remove_custom_button(__("Alternate Item"));
		frm.remove_custom_button("Alternate Item");
	},
});
