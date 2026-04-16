import frappe


def _ensure_owner(doc):
    if doc.owner != frappe.session.user:
        frappe.throw("Not permitted")


@frappe.whitelist()
def list_tasks():
    user = frappe.session.user
    tasks = frappe.get_all(
        "ToDo",
        fields=["name", "description", "status", "modified"],
        filters={"owner": user},
        order_by="modified desc",
    )
    return [
        {
            "id": task.name,
            "title": task.description,
            "done": task.status == "Closed",
        }
        for task in tasks
    ]


@frappe.whitelist()
def add_task(title):
    if not title:
        frappe.throw("Task title is required")

    doc = frappe.get_doc(
        {
            "doctype": "ToDo",
            "description": title,
            "status": "Open",
            "allocated_to": frappe.session.user,
        }
    )
    doc.insert()

    return {
        "id": doc.name,
        "title": doc.description,
        "done": doc.status == "Closed",
    }


@frappe.whitelist()
def update_task(task_id, title=None, done=None):
    doc = frappe.get_doc("ToDo", task_id)
    _ensure_owner(doc)

    if title is not None:
        if not title:
            frappe.throw("Task title is required")
        doc.description = title

    if done is not None:
        doc.status = "Closed" if done else "Open"

    doc.save()

    return {
        "id": doc.name,
        "title": doc.description,
        "done": doc.status == "Closed",
    }


@frappe.whitelist()
def delete_task(task_id):
    doc = frappe.get_doc("ToDo", task_id)
    _ensure_owner(doc)
    frappe.delete_doc("ToDo", task_id)
    return {"ok": True}
