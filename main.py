from flask import (
    Flask, render_template, request, redirect,
    url_for, jsonify, send_from_directory, abort
)
import os, uuid, logging

# ── Flask setup ───────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates")
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# in-memory “DB” — replace with real DB later
submissions = {}

# ── routes ────────────────────────────────────────────────────────────────
@app.route('/')
def index():                          # STEP 1 – upload
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():                         # handle STEP 1 POST
    video = request.files['video']
    activity = request.form['activity']

    submission_id = str(uuid.uuid4())
    filename = f"{submission_id}_{video.filename}"
    video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # store the basics; user details come next step
    submissions[submission_id] = {
        'video_path': filename,
        'activity': activity,
        'first_name': '',
        'last_name': '',
        'email': '',
        'response': None
    }

    app.logger.info(
        f"[UPLOAD] {filename} | Activity: {activity} | ID: {submission_id}"
    )
    return redirect(url_for('details', submission_id=submission_id))

@app.route('/details/<submission_id>', methods=['GET', 'POST'])
def details(submission_id):           # STEP 2 – user details
    sub = submissions.get(submission_id)
    if not sub:
        abort(404)

    if request.method == 'POST':
        sub['first_name'] = request.form['first_name']
        sub['last_name']  = request.form['last_name']
        sub['email']      = request.form['email']
        sub['notes']      = request.form.get('notes', '')
        app.logger.info(f"[DETAILS] ID {submission_id} | email {sub['email']}")
        return redirect(url_for('confirmation', submission_id=submission_id))

    return render_template(
        'details.html',
        submission_id=submission_id
    )

@app.route('/confirmation/<submission_id>')
def confirmation(submission_id):      # STEP 3 – thank-you screen
    sub = submissions.get(submission_id)
    if not sub:
        abort(404)
    return render_template('confirmation.html', submission=sub)

# optional JSON endpoint the front-end could poll
@app.route('/check_update/<submission_id>')
def check_update(submission_id):
    s = submissions.get(submission_id)
    if s:
        return jsonify({'response': s['response']})
    return jsonify({'error': 'Not found'}), 404

# ── admin area (VERY simple auth via query string) ────────────────────────
ADMIN_PASSWORD = "change-me"

def check_admin():
    if request.args.get("password") != ADMIN_PASSWORD:
        abort(403)

@app.route('/admin')
def admin():
    check_admin()
    pending = {sid: s for sid, s in submissions.items() if s['response'] is None}
    return render_template('admin.html', pending=pending, pw=ADMIN_PASSWORD)

@app.route('/admin/respond/<submission_id>', methods=['POST'])
def respond(submission_id):
    check_admin()
    resp = request.form['response']
    if submission_id in submissions:
        submissions[submission_id]['response'] = resp
    return redirect(url_for('admin', password=ADMIN_PASSWORD))

# ── serve uploaded files ──────────────────────────────────────────────────
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ── main ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=port, debug=True)
