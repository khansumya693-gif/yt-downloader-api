
from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# ডাউনলোড ফোল্ডার তৈরি
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# API এন্ডপয়েন্ট
@app.route('/api/download', methods=['POST'])
def download_api():
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'YouTube লিঙ্ক দাও!'}), 400
    
    # ইউনিক ফাইল আইডি
    file_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
    
    ydl_opts = {
        'format': 'best[height<=720]',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # ডাউনলোড URL
        download_url = f"{request.host_url}file/{os.path.basename(filename)}"
        
        return jsonify({
            'success': True,
            'title': info.get('title', 'Unknown'),
            'download_url': download_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ফাইল সার্ভ
@app.route('/file/<filename>')
def serve_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found or expired'}), 404

# CORS (যেকোনো সাইট থেকে কল করা যাবে)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
