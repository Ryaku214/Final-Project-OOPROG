import heapq
import tkinter as tk
from tkinter import ttk, messagebox


# ---------- LINKED LIST: treated patients ----------
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class TreatedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.count = 0

    # Add to the end of the list
    def add_record(self, patient):
        new_node = Node(patient)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self.count += 1

    # Walk through the nodes and collect them in a normal Python list
    def to_list(self):
        result = []
        current = self.head
        while current is not None:
            result.append(current.data)
            current = current.next
        return result


# ---------- MIN-HEAP: waiting room ----------
# Heap item = (severity, ticket, patient)
# Lower severity = treated first. Ticket breaks ties (first come, first served).
class ERSystem:
    def __init__(self):
        self.waiting = []
        self.ticket = 0
        self.treated = TreatedList()
        self.labels = {1: "CRITICAL", 2: "URGENT", 3: "NON-URGENT"}

    # Linear search: returns index in the heap, or -1 if not found
    def find_patient(self, patient_id):
        for i in range(len(self.waiting)):
            patient = self.waiting[i][2]
            if patient["id"].lower() == patient_id.lower():
                return i
        return -1

    # Returns (True/False, message)
    def admit_patient(self, patient_id, name, symptom, severity):
        if self.find_patient(patient_id) != -1:
            return False, "Patient ID '" + patient_id + "' is already waiting."

        self.ticket += 1
        patient = {
            "id": patient_id,
            "name": name,
            "symptom": symptom,
            "severity_label": self.labels[severity],
            "ticket": self.ticket,
        }
        heapq.heappush(self.waiting, (severity, self.ticket, patient))
        return True, "Admitted " + name + " as " + self.labels[severity] + "."

    # Returns the patient dict, or None if nobody is waiting
    def treat_next(self):
        if len(self.waiting) == 0:
            return None
        severity, ticket, patient = heapq.heappop(self.waiting)
        self.treated.add_record(patient)
        return patient

    # Returns True if removed, False if not found
    def cancel_patient(self, patient_id):
        i = self.find_patient(patient_id)
        if i == -1:
            return False
        self.waiting.pop(i)
        heapq.heapify(self.waiting)
        return True


