from flask import Flask, render_template_string, request, redirect
import sqlite3
import os

app = Flask(__name__)

# إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect('fuel_system.db')
    conn.execute('CREATE TABLE IF NOT EXISTS tanks (id INTEGER PRIMARY KEY, name TEXT, current_level INTEGER)')
    conn.execute('CREATE TABLE IF NOT EXISTS operations (id INTEGER PRIMARY KEY, tank_name TEXT, amount INTEGER, user_name TEXT, date_time TEXT)')
    
    check = conn.execute('SELECT count(*) FROM tanks').fetchone()
    if check[0] == 0:
        conn.execute("INSERT INTO tanks (name, current_level) VALUES ('الخزان الرئيسي', 5000)")
        conn.execute("INSERT INTO tanks (name, current_level) VALUES ('الخزان الاحتياطي', 2000)")
    conn.commit()
    conn.close()

# قالب HTML مدمج (لكي لا تحتاج لمجلد templates حالياً)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>نظام إدارة الوقود</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="container py-4 bg-light">
    <h2 class="text-center mb-4">نظام مراقبة مخزون الوقود</h2>
    <div class="row mb-5">
        {% for tank in tanks %}
        <div class="col-md-6">
            <div class="card text-center shadow-sm">
                <div class="card-body">
                    <h5>{{ tank['name'] }}</h5>
                    <p class="display-6 text-primary">{{ tank['current_level'] }} لتر</p>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="card p-4 shadow-sm mb-4">
        <h4>تسجيل سحب جديد</h4>
        <form action="/withdraw" method="post" class="row g-3">
            <div class="col-md-4">
                <select name="tank_id" class="form-select" required>
                    {% for tank in tanks %}<option value="{{ tank['id'] }}">{{ tank['name'] }}</option>{% endfor %}
                </select>
            </div>
            <div class="col-md-3">
                <input type="number" name="amount" class="form-control" placeholder="الكمية" required>
            </div>
            <div class="col-md-3">
                <input type="text" name="user_name" class="form-control" placeholder="اسم الموظف" required>
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-success w-100">تسجيل</button>
            </div>
        </form>
    </div>

    <div class="card p-4 shadow-sm">
        <h4>آخر العمليات</h4>
        <table class="table table-hover">
            <thead><tr><th>الموظف</th><th>الخزان</th><th>الكمية</th><th>التاريخ</th></tr></thead>
            <tbody>
                {% for op in operations %}
                <tr><td>{{ op['user_name'] }}</td><td>{{ op['tank_name'] }}</td><td>{{ op['amount'] }}</td><td>{{ op['date_time'] }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect('fuel_system.db')
    conn.row_factory = sqlite3.Row
    tanks = conn.execute('SELECT * FROM tanks').fetchall()
    operations = conn.execute('SELECT * FROM operations ORDER BY id DESC LIMIT 5').fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, tanks=tanks, operations=operations)

@app.route('/withdraw', methods=['POST'])
def withdraw():
    tank_id = request.form['tank_id']
    amount = int(request.form['amount'])
    user_name = request.form['user_name']
    
    conn = sqlite3.connect('fuel_system.db')
    conn.row_factory = sqlite3.Row
    tank = conn.execute('SELECT * FROM tanks WHERE id = ?', (tank_id,)).fetchone()
    
    if tank and tank['current_level'] >= amount:
        new_level = tank['current_level'] - amount
        conn.execute('UPDATE tanks SET current_level = ? WHERE id = ?', (new_level, tank_id))
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.execute('INSERT INTO operations (tank_name, amount, user_name, date_time) VALUES (?, ?, ?, ?)', 
                     (tank['name'], amount, user_name, now))
        conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
