import frappe
from frappe import _
from frappe.utils import flt

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
    # CUSTOM NAMING SERIES
    # ---------------------------------------------------------
    stock_entry.naming_series = "CNO-STE-"

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