# ==========================================
# PART 2: THE WINDOW (GUI)
# ==========================================
class ERApp:
    def __init__(self, root):
        self.root = root
        self.er = ERSystem()

        root.title("ER Triage & Patient Dispatch System")
        root.geometry("980x560")
        root.columnconfigure(1, weight=1)   # right side stretches
        root.rowconfigure(0, weight=1)

        self.build_form()
        self.build_right_side()
        self.build_status_bar()
        self.refresh()

    # ---------- LEFT SIDE: admit form ----------
    def build_form(self):
        form = ttk.LabelFrame(self.root, text="Admit New Patient", padding=10)
        form.grid(row=0, column=0, sticky="n", padx=10, pady=10)

        ttk.Label(form, text="Patient ID:").grid(row=0, column=0, sticky="w", pady=4)
        self.id_entry = ttk.Entry(form, width=25)
        self.id_entry.grid(row=0, column=1, pady=4)

        ttk.Label(form, text="Name:").grid(row=1, column=0, sticky="w", pady=4)
        self.name_entry = ttk.Entry(form, width=25)
        self.name_entry.grid(row=1, column=1, pady=4)

        ttk.Label(form, text="Symptom:").grid(row=2, column=0, sticky="w", pady=4)
        self.symptom_entry = ttk.Entry(form, width=25)
        self.symptom_entry.grid(row=2, column=1, pady=4)

        ttk.Label(form, text="Severity:").grid(row=3, column=0, sticky="w", pady=4)
        self.severity_box = ttk.Combobox(
            form, width=22, state="readonly",
            values=["1 - Critical", "2 - Urgent", "3 - Non-Urgent"])
        self.severity_box.current(0)
        self.severity_box.grid(row=3, column=1, pady=4)

        ttk.Button(form, text="Admit Patient",
                   command=self.on_admit).grid(row=4, column=0, columnspan=2, pady=12)

        # Big label that shows who is being treated right now
        self.now_label = ttk.Label(form, text="Now treating:\n(nobody yet)",
                                   font=("Arial", 11, "bold"), wraplength=230)
        self.now_label.grid(row=5, column=0, columnspan=2, pady=10)

    # ---------- RIGHT SIDE: buttons + tables ----------
    def build_right_side(self):
        right = ttk.Frame(self.root)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Toolbar
        bar = ttk.Frame(right)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Button(bar, text="Treat Next Patient",
                   command=self.on_treat).pack(side="left", padx=(0, 5))
        ttk.Button(bar, text="Cancel Selected",
                   command=self.on_cancel).pack(side="left", padx=5)

        ttk.Button(bar, text="Search", command=self.on_search).pack(side="right")
        self.search_entry = ttk.Entry(bar, width=15)
        self.search_entry.pack(side="right", padx=5)
        ttk.Label(bar, text="Search ID:").pack(side="right")

        # Two tabs
        self.tabs = ttk.Notebook(right)
        self.tabs.grid(row=1, column=0, sticky="nsew")

        waiting_cols = ("rank", "id", "name", "severity", "symptom")
        self.waiting_tree = self.make_table(waiting_cols,
                                            ("#", "ID", "Name", "Severity", "Symptom"))
        self.tabs.add(self.waiting_tree.master, text="Waiting Room")

        history_cols = ("num", "id", "name", "severity", "symptom")
        self.history_tree = self.make_table(history_cols,
                                            ("#", "ID", "Name", "Severity", "Symptom"))
        self.tabs.add(self.history_tree.master, text="Treated History")

    # Helper: makes a table (Treeview) with a scrollbar inside its own frame
    def make_table(self, columns, headings):
        frame = ttk.Frame(self.tabs)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col, text in zip(columns, headings):
            tree.heading(col, text=text)
            tree.column(col, width=100)
        tree.column(columns[0], width=40, anchor="center")
        tree.column(columns[4], width=250)

        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # Row colors by severity
        tree.tag_configure("CRITICAL", background="#f8d7da")
        tree.tag_configure("URGENT", background="#fff3cd")
        tree.tag_configure("NON-URGENT", background="#d4edda")
        return tree

    def build_status_bar(self):
        self.status = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self.status, relief="sunken",
                  anchor="w", padding=4).grid(row=1, column=0, columnspan=2,
                                              sticky="ew")

    # ---------- Redraw both tables from the data structures ----------
    def refresh(self):
        # Waiting room (sorted copy, so the heap is not changed)
        self.waiting_tree.delete(*self.waiting_tree.get_children())
        rank = 1
        for severity, ticket, p in sorted(self.er.waiting):
            self.waiting_tree.insert(
                "", "end", iid=str(ticket), tags=(p["severity_label"],),
                values=(rank, p["id"], p["name"], p["severity_label"], p["symptom"]))
            rank += 1

        # Treated history (comes from the linked list)
        self.history_tree.delete(*self.history_tree.get_children())
        number = 1
        for p in self.er.treated.to_list():
            self.history_tree.insert(
                "", "end", tags=(p["severity_label"],),
                values=(number, p["id"], p["name"], p["severity_label"], p["symptom"]))
            number += 1

        # Show counts on the tab titles
        self.tabs.tab(0, text="Waiting Room (" + str(len(self.er.waiting)) + ")")
        self.tabs.tab(1, text="Treated History (" + str(self.er.treated.count) + ")")

    # ---------- BUTTON ACTIONS ----------
    def on_admit(self):
        p_id = self.id_entry.get().strip()
        name = self.name_entry.get().strip()
        symptom = self.symptom_entry.get().strip()

        if p_id == "" or name == "" or symptom == "":
            messagebox.showwarning("Missing info", "ID, name, and symptom cannot be empty.")
            return

        severity = int(self.severity_box.get()[0])   # "1 - Critical" -> 1
        ok, message = self.er.admit_patient(p_id, name, symptom, severity)

        if not ok:
            messagebox.showerror("Cannot admit", message)
            return

        # Clear the form for the next patient
        self.id_entry.delete(0, "end")
        self.name_entry.delete(0, "end")
        self.symptom_entry.delete(0, "end")
        self.id_entry.focus()

        self.status.set(message)
        self.refresh()

    def on_treat(self):
        patient = self.er.treat_next()
        if patient is None:
            messagebox.showinfo("Empty", "The waiting room is empty.")
            return

        self.now_label.config(text="Now treating:\n" + patient["name"] +
                              "\n(" + patient["severity_label"] + ")")
        self.status.set("Treating " + patient["name"] + " (ID: " + patient["id"] + ")")
        self.refresh()

    def on_cancel(self):
        selected = self.waiting_tree.selection()
        if len(selected) == 0:
            messagebox.showinfo("Select a patient",
                                "Click a patient in the Waiting Room table first.")
            return

        values = self.waiting_tree.item(selected[0], "values")
        p_id = str(values[1])
        name = values[2]

        if messagebox.askyesno("Confirm", "Remove " + name + " from the waiting room?"):
            self.er.cancel_patient(p_id)
            self.status.set("Removed " + name + " from the waiting room.")
            self.refresh()

    def on_search(self):
        p_id = self.search_entry.get().strip()
        if p_id == "":
            return

        i = self.er.find_patient(p_id)
        if i == -1:
            messagebox.showinfo("Not found", "No waiting patient with ID '" + p_id + "'.")
            return

        ticket = str(self.er.waiting[i][2]["ticket"])
        self.tabs.select(0)                          # switch to Waiting Room tab
        self.waiting_tree.selection_set(ticket)      # highlight the row
        self.waiting_tree.see(ticket)
        self.status.set("Found patient " + p_id + ".")


# ==========================================
# START THE PROGRAM
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = ERApp(root)
    root.mainloop()
