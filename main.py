
"""
Student Record Management System
--------------------------------
GUI : Tkinter / ttk (standard library, no installs needed)
Data: JSON file (students.json, created next to this script)

OOP concepts demonstrated
- Classes / encapsulation : Person, Student, PostgraduateStudent, StudentRepository, StudentApp
- Inheritance             : Student(Person), PostgraduateStudent(Student)
- Polymorphism            : grade(), pass_mark(), summary() are overridden in subclasses
- Exception handling      : custom exceptions + try/except around every user action
"""

import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.json")


# ----------------------------------------------------------------------------
# Custom exceptions
# ----------------------------------------------------------------------------
class ValidationError(Exception):
    """Raised when user input is invalid."""


class DuplicateRecordError(Exception):
    """Raised when adding a student whose ID already exists."""


class RecordNotFoundError(Exception):
    """Raised when a student ID is not in the repository."""


# ----------------------------------------------------------------------------
# Domain model (inheritance + polymorphism)
# ----------------------------------------------------------------------------
class Person:
    """Base class holding personal details with validation."""

    EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")

    def __init__(self, name, age, email):
        self.name = self._validate_name(name)
        self.age = self._validate_age(age)
        self.email = self._validate_email(email)

    @staticmethod
    def _validate_name(name):
        name = str(name).strip()
        if not name:
            raise ValidationError("Name cannot be empty.")
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", name):
            raise ValidationError("Name may contain only letters, spaces, . ' -")
        return name

    @staticmethod
    def _validate_age(age):
        try:
            age = int(str(age).strip())
        except ValueError:
            raise ValidationError("Age must be a whole number.")
        if not 15 <= age <= 100:
            raise ValidationError("Age must be between 15 and 100.")
        return age

    @classmethod
    def _validate_email(cls, email):
        email = str(email).strip()
        if not cls.EMAIL_RE.match(email):
            raise ValidationError("Enter a valid email address (e.g. name@example.com).")
        return email

    def summary(self):
        return f"{self.name} ({self.age})"


class Student(Person):
    """Undergraduate student."""

    LEVEL = "Undergraduate"

    def __init__(self, student_id, name, age, email, course, marks):
        super().__init__(name, age, email)
        self.student_id = self._validate_id(student_id)
        self.course = self._validate_course(course)
        self.marks = self._validate_marks(marks)

    @staticmethod
    def _validate_id(sid):
        sid = str(sid).strip().upper()
        if not sid:
            raise ValidationError("Student ID cannot be empty.")
        if not re.fullmatch(r"[A-Z0-9-]{3,15}", sid):
            raise ValidationError("Student ID must be 3-15 letters, digits or hyphens.")
        return sid

    @staticmethod
    def _validate_course(course):
        course = str(course).strip()
        if not course:
            raise ValidationError("Course cannot be empty.")
        return course

    @staticmethod
    def _validate_marks(marks):
        try:
            marks = float(str(marks).strip())
        except ValueError:
            raise ValidationError("Marks must be a number.")
        if not 0 <= marks <= 100:
            raise ValidationError("Marks must be between 0 and 100.")
        return marks

    # --- polymorphic behaviour -------------------------------------------
    def pass_mark(self):
        return 40.0

    def grade(self):
        m = self.marks
        if m >= 85: return "A"
        if m >= 70: return "B"
        if m >= 55: return "C"
        if m >= self.pass_mark(): return "D"
        return "F"

    def status(self):
        return "Pass" if self.marks >= self.pass_mark() else "Fail"

    def extra(self):
        return ""

    def summary(self):
        return f"{self.student_id} | {super().summary()} | {self.course} | {self.LEVEL} | {self.grade()}"

    # --- persistence ---------------------------------------------------
    def to_dict(self):
        return {
            "type": self.LEVEL,
            "student_id": self.student_id,
            "name": self.name,
            "age": self.age,
            "email": self.email,
            "course": self.course,
            "marks": self.marks,
            "research_topic": "",
        }


class PostgraduateStudent(Student):
    """Postgraduate student: higher pass mark, stricter grading, research topic."""

    LEVEL = "Postgraduate"

    def __init__(self, student_id, name, age, email, course, marks, research_topic):
        super().__init__(student_id, name, age, email, course, marks)
        research_topic = str(research_topic).strip()
        if not research_topic:
            raise ValidationError("Research topic is required for postgraduate students.")
        self.research_topic = research_topic

    def pass_mark(self):          # overrides
        return 50.0

    def grade(self):              # overrides
        m = self.marks
        if m >= 90: return "A"
        if m >= 75: return "B"
        if m >= 60: return "C"
        if m >= self.pass_mark(): return "D"
        return "F"

    def extra(self):              # overrides
        return self.research_topic

    def to_dict(self):            # extends
        data = super().to_dict()
        data["research_topic"] = self.research_topic
        return data


