import os
import time
from flask import Flask, send_from_directory, Response, render_template, request
from flask_cors import CORS  # Import Flask-CORS
from collections import defaultdict

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Directory where HLS files are saved
HLS_DIRECTORY = './output/'
HLS_PLAYLIST = os.path.join(HLS_DIRECTORY, 'index.m3u8')

# Simulated live stream settings
SEGMENT_DURATION = 10  # Each .ts file represents 10 seconds of video
START_TIME = time.time()  # Timestamp when the "live stream" starts
HEADER_LENGTH = 4
FOOTER_LENGTH = 1
CHUNK_LENGTH = 2
HEADER_LINES = []
FOOTER_LINES = []
CHUNK_MAP = defaultdict(list)
video_segment_cache = {}


def get_total_segments(playlist_path):
    """Count the total number of segments in the original HLS playlist."""
    with open(playlist_path, 'r') as f:
        lines = f.readlines()
    # Count the number of EXTINF lines (which correspond to segments)
    return sum(1 for line in lines if line.startswith('#EXTINF'))


@app.route('/<path:filename>')
def stream_hls(filename):
    """Serve HLS playlist and segments."""
    # prune timestamp prefix from filename
    filename = filename.split('_', 1)[1]
    return send_from_directory(HLS_DIRECTORY, filename)


def get_live_playlist(chunk_range):
    current_time = time.time()
    elapsed_time = current_time - START_TIME
    cur_chunk = int(elapsed_time) // SEGMENT_DURATION

    if chunk_range[0] == -1:
        chunk_range[0] = cur_chunk

    if chunk_range[1] == -1:
        chunk_range[1] = cur_chunk

    playlist_content = [*HEADER_LINES]
    for chunk in range(chunk_range[0], chunk_range[1] + 1):
        playlist_content = [*playlist_content, CHUNK_MAP[chunk % len(CHUNK_MAP)][0],
                            f'{chunk}_{CHUNK_MAP[chunk % len(CHUNK_MAP)][1]}']

    playlist_content = [*playlist_content, *FOOTER_LINES]
    return Response("\n".join(playlist_content), content_type='application/vnd.apple.mpegurl')


@app.route('/stream')
def get_chunk():
    """Serve the dynamically updated HLS master playlist with looping."""
    chunkl = request.args.get('chunkl', -1)
    chunkr = request.args.get('chunkr', -1)
    # Set loop_count to the desired number of loops, or -1 for infinite loops
    return get_live_playlist(chunk_range = [chunkl, chunkr])


def init_chunks():
    global HEADER_LINES, FOOTER_LINES, CHUNK_MAP
    with open(HLS_PLAYLIST, 'r') as f:
        lines = [line.strip() for line in f.readlines()]

    HEADER_LINES = lines[:HEADER_LENGTH]
    FOOTER_LINES = lines[-FOOTER_LENGTH:]

    idx = -1
    for line in lines[HEADER_LENGTH:-FOOTER_LENGTH]:
        idx += 1
        CHUNK_MAP[idx // CHUNK_LENGTH].append(line)


if __name__ == '__main__':
    init_chunks()
    app.run(debug=True, port=8001)
