from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import threading
import time

app = Flask(__name__)

# ডাউনলোড ফোল্ডার
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ফাইল অটো-ডিলিট (১ ঘণ্টা পর)
def cleanup_old_files():
    while True:
        time.sleep(3600)  # প্রতি ঘণ্টায় চেক
        now = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.getctime(file_path) < now - 3600:
                try:
                    os.remove(file_path)
                except:
                    pass

# ব্যাকগ্রাউন্ডে ক্লিনআপ চালু
threading.Thread(target=cleanup_old_files, daemon=True).start()

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
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # ডাউনলোড URL
        download_url = f"{request.host_url.rstrip('/')}/file/{os.path.basename(filename)}"
        
        return jsonify({
            'success': True,
            'title': info.get('title', 'Unknown Title'),
            'duration': info.get('duration', 0),
            'download_url': download_url,
            'expires_in': '1 hour'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ফাইল সার্ভ করা
@app.route('/file/<filename>')
def serve_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found or expired'}), 404

# Health Check (Render-এর জন্য)
@app.route('/healthz')
def health_check():
    return jsonify({'status': 'ok', 'service': 'yt-downloader-api'}), 200

# হোম পেজ (অপশনাল)
@app.route('/')
def home():
    return '''
    <h1>YT Downloader API</h1>
    <p>POST /api/download → {"url": "youtube_link"}</p>
    <p>Health: <a href="/healthz">/healthz</a></p>
    '''

# CORS সাপোর্ট (যেকোনো সাইট থেকে কল করা যাবে)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
