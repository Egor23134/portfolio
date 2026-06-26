import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import os
import subprocess
import pandas as pd
import math


# ==================== КЛАСС ДЛЯ РАБОТЫ С БД ====================
class Database:
    def __init__(self, db_file='shoe_shop.db'):
        self.db_file = db_file
        self.conn = None
        self.connect()

    def connect(self):
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row

    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetch_all(self, query, params=()):
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params=()):
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def close(self):
        if self.conn:
            self.conn.close()


# ==================== ДИАЛОГ УПРАВЛЕНИЯ СОТРУДНИКАМИ ====================
class EmployeesDialog(tk.Toplevel):
    def __init__(self, parent, db, user):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.user = user
        self.title("👥 Управление сотрудниками")
        self.geometry("700x500")
        self.configure(bg='#F5EDE4')
        self.transient(parent)
        self.grab_set()

        self.is_admin = user['position'] == 'администратор'

        self.create_widgets()
        self.load_employees()

    def create_widgets(self):
        toolbar = tk.Frame(self, bg='#F5EDE4', height=50)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        if self.is_admin:
            tk.Button(toolbar, text="➕ Добавить", bg='#2C1810', fg='white', font=('Segoe UI', 10),
                      padx=15, command=self.add_employee).pack(side=tk.LEFT, padx=5)
            tk.Button(toolbar, text="✏️ Редактировать", bg='#2C1810', fg='white', font=('Segoe UI', 10),
                      padx=15, command=self.edit_employee).pack(side=tk.LEFT, padx=5)
            tk.Button(toolbar, text="🗑️ Удалить", bg='#8B0000', fg='white', font=('Segoe UI', 10),
                      padx=15, command=self.delete_employee).pack(side=tk.LEFT, padx=5)

        tk.Button(toolbar, text="🔄 Обновить", bg='#C4A484', fg='white', font=('Segoe UI', 10),
                  padx=15, command=self.load_employees).pack(side=tk.LEFT, padx=5)

        frame = tk.Frame(self, bg='#F5EDE4')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ('id', 'full_name', 'position')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        self.tree.heading('id', text='ID')
        self.tree.heading('full_name', text='ФИО')
        self.tree.heading('position', text='Должность')
        self.tree.column('id', width=50)
        self.tree.column('full_name', width=350)
        self.tree.column('position', width=150)

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def load_employees(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        employees = self.db.fetch_all("SELECT id, full_name, position FROM employees ORDER BY id")
        for emp in employees:
            self.tree.insert('', tk.END, values=(emp['id'], emp['full_name'], emp['position']))

    def add_employee(self):
        if not self.is_admin:
            messagebox.showerror("Ошибка", "Недостаточно прав")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Добавление сотрудника")
        dialog.geometry("350x250")
        dialog.configure(bg='#F5EDE4')
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="ФИО:", bg='#F5EDE4', fg='#2C1810', font=('Segoe UI', 11)).pack(pady=10)
        name_entry = tk.Entry(dialog, font=('Segoe UI', 10), width=30, bg='white')
        name_entry.pack(pady=5)

        tk.Label(dialog, text="Должность:", bg='#F5EDE4', fg='#2C1810', font=('Segoe UI', 11)).pack(pady=10)
        pos_var = tk.StringVar(value='продавец')
        tk.Radiobutton(dialog, text="Продавец", variable=pos_var, value='продавец', bg='#F5EDE4', fg='#2C1810',
                       selectcolor='#F5EDE4').pack()
        tk.Radiobutton(dialog, text="Старший продавец", variable=pos_var, value='старший продавец', bg='#F5EDE4',
                       fg='#2C1810', selectcolor='#F5EDE4').pack()
        tk.Radiobutton(dialog, text="Администратор", variable=pos_var, value='администратор', bg='#F5EDE4',
                       fg='#2C1810', selectcolor='#F5EDE4').pack()

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите ФИО")
                return
            self.db.execute("INSERT INTO employees (full_name, position) VALUES (?, ?)", (name, pos_var.get()))
            messagebox.showinfo("Успех", f"Сотрудник {name} добавлен")
            dialog.destroy()
            self.load_employees()

        tk.Button(dialog, text="Сохранить", bg='#2C1810', fg='white', padx=20, command=save).pack(pady=20)

    def edit_employee(self):
        if not self.is_admin:
            messagebox.showerror("Ошибка", "Недостаточно прав")
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите сотрудника")
            return
        item = self.tree.item(selected[0])
        emp_id = item['values'][0]
        emp_name = item['values'][1]
        emp_pos = item['values'][2]

        dialog = tk.Toplevel(self)
        dialog.title("Редактирование сотрудника")
        dialog.geometry("350x250")
        dialog.configure(bg='#F5EDE4')
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="ФИО:", bg='#F5EDE4', fg='#2C1810', font=('Segoe UI', 11)).pack(pady=10)
        name_entry = tk.Entry(dialog, font=('Segoe UI', 10), width=30, bg='white')
        name_entry.insert(0, emp_name)
        name_entry.pack(pady=5)

        tk.Label(dialog, text="Должность:", bg='#F5EDE4', fg='#2C1810', font=('Segoe UI', 11)).pack(pady=10)
        pos_var = tk.StringVar(value=emp_pos)
        tk.Radiobutton(dialog, text="Продавец", variable=pos_var, value='продавец', bg='#F5EDE4', fg='#2C1810',
                       selectcolor='#F5EDE4').pack()
        tk.Radiobutton(dialog, text="Старший продавец", variable=pos_var, value='старший продавец', bg='#F5EDE4',
                       fg='#2C1810', selectcolor='#F5EDE4').pack()
        tk.Radiobutton(dialog, text="Администратор", variable=pos_var, value='администратор', bg='#F5EDE4',
                       fg='#2C1810', selectcolor='#F5EDE4').pack()

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите ФИО")
                return
            self.db.execute("UPDATE employees SET full_name=?, position=? WHERE id=?", (name, pos_var.get(), emp_id))
            messagebox.showinfo("Успех", "Данные обновлены")
            dialog.destroy()
            self.load_employees()

        tk.Button(dialog, text="Сохранить", bg='#2C1810', fg='white', padx=20, command=save).pack(pady=20)

    def delete_employee(self):
        if not self.is_admin:
            messagebox.showerror("Ошибка", "Недостаточно прав")
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите сотрудника")
            return
        item = self.tree.item(selected[0])
        emp_id = item['values'][0]
        emp_name = item['values'][1]

        if emp_name == self.user['full_name']:
            messagebox.showerror("Ошибка", "Нельзя удалить самого себя")
            return

        sales = self.db.fetch_one("SELECT COUNT(*) FROM sales WHERE employee_id = ?", (emp_id,))
        if sales and sales[0] > 0:
            messagebox.showerror("Ошибка", f"Нельзя удалить сотрудника {emp_name}\nУ него есть продажи")
            return

        if messagebox.askyesno("Подтверждение", f"Удалить сотрудника {emp_name}?"):
            self.db.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
            self.load_employees()
            messagebox.showinfo("Успех", "Сотрудник удален")


# ==================== ПРОВЕРКА И СОЗДАНИЕ БД ====================
def ensure_database():
    if not os.path.exists('shoe_shop.db'):
        create_database()


