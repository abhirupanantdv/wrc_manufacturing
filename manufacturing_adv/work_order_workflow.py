import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate, add_days

from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry


MATERIAL_APPROVED_STATE = "Material Transfer Approved"
PRODUCTION_APPROVED_STATE = "Production Approved"
COMPLETED_STATE = "Completed"


def process_work_order_workflow(doc, method=None):
    if doc.docstatus != 1:
        return

    workflow_state = doc.get("workflow_state")

    if workflow_state == MATERIAL_APPROVED_STATE:
        create_material_transfer(doc)

    elif workflow_state == COMPLETED_STATE:
        create_manufacture_entry(doc)


# Backward-compatible names if your current hooks.py still uses these.
def on_work_order_submit(doc, method=None):
    process_work_order_workflow(doc, method)


def on_work_order_update_after_submit(doc, method=None):
    process_work_order_workflow(doc, method)


def _guard_key(work_order_name, purpose):
    return "manufacturing_adv_{}_{}".format(
        frappe.scrub(work_order_name),
        frappe.scrub(purpose),
    )


def _already_processing(work_order_name, purpose):
    key = _guard_key(work_order_name, purpose)
    if frappe.flags.get(key):
        return True
    frappe.flags[key] = True
    return False


def _release_guard(work_order_name, purpose):
    frappe.flags[_guard_key(work_order_name, purpose)] = False


def _get_submitted_stock_entries(work_order, purpose):
    return frappe.get_all(
        "Stock Entry",
        filters={
            "work_order": work_order,
            "purpose": purpose,
            "docstatus": 1,
        },
        fields=["name", "fg_completed_qty", "posting_date", "posting_time"],
        order_by="creation asc",
    )


# def _make_and_submit_stock_entry(work_order_name, purpose, qty):
#     qty = flt(qty)

#     if qty <= 0:
#         return None

#     stock_entry_dict = make_stock_entry(
#         work_order_name,
#         purpose,
#         qty,
#     )

#     if not stock_entry_dict:
#         frappe.throw(
#             _("ERPNext did not return a Stock Entry for {0}.").format(
#                 frappe.bold(purpose)
#             )
#         )

#     stock_entry = frappe.get_doc(stock_entry_dict)

#     # Do not bypass ERPNext Stock Entry validation.
#     stock_entry.flags.ignore_permissions = True
#     stock_entry.insert(ignore_permissions=True)
#     stock_entry.submit()

#     return stock_entry


def get_stock_entry_naming_series(work_order):
    """
    Returns the naming series for auto-created Stock Entry.
    Uses GLC-STE-.YYYY.- (matching the Work Order's prefix if applicable).
    """
    if not work_order:
        return "GLC-STE-.YYYY.-"

    if isinstance(work_order, str):
        res = frappe.db.get_value(
            "Work Order", work_order, ["naming_series", "name"]
        )
        wo_series, wo_name = res if res else ("", work_order)
    else:
        wo_series = work_order.get("naming_series") or ""
        wo_name = work_order.get("name") or ""

    for candidate in ["GLC", "NN1", "CNO", "CPCC", "CPPB"]:
        if (wo_series and wo_series.startswith(candidate)) or (wo_name and wo_name.startswith(candidate)):
            target_series = f"{candidate}-STE-.YYYY.-"
            options = (
                frappe.get_meta("Stock Entry").get_field("naming_series").options or ""
            ).split("\n")
            if target_series in options:
                return target_series

    return "GLC-STE-.YYYY.-"


