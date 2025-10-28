from tkinter import *
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import date

# ===== SETUP DATABASE =====
def setup_db():
    conn = sqlite3.connect("library.db")
    cur = conn.cursor()

    # Create tables if they don't exist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        quantity INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS borrowed_books(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        book_id INTEGER,
        borrow_date TEXT,
        return_date TEXT,
        fine REAL,
        FOREIGN KEY(book_id) REFERENCES books(id)
    )
    """)

    # Add some books if the table is empty
    cur.execute("SELECT COUNT(*) FROM books")
    if cur.fetchone()[0] == 0:
        sample_books = [
            ("Learn Python", 4),
            ("Database Systems", 3),
            ("Data Structures", 3),
            ("Web Development", 2),
            ("AI Basics", 2)
        ]
        cur.executemany("INSERT INTO books(title, quantity) VALUES(?, ?)", sample_books)

    conn.commit()
    conn.close()

# ===== LOAD AVAILABLE BOOKS =====
def load_books():
    conn = sqlite3.connect("library.db")
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM books WHERE quantity > 0")
    books = cur.fetchall()
    conn.close()

    combo_book["values"] = [f"{b[0]} - {b[1]}" for b in books]
    if books:
        combo_book.current(0)

# ===== SHOW ALL BORROWED BOOKS =====
def show_records(search=""):
    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect("library.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT borrowed_books.id, borrowed_books.student_name, books.title,
               borrowed_books.borrow_date, borrowed_books.return_date, borrowed_books.fine
        FROM borrowed_books
        JOIN books ON borrowed_books.book_id = books.id
        WHERE borrowed_books.student_name LIKE ? OR books.title LIKE ?
    """, (f"%{search}%", f"%{search}%"))
    rows = cur.fetchall()
    conn.close()

    for r in rows:
        tag = "fine" if r[5] > 0 else ""
        tree.insert("", END, values=r, tags=(tag,))
    lbl_total.config(text=f"Total Records: {len(rows)}")

# ===== ADD BORROW RECORD =====
def borrow_book():
    name = entry_name.get().strip()
    if name == "":
        messagebox.showwarning("Missing Info", "Please enter student name.")
        return

    if combo_book.get() == "":
        messagebox.showwarning("Missing Info", "Please choose a book.")
        return

    book_id = int(combo_book.get().split(" - ")[0])
    b_date = borrow_date.get_date()
    r_date = return_date.get_date()

    if r_date < b_date:
        messagebox.showerror("Date Error", "Return date cannot be before borrow date.")
        return

    fine = 0
    today = date.today()
    if today > r_date:
        fine = (today - r_date).days * 5  # R5 per late day

    conn = sqlite3.connect("library.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO borrowed_books(student_name, book_id, borrow_date, return_date, fine) VALUES(?,?,?,?,?)",
                (name, book_id, b_date.strftime("%m/%d/%Y"), r_date.strftime("%m/%d/%Y"), fine))
    cur.execute("UPDATE books SET quantity = quantity - 1 WHERE id=?", (book_id,))
    conn.commit()
    conn.close()

    messagebox.showinfo("Done", "Book borrowed successfully!")
    clear_form()
    load_books()
    show_records()

# ===== DELETE RECORD =====
def delete_record():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Select a record to delete.")
        return

    sure = messagebox.askyesno("Confirm", "Are you sure you want to delete this record?")
    if not sure:
        return

    record = tree.item(selected[0])["values"]
    borrow_id, book_title = record[0], record[2]

    conn = sqlite3.connect("library.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM books WHERE title=?", (book_title,))
    book_id = cur.fetchone()[0]
    cur.execute("DELETE FROM borrowed_books WHERE id=?", (borrow_id,))
    cur.execute("UPDATE books SET quantity = quantity + 1 WHERE id=?", (book_id,))
    conn.commit()
    conn.close()

    messagebox.showinfo("Deleted", "Record deleted successfully!")
    load_books()
    show_records()

# ===== CLEAR FORM =====
def clear_form():
    entry_name.delete(0, END)
    borrow_date.set_date(date.today())
    return_date.set_date(date.today())
    load_books()

# ===== SEARCH FUNCTION =====
def search_records(*args):
    show_records(search_var.get())

# ===== MAIN GUI =====
setup_db()

win = Tk()
win.title("Student Book Borrow System")
win.geometry("900x500")
win.config(bg="lightgray")

# Left Side - Form
frame_left = LabelFrame(win, text="Borrow a Book", bg="lightgray", padx=15, pady=10)
frame_left.pack(side=LEFT, fill=Y, padx=10, pady=10)

Label(frame_left, text="Student Name:", bg="lightgray").grid(row=0, column=0, sticky="w")
entry_name = Entry(frame_left, width=25)
entry_name.grid(row=0, column=1, pady=5)

Label(frame_left, text="Book:", bg="lightgray").grid(row=1, column=0, sticky="w")
combo_book = ttk.Combobox(frame_left, width=23, state="readonly")
combo_book.grid(row=1, column=1, pady=5)

Label(frame_left, text="Borrow Date:", bg="lightgray").grid(row=2, column=0, sticky="w")
borrow_date = DateEntry(frame_left, width=12)
borrow_date.grid(row=2, column=1, sticky="w")

Label(frame_left, text="Return Date:", bg="lightgray").grid(row=3, column=0, sticky="w")
return_date = DateEntry(frame_left, width=12)
return_date.grid(row=3, column=1, sticky="w")

Button(frame_left, text="Borrow", bg="green", fg="white", width=10, command=borrow_book).grid(row=4, column=0, pady=10)
Button(frame_left, text="Delete", bg="red", fg="white", width=10, command=delete_record).grid(row=4, column=1, pady=10, sticky="w")
Button(frame_left, text="Clear", bg="gray", fg="white", width=10, command=clear_form).grid(row=4, column=1, pady=10, sticky="e")

# ===== Treeview table =====
# Frame for right side with the search and table
frame_right = Frame(win, bg="lightgray")
frame_right.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

# code for search bar and total records
Label(frame_right, text="Search:", bg="lightgray").grid(row=0, column=0, sticky="w")
search_var = StringVar()
search_var.trace_add("write", search_records)
Entry(frame_right, textvariable=search_var, width=40).grid(row=0, column=1, padx=5)

lbl_total = Label(frame_right, text="Total Records: 0", bg="lightgray")
lbl_total.grid(row=0, column=2, padx=20)

# Treeview style 
style = ttk.Style()
style.theme_use("default")  
style.configure("Treeview.Heading", background="blue", foreground="white", font=("Arial", 10, "bold"))

# Columns for table
cols = ("ID", "Student", "Book", "Borrow Date", "Return Date", "Fine")
tree = ttk.Treeview(frame_right, columns=cols, show="headings", height=18)

for c in cols:
    tree.heading(c, text=c)
    tree.column(c, anchor="center", width=130)  # making all columns center, except ID
tree.column("ID", width=40)

# Vertical scrollbar
scroll = ttk.Scrollbar(frame_right, orient=VERTICAL, command=tree.yview)
tree.configure(yscroll=scroll.set)

# Place table and scrollbar
tree.grid(row=1, column=0, columnspan=3, pady=5)
scroll.grid(row=1, column=3, sticky="ns", pady=5)

# Highlight rows with fine > 0 (red for bad students lol)
tree.tag_configure("fine", background="lightcoral")

# Load data
load_books()
show_records()

win.mainloop()