def create_database():
    conn = sqlite3.connect('shoe_shop.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        position TEXT DEFAULT 'продавец'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        brand TEXT,
        category TEXT,
        size INTEGER,
        color TEXT,
        material TEXT,
        season TEXT,
        purchase_price INTEGER,
        selling_price INTEGER,
        stock INTEGER DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shoe_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price INTEGER NOT NULL,
        total_price INTEGER NOT NULL,
        profit INTEGER NOT NULL,
        sale_date TEXT NOT NULL,
        FOREIGN KEY (shoe_id) REFERENCES shoes (id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
    )
    ''')

    employees = [
        ('Анна Иванова', 'продавец'),
        ('Екатерина Петрова', 'старший продавец'),
        ('Мария Сидорова', 'продавец'),
        ('Администратор', 'администратор')
    ]
    cursor.executemany("INSERT INTO employees (full_name, position) VALUES (?, ?)", employees)

    shoes = [
        ('Nike Air Max', 'Nike', 'кроссовки', 42, 'белый', 'текстиль', 'всесезон', 3000, 5500, 10),
        ('Adidas Ultraboost', 'Adidas', 'кроссовки', 43, 'черный', 'текстиль', 'всесезон', 4000, 7500, 8),
        ('ECCO Soft 7', 'ECCO', 'кеды', 41, 'бежевый', 'кожа', 'лето', 5000, 8900, 5),
        ('Timberland Classic', 'Timberland', 'ботинки', 44, 'коричневый', 'кожа', 'зима', 6000, 12000, 3),
        ('Clarks Desert Boot', 'Clarks', 'ботинки', 42, 'бежевый', 'замша', 'демисезон', 4500, 8500, 6)
    ]
    cursor.executemany('''
    INSERT INTO shoes (name, brand, category, size, color, material, season, purchase_price, selling_price, stock)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', shoes)

    conn.commit()
    conn.close()


class ShoeShopApp:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.db = Database()
        self.current_button = None  # Для отслеживания текущей нажатой кнопки

        self.root.title(f"👞 SHOE STORE — {user['full_name']} ({user['position']})")
        self.root.geometry("1400x800")
        self.root.configure(bg='#F5EDE4')

        self.is_admin = user['position'] == 'администратор'
        self.is_senior = user['position'] == 'старший продавец' or self.is_admin

        self.setup_styles()
        self.create_widgets()
        self.load_shoes()
        self.load_sales()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', background='#FFFFFF', foreground='#2C1810',
                        fieldbackground='#FFFFFF', borderwidth=0)
        style.configure('Treeview.Heading', background='#E8DCCC', foreground='#2C1810',
                        font=('Segoe UI', 10, 'bold'), borderwidth=0)

    def create_widgets(self):
        toolbar = tk.Frame(self.root, bg='#2C1810', height=50)
        toolbar.pack(fill=tk.X)

        # Создаем кнопки с сохранением ссылок
        self.btn_dashboard = tk.Button(toolbar, text="🏠 ГЛАВНАЯ", font=('Segoe UI', 11, 'bold'),
                                       bg='#C4A484', fg='white', padx=20, pady=5,
                                       command=lambda: self.on_button_click(self.show_dashboard, self.btn_dashboard))
        self.btn_dashboard.pack(side=tk.LEFT, padx=10, pady=5)

        self.btn_products = tk.Button(toolbar, text="👟 ТОВАРЫ", font=('Segoe UI', 11, 'bold'),
                                      bg='#C4A484', fg='white', padx=20, pady=5,
                                      command=lambda: self.on_button_click(self.show_products, self.btn_products))
        self.btn_products.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_sales = tk.Button(toolbar, text="💰 ПРОДАЖИ", font=('Segoe UI', 11, 'bold'),
                                   bg='#C4A484', fg='white', padx=20, pady=5,
                                   command=lambda: self.on_button_click(self.show_sales, self.btn_sales))
        self.btn_sales.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_analytics = tk.Button(toolbar, text="📊 АНАЛИТИКА", font=('Segoe UI', 11, 'bold'),
                                       bg='#C4A484', fg='white', padx=20, pady=5,
                                       command=lambda: self.on_button_click(self.show_analytics, self.btn_analytics))
        self.btn_analytics.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_employees = tk.Button(toolbar, text="👥 СОТРУДНИКИ", font=('Segoe UI', 11, 'bold'),
                                       bg='#C4A484', fg='white', padx=20, pady=5,
                                       command=lambda: self.on_button_click(self.open_employees, self.btn_employees))
        self.btn_employees.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_help = tk.Button(toolbar, text="📖 СПРАВКА", font=('Segoe UI', 11, 'bold'),
                                  bg='#C4A484', fg='white', padx=20, pady=5,
                                  command=lambda: self.on_button_click(self.show_help, self.btn_help))
        self.btn_help.pack(side=tk.LEFT, padx=5, pady=5)

        welcome_frame = tk.Frame(self.root, bg='#F5EDE4', height=60)
        welcome_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(welcome_frame, text=f"👋 Добро пожаловать, {self.user['full_name']}!",
                 font=('Segoe UI', 16, 'bold'), bg='#F5EDE4', fg='#2C1810').pack(side=tk.LEFT)
        tk.Label(welcome_frame, text=f"📅 {datetime.now().strftime('%d.%m.%Y')}",
                 font=('Segoe UI', 11), bg='#F5EDE4', fg='#8B5E3C').pack(side=tk.RIGHT)

        self.content_area = tk.Frame(self.root, bg='#F5EDE4')
        self.content_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.show_dashboard()
        # Устанавливаем начальную активную кнопку
        self.set_active_button(self.btn_dashboard)

    def on_button_click(self, command, button):
        """Обработчик нажатия на кнопку меню"""
        self.set_active_button(button)
        command()

    def set_active_button(self, active_btn):
        """Устанавливает активную кнопку (меняет цвет)"""
        buttons = [self.btn_dashboard, self.btn_products, self.btn_sales,
                   self.btn_analytics, self.btn_employees, self.btn_help]
        for btn in buttons:
            if btn == active_btn:
                btn.config(bg='#8B5E3C')  # Активный цвет
            else:
                btn.config(bg='#C4A484')  # Обычный цвет

    def clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def open_employees(self):
        EmployeesDialog(self.root, self.db, self.user)

    # ==================== ДАШБОРД ====================
    def show_dashboard(self):
        self.clear_content()
        stats_frame = tk.Frame(self.content_area, bg='#F5EDE4')
        stats_frame.pack(fill=tk.X, pady=(0, 20))

        total_shoes = self.db.fetch_one("SELECT COUNT(*) FROM shoes")[0]
        total_sales = self.db.fetch_one("SELECT SUM(total_price) FROM sales")[0] or 0
        total_profit = self.db.fetch_one("SELECT SUM(profit) FROM sales")[0] or 0
        low_stock = self.db.fetch_one("SELECT COUNT(*) FROM shoes WHERE stock < 5")[0]

        stats = [
            ("👟 Всего моделей", total_shoes, "#E8DCCC"),
            ("💰 Выручка", f"{total_sales:,.0f} ₽", "#D4B494"),
            ("📈 Прибыль", f"{total_profit:,.0f} ₽", "#C4A484"),
            ("⚠️ Низкий остаток", low_stock, "#2C1810")
        ]

        for label, value, color in stats:
            card = tk.Frame(stats_frame, bg=color, relief=tk.RAISED, bd=0)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            tk.Label(card, text=label, font=('Segoe UI', 11), bg=color, fg='#2C1810').pack(pady=(15, 5))
            tk.Label(card, text=str(value), font=('Segoe UI', 20, 'bold'), bg=color, fg='#2C1810').pack(pady=(0, 15))

    # ==================== ТОВАРЫ ====================
    def show_products(self):
        self.clear_content()

        search_frame = tk.Frame(self.content_area, bg='#FFFFFF', relief=tk.RAISED, bd=1)
        search_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(search_frame, text="🔍 НАЙТИ ТОВАР", font=('Segoe UI', 10, 'bold'),
                 bg='#FFFFFF', fg='#2C1810').pack(side=tk.LEFT, padx=15, pady=10)

        tk.Label(search_frame, text="Название:", bg='#FFFFFF', fg='#2C1810').pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=15)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="Бренд:", bg='#FFFFFF', fg='#2C1810').pack(side=tk.LEFT, padx=5)
        self.search_brand = tk.Entry(search_frame, width=12)
        self.search_brand.pack(side=tk.LEFT, padx=5)

        # НОВЫЕ ПОЛЯ: Категория и Размер
        tk.Label(search_frame, text="Категория:", bg='#FFFFFF', fg='#2C1810').pack(side=tk.LEFT, padx=5)
        categories = ['все', 'кроссовки', 'туфли', 'ботинки', 'кеды', 'сандалии', 'сапоги', 'мокасины', 'лоферы']
        self.search_category = ttk.Combobox(search_frame, values=categories, state='readonly', width=12)
        self.search_category.set('все')
        self.search_category.pack(side=tk.LEFT, padx=5)

        tk.Label(search_frame, text="Размер:", bg='#FFFFFF', fg='#2C1810').pack(side=tk.LEFT, padx=5)
        sizes = ['все'] + [str(s) for s in range(35, 47)]
        self.search_size = ttk.Combobox(search_frame, values=sizes, state='readonly', width=6)
        self.search_size.set('все')
        self.search_size.pack(side=tk.LEFT, padx=5)

        tk.Button(search_frame, text="ИСКАТЬ", bg='#C4A484', fg='white', padx=15,
                  command=self.search_shoes).pack(side=tk.LEFT, padx=10)
        tk.Button(search_frame, text="СБРОС", bg='#E8DCCC', fg='#2C1810', padx=15,
                  command=self.load_shoes).pack(side=tk.LEFT, padx=5)

        # НОВАЯ КНОПКА: Выгрузить в Excel (отфильтрованные товары)
        tk.Button(search_frame, text="📤 ВЫГРУЗИТЬ В EXCEL", bg='#2C1810', fg='white', padx=15,
                  command=self.export_filtered_shoes).pack(side=tk.LEFT, padx=10)

        if self.is_senior:
            tk.Button(search_frame, text="➕ ДОБАВИТЬ", bg='#2C1810', fg='white', padx=15,
                      command=self.add_shoe).pack(side=tk.RIGHT, padx=15)
            tk.Button(search_frame, text="🗑️ УДАЛИТЬ", bg='#8B0000', fg='white', padx=15,
                      command=self.delete_shoe).pack(side=tk.RIGHT, padx=5)

        table_frame = tk.Frame(self.content_area, bg='#F5EDE4')
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('id', 'name', 'brand', 'category', 'size', 'color', 'selling_price', 'stock', 'buy')
        self.products_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=25)

        headings = {
            'id': 'ID', 'name': 'НАЗВАНИЕ', 'brand': 'БРЕНД', 'category': 'КАТЕГОРИЯ',
            'size': 'РАЗМЕР', 'color': 'ЦВЕТ', 'selling_price': 'ЦЕНА (₽)', 'stock': 'ОСТАТОК', 'buy': 'КУПИТЬ'
        }

        for col, heading in headings.items():
            self.products_tree.heading(col, text=heading)
            if col == 'buy':
                self.products_tree.column(col, width=80)
            else:
                self.products_tree.column(col, width=100)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scroll.set)
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Обработчик клика для кнопки "Купить"
        self.products_tree.bind('<ButtonRelease-1>', self.on_tree_click)

        if self.is_senior:
            self.products_tree.bind('<Double-1>', self.edit_shoe)

        self.load_shoes()

    def get_filtered_shoes_query(self):
        """Возвращает SQL-запрос и параметры для поиска товаров"""
        name = self.search_entry.get().strip()
        brand = self.search_brand.get().strip()
        category = self.search_category.get()
        size = self.search_size.get()

        query = "SELECT id, name, brand, category, size, color, selling_price, stock FROM shoes WHERE stock > 0"
        params = []
        conditions = []

        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        if brand:
            conditions.append("brand LIKE ?")
            params.append(f"%{brand}%")
        if category and category != 'все':
            conditions.append("category = ?")
            params.append(category)
        if size and size != 'все':
            conditions.append("size = ?")
            params.append(int(size))

        if conditions:
            query += " AND " + " AND ".join(conditions)

        return query, params

    def export_filtered_shoes(self):
        """Выгрузка отфильтрованных товаров в Excel"""
        query, params = self.get_filtered_shoes_query()
        shoes = self.db.fetch_all(query, params)

        if not shoes:
            messagebox.showwarning("Предупреждение", "Нет товаров для выгрузки")
            return

        data = []
        for shoe in shoes:
            data.append({
                'ID': shoe['id'],
                'Название': shoe['name'],
                'Бренд': shoe['brand'],
                'Категория': shoe['category'] or '-',
                'Размер': shoe['size'],
                'Цвет': shoe['color'] or '-',
                'Цена продажи (₽)': shoe['selling_price'],
                'Остаток (шт)': shoe['stock']
            })

        df = pd.DataFrame(data)

        # Диалог выбора файла
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"товары_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if filename:
            df.to_excel(filename, index=False)
            messagebox.showinfo("Успех", f"✅ Выгружено {len(data)} товаров в файл:\n{filename}")
            os.startfile(filename)

    def on_tree_click(self, event):
        """Обработчик клика на таблицу товаров"""
        region = self.products_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.products_tree.identify_column(event.x)
            if column == '#9':  # Колонка "КУПИТЬ" (9-я колонка)
                item = self.products_tree.identify_row(event.y)
                if item:
                    shoe_id = self.products_tree.item(item, 'values')[0]
                    shoe = self.db.fetch_one("SELECT * FROM shoes WHERE id = ?", (shoe_id,))
                    if shoe:
                        self.quick_purchase(shoe)

    def quick_purchase(self, shoe):
        """Быстрая покупка товара"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🛒 Быстрая покупка")
        dialog.geometry("400x300")
        dialog.configure(bg='#F5EDE4')
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"Товар: {shoe['name']}", font=('Segoe UI', 12, 'bold'),
                 bg='#F5EDE4', fg='#2C1810').pack(pady=10)
        tk.Label(dialog, text=f"Бренд: {shoe['brand']}", font=('Segoe UI', 11),
                 bg='#F5EDE4', fg='#2C1810').pack()
        tk.Label(dialog, text=f"Цена: {shoe['selling_price']:,} ₽", font=('Segoe UI', 11),
                 bg='#F5EDE4', fg='#2C1810').pack()
        tk.Label(dialog, text=f"В наличии: {shoe['stock']} шт", font=('Segoe UI', 11),
                 bg='#F5EDE4', fg='#2C1810').pack()

        tk.Label(dialog, text="Количество:", font=('Segoe UI', 11),
                 bg='#F5EDE4', fg='#2C1810').pack(pady=10)
        qty_entry = tk.Entry(dialog, font=('Segoe UI', 11), width=10)
        qty_entry.pack()
        qty_entry.insert(0, "1")

        def purchase():
            try:
                qty = int(qty_entry.get())
                if qty <= 0:
                    messagebox.showerror("Ошибка", "Количество должно быть больше 0")
                    return
                if qty > shoe['stock']:
                    messagebox.showerror("Ошибка", f"Недостаточно товара. В наличии: {shoe['stock']}")
                    return

                total = shoe['selling_price'] * qty
                profit = (shoe['selling_price'] - shoe['purchase_price']) * qty
                date = datetime.now().strftime('%Y-%m-%d')

                self.db.execute(
                    "INSERT INTO sales (shoe_id, employee_id, quantity, unit_price, total_price, profit, sale_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (shoe['id'], self.user['id'], qty, shoe['selling_price'], total, profit, date))
                self.db.execute("UPDATE shoes SET stock = stock - ? WHERE id = ?", (qty, shoe['id']))

                messagebox.showinfo("Успех", f"✅ Покупка оформлена!\nСумма: {total:,.0f} ₽")
                dialog.destroy()
                self.load_shoes()
                self.load_sales()  # Обновляем историю продаж (новая запись будет сверху)
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное количество")

        tk.Button(dialog, text="💸 КУПИТЬ", bg='#2C1810', fg='white', font=('Segoe UI', 11, 'bold'),
                  padx=30, pady=10, command=purchase).pack(pady=20)
        tk.Button(dialog, text="Отмена", bg='#8B0000', fg='white', padx=20, command=dialog.destroy).pack()

    def load_shoes(self):
        if not hasattr(self, 'products_tree'):
            return
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        shoes = self.db.fetch_all(
            "SELECT id, name, brand, category, size, color, selling_price, stock FROM shoes WHERE stock > 0 ORDER BY id")
        for shoe in shoes:
            self.products_tree.insert('', tk.END, values=(
                shoe['id'], shoe['name'], shoe['brand'], shoe['category'] or '-',
                shoe['size'], shoe['color'], f"{shoe['selling_price']:,.0f}", shoe['stock'], "🛒 КУПИТЬ"
            ))

    def search_shoes(self):
        query, params = self.get_filtered_shoes_query()
        shoes = self.db.fetch_all(query, params)
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        for shoe in shoes:
            self.products_tree.insert('', tk.END, values=(
                shoe['id'], shoe['name'], shoe['brand'], shoe['category'] or '-',
                shoe['size'], shoe['color'], f"{shoe['selling_price']:,.0f}", shoe['stock'], "🛒 КУПИТЬ"
            ))
        if not shoes:
            messagebox.showinfo("Результат", "Товары не найдены")

    def delete_shoe(self):
        if not self.is_senior:
            messagebox.showerror("Ошибка", "Недостаточно прав")
            return
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите товар для удаления")
            return
        item = self.products_tree.item(selected[0])
        shoe_id = item['values'][0]
        shoe_name = item['values'][1]
        sales = self.db.fetch_one("SELECT COUNT(*) FROM sales WHERE shoe_id = ?", (shoe_id,))
        if sales and sales[0] > 0:
            messagebox.showerror("Ошибка", f"Нельзя удалить товар {shoe_name}\nПо нему есть продажи")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить товар {shoe_name}?"):
            self.db.execute("DELETE FROM shoes WHERE id = ?", (shoe_id,))
            self.load_shoes()
            messagebox.showinfo("Успех", "Товар удален")

    def add_shoe(self):
        self.open_shoe_dialog()

    def edit_shoe(self, event):
        selected = self.products_tree.selection()
        if selected:
            item = self.products_tree.item(selected[0])
            shoe_id = item['values'][0]
            shoe = self.db.fetch_one("SELECT * FROM shoes WHERE id = ?", (shoe_id,))
            self.open_shoe_dialog(shoe)

    def open_shoe_dialog(self, shoe=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("👞 ДОБАВЛЕНИЕ ТОВАРА" if not shoe else "✏️ РЕДАКТИРОВАНИЕ")
        dialog.geometry("500x650")
        dialog.configure(bg='#F5EDE4')
        dialog.transient(self.root)
        dialog.grab_set()

        categories = ['кроссовки', 'туфли', 'ботинки', 'кеды', 'сандалии', 'сапоги', 'мокасины', 'лоферы']
        sizes = [str(s) for s in range(35, 47)]
        colors = ['белый', 'черный', 'коричневый', 'бежевый', 'серый', 'синий', 'красный', 'зеленый']
        materials = ['кожа', 'замша', 'текстиль', 'нубук', 'искусственная кожа']
        seasons = ['лето', 'зима', 'демисезон', 'всесезон']

        fields = {}
        labels_combo = ['Категория', 'Размер', 'Цвет', 'Материал', 'Сезон']
        combo_values = {'Категория': categories, 'Размер': sizes, 'Цвет': colors, 'Материал': materials,
                        'Сезон': seasons}

        for label in labels_combo:
            frame = tk.Frame(dialog, bg='#F5EDE4')
            frame.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(frame, text=label + ":", width=15, anchor='w', bg='#F5EDE4', fg='#2C1810').pack(side=tk.LEFT)
            combo = ttk.Combobox(frame, values=combo_values[label], state='readonly', width=27)
            combo.pack(side=tk.LEFT, padx=5)
            if shoe:
                if label == 'Категория':
                    combo.set(shoe['category'] or '')
                elif label == 'Размер':
                    combo.set(str(shoe['size']) if shoe['size'] else '')
                elif label == 'Цвет':
                    combo.set(shoe['color'] or '')
                elif label == 'Материал':
                    combo.set(shoe['material'] or '')
                elif label == 'Сезон':
                    combo.set(shoe['season'] or '')
            fields[label] = combo

        labels_entry = ['Название', 'Бренд', 'Цена закупки', 'Цена продажи', 'Остаток']
        for label in labels_entry:
            frame = tk.Frame(dialog, bg='#F5EDE4')
            frame.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(frame, text=label + ":", width=15, anchor='w', bg='#F5EDE4', fg='#2C1810').pack(side=tk.LEFT)
            entry = tk.Entry(frame, width=30, bg='white')
            entry.pack(side=tk.LEFT, padx=5)
            if shoe:
                if label == 'Название':
                    entry.insert(0, shoe['name'] or '')
                elif label == 'Бренд':
                    entry.insert(0, shoe['brand'] or '')
                elif label == 'Цена закупки':
                    entry.insert(0, str(shoe['purchase_price'] or ''))
                elif label == 'Цена продажи':
                    entry.insert(0, str(shoe['selling_price'] or ''))
                elif label == 'Остаток':
                    entry.insert(0, str(shoe['stock'] or ''))
            fields[label] = entry

        def save():
            try:
                name = fields['Название'].get().strip()
                brand = fields['Бренд'].get().strip()
                if not name or not brand:
                    messagebox.showerror("Ошибка", "Название и бренд обязательны")
                    return
                category = fields['Категория'].get()
                size = int(fields['Размер'].get()) if fields['Размер'].get().isdigit() else 40
                color = fields['Цвет'].get()
                material = fields['Материал'].get()
                season = fields['Сезон'].get()
                purchase_price = int(fields['Цена закупки'].get()) if fields['Цена закупки'].get().isdigit() else 0
                selling_price = int(fields['Цена продажи'].get()) if fields['Цена продажи'].get().isdigit() else 0
                stock = int(fields['Остаток'].get()) if fields['Остаток'].get().isdigit() else 1
                if purchase_price <= 0 or purchase_price > 1000000:
                    messagebox.showerror("Ошибка", "Цена закупки должна быть от 1 до 1 000 000 ₽")
                    return
                if selling_price <= purchase_price:
                    messagebox.showerror("Ошибка", "Цена продажи должна быть больше цены закупки")
                    return
                if stock < 0 or stock > 500:
                    messagebox.showerror("Ошибка", "Остаток должен быть от 0 до 500 шт")
                    return
                if shoe:
                    self.db.execute("""
                        UPDATE shoes SET name=?, brand=?, category=?, size=?, color=?, material=?, season=?,
                        purchase_price=?, selling_price=?, stock=? WHERE id=?
                    """, (name, brand, category, size, color, material, season, purchase_price, selling_price, stock,
                          shoe['id']))
                    messagebox.showinfo("Успех", "Данные обновлены")
                else:
                    self.db.execute("""
                        INSERT INTO shoes (name, brand, category, size, color, material, season, purchase_price, selling_price, stock)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (name, brand, category, size, color, material, season, purchase_price, selling_price, stock))
                    messagebox.showinfo("Успех", "Товар добавлен")
                dialog.destroy()
                self.load_shoes()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        btn_frame = tk.Frame(dialog, bg='#F5EDE4')
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="💾 СОХРАНИТЬ", bg='#2C1810', fg='white', padx=20, command=save).pack(side=tk.LEFT,
                                                                                                       padx=10)
        tk.Button(btn_frame, text="❌ ОТМЕНА", bg='#8B0000', fg='white', padx=20, command=dialog.destroy).pack(
            side=tk.LEFT, padx=10)

    # ==================== ПРОДАЖИ ====================
    def show_sales(self):
        self.clear_content()
        left_panel = tk.Frame(self.content_area, bg='#F5EDE4')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        sell_frame = tk.LabelFrame(left_panel, text="🛒 ОФОРМЛЕНИЕ ПРОДАЖИ", font=('Segoe UI', 12, 'bold'), bg='#F5EDE4',
                                   fg='#2C1810', padx=20, pady=20)
        sell_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(sell_frame, text="ВЫБЕРИТЕ ТОВАР:", bg='#F5EDE4', fg='#2C1810', font=('Segoe UI', 10)).pack(anchor='w',
                                                                                                             pady=5)
        self.sell_combo = ttk.Combobox(sell_frame, state='readonly', width=50, font=('Segoe UI', 10))
        self.sell_combo.pack(fill=tk.X, pady=5)
        tk.Label(sell_frame, text="КОЛИЧЕСТВО:", bg='#F5EDE4', fg='#2C1810', font=('Segoe UI', 10)).pack(anchor='w',
                                                                                                         pady=5)
        self.sell_qty = tk.Entry(sell_frame, font=('Segoe UI', 11), width=15)
        self.sell_qty.pack(pady=5)
        tk.Button(sell_frame, text="💸 ОФОРМИТЬ ПРОДАЖУ", font=('Segoe UI', 11, 'bold'), bg='#2C1810', fg='white',
                  padx=20, pady=10, command=self.process_sale).pack(pady=20)
        if self.is_admin:
            tk.Button(sell_frame, text="🗑️ УДАЛИТЬ ПРОДАЖУ", font=('Segoe UI', 10), bg='#8B0000', fg='white', padx=20,
                      pady=8, command=self.delete_sale).pack(pady=5)

        right_panel = tk.Frame(self.content_area, bg='#F5EDE4')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        history_frame = tk.LabelFrame(right_panel, text="📜 ИСТОРИЯ ПРОДАЖ", font=('Segoe UI', 12, 'bold'), bg='#F5EDE4',
                                      fg='#2C1810', padx=10, pady=10)
        history_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('id', 'name', 'brand', 'employee', 'quantity', 'total', 'profit', 'date')
        self.sales_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=22)
        headings = {'id': '№', 'name': 'ТОВАР', 'brand': 'БРЕНД', 'employee': 'ПРОДАВЕЦ', 'quantity': 'КОЛ-ВО',
                    'total': 'СУММА (₽)', 'profit': 'ПРИБЫЛЬ (₽)', 'date': 'ДАТА'}
        for col, heading in headings.items():
            self.sales_tree.heading(col, text=heading)
            self.sales_tree.column(col, width=100)
        scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scroll.set)
        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_sell_items()
        self.load_sales()

    def load_sell_items(self):
        if not hasattr(self, 'sell_combo'):
            return
        shoes = self.db.fetch_all("SELECT id, name, brand, selling_price, stock FROM shoes WHERE stock > 0")
        items = [f"{s['name']} ({s['brand']}) — {s['selling_price']:,} ₽ (в наличии: {s['stock']})" for s in shoes]
        self.sell_combo['values'] = items
        if items:
            self.sell_combo.current(0)

    def process_sale(self):
        idx = self.sell_combo.current()
        shoes = self.db.fetch_all("SELECT id, purchase_price, selling_price, stock FROM shoes WHERE stock > 0")
        if idx >= len(shoes):
            return
        shoe = shoes[idx]
        qty = self.sell_qty.get().strip()
        if not qty:
            messagebox.showerror("Ошибка", "Введите количество")
            return
        if not qty.isdigit():
            messagebox.showerror("Ошибка", "Введите целое число")
            return
        qty_int = int(qty)
        if qty_int <= 0:
            messagebox.showerror("Ошибка", "Количество должно быть больше 0")
            return
        if qty_int > shoe['stock']:
            messagebox.showerror("Ошибка", f"Недостаточно товара. В наличии: {shoe['stock']}")
            return
        total = shoe['selling_price'] * qty_int
        profit = (shoe['selling_price'] - shoe['purchase_price']) * qty_int
        date = datetime.now().strftime('%Y-%m-%d')
        self.db.execute(
            "INSERT INTO sales (shoe_id, employee_id, quantity, unit_price, total_price, profit, sale_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (shoe['id'], self.user['id'], qty_int, shoe['selling_price'], total, profit, date))
        self.db.execute("UPDATE shoes SET stock = stock - ? WHERE id = ?", (qty_int, shoe['id']))
        messagebox.showinfo("Успех", f"👞 Продажа оформлена!\nСумма: {total:,.0f} ₽")
        self.sell_qty.delete(0, tk.END)
        self.load_sell_items()
        self.load_sales()

    def load_sales(self):
        if not hasattr(self, 'sales_tree'):
            return
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)
        # Сортировка по ID в обратном порядке (новые продажи сверху)
        sales = self.db.fetch_all("""
            SELECT s.id, sh.name, sh.brand, e.full_name, s.quantity, s.total_price, s.profit, s.sale_date
            FROM sales s
            JOIN shoes sh ON s.shoe_id = sh.id
            JOIN employees e ON s.employee_id = e.id
            ORDER BY s.id DESC
        """)
        for sale in sales:
            self.sales_tree.insert('', tk.END, values=(
                sale['id'], sale['name'], sale['brand'], sale['full_name'],
                sale['quantity'], f"{sale['total_price']:,.0f}", f"{sale['profit']:,.0f}", sale['sale_date']
            ))

    def delete_sale(self):
        if not hasattr(self, 'sales_tree'):
            return
        selected = self.sales_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите продажу")
            return
        if messagebox.askyesno("Подтверждение", "Удалить продажу?"):
            item = self.sales_tree.item(selected[0])
            sale_id = item['values'][0]
            self.db.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
            self.load_sales()
            messagebox.showinfo("Успех", "Продажа удалена")

    # ==================== АНАЛИТИКА ====================
    def show_analytics(self):
        self.clear_content()

        canvas = tk.Canvas(self.content_area, bg='#F5EDE4', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_area, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#F5EDE4')
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(scrollable_frame, bg='#F5EDE4')
        btn_frame.pack(pady=20)

        buttons = [
            ("📊 ABC-анализ", self.export_abc),
            ("📈 XYZ-анализ", self.export_xyz),
            ("🔄 ABC-XYZ анализ (совместный)", self.export_abc_xyz),
            ("🏷️ Отчет по брендам", self.report_by_brand),
            ("📋 Отчет по категориям", self.report_by_category),
            ("👟 Отчет по размерам", self.report_by_size),
            ("👥 Отчет по сотрудникам", self.report_by_employees),
            ("📦 Отчет об остатках моделей", self.report_by_stock),
            ("💰 Отчет по итогам выручки с удельным весом", self.report_revenue_with_weight)  # НОВЫЙ ОТЧЕТ
        ]

        for text, cmd in buttons:
            btn = tk.Button(btn_frame, text=text, font=('Segoe UI', 11, 'bold'),
                            bg='#2C1810', fg='white', padx=30, pady=10, cursor='hand2',
                            width=35, command=cmd)
            btn.pack(pady=5)

    def export_abc(self):
        sales_data = self.db.fetch_all("""
            SELECT sh.name, sh.brand, SUM(s.total_price) as total_revenue
            FROM sales s JOIN shoes sh ON s.shoe_id = sh.id
            GROUP BY sh.id
            ORDER BY total_revenue DESC
        """)

        total_all = sum(d['total_revenue'] for d in sales_data)
        data = []
        cumulative = 0

        for row in sales_data:
            product = f"{row['name']} ({row['brand']})"
            revenue = row['total_revenue']
            share = (revenue / total_all * 100) if total_all > 0 else 0
            cumulative += share

            if cumulative <= 80:
                abc_class = 'A'
            elif cumulative <= 95:
                abc_class = 'B'
            else:
                abc_class = 'C'

            data.append({
                'Товар': product,
                'Выручка (руб)': f"{revenue:,.0f}",
                'Удельный вес (%)': round(share, 2),
                'Совокупный %': round(cumulative, 2),
                'ABC класс': abc_class
            })

        df = pd.DataFrame(data)
        filename = f"abc_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        messagebox.showinfo("Экспорт", f"ABC-анализ сохранен в {filename}")
        os.startfile(filename)

    def export_xyz(self):
        sales_data = self.db.fetch_all("""
            SELECT sh.id, sh.name, sh.brand, 
                   strftime('%Y-%m', s.sale_date) as month,
                   SUM(s.quantity) as total_quantity
            FROM sales s 
            JOIN shoes sh ON s.shoe_id = sh.id
            WHERE s.sale_date >= date('now', '-6 months')
            GROUP BY sh.id, month
            ORDER BY sh.id, month
        """)
        if not sales_data:
            messagebox.showinfo("XYZ анализ", "Нет данных за последние 6 месяцев")
            return

        products_data = {}
        total_quantity_all = 0

        for row in sales_data:
            key = row['id']
            if key not in products_data:
                products_data[key] = {
                    'name': f"{row['name']} ({row['brand']})",
                    'revenues': []
                }
            products_data[key]['revenues'].append(row['total_quantity'])
            total_quantity_all += row['total_quantity']

        results = []
        for product_id, data in products_data.items():
            revenues = data['revenues']
            product_total = sum(revenues)
            share = (product_total / total_quantity_all * 100) if total_quantity_all > 0 else 0

            if len(revenues) >= 2 and sum(revenues) > 0:
                mean = sum(revenues) / len(revenues)
                variance = sum((x - mean) ** 2 for x in revenues) / len(revenues)
                std_dev = math.sqrt(variance)
                cv = (std_dev / mean) * 100
            else:
                cv = 100

            if cv <= 10:
                xyz_class = 'X'
            elif cv <= 25:
                xyz_class = 'Y'
            else:
                xyz_class = 'Z'

            results.append({
                'Товар': data['name'],
                'Объем продаж (шт)': product_total,
                'Удельный вес (%)': round(share, 2),
                'Кол-во месяцев': len(revenues),
                'Среднее кол-во': round(sum(revenues) / len(revenues), 2) if revenues else 0,
                'Коэффициент вариации (%)': round(cv, 2),
                'XYZ класс': xyz_class
            })

        class_order = {'X': 0, 'Y': 1, 'Z': 2}
        results.sort(key=lambda x: (class_order.get(x['XYZ класс'], 3), x['Коэффициент вариации (%)']))

        df = pd.DataFrame(results)
        filename = f"xyz_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)

        x_count = sum(1 for d in results if d['XYZ класс'] == 'X')
        y_count = sum(1 for d in results if d['XYZ класс'] == 'Y')
        z_count = sum(1 for d in results if d['XYZ класс'] == 'Z')

        messagebox.showinfo("Экспорт", f"✅ XYZ-анализ сохранен в {filename}\n\n"
                                       f"X (стабильные, CV ≤ 10%): {x_count}\n"
                                       f"Y (средние, CV ≤ 25%): {y_count}\n"
                                       f"Z (нестабильные, CV > 25%): {z_count}")
        os.startfile(filename)

    def export_abc_xyz(self):
        try:
            # ABC анализ
            abc_data = self.db.fetch_all("""
                SELECT sh.id, sh.name, sh.brand, SUM(s.total_price) as total_revenue
                FROM sales s
                JOIN shoes sh ON s.shoe_id = sh.id
                GROUP BY sh.id
                ORDER BY total_revenue DESC
            """)
            if not abc_data:
                messagebox.showinfo("ABC-XYZ анализ", "Нет данных для анализа")
                return

            total_all = sum(d['total_revenue'] for d in abc_data)
            cumulative = 0
            abc_classes = {}
            abc_shares = {}

            for row in abc_data:
                share = (row['total_revenue'] / total_all * 100) if total_all > 0 else 0
                cumulative += share
                if cumulative <= 70:
                    abc_class = 'A'
                elif cumulative <= 90:
                    abc_class = 'B'
                else:
                    abc_class = 'C'
                abc_classes[row['id']] = abc_class
                abc_shares[row['id']] = share

            # XYZ анализ
            xyz_sales = self.db.fetch_all("""
                SELECT sh.id, sh.name, sh.brand, 
                       strftime('%Y-%m', s.sale_date) as month,
                       SUM(s.quantity) as total_quantity
                FROM sales s 
                JOIN shoes sh ON s.shoe_id = sh.id
                WHERE s.sale_date >= date('now', '-6 months')
                GROUP BY sh.id, month
            """)

            products_data = {}
            total_quantity_all = 0

            for row in xyz_sales:
                key = row['id']
                if key not in products_data:
                    products_data[key] = []
                products_data[key].append(row['total_quantity'])
                total_quantity_all += row['total_quantity']

            xyz_classes = {}
            cv_values = {}
            xyz_shares = {}

            for pid, revenues in products_data.items():
                product_total = sum(revenues)
                share = (product_total / total_quantity_all * 100) if total_quantity_all > 0 else 0
                xyz_shares[pid] = share

                if len(revenues) >= 2 and sum(revenues) > 0:
                    mean = sum(revenues) / len(revenues)
                    variance = sum((x - mean) ** 2 for x in revenues) / len(revenues)
                    std_dev = math.sqrt(variance)
                    cv = (std_dev / mean) * 100
                else:
                    cv = 100
                cv_values[pid] = round(cv, 2)

                if cv <= 10:
                    xyz_class = 'X'
                elif cv <= 25:
                    xyz_class = 'Y'
                else:
                    xyz_class = 'Z'
                xyz_classes[pid] = xyz_class

            # Объединяем
            data = []
            for row in abc_data:
                product_name = f"{row['name']} ({row['brand']})"
                data.append({
                    'Товар': product_name,
                    'Выручка (руб)': round(row['total_revenue'], 2),
                    'Уд. вес ABC (%)': round(abc_shares.get(row['id'], 0), 2),
                    'ABC класс': abc_classes.get(row['id'], 'C'),
                    'Объем продаж (шт)': sum(products_data.get(row['id'], [0])),
                    'Уд. вес XYZ (%)': round(xyz_shares.get(row['id'], 0), 2),
                    'XYZ класс': xyz_classes.get(row['id'], 'Z'),
                    'CV (%)': cv_values.get(row['id'], 100)
                })

            abc_order = {'A': 0, 'B': 1, 'C': 2}
            xyz_order = {'X': 0, 'Y': 1, 'Z': 2}
            data.sort(key=lambda x: (abc_order.get(x['ABC класс'], 3), xyz_order.get(x['XYZ класс'], 3)))

            df = pd.DataFrame(data)
            filename = f"abc_xyz_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)

            abc_counts = {'A': 0, 'B': 0, 'C': 0}
            xyz_counts = {'X': 0, 'Y': 0, 'Z': 0}
            for item in data:
                abc_counts[item['ABC класс']] += 1
                xyz_counts[item['XYZ класс']] += 1

            messagebox.showinfo("Экспорт", f"✅ ABC-XYZ анализ сохранен в {filename}\n\n"
                                           f"📊 ABC: A={abc_counts['A']}, B={abc_counts['B']}, C={abc_counts['C']}\n"
                                           f"📊 XYZ: X={xyz_counts['X']}, Y={xyz_counts['Y']}, Z={xyz_counts['Z']}")
            os.startfile(filename)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при анализе: {str(e)}")

    def report_by_brand(self):
        data = self.db.fetch_all("""
            SELECT sh.brand, COUNT(s.id) as sales_count, SUM(s.total_price) as total_revenue
            FROM sales s
            JOIN shoes sh ON s.shoe_id = sh.id
            GROUP BY sh.brand
            ORDER BY total_revenue DESC
        """)
        total_revenue = sum(d['total_revenue'] for d in data)
        report_data = []
        for d in data:
            share = (d['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            report_data.append({
                'Бренд': d['brand'],
                'Кол-во продаж': d['sales_count'],
                'Выручка (руб)': round(d['total_revenue'], 2),
                'Удельный вес (%)': round(share, 2)
            })
        df = pd.DataFrame(report_data)
        filename = f"report_by_brand_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        messagebox.showinfo("Экспорт", f"Отчет по брендам сохранен в {filename}")
        os.startfile(filename)

    def report_by_category(self):
        data = self.db.fetch_all("""
            SELECT sh.category, COUNT(s.id) as sales_count, SUM(s.total_price) as total_revenue
            FROM sales s
            JOIN shoes sh ON s.shoe_id = sh.id
            GROUP BY sh.category
            ORDER BY total_revenue DESC
        """)
        total_revenue = sum(d['total_revenue'] for d in data)
        report_data = []
        for d in data:
            share = (d['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            report_data.append({
                'Категория': d['category'] or 'Не указана',
                'Кол-во продаж': d['sales_count'],
                'Выручка (руб)': round(d['total_revenue'], 2),
                'Удельный вес (%)': round(share, 2)
            })
        df = pd.DataFrame(report_data)
        filename = f"report_by_category_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        messagebox.showinfo("Экспорт", f"Отчет по категориям сохранен в {filename}")
        os.startfile(filename)

    def report_by_size(self):
        data = self.db.fetch_all("""
            SELECT sh.size, COUNT(s.id) as sales_count, SUM(s.total_price) as total_revenue
            FROM sales s
            JOIN shoes sh ON s.shoe_id = sh.id
            GROUP BY sh.size
            ORDER BY sh.size
        """)
        total_revenue = sum(d['total_revenue'] for d in data)
        report_data = []
        for d in data:
            share = (d['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            report_data.append({
                'Размер': d['size'],
                'Кол-во продаж': d['sales_count'],
                'Выручка (руб)': round(d['total_revenue'], 2),
                'Удельный вес (%)': round(share, 2)
            })
        df = pd.DataFrame(report_data)
        filename = f"report_by_size_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        messagebox.showinfo("Экспорт", f"Отчет по размерам сохранен в {filename}")
        os.startfile(filename)

    def report_by_employees(self):
        data = self.db.fetch_all("""
            SELECT e.full_name, e.position, COUNT(s.id) as sales_count, SUM(s.total_price) as total_revenue
            FROM employees e
            LEFT JOIN sales s ON e.id = s.employee_id
            GROUP BY e.id
            ORDER BY total_revenue DESC
        """)
        total_revenue = sum(d['total_revenue'] or 0 for d in data)
        report_data = []
        for d in data:
            share = ((d['total_revenue'] or 0) / total_revenue * 100) if total_revenue > 0 else 0
            report_data.append({
                'Сотрудник': d['full_name'],
                'Должность': d['position'],
                'Кол-во продаж': d['sales_count'] or 0,
                'Выручка (руб)': round(d['total_revenue'] or 0, 2),
                'Удельный вес (%)': round(share, 2)
            })
        df = pd.DataFrame(report_data)
        filename = f"report_by_employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        messagebox.showinfo("Экспорт", f"Отчет по сотрудникам сохранен в {filename}")
        os.startfile(filename)

    def report_by_stock(self):
        """Новый отчет: Остатки моделей обуви"""
        data = self.db.fetch_all("""
            SELECT name, brand, category, size, color, stock, selling_price
            FROM shoes
            WHERE stock > 0
            ORDER BY stock DESC, brand, name
        """)
        total_stock = sum(d['stock'] for d in data)
        report_data = []
        for d in data:
            share = (d['stock'] / total_stock * 100) if total_stock > 0 else 0
            report_data.append({
                'Название': d['name'],
                'Бренд': d['brand'],
                'Категория': d['category'] or '-',
                'Размер': d['size'],
                'Цвет': d['color'] or '-',
                'Остаток (шт)': d['stock'],
                'Цена продажи (₽)': f"{d['selling_price']:,}",
                'Удельный вес остатка (%)': round(share, 2)
            })
        df = pd.DataFrame(report_data)
        filename = f"stock_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        messagebox.showinfo("Экспорт",
                            f"📦 Отчет об остатках сохранен в {filename}\n\nВсего товаров на складе: {total_stock} шт")
        os.startfile(filename)

    def report_revenue_with_weight(self):
        """НОВЫЙ ОТЧЕТ: Итоги выручки с удельным весом"""
        # Общая выручка по всем продажам
        total_revenue = self.db.fetch_one("SELECT SUM(total_price) FROM sales")[0] or 0

        # Данные по продажам с группировкой по товарам
        data = self.db.fetch_all("""
            SELECT 
                sh.id,
                sh.name,
                sh.brand,
                sh.category,
                COUNT(s.id) as sales_count,
                SUM(s.quantity) as total_quantity,
                SUM(s.total_price) as total_revenue,
                SUM(s.profit) as total_profit
            FROM sales s
            JOIN shoes sh ON s.shoe_id = sh.id
            GROUP BY sh.id
            ORDER BY total_revenue DESC
        """)

        report_data = []
        cumulative_revenue = 0
        cumulative_profit = 0

        for d in data:
            revenue_share = (d['total_revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            cumulative_revenue += d['total_revenue']

            # Для прибыли считаем отдельно
            profit_share = (d['total_profit'] / total_revenue * 100) if total_revenue > 0 else 0
            cumulative_profit += d['total_profit']

            report_data.append({
                'ID товара': d['id'],
                'Название': d['name'],
                'Бренд': d['brand'],
                'Категория': d['category'] or '-',
                'Кол-во продаж': d['sales_count'],
                'Кол-во единиц': d['total_quantity'],
                'Выручка (руб)': round(d['total_revenue'], 2),
                'Уд. вес выручки (%)': round(revenue_share, 2),
                'Кумулятивная выручка (%)': round(
                    (cumulative_revenue / total_revenue * 100) if total_revenue > 0 else 0, 2),
                'Прибыль (руб)': round(d['total_profit'], 2),
                'Уд. вес прибыли (%)': round(profit_share, 2),
                'Кумулятивная прибыль (%)': round((cumulative_profit / total_revenue * 100) if total_revenue > 0 else 0,
                                                  2)
            })

        # Добавляем итоговую строку
        report_data.append({
            'ID товара': 'ИТОГО',
            'Название': '',
            'Бренд': '',
            'Категория': '',
            'Кол-во продаж': sum(d['sales_count'] for d in data),
            'Кол-во единиц': sum(d['total_quantity'] for d in data),
            'Выручка (руб)': round(total_revenue, 2),
            'Уд. вес выручки (%)': 100.0,
            'Кумулятивная выручка (%)': 100.0,
            'Прибыль (руб)': round(sum(d['total_profit'] for d in data), 2),
            'Уд. вес прибыли (%)': 100.0,
            'Кумулятивная прибыль (%)': 100.0
        })

        df = pd.DataFrame(report_data)
        filename = f"revenue_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        messagebox.showinfo("Экспорт",
                            f"💰 Отчет по выручке сохранен в {filename}\n\n"
                            f"Общая выручка: {total_revenue:,.0f} ₽\n"
                            f"Всего товаров: {len(data)}")
        os.startfile(filename)

    # ==================== СПРАВКА ====================
    def show_help(self):
        self.clear_content()

        help_frame = tk.Frame(self.content_area, bg='#FFFFFF', relief=tk.RAISED, bd=1)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=30)

        tk.Label(help_frame, text="📖 СПРАВКА", font=('Segoe UI', 20, 'bold'),
                 bg='#FFFFFF', fg='#2C1810').pack(pady=20)

        # Три кнопки в разделе справки
        btn_frame = tk.Frame(help_frame, bg='#FFFFFF')
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="📘 Руководство пользователя", font=('Segoe UI', 12),
                  bg='#2C1810', fg='white', padx=25, pady=12, width=25,
                  command=self.show_user_guide).pack(side=tk.LEFT, padx=15)

        tk.Button(btn_frame, text="ℹ️ О программе", font=('Segoe UI', 12),
                  bg='#2C1810', fg='white', padx=25, pady=12, width=25,
                  command=self.show_about).pack(side=tk.LEFT, padx=15)

        tk.Button(btn_frame, text="👨‍💻 О разработчике", font=('Segoe UI', 12),
                  bg='#2C1810', fg='white', padx=25, pady=12, width=25,
                  command=self.show_developer).pack(side=tk.LEFT, padx=15)

        # Область для отображения содержимого
        self.help_content = tk.Frame(help_frame, bg='#F5EDE4')
        self.help_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # По умолчанию показываем руководство пользователя
        self.show_user_guide()

    def show_user_guide(self):
        self.clear_help_content()
        text_widget = tk.Text(self.help_content, wrap=tk.WORD, bg='#F5EDE4', fg='#2C1810',
                              font=('Segoe UI', 11), padx=20, pady=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        guide_text = """
👞 SHOE STORE - РУКОВОДСТВО ПОЛЬЗОВАТЕЛЯ
============================================

1. 👤 РОЛИ ПОЛЬЗОВАТЕЛЕЙ
------------------------
• Администратор - полный доступ ко всем функциям
• Старший продавец - управление товарами и продажами
• Продавец - только оформление продаж

2. 👟 ТОВАРЫ
-----------
• Поиск по названию, бренду, категории и размеру
• Кнопка "КУПИТЬ" для быстрого оформления покупки
• Выгрузка отфильтрованных товаров в Excel
• Добавление/редактирование/удаление (админ и старший продавец)
• Двойной клик для редактирования

3. 💰 ПРОДАЖИ
------------
• Выберите товар из списка
• Укажите количество
• Нажмите "ОФОРМИТЬ ПРОДАЖУ"
• История продаж отсортирована по № (новые сверху)

4. 📊 ОТЧЕТЫ
-----------
• ABC-анализ - по выручке (A,B,C) с удельным весом
• XYZ-анализ - по стабильности (X,Y,Z) с удельным весом
• ABC-XYZ анализ - совместный с удельным весом
• Отчеты по брендам, категориям, размерам, сотрудникам
• Отчет об остатках моделей
• Отчет по итогам выручки с удельным весом

5. 👥 СОТРУДНИКИ
---------------
• Добавление/редактирование/удаление (только администратор)

============================================
        """
        text_widget.insert('1.0', guide_text)
        text_widget.config(state=tk.DISABLED)

    def show_about(self):
        self.clear_help_content()
        about_frame = tk.Frame(self.help_content, bg='#F5EDE4')
        about_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(about_frame, text="👞 SHOE STORE", font=('Segoe UI', 24, 'bold'),
                 bg='#F5EDE4', fg='#2C1810').pack(pady=(40, 10))
        tk.Label(about_frame, text="Обувной магазин", font=('Segoe UI', 14),
                 bg='#F5EDE4', fg='#8B5E3C').pack(pady=5)
        tk.Label(about_frame, text="Версия: 3.0", font=('Segoe UI', 12),
                 bg='#F5EDE4', fg='#2C1810').pack(pady=5)
        tk.Label(about_frame, text=f"Пользователь: {self.user['full_name']}", font=('Segoe UI', 12),
                 bg='#F5EDE4', fg='#2C1810').pack(pady=5)
        tk.Label(about_frame, text=f"Должность: {self.user['position']}", font=('Segoe UI', 12),
                 bg='#F5EDE4', fg='#2C1810').pack(pady=5)
        tk.Label(about_frame, text="\nРазработано в рамках учебной практики", font=('Segoe UI', 11, 'italic'),
                 bg='#F5EDE4', fg='#8B5E3C').pack(pady=20)

    def show_developer(self):
        self.clear_help_content()
        dev_frame = tk.Frame(self.help_content, bg='#F5EDE4')
        dev_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(dev_frame, text="👨‍💻 О РАЗРАБОТЧИКЕ", font=('Segoe UI', 20, 'bold'),
                 bg='#F5EDE4', fg='#2C1810').pack(pady=(40, 20))

        info = """
        Разработчик: Студент группы ИС-944

        Проект: SHOE STORE - система управления обувным магазином

        Технологии:
        • Python 3.x
        • Tkinter (GUI)
        • SQLite (база данных)
        • Pandas (экспорт отчетов в Excel)

        Функциональность:
        • Управление товарами и сотрудниками
        • Оформление и история продаж
        • Аналитические отчеты (ABC, XYZ, ABC-XYZ)
        • Экспорт данных в Excel

        Дата разработки: 2026
        """

        text_widget = tk.Text(dev_frame, wrap=tk.WORD, bg='#F5EDE4', fg='#2C1810',
                              font=('Segoe UI', 12), padx=30, pady=20, height=15)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=20)
        text_widget.insert('1.0', info)
        text_widget.config(state=tk.DISABLED)

    def clear_help_content(self):
        for widget in self.help_content.winfo_children():
            widget.destroy()


