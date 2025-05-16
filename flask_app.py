from flask import Flask, request, jsonify
from ytmusicapi import YTMusic
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

yt = YTMusic()

@app.route("/", methods=['POST'])
# @app.route("/")
def hello_world():
    song_url = request.form.get("song")
    # song_url = "hataarindai"
    try:
        search_results = yt.search(song_url, filter="songs")
        # res = yt.get_song("KiYpAEiG5H8")
        return search_results
    except Exception as e:
        return str(e), 500

@app.route("/detail", methods=['POST'])
def get_yt_metadata():
    video_id = request.form.get("videoId")
    if not video_id:
        return jsonify({"error": "Missing 'videoId' parameter"}), 400

    try:
        # ydl_opts = {
        #     'quiet': True,
        #     'no_warnings': True,
        #     'skip_download': True,
        # }
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            # Add these to help with PythonAnywhere environment
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            },
            'extractor_args': {'youtube': {'player_client': ['android']}},
            # Add a source address to avoid IP restrictions
            'source_address': '0.0.0.0',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

            # Filter only audio formats with defined abr
            audio_formats = [
                f for f in info['formats']
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('abr') is not None
            ]
            if not audio_formats:
                return jsonify({"error": "No valid audio formats found"}), 404

            # Sort by audio bitrate
            best_audio = sorted(audio_formats, key=lambda x: x['abr'], reverse=True)[0]

            def format_number(num):
                if num is None:
                    return "0"
                if num >= 1_000_000:
                    return f"{num / 1_000_000:.1f}M"
                elif num >= 1_000:
                    return f"{num / 1_000:.1f}K"
                return str(num)

            return jsonify({
                "url": best_audio['url'],
                "type": best_audio['ext'],
                "title": info.get('title'),
                "author": info.get('uploader') or info.get('channel'),
                "likes": format_number(info.get('like_count')),
                "views": format_number(info.get('view_count')),
                "year": info.get('upload_date', '')[:4] if info.get('upload_date') else '',
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)