def _make_and_submit_stock_entry(work_order_name, purpose, qty):
    qty = flt(qty)

    if qty <= 0:
        return None

    # ERPNext standard Work Order -> Stock Entry creation
    stock_entry_dict = make_stock_entry(
        work_order_name,
        purpose,
        qty,
    )

    if not stock_entry_dict:
        frappe.throw(
            _("ERPNext did not return a Stock Entry for {0}.").format(
                frappe.bold(purpose)
            )
        )

    stock_entry = frappe.get_doc(stock_entry_dict)

    # ---------------------------------------------------------
    # CUSTOM NAMING SERIES (Default: GLC-STE-.YYYY.-)
    # ---------------------------------------------------------
    stock_entry.naming_series = get_stock_entry_naming_series(work_order_name)

    # ---------------------------------------------------------
    # CUSTOM REMARKS
    # ---------------------------------------------------------
    if purpose == "Material Transfer for Manufacture":
        stock_entry.remarks = (
            f"Stock transfer for material against Work Order {work_order_name}"
        )

    elif purpose == "Manufacture":
        stock_entry.remarks = (
            f"Manufacturing stock entry against Work Order {work_order_name}"
        )

    else:
        stock_entry.remarks = (
            f"{purpose} against Work Order {work_order_name}"
        )

    # Keep ERPNext validation enabled
    stock_entry.flags.ignore_permissions = True

    stock_entry.insert(ignore_permissions=True)
    stock_entry.submit()

    return stock_entry

def create_material_transfer(doc):
    purpose = "Material Transfer for Manufacture"

    if _already_processing(doc.name, purpose):
        return

    try:
        work_order = frappe.get_doc("Work Order", doc.name)

        if work_order.docstatus != 1:
            frappe.throw(
                _("Work Order {0} must be submitted before material transfer.").format(
                    frappe.bold(work_order.name)
                )
            )

        if work_order.workflow_state != MATERIAL_APPROVED_STATE:
            return

        if work_order.skip_transfer:
            frappe.throw(
                _(
                    "Skip Material Transfer is enabled on Work Order {0}. "
                    "Disable it because this workflow requires an automatic "
                    "Material Transfer for Manufacture."
                ).format(frappe.bold(work_order.name))
            )

        if not work_order.bom_no:
            frappe.throw(_("BOM is required on the Work Order."))

        if not work_order.wip_warehouse:
            frappe.throw(_("WIP Warehouse is required on the Work Order."))

        if not work_order.fg_warehouse:
            frappe.throw(_("Finished Goods Warehouse is required on the Work Order."))

        if work_order.transfer_material_against == "Job Card":
            frappe.throw(
                _(
                    "Transfer Material Against is set to Job Card. "
                    "For this automatic workflow set it to <b>Work Order</b>."
                )
            )

        pending_qty = flt(work_order.qty) - flt(
            work_order.material_transferred_for_manufacturing
        )

        if pending_qty <= 0:
            return

        stock_entry = _make_and_submit_stock_entry(
            work_order.name,
            purpose,
            pending_qty,
        )

        if not stock_entry:
            return

        work_order.reload()

        frappe.msgprint(
            _(
                "Material Transfer for Manufacture <b>{0}</b> was created and "
                "submitted automatically for Work Order <b>{1}</b>."
            ).format(stock_entry.name, work_order.name),
            alert=True,
        )

    finally:
        _release_guard(doc.name, purpose)


