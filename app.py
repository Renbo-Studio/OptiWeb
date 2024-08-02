from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
from PIL import Image
import io

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

def optimize_image(img, max_size=(1920, 1080), quality=85):
    """Optimize the image while preserving quality and transparency."""
    original_size = img.size[0] * img.size[1] * len(img.getbands())
    
    img.thumbnail(max_size, Image.LANCZOS)
    
    # Determine the output format
    output_format = 'PNG' if img.mode == 'RGBA' else 'JPEG'
    
    buffer = io.BytesIO()
    if output_format == 'PNG':
        img.save(buffer, format='PNG', optimize=True)
    else:
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            img = background
        elif img.mode == 'CMYK':
            img = img.convert('RGB')
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
    
    optimized_size = buffer.tell()
    
    if optimized_size >= original_size:
        return img, 0, output_format  # No reduction
    
    buffer.seek(0)
    return Image.open(buffer), (1 - optimized_size / original_size) * 100, output_format

@app.route('/upload', methods=['POST'])
def upload_file():
    download_links = []
    size_reductions = []
    if request.method == 'POST':
        files = request.files.getlist('files')
        uploaded_count = 0
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if uploaded_count >= 6:
                    break  # Limit to 6 files
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    original_size = os.path.getsize(file_path)
                    img = Image.open(file_path)
                    optimized_img, reduction_percentage, output_format = optimize_image(img)
                    
                    optimized_filename = f'optimized_{os.path.splitext(filename)[0]}.{output_format.lower()}'
                    optimized_file_path = os.path.join(app.config['UPLOAD_FOLDER'], optimized_filename)
                    
                    optimized_img.save(optimized_file_path, format=output_format, quality=85, optimize=True)
                    
                    optimized_size = os.path.getsize(optimized_file_path)
                    actual_reduction = (1 - optimized_size / original_size) * 100
                    
                    download_links.append(url_for('download_file', filename=optimized_filename))
                    size_reductions.append(f"{actual_reduction:.2f}%")
                elif filename.lower().endswith('.mp4'):
                    # Process video using moviepy or ffmpeg (not implemented in this example)
                    download_links.append(url_for('download_file', filename=filename))
                    size_reductions.append("N/A")
                
                uploaded_count += 1
        
        return render_template('index.html', download_links=download_links, size_reductions=size_reductions, zip=zip)
    return render_template('index.html', error='Invalid file format')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)