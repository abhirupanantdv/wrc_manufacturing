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

	before_workflow_action: function (frm) {
		if (frm.selected_workflow_action === "Approve and Manufacture") {
			const requires_batch = cint(frm.doc.has_batch_no) === 1 || cint(frm.doc.has_serial_no) === 1;
			if (requires_batch) {
				// Instantly cancel standard Frappe workflow call and open single batch modal
				frappe.dom.unfreeze();
				frm.selected_workflow_action = null;
				open_manufacture_batch_dialog(frm);
				return Promise.reject("BATCH_MODAL_REQUIRED");
			}
		}
	},

	allow_alternative_item: function (frm) {
		frm.remove_custom_button(__("Alternate Item"));
		frm.remove_custom_button("Alternate Item");
	},
});

function open_manufacture_batch_dialog(frm) {
	// Guard against opening multiple dialogs
	if (frm._manufacture_batch_dialog && frm._manufacture_batch_dialog.display) {
		return;
	}
	if ($(".modal.show:contains('Approve & Manufacture')").length > 0) {
		return;
	}

	// Fetch item details (expiry date / shelf life)
	frappe.db.get_value("Item", frm.doc.production_item, [
		"has_batch_no",
		"has_serial_no",
		"has_expiry_date",
		"shelf_life_in_days",
		"create_new_batch"
	]).then((r) => {
		if (frm._manufacture_batch_dialog && frm._manufacture_batch_dialog.display) {
			return;
		}
		const info = r && r.message ? r.message : {
			has_batch_no: frm.doc.has_batch_no,
			has_serial_no: frm.doc.has_serial_no,
			has_expiry_date: 0,
			shelf_life_in_days: 0,
			create_new_batch: 0
		};
		render_batch_dialog(frm, info);
	});
}

