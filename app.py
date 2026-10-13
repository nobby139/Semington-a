import os
import psycopg2
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def get_db_connection():
    """Connect to Neon DB using your connection string or environment variable."""
    # Replace the string below with your actual Neon connection string if not using environment variables
    conn = psycopg2.connect(
        os.environ.get("DATABASE_URL", "postgresql://your_user:your_password@your_neon_host/your_dbname")
    )
    return conn

@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')

@app.route('/fixtures')
def fixtures():
    return render_template('fixtures.html')

@app.route('/scoreboard')
def scoreboard():
    return render_template('scoreboard.html')

@app.route('/match-results')
@app.route('/results')
def match_results():
    return render_template('results.html')

@app.route('/to-catch')
@app.route('/tocatch')
def to_catch():
    return render_template('tocatch.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/rules')
def rules():
    return render_template('rules.html')

# --- New Season Rates & Fines Page Route ---
@app.route('/season-rates')
def season_rates():
    return render_template('season-rates.html')

# --- Neon DB API Routes for Rates & Fines ---
@app.route('/api/rates', methods=['GET'])
def get_rates():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, rate_item, amount, match_type, effective_from, effective_to 
        FROM season_rates 
        ORDER BY effective_from DESC, rate_item ASC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    rates = []
    for r in rows:
        rates.append({
            'id': r[0],
            'rate_item': r[1],
            'amount': float(r[2]),
            'match_type': r[3],
            'effective_from': r[4].strftime('%Y-%m-%d') if r[4] else None,
            'effective_to': r[5].strftime('%Y-%m-%d') if r[5] else None
        })
    return jsonify(rates)

@app.route('/api/rates/add', methods=['POST'])
def add_rate():
    data = request.json
    rate_item = data.get('rate_item')
    amount = data.get('amount')
    match_type = data.get('match_type', 'All')
    effective_from = data.get('effective_from')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Close off the previous active rate for this item and match type
        cur.execute("""
            UPDATE season_rates 
            SET effective_to = %s 
            WHERE rate_item = %s 
              AND match_type = %s 
              AND effective_to IS NULL;
        """, (effective_from, rate_item, match_type))

        # Insert the new rate rule
        cur.execute("""
            INSERT INTO season_rates (rate_item, amount, match_type, effective_from)
            VALUES (%s, %s, %s, %s);
        """, (rate_item, amount, match_type, effective_from))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Rate saved successfully!'}), 200

    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