def student_from_dict(d):
    """Factory: build the right Student subclass from stored data."""
    if d.get("type") == "Postgraduate":
        return PostgraduateStudent(d["student_id"], d["name"], d["age"], d["email"],
                                   d["course"], d["marks"], d.get("research_topic", ""))
    return Student(d["student_id"], d["name"], d["age"], d["email"], d["course"], d["marks"])


# ----------------------------------------------------------------------------
# Repository (file storage)
# ----------------------------------------------------------------------------
class StudentRepository:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self._students = {}
        self.load()

    def load(self):
        self._students = {}
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for d in json.load(f):
                    s = student_from_dict(d)
                    self._students[s.student_id] = s
        except (json.JSONDecodeError, KeyError, ValidationError) as e:
            raise ValueError(f"Data file is corrupted: {e}")

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self._students.values()], f, indent=2)

    def add(self, student):
        if student.student_id in self._students:
            raise DuplicateRecordError(f"Student ID {student.student_id} already exists.")
        self._students[student.student_id] = student
        self.save()

    def update(self, student):
        if student.student_id not in self._students:
            raise RecordNotFoundError(f"Student ID {student.student_id} not found.")
        self._students[student.student_id] = student
        self.save()

    def delete(self, student_id):
        if student_id not in self._students:
            raise RecordNotFoundError(f"Student ID {student_id} not found.")
        del self._students[student_id]
        self.save()

    def all(self):
        return sorted(self._students.values(), key=lambda s: s.student_id)

    def search(self, query):
        q = query.strip().lower()
        if not q:
            return self.all()
        return [s for s in self.all()
                if q in s.student_id.lower() or q in s.name.lower()
                or q in s.course.lower() or q in s.email.lower()]