def create_manufacture_entry(doc):
    purpose = "Manufacture"

    if _already_processing(doc.name, purpose):
        return

    try:
        work_order = frappe.get_doc("Work Order", doc.name)

        if work_order.docstatus != 1:
            frappe.throw(
                _("Work Order {0} must be submitted before manufacture.").format(
                    frappe.bold(work_order.name)
                )
            )

        if work_order.workflow_state != COMPLETED_STATE:
            return

        if not work_order.bom_no:
            frappe.throw(_("BOM is required on the Work Order."))

        if not work_order.fg_warehouse:
            frappe.throw(_("Finished Goods Warehouse is required on the Work Order."))

        if work_order.skip_transfer:
            available_to_manufacture = (
                flt(work_order.qty) - flt(work_order.produced_qty)
            )
        else:
            available_to_manufacture = (
                flt(work_order.material_transferred_for_manufacturing)
                - flt(work_order.produced_qty)
            )

        if available_to_manufacture <= 0:
            if flt(work_order.produced_qty) >= flt(work_order.qty):
                return

            frappe.throw(
                _(
                    "There is no transferred quantity available to manufacture."
                    "<br><br>Work Order Qty: <b>{0}</b>"
                    "<br>Transferred Qty: <b>{1}</b>"
                    "<br>Produced Qty: <b>{2}</b>"
                ).format(
                    work_order.qty,
                    work_order.material_transferred_for_manufacturing,
                    work_order.produced_qty,
                )
            )

        remaining_work_order_qty = (
            flt(work_order.qty) - flt(work_order.produced_qty)
        )

        manufacture_qty = min(
            flt(available_to_manufacture),
            flt(remaining_work_order_qty),
        )

        if manufacture_qty <= 0:
            return

        # Check if finished good item requires batch or serial tracking
        item = frappe.get_cached_doc("Item", work_order.production_item)
        if item.has_batch_no or item.has_serial_no:
            frappe.throw(
                _(
                    "Item {0} requires Batch No / Serial No to manufacture.<br><br>"
                    "Please use the <b>Approve and Manufacture</b> dialog on the Work Order to create or select a batch."
                ).format(frappe.bold(work_order.production_item)),
                title=_("Batch / Serial Details Required"),
            )

        stock_entry = _make_and_submit_stock_entry(
            work_order.name,
            purpose,
            manufacture_qty,
        )

        if not stock_entry:
            return

        work_order.reload()

        frappe.msgprint(
            _(
                "Manufacture Stock Entry <b>{0}</b> was created and submitted "
                "automatically for Work Order <b>{1}</b>."
            ).format(stock_entry.name, work_order.name),
            alert=True,
        )

    finally:
        _release_guard(doc.name, purpose)


@frappe.whitelist()
def run_for_work_order(work_order):
    doc = frappe.get_doc("Work Order", work_order)

    result = {
        "work_order": doc.name,
        "docstatus": doc.docstatus,
        "workflow_state": doc.get("workflow_state"),
        "status_before": doc.status,
    }

    process_work_order_workflow(doc)

    doc.reload()

    result.update(
        {
            "status_after": doc.status,
            "material_transferred_for_manufacturing": flt(
                doc.material_transferred_for_manufacturing
            ),
            "produced_qty": flt(doc.produced_qty),
            "stock_entries": frappe.get_all(
                "Stock Entry",
                filters={"work_order": doc.name},
                fields=["name", "purpose", "docstatus", "fg_completed_qty"],
                order_by="creation asc",
            ),
        }
    )

    return result


@frappe.whitelist()
def diagnostic(work_order):
    doc = frappe.get_doc("Work Order", work_order)

    return {
        "work_order": doc.name,
        "docstatus": doc.docstatus,
        "workflow_state": doc.get("workflow_state"),
        "status": doc.status,
        "qty": flt(doc.qty),
        "produced_qty": flt(doc.produced_qty),
        "material_transferred_for_manufacturing": flt(
            doc.material_transferred_for_manufacturing
        ),
        "skip_transfer": doc.skip_transfer,
        "transfer_material_against": doc.transfer_material_against,
        "bom_no": doc.bom_no,
        "source_warehouse": doc.source_warehouse,
        "wip_warehouse": doc.wip_warehouse,
        "fg_warehouse": doc.fg_warehouse,
        "submitted_material_transfers": _get_submitted_stock_entries(
            doc.name,
            "Material Transfer for Manufacture",
        ),
        "submitted_manufacture_entries": _get_submitted_stock_entries(
            doc.name,
            "Manufacture",
        ),
    }


