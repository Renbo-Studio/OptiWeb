from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    download_links = []
    if request.method == 'POST':
        # Get all files from the request
        files = request.files.getlist('files')
        uploaded_count = 0
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if uploaded_count >= 6:
                    break  # Limit to 6 files
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                # Process file (resize, compress, etc.)
                if filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    img = Image.open(file_path)
                    img.thumbnail((800, 800))
                    optimized_filename = 'optimized_' + filename
                    optimized_file_path = os.path.join(app.config['UPLOAD_FOLDER'], optimized_filename)
                    img.save(optimized_file_path)
                    download_links.append(url_for('download_file', filename=optimized_filename))
                elif filename.endswith('.mp4'):
                    # Process video using moviepy or ffmpeg
                    download_links.append(url_for('download_file', filename=filename))
                uploaded_count += 1
        return render_template('index.html', download_links=download_links)
    return render_template('index.html', error='Invalid file format')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
