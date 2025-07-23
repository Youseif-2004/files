from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "activation_codes.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activation_codes (
            code TEXT PRIMARY KEY,
            used INTEGER DEFAULT 0,
            device_id TEXT
        )
    ''')
    return conn

@app.route('/activate', methods=['POST'])
def activate():
    data = request.json
    code = data.get('code')
    device_id = data.get('device_id')
    if not code or not device_id:
        return jsonify({'success': False, 'error': 'code and device_id required'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT used, device_id FROM activation_codes WHERE code=?', (code,))
    row = cur.fetchone()
    if not row:
        return jsonify({'success': False, 'error': 'invalid_code'}), 404
    used, db_device_id = row
    if used == 0:
        cur.execute('UPDATE activation_codes SET used=1, device_id=? WHERE code=?', (device_id, code))
        conn.commit()
        return jsonify({'success': True, 'message': 'activated'})
    elif db_device_id == device_id:
        return jsonify({'success': True, 'message': 'already_activated'})
    else:
        return jsonify({'success': False, 'error': 'code_used_on_another_device'}), 403

@app.route('/add_codes', methods=['POST'])
def add_codes():
    codes = request.json.get('codes', [])
    if not codes or not isinstance(codes, list):
        return jsonify({'success': False, 'error': 'codes list required'}), 400
    conn = get_db()
    cur = conn.cursor()
    added = 0
    for code in codes:
        try:
            cur.execute('INSERT INTO activation_codes (code, used, device_id) VALUES (?, 0, NULL)', (code,))
            added += 1
        except Exception:
            continue
    conn.commit()
    return jsonify({'success': True, 'added': added})

@app.route('/')
def home():
    return 'Activation API is running!'

if __name__ == '__main__':
    app.run(debug=True)