@frappe.whitelist()
def get_item_batch_details(item_code):
    item = frappe.get_cached_doc("Item", item_code)
    return {
        "item_code": item.name,
        "item_name": item.item_name,
        "has_batch_no": cint(item.has_batch_no),
        "has_serial_no": cint(item.has_serial_no),
        "has_expiry_date": cint(item.has_expiry_date),
        "shelf_life_in_days": cint(item.shelf_life_in_days),
        "create_new_batch": cint(item.create_new_batch),
        "batch_number_series": item.batch_number_series,
    }


@frappe.whitelist()
def get_or_create_draft_manufacture_entry(work_order, qty=None):
    wo = frappe.get_doc("Work Order", work_order)
    if wo.docstatus != 1:
        frappe.throw(_("Work Order {0} must be submitted.").format(wo.name))

    # Check for existing draft Manufacture Stock Entry
    drafts = frappe.get_all(
        "Stock Entry",
        filters={
            "work_order": wo.name,
            "purpose": "Manufacture",
            "docstatus": 0,
        },
        fields=["name"],
        order_by="creation desc",
        limit=1,
    )
    if drafts:
        return drafts[0].name

    available_to_manufacture = (
        flt(wo.qty) - flt(wo.produced_qty)
        if wo.skip_transfer
        else flt(wo.material_transferred_for_manufacturing) - flt(wo.produced_qty)
    )
    remaining_wo_qty = flt(wo.qty) - flt(wo.produced_qty)
    manufacture_qty = flt(qty) if qty else min(available_to_manufacture, remaining_wo_qty)

    if manufacture_qty <= 0:
        frappe.throw(
            _(
                "There is no transferred quantity available to manufacture for Work Order {0}."
            ).format(wo.name)
        )

    stock_entry_dict = make_stock_entry(wo.name, "Manufacture", manufacture_qty)
    if not stock_entry_dict:
        frappe.throw(_("Failed to create Manufacture Stock Entry."))

    stock_entry = frappe.get_doc(stock_entry_dict)
    stock_entry.naming_series = get_stock_entry_naming_series(wo)
    stock_entry.remarks = f"Manufacturing stock entry against Work Order {wo.name}"
    stock_entry.flags.ignore_permissions = True
    stock_entry.insert(ignore_permissions=True)

    return stock_entry.name