function render_batch_dialog(frm, info) {
	// Guard: Do not open if already displayed
	if (frm._manufacture_batch_dialog && frm._manufacture_batch_dialog.display) {
		return;
	}
	if ($(".modal.show:contains('Approve & Manufacture')").length > 0) {
		return;
	}
	const pending_qty = flt(frm.doc.qty) - flt(frm.doc.produced_qty);

	const fields = [
		{
			fieldtype: "HTML",
			fieldname: "item_summary",
			options: `
				<div style="background: var(--bg-light-gray, #f8f9fa); padding: 12px 16px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid var(--primary, #1b84ff);">
					<div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); font-weight: 600;">Finished Good to Manufacture</div>
					<div style="font-size: 16px; font-weight: 600; margin-top: 2px; margin-bottom: 4px; color: var(--text-color);">
						${frappe.utils.escape_html(frm.doc.item_name || frm.doc.production_item)}
						<span style="font-weight: normal; font-size: 13px; color: var(--text-muted);">(${frappe.utils.escape_html(frm.doc.production_item)})</span>
					</div>
					<div style="font-size: 13px; color: var(--text-color);">
						Quantity to Produce: <b>${pending_qty} ${frappe.utils.escape_html(frm.doc.stock_uom || "")}</b>
						&nbsp;&bull;&nbsp; Work Order: <b>${frappe.utils.escape_html(frm.doc.name)}</b>
					</div>
				</div>
			`,
		},
	];

	if (info.has_batch_no) {
		fields.push(
			{
				fieldtype: "Select",
				fieldname: "batch_action",
				label: __("Batch Option"),
				options: [
					{ label: __("Create New Batch"), value: "Create New Batch" },
					{ label: __("Use Existing Batch"), value: "Use Existing Batch" },
				],
				default: "Create New Batch",
				reqd: 1,
			},
			{
				fieldtype: "Data",
				fieldname: "new_batch_id",
				label: __("New Batch ID / Lot No"),
				description: __("Enter the new batch code or lot number for this production run."),
			},
			{
				fieldtype: "Link",
				fieldname: "existing_batch_no",
				label: __("Existing Batch No"),
				options: "Batch",
				onchange: function () {
					const b_name = dialog.get_value("existing_batch_no");
					if (b_name) {
						frappe.db.get_value("Batch", b_name, ["manufacturing_date", "expiry_date"]).then((r) => {
							if (r && r.message) {
								if (r.message.manufacturing_date) {
									dialog.set_value("manufacturing_date", r.message.manufacturing_date);
								}
								if (r.message.expiry_date) {
									dialog.set_value("expiry_date", r.message.expiry_date);
								}
							}
						});
					}
				},
			},
			{
				fieldtype: "Column Break",
				fieldname: "col_break_dates",
			},
			{
				fieldtype: "Date",
				fieldname: "manufacturing_date",
				label: __("Manufacturing Date"),
				default: frappe.datetime.get_today(),
				reqd: 1,
			},
			{
				fieldtype: "Date",
				fieldname: "expiry_date",
				label: __("Expiry Date"),
				description: info.has_expiry_date
					? __("Mandatory for perishable/food items.")
					: __("Optional expiry date."),
				reqd: info.has_expiry_date ? 1 : 0,
			},
			{
				fieldtype: "Section Break",
				fieldname: "sec_break_serials",
			}
		);
	}

	if (info.has_serial_no) {
		fields.push({
			fieldtype: "Small Text",
			fieldname: "serial_nos",
			label: __("Serial Numbers"),
			description: __("Enter {0} serial numbers (one per line).", [pending_qty]),
			reqd: 1,
		});
	}

	const dialog = new frappe.ui.Dialog({
		title: __("Approve & Manufacture: Batch / Serial Details"),
		fields: fields,
		size: "large",
		primary_action_label: __("Manufacture & Complete"),
		primary_action: function (values) {
			if (info.has_batch_no) {
				const is_new = (values.batch_action || "Create New Batch") === "Create New Batch";
				if (is_new && !values.new_batch_id) {
					frappe.msgprint({
						message: __("Please enter a New Batch ID / Lot No."),
						indicator: "red",
						title: __("Batch ID Required"),
					});
					return;
				}
				if (!is_new && !values.existing_batch_no) {
					frappe.msgprint({
						message: __("Please select an Existing Batch No."),
						indicator: "red",
						title: __("Batch Required"),
					});
					return;
				}
				if (info.has_expiry_date && is_new && !values.expiry_date) {
					frappe.msgprint({
						message: __("Please set an Expiry Date for Item {0}.", [frm.doc.production_item]),
						indicator: "red",
						title: __("Expiry Date Required"),
					});
					return;
				}
			}

			if (info.has_serial_no && !values.serial_nos) {
				frappe.msgprint({
					message: __("Please enter Serial Numbers."),
					indicator: "red",
					title: __("Serial Numbers Required"),
				});
				return;
			}

			dialog.get_primary_btn().prop("disabled", true);
			frappe.dom.freeze(__("Creating Batch and submitting Manufacture Stock Entry..."));

			frappe.call({
				method: "manufacturing_adv.work_order_workflow.complete_manufacture_with_batch",
				args: {
					work_order: frm.doc.name,
					batch_action: values.batch_action || "Create New Batch",
					batch_id: values.new_batch_id,
					existing_batch_no: values.existing_batch_no,
					manufacturing_date: values.manufacturing_date,
					expiry_date: values.expiry_date,
					serial_nos: values.serial_nos,
				},
				callback: function (r) {
					frappe.dom.unfreeze();
					if (r && r.message && r.message.status === "success") {
						dialog.hide();
						frappe.show_alert({
							message: __(
								"Manufacture Stock Entry <b>{0}</b> created and submitted successfully with Batch <b>{1}</b>.",
								[r.message.stock_entry, r.message.batch_no || ""]
							),
							indicator: "green",
						});
						frm.reload_doc();
					} else {
						dialog.get_primary_btn().prop("disabled", false);
					}
				},
				error: function () {
					frappe.dom.unfreeze();
					dialog.get_primary_btn().prop("disabled", false);
				},
			});
		},
	});

	// Dynamic visibility and fetching for batch options
	if (info.has_batch_no) {
		const fetch_existing_batch_dates = function () {
			const b_name = dialog.get_value("existing_batch_no");
			if (b_name) {
				frappe.db.get_value("Batch", b_name, ["manufacturing_date", "expiry_date"]).then((r) => {
					if (r && r.message) {
						if (r.message.manufacturing_date) {
							dialog.set_value("manufacturing_date", r.message.manufacturing_date);
						}
						if (r.message.expiry_date) {
							dialog.set_value("expiry_date", r.message.expiry_date);
						}
					}
				});
			}
		};

		const toggle_batch_fields = function () {
			const is_new = (dialog.get_value("batch_action") || "Create New Batch") === "Create New Batch";
			dialog.set_df_property("new_batch_id", "hidden", !is_new);
			dialog.set_df_property("new_batch_id", "reqd", is_new ? 1 : 0);
			dialog.set_df_property("existing_batch_no", "hidden", is_new);
			dialog.set_df_property("existing_batch_no", "reqd", !is_new ? 1 : 0);

			if (is_new) {
				dialog.set_df_property("manufacturing_date", "read_only", 0);
				dialog.set_df_property("expiry_date", "read_only", 0);
				dialog.set_value("manufacturing_date", frappe.datetime.get_today());
				if (info.shelf_life_in_days > 0) {
					dialog.set_value(
						"expiry_date",
						frappe.datetime.add_days(frappe.datetime.get_today(), info.shelf_life_in_days)
					);
				}
			} else {
				dialog.set_df_property("manufacturing_date", "read_only", 1);
				dialog.set_df_property("expiry_date", "read_only", 1);
				fetch_existing_batch_dates();
			}
		};

		dialog.fields_dict.batch_action.$input.on("change", toggle_batch_fields);
		toggle_batch_fields();

		if (dialog.fields_dict.existing_batch_no) {
			dialog.fields_dict.existing_batch_no.get_query = function () {
				return {
					filters: {
						item: frm.doc.production_item,
						disabled: 0,
					},
				};
			};

			const batch_field = dialog.get_field("existing_batch_no");
			batch_field.df.onchange = fetch_existing_batch_dates;
			batch_field.$input.on("change awesomplete-selectcomplete blur", fetch_existing_batch_dates);
		}

		if (info.shelf_life_in_days > 0) {
			dialog.fields_dict.manufacturing_date.$input.on("change", function () {
				const is_new = (dialog.get_value("batch_action") || "Create New Batch") === "Create New Batch";
				if (is_new) {
					const mfg_date = dialog.get_value("manufacturing_date");
					if (mfg_date) {
						dialog.set_value(
							"expiry_date",
							frappe.datetime.add_days(mfg_date, info.shelf_life_in_days)
						);
					}
				}
			});

			const initial_mfg = dialog.get_value("manufacturing_date");
			if (initial_mfg && !dialog.get_value("expiry_date")) {
				dialog.set_value(
					"expiry_date",
					frappe.datetime.add_days(initial_mfg, info.shelf_life_in_days)
				);
			}
		}
	}

	frm._manufacture_batch_dialog = dialog;
	dialog.$wrapper.on("hidden.bs.modal", function () {
		frm._manufacture_batch_dialog = null;
	});

	dialog.show();
}
