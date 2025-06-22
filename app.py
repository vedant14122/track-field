from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
import uuid

app = Flask(__name__)
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
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video.save(filepath)

    submissions[submission_id] = {
        'video_path': filename,
        'activity': activity,
        'response': None
    }

    return redirect(url_for('check_response', submission_id=submission_id))

@app.route('/check/<submission_id>')
def check_response(submission_id):
    submission = submissions.get(submission_id)
    if not submission:
        return "Submission not found", 404
    return render_template('response.html', submission=submission, submission_id=submission_id)

@app.route('/check_update/<submission_id>')
def check_update(submission_id):
    submission = submissions.get(submission_id)
    if submission:
        return jsonify({'response': submission['response']})
    return jsonify({'error': 'Not found'}), 404

@app.route('/admin')
def admin():
    pending = {sid: s for sid, s in submissions.items() if s['response'] is None}
    return render_template('admin.html', pending=pending)

@app.route('/admin/respond/<submission_id>', methods=['POST'])
def respond(submission_id):
    response = request.form.get('response')
    if submission_id in submissions:
        submissions[submission_id]['response'] = response
    return redirect(url_for('admin'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
