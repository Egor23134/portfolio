import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('shoe_shop.db')
cursor = conn.cursor()

# Удаляем старые таблицы
cursor.execute('DROP TABLE IF EXISTS sales')
cursor.execute('DROP TABLE IF EXISTS shoes')
cursor.execute('DROP TABLE IF EXISTS employees')

print("✅ Старые таблицы удалены")

# Таблица сотрудников
cursor.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    position TEXT DEFAULT 'продавец'
)
''')

# Таблица обуви
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

# Таблица продаж
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

print("✅ Таблицы созданы")

# Добавляем сотрудников
employees = [
    ('Анна Иванова', 'продавец'),
    ('Екатерина Петрова', 'старший продавец'),
    ('Мария Сидорова', 'продавец'),
    ('Администратор', 'администратор')
]

cursor.executemany("INSERT INTO employees (full_name, position) VALUES (?, ?)", employees)
print("✅ Добавлено 4 сотрудника")

# Генерация 120+ пар обуви
brands = ['Nike', 'Adidas', 'Puma', 'Reebok', 'New Balance', 'ECCO', 'Clarks', 'Timberland', 'Skechers', 'Crocs']
categories = ['кроссовки', 'туфли', 'ботинки', 'сандалии', 'сапоги', 'мокасины', 'лоферы', 'кеды']
colors = ['белый', 'черный', 'коричневый', 'бежевый', 'серый', 'синий', 'красный', 'зеленый']
materials = ['кожа', 'замша', 'текстиль', 'нубук', 'искусственная кожа']
seasons = ['лето', 'зима', 'демисезон', 'всесезон']

shoe_names = [
    'Air Max', 'Classic Leather', 'Ultraboost', 'Superstar', 'Gazelle', 'Stan Smith',
    'Chuck Taylor', 'Old Skool', 'Authentic', 'Gel-Kayano', 'Kayano', 'GT-2000',
    '574', '327', '990', 'Fresh Foam', 'M670', 'M1500', 'Celeris', 'Biom',
    'Desert Boot', 'Wallabee', 'Bushacre', 'Clarkson', 'Originals', 'Court Yard',
    'Hiking Boot', 'Waterproof', 'Chelsea', 'Loafer', 'Penny', 'Tassel', 'Monk Strap'
]

shoes = []
for i in range(130):
    name = random.choice(shoe_names) + " " + str(random.randint(1, 99))
    brand = random.choice(brands)
    category = random.choice(categories)
    size = random.choice([36, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    color = random.choice(colors)
    material = random.choice(materials)
    season = random.choice(seasons)
    purchase_price = random.randint(500, 5000)
    selling_price = purchase_price + random.randint(200, 2500)
    stock = random.randint(0, 25)
    shoes.append((name, brand, category, size, color, material, season, purchase_price, selling_price, stock))

cursor.executemany('''
INSERT INTO shoes (name, brand, category, size, color, material, season, purchase_price, selling_price, stock)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', shoes)

print(f"✅ Добавлено {len(shoes)} пар обуви")

# Генерация продаж
cursor.execute("SELECT id FROM employees")
employee_ids = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT id, purchase_price, selling_price FROM shoes")
shoe_data = cursor.fetchall()

sales = []
today = datetime.now()
for day in range(1, 60):
    date = (today - timedelta(days=day)).strftime('%Y-%m-%d')
    for _ in range(random.randint(0, 3)):
        employee_id = random.choice(employee_ids)
        shoe = random.choice(shoe_data)
        shoe_id, purchase, selling = shoe
        quantity = random.randint(1, 3)
        total_price = selling * quantity
        profit = (selling - purchase) * quantity
        sales.append((shoe_id, employee_id, quantity, selling, total_price, profit, date))

cursor.executemany('''
INSERT INTO sales (shoe_id, employee_id, quantity, unit_price, total_price, profit, sale_date)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', sales)

print(f"✅ Добавлено {len(sales)} продаж")

# Обновляем остатки
for sale in sales:
    cursor.execute("UPDATE shoes SET stock = stock - ? WHERE id = ?", (sale[2], sale[0]))

conn.commit()

# Статистика
cursor.execute("SELECT COUNT(*) FROM shoes")
print(f"👟 Обуви в базе: {cursor.fetchone()[0]} пар")
cursor.execute("SELECT COUNT(*) FROM sales")
print(f"💰 Продаж: {cursor.fetchone()[0]}")

conn.close()
print("\n✅ База данных 'shoe_shop.db' успешно создана!")
