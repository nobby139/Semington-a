from flask import Flask, render_template

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)