@frappe.whitelist()
def complete_manufacture_with_batch(
    work_order,
    batch_action="Create New Batch",
    batch_id=None,
    existing_batch_no=None,
    manufacturing_date=None,
    expiry_date=None,
    serial_nos=None,
):
    wo = frappe.get_doc("Work Order", work_order)
    if wo.docstatus != 1:
        frappe.throw(_("Work Order {0} must be submitted.").format(wo.name))

    item = frappe.get_cached_doc("Item", wo.production_item)

    batch_name = None
    if item.has_batch_no:
        if batch_action == "Use Existing Batch":
            if not existing_batch_no:
                frappe.throw(_("Please select an existing Batch No."))
            batch_item = frappe.db.get_value("Batch", existing_batch_no, "item")
            if batch_item != wo.production_item:
                frappe.throw(
                    _("Batch {0} does not belong to item {1}.").format(
                        existing_batch_no, wo.production_item
                    )
                )
            batch_name = existing_batch_no
        else:
            # Create New Batch
            if not batch_id and not item.create_new_batch:
                frappe.throw(
                    _("Batch ID / Lot No is required for item {0}.").format(
                        wo.production_item
                    )
                )

            mfg_date = manufacturing_date or nowdate()
            exp_date = expiry_date
            if item.has_expiry_date and not exp_date:
                if item.shelf_life_in_days:
                    exp_date = add_days(mfg_date, item.shelf_life_in_days)
                else:
                    frappe.throw(
                        _("Expiry Date is mandatory for batched item {0}.").format(
                            wo.production_item
                        )
                    )

            batch_args = {
                "doctype": "Batch",
                "item": wo.production_item,
                "manufacturing_date": mfg_date,
            }
            if batch_id:
                batch_args["batch_id"] = batch_id.strip()
            if exp_date:
                batch_args["expiry_date"] = exp_date

            batch_doc = frappe.get_doc(batch_args)
            batch_doc.flags.ignore_permissions = True
            batch_doc.insert(ignore_permissions=True)
            batch_name = batch_doc.name

    if item.has_serial_no:
        if not serial_nos and not item.serial_no_series:
            frappe.throw(
                _("Serial numbers are mandatory for item {0}.").format(
                    wo.production_item
                )
            )

    # Check for existing draft Stock Entry or create one
    drafts = frappe.get_all(
        "Stock Entry",
        filters={
            "work_order": wo.name,
            "purpose": "Manufacture",
            "docstatus": 0,
        },
        fields=["name"],
        order_by="creation desc",
        limit=1,
    )

    if drafts:
        se = frappe.get_doc("Stock Entry", drafts[0].name)
    else:
        available_to_manufacture = (
            flt(wo.qty) - flt(wo.produced_qty)
            if wo.skip_transfer
            else flt(wo.material_transferred_for_manufacturing) - flt(wo.produced_qty)
        )
        remaining_wo_qty = flt(wo.qty) - flt(wo.produced_qty)
        manufacture_qty = min(available_to_manufacture, remaining_wo_qty)
        if manufacture_qty <= 0:
            frappe.throw(_("No quantity available to manufacture."))

        se_dict = make_stock_entry(wo.name, "Manufacture", manufacture_qty)
        se = frappe.get_doc(se_dict)
        se.naming_series = get_stock_entry_naming_series(wo)
        se.remarks = f"Manufacturing stock entry against Work Order {wo.name}"

    # Set batch and serial on finished good item row
    for d in se.items:
        if d.is_finished_item and d.item_code == wo.production_item:
            if batch_name:
                d.batch_no = batch_name
                d.use_serial_batch_fields = 1
            if serial_nos:
                d.serial_no = serial_nos.strip()
                d.use_serial_batch_fields = 1

    se.flags.ignore_permissions = True
    if not se.name:
        se.insert(ignore_permissions=True)
    else:
        se.save(ignore_permissions=True)

    se.submit()

    # Transition Work Order workflow state
    wo.reload()
    if flt(wo.produced_qty) >= flt(wo.qty):
        if wo.workflow_state != COMPLETED_STATE:
            wo.db_set("workflow_state", COMPLETED_STATE)
            wo.add_comment(
                "Workflow",
                _("Manufacture completed with Stock Entry {0} and Batch {1}").format(
                    se.name, batch_name or ""
                ),
            )

    return {
        "status": "success",
        "stock_entry": se.name,
        "batch_no": batch_name,
        "workflow_state": wo.workflow_state,
        "produced_qty": wo.produced_qty,
    }


def on_stock_entry_submit(doc, method=None):
    if doc.purpose == "Manufacture" and doc.work_order:
        wo = frappe.get_doc("Work Order", doc.work_order)
        if flt(wo.produced_qty) >= flt(wo.qty):
            if wo.workflow_state != COMPLETED_STATE:
                wo.db_set("workflow_state", COMPLETED_STATE)
                wo.add_comment(
                    "Workflow",
                    _("Completed via Manufacture Stock Entry {0}").format(
                        frappe.utils.get_link_to_form("Stock Entry", doc.name)
                    ),
                )


def on_stock_entry_cancel(doc, method=None):
    if doc.purpose == "Manufacture" and doc.work_order:
        wo = frappe.get_doc("Work Order", doc.work_order)
        if flt(wo.produced_qty) < flt(wo.qty):
            if wo.workflow_state == COMPLETED_STATE:
                wo.db_set("workflow_state", PRODUCTION_APPROVED_STATE)
                wo.add_comment(
                    "Workflow",
                    _("Reverted to {0} after cancellation of Stock Entry {1}").format(
                        PRODUCTION_APPROVED_STATE,
                        frappe.utils.get_link_to_form("Stock Entry", doc.name),
                    ),
                )

