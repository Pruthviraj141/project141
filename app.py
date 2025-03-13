import os
import zipfile
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ZIP_FOLDER'] = 'zips'

# Ensure necessary directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ZIP_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if the uploaded file is a PDF."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the homepage with predefined sections."""
    sections = ["1.1", "1.2", "2.1", "2.2"]
    return render_template('index.html', sections=sections)

@app.route('/upload/<section>', methods=['POST'])
def upload_file(section):
    """Handle file uploads and organize them in structured folders."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Organize by the main folder (e.g., "1.1" -> "1")
        folder = section.split('.')[0]
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(folder_path, exist_ok=True)

        # Ensure unique filenames using timestamps
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = secure_filename(file.filename)
        unique_filename = f"{section}_{timestamp}_{filename}"

        file_path = os.path.join(folder_path, unique_filename)
        file.save(file_path)

        return jsonify({'message': 'File uploaded successfully'}), 200

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/view/<section>')
def view_file(section):
    """Retrieve and serve the first matching file for a given section."""
    folder = section.split('.')[0]
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)

    if not os.path.exists(folder_path):
        return jsonify({'error': 'Folder not found'}), 404

    for file in os.listdir(folder_path):
        if file.startswith(section):
            return send_file(os.path.join(folder_path, file))

    return jsonify({'error': 'File not found'}), 404


import shutil

@app.route('/convert-and-download-zip', methods=['GET'])
def convert_and_download_zip():
    zip_path = os.path.join(app.config['ZIP_FOLDER'], 'all_pdfs.zip')

    # Step 1: Ensure ZIP folder exists and delete old ZIP
    os.makedirs(app.config['ZIP_FOLDER'], exist_ok=True)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # Step 2: Create a fresh ZIP file
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for folder in os.listdir(app.config['UPLOAD_FOLDER']):
            folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, app.config['UPLOAD_FOLDER'])
                    zipf.write(file_path, arcname=arcname)

    # Step 3: Send ZIP file
    if os.path.exists(zip_path):
        response = send_file(zip_path, as_attachment=True)

        # Step 4: ✅ DELETE ALL FILES after sending ZIP
        shutil.rmtree(app.config['UPLOAD_FOLDER'])  # Delete entire uploads folder
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Recreate empty folder

        return response

    return jsonify({'error': 'ZIP file creation failed'}), 500

if __name__ == '__main__':
    app.run(debug=True)
