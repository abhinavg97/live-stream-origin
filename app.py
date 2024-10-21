import os
import time
from flask import Flask, send_from_directory, Response, render_template, request
from flask_cors import CORS  # Import Flask-CORS
from collections import defaultdict

app = Flask(__name__, template_folder='/Users/ajitsharmakasturi/Desktop/hyperscale/live-stream-origin/templates')
CORS(app)  # Enable CORS for all routes

# Directory where HLS files are saved
HLS_DIRECTORY = '/Users/ajitsharmakasturi/Desktop/hyperscale/live-stream-origin/output/'
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


def get_total_segments(playlist_path):
    """Count the total number of segments in the original HLS playlist."""
    with open(playlist_path, 'r') as f:
        lines = f.readlines()
    # Count the number of EXTINF lines (which correspond to segments)
    return sum(1 for line in lines if line.startswith('#EXTINF'))


# def get_live_playlist(looped_playlist_path, loop_count):
#     """Simulate the live playlist by looping over the segments."""
#     current_time = time.time()
#     elapsed_time = current_time - START_TIME
#     total_segments = get_total_segments(looped_playlist_path)
#     segments_available = int(elapsed_time // SEGMENT_DURATION)  # Number of segments that should be available
#
#     # Calculate how many full loops we've done
#     num_full_loops = segments_available // total_segments
#
#     # If the number of full loops exceeds the allowed loop count, cap it
#     if loop_count > 0 and num_full_loops >= loop_count:
#         segments_available = total_segments * loop_count  # Cap at the last segment in the final loop
#
#     # Effective segment index for the current loop (handles looping)
#     effective_segment = segments_available % total_segments
#
#     # Read the original playlist file
#     with open(looped_playlist_path, 'r') as f:
#         lines = f.readlines()
#
#     # Filter lines to only include the header and the segments that are currently available
#     playlist_content = []
#     segment_count = 0
#     current_loop = 0
#
#     for line in lines:
#         if line.startswith('#EXTINF'):
#             # Only include segments up to the current available point in the current loop
#             if segment_count < effective_segment or (current_loop < num_full_loops and loop_count != num_full_loops):
#                 playlist_content.append(line)
#                 segment_count += 1
#         elif line.endswith('.ts\n'):
#             if segment_count <= effective_segment:
#                 # Loop the segment index and handle multiple loops
#                 current_segment = f'index{segment_count % total_segments}.ts\n'
#                 playlist_content.append(current_segment)
#                 if segment_count % total_segments == total_segments - 1:
#                     current_loop += 1
#         else:
#             # Add header and metadata lines
#             playlist_content.append(line)
#
#     # Add the end of playlist marker if the loop count is capped
#     if loop_count > 0 and num_full_loops >= loop_count:
#         playlist_content.append('#EXT-X-ENDLIST\n')
#
#     # Dummy logic
#     playlist_content = []
#     for line in lines:
#         playlist_content.append(line)
#
#     return Response("\n".join(playlist_content), content_type='application/vnd.apple.mpegurl')


@app.route('/<path:filename>')
def stream_hls(filename):
    """Serve HLS playlist and segments."""
    return send_from_directory(HLS_DIRECTORY, filename)


# @app.route('/stream')
# def stream_video():
#     """Serve the dynamically updated HLS master playlist with looping."""
#     # Set loop_count to the desired number of loops, or -1 for infinite loops
#     return get_live_playlist(HLS_PLAYLIST, loop_count=-1)


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
        playlist_content = [*playlist_content, *CHUNK_MAP[chunk % len(CHUNK_MAP)]]

    playlist_content = [*playlist_content, *FOOTER_LINES]
    return Response("\n".join(playlist_content), content_type='application/vnd.apple.mpegurl')

@app.route('/stream')
def get_chunk():
    """Serve the dynamically updated HLS master playlist with looping."""
    chunkl = request.args.get('chunkl', -1)
    chunkr = request.args.get('chunkr', -1)
    # Set loop_count to the desired number of loops, or -1 for infinite loops
    return get_live_playlist(chunk_range = [chunkl, chunkr])


@app.route('/')
def index():
    """Serve the HTML player."""
    return render_template('index.html')


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
    app.run(debug=True, port=8000)