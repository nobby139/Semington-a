# ==========================================================================
# IMPORTS & INITIALIZATION
# ==========================================================================
import os
import psycopg2
import datetime
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    session,
)
from dotenv import load_dotenv

# Load environment variables from your local hidden .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = (
    "your_secret_key_here"  # Required for flash messages and admin sessions
)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Securely fetch your Neon connection string
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Admin Authorization Decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({"message": "Unauthorized. Admin access required."}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Login & Auth Routes ---
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password')
    
    expected_password = os.getenv("ADMIN_PASSWORD")
    
    if password and password == expected_password: 
        session['is_admin'] = True
        return jsonify({"success": True, "message": "Logged in successfully"})
    
    return jsonify({"success": False, "message": "Incorrect password"}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out"})

@app.route('/api/auth/status')
def auth_status():
    return jsonify({"is_admin": session.get('is_admin', False)})


# ==========================================================================
# DATABASE CONFIGURATION & CONNECTION
# ==========================================================================
def get_db_connection():
    """Connect to Neon DB using your connection string."""
    conn = psycopg2.connect(
        os.environ.get(
            "DATABASE_URL", 
            "postgresql://neondb_owner:npg_kvrxNPF3B4cC@ep-frosty-star-zapw57pu.c-2.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        )
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


# ==========================================================================
# MATCH RESULTS ROUTE (DB CONNECTED)
# ==========================================================================
@app.route('/match-results')
@app.route('/results')
def match_results():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                match_id,
                match_details,
                home_away,
                player_name,
                total_score,
                position,
                ducks,
                spares,
                legs_won,
                top_score,
                league_avg
            FROM match_results
            ORDER BY match_id DESC;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        results = [{
            "match_id": r[0],
            "details": r[1],
            "home_away": r[2],
            "player_name": r[3],
            "total_score": r[4],
            "position": r[5],
            "ducks": r[6],
            "spares": r[7],
            "legs_won": r[8],
            "top_score": r[9],
            "league_avg": float(r[10]) if r[10] is not None else 0.0
        } for r in rows]

        return render_template(
            'match_results.html', 
            results=results, 
            rows_count=len(results),
            matches_count=len(set(r['match_id'] for r in results)),
            last_updated="Sunday, 26 April 2026 at 09:21"
        )
    except Exception as e:
        print("Database error in match_results:", e)
        return render_template('match_results.html', results=[], rows_count=0)


# ==========================================================================
# TO CATCH ROUTE (DB CONNECTED WITH DYNAMIC MATH)
# ==========================================================================
@app.route('/to-catch')
@app.route('/tocatch')
def to_catch():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                player_name,
                total_pins,
                games_played
            FROM player_stats
            WHERE is_league = TRUE;
        """)
        raw_players = cur.fetchall()
        cur.close()
        conn.close()
        
        players_list = []
        for r in raw_players:
            p_name = r[0]
            t_pins = r[1] or 0
            g_played = r[2] or 0
            avg = round(t_pins / g_played, 2) if g_played > 0 else 0.0
            players_list.append({
                "player_name": p_name,
                "total_pins": t_pins,
                "games_played": g_played,
                "avg": avg
            })
            
        players_list.sort(key=lambda x: x['avg'], reverse=True)
        
        players_data = []
        for i, row in enumerate(players_list):
            player_dict = row.copy()
            if i == 0:
                player_dict["pins_behind"] = 0
            else:
                target_avg = players_data[i - 1]["avg"]
                current_games = player_dict["games_played"]
                current_pins = player_dict["total_pins"]
                needed = (target_avg * current_games) - current_pins
                player_dict["pins_behind"] = max(0, int(needed + 1))
                
            players_data.append(player_dict)

        return render_template(
            'to_catch.html', 
            players_data=players_data,
            last_updated="Sunday, 26 April 2026 at 09:21"
        )
    except Exception as e:
        print("Database error in to_catch:", e)
        return render_template('to_catch.html', players_data=[])

# =====================================================================
# GALLERY ROUTE
# =====================================================================
@app.route('/gallery')
def gallery():
    gallery_items = [
        {
            "filename": "2024 - 2025 Division 1 Winners Cup.JPG",
            "caption": "2024 - 2025 Division 1 Winners Cup",
            "type": "image"
        },
        {
            "filename": "2024 - 2025 Winners Shield.jpeg",
            "caption": "2024 - 2025 Winners Shield",
            "type": "image"
        },
        {
            "filename": "John Hurn Doing the Dorset Flop.MP4",
            "caption": "John Hurn Doing the Dorset Flop",
            "type": "video"
        },
        {
            "filename": "VIDEO-2026-04-10-21-54-33.mp4",
            "caption": "VIDEO-2026-04-10-21-54-33",
            "type": "video"
        }
    ]
    return render_template("gallery.html", gallery_items=gallery_items)

@app.route('/rules')
def rules():
    return render_template('rules.html')
    


# ==========================================================================
# SEASON RATES & FINES ROUTES
# ==========================================================================

@app.route('/season-rates')
def season_rates():
    # Pass admin status to the template so JS can show edit controls only for Treasurers
    is_admin = session.get('is_admin', False)
    return render_template('season-rates.html', is_admin=is_admin)


@app.route('/api/rates', methods=['GET'])
def get_rates():
    # Public route: Anyone can fetch the stored rates from Neon
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
        "id": r[0], 
        "rate_item": r[1], 
        "amount": float(r[2]), 
        "match_type": r[3], 
        "effective_from": str(r[4]), 
        "effective_to": str(r[5]) if r[5] else None
    } for r in rows]
    
    return jsonify(rates_list)


@app.route('/api/rates/add', methods=['POST'])
def add_rate():
    # SECURITY: Block non-admin users from adding rates
    if not session.get('is_admin'):
        return jsonify({"message": "Unauthorized access"}), 403

    data = request.get_json()
    if not data or not data.get('rate_item') or data.get('amount') is None:
        return jsonify({"message": "Missing required rate information"}), 400

    rate_item = data.get('rate_item')
    amount = data.get('amount')
    match_type = data.get('match_type', 'All')
    effective_from = data.get('effective_from')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO season_rates (rate_item, amount, match_type, effective_from)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (rate_item, amount, match_type, effective_from))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Rate added successfully", "id": new_id}), 201

    except Exception as e:
        print("Database error:", e)
        return jsonify({"message": "Database insertion error"}), 500

@app.route('/api/rates/save-all', methods=['POST'])
def save_all_rates():
    if not session.get('is_admin'):
        return jsonify({"message": "Unauthorized access"}), 403

    data = request.get_json()
    match_type = data.get('match_type')
    rates = data.get('rates', [])
    effective_from = data.get('effective_from')

    if not match_type or not rates:
        return jsonify({"message": "Invalid data received"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        for r in rates:
            if effective_from and effective_from.strip():
                cur.execute("""
                    INSERT INTO season_rates (rate_item, amount, match_type, effective_from)
                    VALUES (%s, %s, %s, %s);
                """, (r['rate_item'], r['amount'], match_type, effective_from))
            else:
                cur.execute("""
                    INSERT INTO season_rates (rate_item, amount, match_type, effective_from)
                    VALUES (%s, %s, %s, CURRENT_DATE);
                """, (r['rate_item'], r['amount'], match_type))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Successfully saved all rates"}), 200

    except Exception as e:
        print("Database save error:", e)
        return jsonify({"message": "Database update error"}), 500





# ==========================================================================
# TEAM & PLAYER MANAGEMENT ROUTES
# ==========================================================================
@app.route('/manage-teams', methods=['GET', 'POST'])
def manage_teams():
    if not session.get('is_admin'):
        flash("Admin access required to view Manage Teams.", "danger")
        return redirect(url_for('home'))
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    
    if request.method == 'POST':
        action = request.form.get('action')
        print(f"DEBUG: Received POST action -> '{action}'")
        print(f"DEBUG: Full form data -> {request.form.to_dict()}")
        
        # 1. Add Division
        if action == 'add_division':
            division_name = request.form.get('division_name')
            try:
                cur.execute(
                    "INSERT INTO divisions (division_name) VALUES (%s)",
                    (division_name,)
                )
                conn.commit()
                flash(f"Division '{division_name}' added successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error adding division: {e}", "danger")

        # 2. Add Team to Division
        elif action == 'add_team':
            team_name = request.form.get('team_name')
            division_id = request.form.get('division_id')
            effective_from = request.form.get('effective_from') or datetime.date.today().strftime('%Y-%m-%d')
            try:
                cur.execute(
                    "INSERT INTO teams (team_name, division_id, effective_from) VALUES (%s, %s, %s)",
                    (team_name, division_id, effective_from)
                )
                conn.commit()
                flash(f"Team '{team_name}' added successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error adding team: {e}", "danger")
            
        # 3. Add Player to Team (with Spare & Effective Date Support)
        elif action == 'add_player':
            player_name = request.form.get('player_name')
            team_id = request.form.get('team_id')
            is_spare = True if request.form.get('is_spare') == 'yes' else False
            effective_from = request.form.get('player_effective_from') or datetime.date.today().strftime('%Y-%m-%d')
            try:
                cur.execute(
                    "INSERT INTO players (player_name, team_id, is_spare, effective_from) VALUES (%s, %s, %s, %s)",
                    (player_name, team_id, is_spare, effective_from)
                )
                conn.commit()
                player_type = "Spare player" if is_spare else "Player"
                flash(f"{player_type} '{player_name}' added successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error adding player: {e}", "danger")

        # 4. Toggle Player Status (Regular <-> Spare with Effective Date)
        elif action == 'toggle_player_status':
            player_id = request.form.get('player_id')
            current_status = request.form.get('current_status') == 'True'
            new_status = not current_status
            effective_from = request.form.get('status_effective_from') or datetime.date.today().strftime('%Y-%m-%d')
            try:
                cur.execute(
                    "UPDATE players SET is_spare = %s, effective_from = %s WHERE id = %s",
                    (new_status, effective_from, player_id)
                )
                conn.commit()
                status_label = "Spare" if new_status else "Regular"
                flash(f"Player status updated to {status_label} (effective {effective_from}) successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error updating player status: {e}", "danger")
        
        # 5. Update Team Division (with Effective Date)
        elif action == 'update_team_division':
            team_id = request.form.get('team_id')
            new_division_id = request.form.get('new_division_id')
            effective_from = request.form.get('effective_from') or datetime.date.today().strftime('%Y-%m-%d')
            try:
                cur.execute(
                    "UPDATE teams SET division_id = %s, effective_from = %s WHERE id = %s",
                    (new_division_id, effective_from, team_id)
                )
                conn.commit()
                flash("Team division updated successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error updating team division: {e}", "danger")

        # 6. Batch Update All Players (Status + Effective Dates)
        elif action == 'update_all_players':
            player_ids = request.form.getlist('player_id')
            try:
                for p_id in player_ids:
                    is_spare_val = request.form.get(f'is_spare_{p_id}') == 'true'
                    submitted_date = request.form.get(f'effective_from_{p_id}')
                    effective_from_val = submitted_date if submitted_date else datetime.date.today().strftime('%Y-%m-%d')
                    
                    cur.execute(
                        "UPDATE players SET is_spare = %s, effective_from = %s WHERE id = %s",
                        (is_spare_val, effective_from_val, p_id)
                    )
                conn.commit()
                flash("All player changes saved successfully!", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error saving player changes: {e}", "danger")
        
        # Batch Update All Players (Status + Effective Dates)
        elif action == 'update_all_players':
            player_ids = request.form.getlist('player_id')
            try:
                for p_id in player_ids:
                    is_spare_val = request.form.get(f'is_spare_{p_id}') == 'true'
                    submitted_date = request.form.get(f'effective_from_{p_id}')
                    effective_from_val = submitted_date if submitted_date else datetime.date.today().strftime('%Y-%m-%d')
                    
                    cur.execute(
                        "UPDATE players SET is_spare = %s, effective_from = %s WHERE id = %s",
                        (is_spare_val, effective_from_val, p_id)
                    )
                conn.commit()
                flash("All player changes saved successfully!", "success")
            except Exception as e:
                conn.rollback()
                print(f"CRITICAL ERROR IN BATCH UPDATE: {e}")
                flash(f"Error saving player changes: {e}", "danger")
            finally:
                # Ensure cursor and connection close even if an error occurs
                cur.close()
                conn.close()
                return redirect(url_for('manage_teams'))
            
        cur.close()
        conn.close()
        return redirect(url_for('manage_teams'))

    # Fetch Divisions for dropdown
    cur.execute("SELECT id, division_name FROM divisions ORDER BY division_name;")
    divisions = cur.fetchall()

    # Fetch Teams with Division Names and Effective From Date
    cur.execute("""
        SELECT t.id, t.team_name, d.division_name, t.effective_from 
        FROM teams t 
        JOIN divisions d ON t.division_id = d.id 
        ORDER BY d.division_name, t.team_name;
    """)
    teams = cur.fetchall()
    
    # Fetch Players with Team, Division Names, Spare Status, and Effective From Date
    cur.execute("""
        SELECT p.id, p.player_name, t.team_name, d.division_name, p.is_spare, p.effective_from 
        FROM players p 
        JOIN teams t ON p.player_name = p.player_name AND p.team_id = t.id 
        JOIN divisions d ON t.division_id = d.id 
        ORDER BY d.division_name, t.team_name, p.is_spare, p.player_name;
    """)
    # Note: Use your original clean player query if preferred, ensuring p.effective_from is selected:
    cur.execute("""
        SELECT p.id, p.player_name, t.team_name, d.division_name, p.is_spare, p.effective_from 
        FROM players p 
        JOIN teams t ON p.team_id = t.id 
        JOIN divisions d ON t.division_id = d.id 
        ORDER BY d.division_name, t.team_name, p.is_spare, p.player_name;
    """)
    players = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('manage_teams.html', divisions=divisions, teams=teams, players=players)

# ==========================================================================
# APPLICATION EXECUTION ENTRY POINT
# ==========================================================================
if __name__ == '__main__':
    app.run(debug=True)