# ==================== ОКНО АВТОРИЗАЦИИ ====================
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("👞 SHOE STORE — вход")
        self.root.geometry("450x400")
        self.root.configure(bg='#F5EDE4')

        ensure_database()

        self.db = Database()
        self.root.eval('tk::PlaceWindow . center')

        main_frame = tk.Frame(self.root, bg='#FFFFFF', relief=tk.RAISED, bd=1)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        tk.Label(main_frame, text="👞 SHOE STORE", font=('Segoe UI', 26, 'bold'),
                 bg='#FFFFFF', fg='#2C1810').pack(pady=(30, 5))
        tk.Label(main_frame, text="Обувной магазин", font=('Segoe UI', 12),
                 bg='#FFFFFF', fg='#8B5E3C').pack(pady=(0, 30))

        tk.Label(main_frame, text="Выберите сотрудника", font=('Segoe UI', 12),
                 bg='#FFFFFF', fg='#2C1810').pack()

        employees = self.db.fetch_all("SELECT id, full_name, position FROM employees ORDER BY id")
        self.employee_names = [f"{e['full_name']} ({e['position']})" for e in employees]
        self.employee_ids = [e['id'] for e in employees]

        self.combo = ttk.Combobox(main_frame, values=self.employee_names, width=35,
                                  state='readonly', font=('Segoe UI', 11))
        self.combo.pack(pady=15)

        if self.employee_names:
            self.combo.current(0)

        tk.Button(main_frame, text="👞 ВОЙТИ 👞", font=('Segoe UI', 12, 'bold'),
                  bg='#2C1810', fg='white', padx=25, pady=8, command=self.login).pack(pady=20)

        tk.Button(main_frame, text="ВЫХОД", font=('Segoe UI', 10),
                  bg='#E8DCCC', fg='#2C1810', padx=20, pady=5, command=self.root.quit).pack()

    def login(self):
        if not self.combo.get():
            messagebox.showwarning("Ошибка", "Выберите сотрудника")
            return

        idx = self.combo.current()
        employee_id = self.employee_ids[idx]
        user = self.db.fetch_one("SELECT * FROM employees WHERE id = ?", (employee_id,))

        if user:
            self.root.destroy()
            new_root = tk.Tk()
            new_root.configure(bg='#F5EDE4')
            app = ShoeShopApp(new_root, user)
            new_root.mainloop()
        else:
            messagebox.showerror("Ошибка", "Пользователь не найден")


# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='#F5EDE4')
    login = LoginWindow(root)
    root.mainloop()