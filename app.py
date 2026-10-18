# ==========================================================================
# IMPORTS & INITIALIZATION
# ==========================================================================
import os
import psycopg2
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Required for flash messages


# ==========================================================================
# DATABASE CONFIGURATION & CONNECTION
# ==========================================================================
def get_db_connection():
    """Connect to Neon DB using your connection string or environment variable."""
    conn = psycopg2.connect(
        os.environ.get("DATABASE_URL", "postgresql://your_user:your_password@your_neon_host/your_dbname")
    )
    return conn


# ==========================================================================
# CORE WEBSITE & PAGE ROUTES
# ==========================================================================
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


# ==========================================================================
# SEASON RATES & FINES ROUTES
# ==========================================================================
@app.route('/season-rates')
def season_rates():
    return render_template('season-rates.html')

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
    
    rates_list = [{
        "id": r[0], "rate_item": r[1], "amount": float(r[2]), 
        "match_type": r[3], "effective_from": str(r[4]), "effective_to": str(r[5])
    } for r in rows]
    return jsonify(rates_list)


# ==========================================================================
# TEAM & PLAYER MANAGEMENT ROUTES
# ==========================================================================
@app.route('/manage-teams', methods=['GET', 'POST'])
def manage_teams():
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Handle adding a new team
        if action == 'add_team':
            team_name = request.form.get('team_name')
            division = request.form.get('division')
            try:
                cur.execute(
                    "INSERT INTO teams (team_name, division) VALUES (%s, %s)",
                    (team_name, division)
                )
                conn.commit()
                flash(f"Team '{team_name}' added to {division} successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error adding team: {e}", "danger")
            
        # Handle adding a new player to a team
        elif action == 'add_player':
            player_name = request.form.get('player_name')
            team_id = request.form.get('team_id')
            try:
                cur.execute(
                    "INSERT INTO players (player_name, team_id) VALUES (%s, %s)",
                    (player_name, team_id)
                )
                conn.commit()
                flash(f"Player '{player_name}' added to team successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error adding player: {e}", "danger")
            
        cur.close()
        conn.close()
        return redirect(url_for('manage_teams'))

    # Fetch existing teams for dropdown selection
    cur.execute("SELECT id, team_name, division FROM teams ORDER BY division, team_name;")
    teams = cur.fetchall()
    
    # Fetch existing players for roster overview table
    cur.execute("""
        SELECT p.id, p.player_name, t.team_name, t.division 
        FROM players p 
        JOIN teams t ON p.team_id = t.id 
        ORDER BY t.division, t.team_name, p.player_name;
    """)
    players = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('manage_teams.html', teams=teams, players=players)


# ==========================================================================
# APPLICATION EXECUTION ENTRY POINT
# ==========================================================================
if __name__ == '__main__':
    app.run(debug=True)
