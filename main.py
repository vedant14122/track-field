from flask import (
    Flask, render_template, request, redirect,
    url_for, jsonify, send_from_directory, abort
)
import os, uuid, logging

app = Flask(__name__, template_folder="templates")
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

submissions = {}

ADMIN_PASSWORD = "change-me"

def check_admin():
    if request.args.get("password") != ADMIN_PASSWORD:
        abort(403)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    video = request.files['video']
    activity = request.form['activity']

    submission_id = str(uuid.uuid4())
    filename = f"{submission_id}_{video.filename}"
    video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    submissions[submission_id] = {
        'video_path': filename,
        'activity': activity,
        'first_name': '',
        'last_name': '',
        'email': '',
        'response': None
    }

    app.logger.info(f"[UPLOAD] {filename} | Activity: {activity} | ID: {submission_id}")
    return redirect(url_for('details', submission_id=submission_id))

@app.route('/details/<submission_id>', methods=['GET', 'POST'])
def details(submission_id):
    sub = submissions.get(submission_id)
    if not sub:
        abort(404)

    if request.method == 'POST':
        sub['first_name'] = request.form['first_name']
        sub['last_name'] = request.form['last_name']
        sub['email'] = request.form['email']
        sub['notes'] = request.form.get('notes', '')
        app.logger.info(f"[DETAILS] ID {submission_id} | email {sub['email']}")
        return redirect(url_for('confirmation', submission_id=submission_id))

    return render_template('details.html', submission_id=submission_id)

@app.route('/confirmation/<submission_id>')
def confirmation(submission_id):
    sub = submissions.get(submission_id)
    if not sub:
        abort(404)
    return render_template('confirmation.html', submission=sub)

@app.route('/check_update/<submission_id>')
def check_update(submission_id):
    s = submissions.get(submission_id)
    if s:
        return jsonify({'response': s['response']})
    return jsonify({'error': 'Not found'}), 404

# ── New user dashboard ──────────────────────────────────────────────
@app.route('/user/dashboard')
def user_dashboard():
    # For demo, create fake user stats (replace with real data)
    user_stats = {
        "name": "Demo User",
        "performance_data": [5, 7, 6, 8],  # km distances over weeks
        "activities": [
            "Ran 5km in 25 minutes",
            "Updated profile information",
            "Joined TrackField challenge"
        ]
    }
    return render_template('user_dashboard.html', stats=user_stats)

# ── Admin dashboard with charts and tables ───────────────────────────
@app.route('/admin/dashboard')
def admin_dashboard():
    check_admin()

    # For demo, create dummy users data (replace with real DB data)
    users = [
        {"id": 1001, "name": "Jane Doe", "email": "jane@example.com", "role": "Member", "last_login": "2025-06-23"},
        {"id": 1002, "name": "John Smith", "email": "john@example.com", "role": "Admin", "last_login": "2025-06-24"},
    ]
    # Dummy monthly user stats
    monthly_stats = {
        "labels": ["June", "July", "August", "September"],
        "new_users": [12, 19, 3, 5],
        "active_users": [7, 11, 5, 8],
    }

    return render_template('admin_dashboard.html', users=users, stats=monthly_stats, pw=ADMIN_PASSWORD)

# ── Move old admin submissions management here ─────────────────────────
@app.route('/admin/submissions')
def admin_submissions():
    check_admin()
    pending = {sid: s for sid, s in submissions.items() if s['response'] is None}
    return render_template('admin.html', pending=pending, pw=ADMIN_PASSWORD)

@app.route('/admin/respond/<submission_id>', methods=['POST'])
def respond(submission_id):
    check_admin()
    resp = request.form['response']
    if submission_id in submissions:
        submissions[submission_id]['response'] = resp
    return redirect(url_for('admin_submissions', password=ADMIN_PASSWORD))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=port, debug=True)
