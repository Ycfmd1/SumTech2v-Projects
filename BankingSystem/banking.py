import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
from datetime import datetime

# DATABASE SETUP 
conn = sqlite3.connect('bank_users.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    pin TEXT NOT NULL,
    account_type TEXT NOT NULL,
    balance REAL DEFAULT 0
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    amount REAL,
    date TEXT,
    target_user INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

conn.commit()

# BANKING LOGIC 
class BankingSystem:
    def __init__(self, db_cursor):
        self.cursor = db_cursor

    def create_account(self, name, pin, account_type):
        self.cursor.execute("INSERT INTO users (name, pin, account_type, balance) VALUES (?, ?, ?, 0)", (name, pin, account_type))
        conn.commit()

    def login(self, name, pin):
        self.cursor.execute("SELECT * FROM users WHERE name=? AND pin=?", (name, pin))
        return self.cursor.fetchone()

    def deposit(self, user_id, amount):
        self.cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
        self.record_transaction(user_id, "Deposit", amount)
        conn.commit()

    def withdraw(self, user_id, amount):
        balance = self.get_balance(user_id)
        if amount > balance:
            return False
        self.cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, user_id))
        self.record_transaction(user_id, "Withdraw", amount)
        conn.commit()
        return True

    def transfer(self, from_id, to_name, amount):
        self.cursor.execute("SELECT id FROM users WHERE name=?", (to_name,))
        row = self.cursor.fetchone()
        if not row:
            return False
        to_id = row[0]
        if not self.withdraw(from_id, amount):
            return False
        self.deposit(to_id, amount)
        self.record_transaction(from_id, "Transfer", amount, to_id)
        return True

    def get_balance(self, user_id):
        self.cursor.execute("SELECT balance FROM users WHERE id=?", (user_id,))
        return self.cursor.fetchone()[0]

    def record_transaction(self, user_id, trans_type, amount, target_user=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO transactions (user_id, type, amount, date, target_user) VALUES (?, ?, ?, ?, ?)", (user_id, trans_type, amount, now, target_user))
        conn.commit()

    def get_transactions(self, user_id):
        self.cursor.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC", (user_id,))
        return self.cursor.fetchall()


# GUI CLASS 
class BankApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Elite Bank")
        self.bs = BankingSystem(c)
        self.user = None

        self.main_menu()

    def clear(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def main_menu(self):
        self.clear()
        tk.Label(self.master, text="Elite Banking System", font=("Helvetica", 16)).pack(pady=10)

        tk.Button(self.master, text="Create Account", width=20, command=self.create_account_ui).pack(pady=5)
        tk.Button(self.master, text="Login", width=20, command=self.login_ui).pack(pady=5)
        tk.Button(self.master, text="Exit", width=20, command=self.master.quit).pack(pady=5)

    def create_account_ui(self):
        self.clear()
        tk.Label(self.master, text="Create Account", font=("Helvetica", 14)).pack(pady=10)

        name_entry = tk.Entry(self.master)
        pin_entry = tk.Entry(self.master, show="*")
        type_var = tk.StringVar(value="Checking")

        tk.Label(self.master, text="Name").pack()
        name_entry.pack()

        tk.Label(self.master, text="4-digit PIN").pack()
        pin_entry.pack()

        tk.Label(self.master, text="Account Type").pack()
        tk.OptionMenu(self.master, type_var, "Checking", "Savings").pack()

        def submit():
            name = name_entry.get()
            pin = pin_entry.get()
            acc_type = type_var.get()
            if len(pin) != 4 or not pin.isdigit():
                messagebox.showerror("Error", "PIN must be 4 digits.")
                return
            self.bs.create_account(name, pin, acc_type)
            messagebox.showinfo("Success", f"Account created for {name}.")
            self.main_menu()

        tk.Button(self.master, text="Create", command=submit).pack(pady=10)
        tk.Button(self.master, text="Back", command=self.main_menu).pack()

    def login_ui(self):
        self.clear()

        name_entry = tk.Entry(self.master)
        pin_entry = tk.Entry(self.master, show="*")

        tk.Label(self.master, text="Login", font=("Helvetica", 14)).pack(pady=10)
        tk.Label(self.master, text="Name").pack()
        name_entry.pack()
        tk.Label(self.master, text="PIN").pack()
        pin_entry.pack()

        def login():
            name = name_entry.get()
            pin = pin_entry.get()
            user = self.bs.login(name, pin)
            if user:
                self.user = user
                self.dashboard()
            else:
                messagebox.showerror("Error", "Invalid credentials")

        tk.Button(self.master, text="Login", command=login).pack(pady=10)
        tk.Button(self.master, text="Back", command=self.main_menu).pack()

    def dashboard(self):
        self.clear()
        tk.Label(self.master, text=f"Welcome {self.user[1]}", font=("Helvetica", 14)).pack(pady=10)

        def check_balance():
            balance = self.bs.get_balance(self.user[0])
            messagebox.showinfo("Balance", f"Your balance is: ${balance:.2f}")

        def deposit():
            amount = simpledialog.askfloat("Deposit", "Enter amount:")
            if amount:
                self.bs.deposit(self.user[0], amount)
                messagebox.showinfo("Success", "Amount deposited.")

        def withdraw():
            amount = simpledialog.askfloat("Withdraw", "Enter amount:")
            if amount:
                success = self.bs.withdraw(self.user[0], amount)
                if success:
                    messagebox.showinfo("Success", "Amount withdrawn.")
                else:
                    messagebox.showerror("Error", "Insufficient funds.")

        def transfer():
            to_user = simpledialog.askstring("Transfer", "Enter recipient name:")
            amount = simpledialog.askfloat("Transfer", "Enter amount:")
            if to_user and amount:
                if self.bs.transfer(self.user[0], to_user, amount):
                    messagebox.showinfo("Success", "Transfer complete.")
                else:
                    messagebox.showerror("Error", "Transfer failed.")

        def view_transactions():
            txns = self.bs.get_transactions(self.user[0])
            log = "\n".join([f"{row[3]} | {row[2]} | ${row[3]} | To: {row[5] if row[5] else '-'}" for row in txns])
            messagebox.showinfo("Transactions", log or "No transactions yet.")

        tk.Button(self.master, text="Check Balance", command=check_balance).pack(pady=5)
        tk.Button(self.master, text="Deposit", command=deposit).pack(pady=5)
        tk.Button(self.master, text="Withdraw", command=withdraw).pack(pady=5)
        tk.Button(self.master, text="Transfer", command=transfer).pack(pady=5)
        tk.Button(self.master, text="Transaction History", command=view_transactions).pack(pady=5)
        tk.Button(self.master, text="Logout", command=self.main_menu).pack(pady=10)



if __name__ == "__main__":
    root = tk.Tk()
    app = BankApp(root)
    root.geometry("400x500")
    root.mainloop()
