from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os, uuid

app = Flask(__name__, template_folder = "templates")
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

submissions = {}

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
        'response': None
    }
    return redirect(url_for('check_response', submission_id=submission_id))

@app.route('/check/<submission_id>')
def check_response(submission_id):
    s = submissions.get(submission_id)
    if not s:
        return "Not found", 404
    return render_template('response.html', submission=s, submission_id=submission_id)

@app.route('/check_update/<submission_id>')
def check_update(submission_id):
    s = submissions.get(submission_id)
    if s:
        return jsonify({'response': s['response']})
    return jsonify({'error': 'Not found'}), 404

@app.route('/admin')
def admin():
    pending = {sid: s for sid, s in submissions.items() if s['response'] is None}
    return render_template('admin.html', pending=pending)

@app.route('/admin/respond/<submission_id>', methods=['POST'])
def respond(submission_id):
    resp = request.form['response']
    if submission_id in submissions:
        submissions[submission_id]['response'] = resp
    return redirect(url_for('admin'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Bind to 0.0.0.0 for Render and listen on PORT env var if available
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