# ----------------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------------
class StudentApp(tk.Tk):
    COLUMNS = ("ID", "Name", "Age", "Email", "Course", "Level", "Marks", "Grade", "Status")

    def __init__(self):
        super().__init__()
        self.title("Student Record Management System")
        self.geometry("1100x560")
        self.minsize(950, 500)

        try:
            self.repo = StudentRepository()
        except ValueError as e:
            messagebox.showerror("Load error", str(e))
            self.repo = StudentRepository(path=DATA_FILE + ".new")

        self.vars = {k: tk.StringVar() for k in
                     ("id", "name", "age", "email", "course", "marks", "level", "research")}
        self.vars["level"].set("Undergraduate")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())

        self._build_ui()
        self.refresh()

    # ---------------- UI construction ----------------
    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=26)
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))

        left = ttk.Frame(self, padding=12)
        left.pack(side="left", fill="y")
        right = ttk.Frame(self, padding=12)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="Student Details", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        fields = [("Student ID", "id"), ("Name", "name"), ("Age", "age"),
                  ("Email", "email"), ("Course", "course"), ("Marks (0-100)", "marks")]
        self.entries = {}
        for i, (label, key) in enumerate(fields, start=1):
            ttk.Label(left, text=label).grid(row=i, column=0, sticky="w", pady=4)
            e = ttk.Entry(left, textvariable=self.vars[key], width=28)
            e.grid(row=i, column=1, pady=4, padx=(8, 0))
            self.entries[key] = e

        r = len(fields) + 1
        ttk.Label(left, text="Level").grid(row=r, column=0, sticky="w", pady=4)
        level = ttk.Combobox(left, textvariable=self.vars["level"], state="readonly",
                             values=("Undergraduate", "Postgraduate"), width=25)
        level.grid(row=r, column=1, pady=4, padx=(8, 0))
        level.bind("<<ComboboxSelected>>", lambda _e: self._toggle_research())

        ttk.Label(left, text="Research topic").grid(row=r + 1, column=0, sticky="w", pady=4)
        self.research_entry = ttk.Entry(left, textvariable=self.vars["research"], width=28)
        self.research_entry.grid(row=r + 1, column=1, pady=4, padx=(8, 0))
        self._toggle_research()

        btns = ttk.Frame(left)
        btns.grid(row=r + 2, column=0, columnspan=2, pady=16)
        ttk.Button(btns, text="Add", width=10, command=self.add_student).grid(row=0, column=0, padx=3, pady=3)
        ttk.Button(btns, text="Update", width=10, command=self.update_student).grid(row=0, column=1, padx=3, pady=3)
        ttk.Button(btns, text="Delete", width=10, command=self.delete_student).grid(row=1, column=0, padx=3, pady=3)
        ttk.Button(btns, text="Clear", width=10, command=self.clear_form).grid(row=1, column=1, padx=3, pady=3)

        # Right side: search + table
        top = ttk.Frame(right)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Search:").pack(side="left")
        ttk.Entry(top, textvariable=self.search_var, width=40).pack(side="left", padx=8)
        ttk.Label(top, text="(ID, name, course or email)").pack(side="left")

        table_frame = ttk.Frame(right)
        table_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings", selectmode="browse")
        widths = (80, 130, 45, 170, 120, 95, 55, 50, 55)
        for col, w in zip(self.COLUMNS, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center" if col in ("Age", "Marks", "Grade", "Status") else "w")
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.tag_configure("fail", foreground="#b00020")

        self.status_var = tk.StringVar()
        ttk.Label(right, textvariable=self.status_var).pack(anchor="w", pady=(8, 0))

    def _toggle_research(self):
        is_pg = self.vars["level"].get() == "Postgraduate"
        self.research_entry.configure(state="normal" if is_pg else "disabled")
        if not is_pg:
            self.vars["research"].set("")

    # ---------------- helpers ----------------
    def build_student(self):
        v = {k: var.get() for k, var in self.vars.items()}
        if v["level"] == "Postgraduate":
            return PostgraduateStudent(v["id"], v["name"], v["age"], v["email"],
                                       v["course"], v["marks"], v["research"])
        return Student(v["id"], v["name"], v["age"], v["email"], v["course"], v["marks"])

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        results = self.repo.search(self.search_var.get())
        for s in results:
            self.tree.insert("", "end", iid=s.student_id,
                             values=(s.student_id, s.name, s.age, s.email, s.course,
                                     s.LEVEL, f"{s.marks:g}", s.grade(), s.status()),
                             tags=("fail",) if s.status() == "Fail" else ())
        self.status_var.set(f"Showing {len(results)} of {len(self.repo.all())} records")

    def clear_form(self):
        for k, var in self.vars.items():
            var.set("Undergraduate" if k == "level" else "")
        self._toggle_research()
        self.entries["id"].configure(state="normal")
        self.tree.selection_remove(self.tree.selection())

    def on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        s = next((x for x in self.repo.all() if x.student_id == sel[0]), None)
        if s is None:
            return
        self.vars["id"].set(s.student_id)
        self.vars["name"].set(s.name)
        self.vars["age"].set(s.age)
        self.vars["email"].set(s.email)
        self.vars["course"].set(s.course)
        self.vars["marks"].set(f"{s.marks:g}")
        self.vars["level"].set(s.LEVEL)
        self._toggle_research()
        self.entries["id"].configure(state="normal")
        self.vars["research"].set(s.extra())
        # research entry may be disabled for UG; that's fine

    # ---------------- actions ----------------
    def add_student(self):
        try:
            self.repo.add(self.build_student())
        except (ValidationError, DuplicateRecordError) as e:
            messagebox.showwarning("Cannot add", str(e))
        except OSError as e:
            messagebox.showerror("File error", f"Could not save data:\n{e}")
        else:
            self.refresh()
            self.clear_form()
            messagebox.showinfo("Success", "Student added.")

    def update_student(self):
        try:
            self.repo.update(self.build_student())
        except (ValidationError, RecordNotFoundError) as e:
            messagebox.showwarning("Cannot update", str(e))
        except OSError as e:
            messagebox.showerror("File error", f"Could not save data:\n{e}")
        else:
            self.refresh()
            messagebox.showinfo("Success", "Student updated.")

    def delete_student(self):
        sid = self.vars["id"].get().strip().upper()
        try:
            if not sid:
                raise ValidationError("Select a student (or enter an ID) to delete.")
            if sid not in {s.student_id for s in self.repo.all()}:
                raise RecordNotFoundError(f"Student ID {sid} not found.")
            if not messagebox.askyesno("Confirm delete", f"Delete student {sid}?"):
                return
            self.repo.delete(sid)
        except (ValidationError, RecordNotFoundError) as e:
            messagebox.showwarning("Cannot delete", str(e))
        except OSError as e:
            messagebox.showerror("File error", f"Could not save data:\n{e}")
        else:
            self.refresh()
            self.clear_form()


if __name__ == "__main__":
    StudentApp().mainloop()
