import os
import subprocess
import uuid
from flask import Flask, render_template_string, request, send_from_directory, jsonify, make_response

app = Flask(__name__)

# CONFIGURATION
MUSIC_DIR = '/music'

# HTML TEMPLATE
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SimpleCut</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; max-width: 900px; margin: 20px auto; padding: 20px; background: #f4f4f9; color: #333; }
        .card { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        h2 { margin-top: 0; display: flex; justify-content: space-between; align-items: center; }
        .shortcuts-hint { font-size: 12px; color: #888; font-weight: normal; }
        
        .file-group { display: grid; grid-template-columns: 1fr 2fr; gap: 15px; margin-bottom: 15px; align-items: center; }
        label { font-weight: bold; font-size: 14px; color: #555; }
        select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background: #fff; }
        
        /* Players */
        audio { width: 100%; margin: 15px 0; outline: none; }
        
        /* Time Controls */
        .time-controls { display: flex; gap: 20px; margin-bottom: 20px; background: #f8f9fa; padding: 15px; border-radius: 6px; border: 1px solid #eee; }
        .control-group { flex: 1; text-align: center; }
        .control-group h4 { margin: 0 0 10px 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
        
        .nudge-container { display: flex; align-items: center; justify-content: center; gap: 5px; }
        input.time-input { width: 90px; padding: 8px; font-size: 16px; text-align: center; border: 1px solid #ccc; border-radius: 4px; font-family: monospace; font-weight: bold; }
        
        button { cursor: pointer; border: none; border-radius: 4px; transition: 0.2s; font-weight: bold; }
        .btn-nudge { padding: 5px 10px; background: #e9ecef; color: #333; font-size: 12px; }
        .btn-nudge:hover { background: #ced4da; }
        .btn-set { padding: 8px 15px; background: #007bff; color: white; margin-top: 8px; width: 100%; }
        .btn-set:hover { background: #0056b3; }

        .action-area { display: flex; gap: 10px; margin-top: 20px; border-top: 2px solid #eee; padding-top: 20px; }
        .btn-main { flex: 1; padding: 15px; font-size: 16px; text-transform: uppercase; }
        .cut-btn { background: #28a745; color: white; }
        .cut-btn:hover { background: #218838; }
        .del-btn { background: #dc3545; color: white; max-width: 100px; }
        
        /* PREVIEW ZONE */
        #preview-zone { 
            display: none; 
            margin-top: 20px; 
            padding: 20px; 
            background: #e8f5e9; 
            border: 2px solid #c3e6cb; 
            border-radius: 8px; 
        }
        #preview-zone h3 { margin-top: 0; color: #1b5e20; margin-bottom: 5px;}
        .preview-hint { font-size: 12px; color: #2e7d32; margin-bottom: 10px; display:block;}
        .preview-actions { display: flex; gap: 10px; margin-top: 10px; }
        .btn-replace { flex: 2; background: #155724; color: white; padding: 12px; font-size: 16px; }
        .btn-replace:hover { background: #0b2e13; }
        .btn-discard { flex: 1; background: #fff; color: #c62828; border: 1px solid #c62828; padding: 12px; font-size: 16px; }
        .btn-discard:hover { background: #ffebee; }

        /* Status */
        #status { margin-top: 15px; padding: 10px; text-align: center; border-radius: 4px; font-weight: bold; display: none; }
        .success { background: #d4edda; color: #155724; display: block !important; }
        .error { background: #f8d7da; color: #721c24; display: block !important; }
        .processing { background: #e2e3e5; color: #383d41; display: block !important; }
        
        /* Loading Overlay */
        #loading-overlay {
            position: fixed; top:0; left:0; width:100%; height:100%;
            background: rgba(255,255,255,0.8);
            display: none; flex-direction: column;
            align-items: center; justify-content: center;
            z-index: 999;
        }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div id="loading-overlay">
        <div class="spinner"></div>
        <h3 id="loading-msg">Working...</h3>
    </div>

    <div class="card">
        <h2>
            <span>SimpleCut</span>
            <span class="shortcuts-hint">Space (Play) | "I" (In) | "O" (Out)</span>
        </h2>
        
        <div class="file-group">
            <select id="folderList" onchange="onFolderChange()"></select>
            <select id="fileList" onchange="loadTrack()"></select>
        </div>

        <div style="text-align:center; margin-bottom:5px; font-size:12px; color:#666;">Currently Editing: <b id="edit-mode-label">None</b></div>
        <audio id="player" controls></audio>

        <div class="time-controls">
            <div class="control-group">
                <h4>Start Time</h4>
                <div class="nudge-container">
                    <button class="btn-nudge" onclick="nudge('startTime', -1)">-1s</button>
                    <button class="btn-nudge" onclick="nudge('startTime', -0.1)">-0.1</button>
                    <input type="text" id="startTime" value="00:00:00.00">
                    <button class="btn-nudge" onclick="nudge('startTime', 0.1)">+0.1</button>
                    <button class="btn-nudge" onclick="nudge('startTime', 1)">+1s</button>
                </div>
                <button class="btn-set" onclick="setStart()">Set Start (I)</button>
            </div>

            <div class="control-group">
                <h4>End Time</h4>
                <div class="nudge-container">
                    <button class="btn-nudge" onclick="nudge('endTime', -1)">-1s</button>
                    <button class="btn-nudge" onclick="nudge('endTime', -0.1)">-0.1</button>
                    <input type="text" id="endTime" value="00:00:00.00">
                    <button class="btn-nudge" onclick="nudge('endTime', 0.1)">+0.1</button>
                    <button class="btn-nudge" onclick="nudge('endTime', 1)">+1s</button>
                </div>
                <button class="btn-set" onclick="setEnd()">Set End (O)</button>
            </div>
        </div>

        <div class="action-area">
            <button class="btn-main cut-btn" onclick="cutFile()">Cut</button>
            <button class="btn-main del-btn" onclick="deleteFile()">Delete</button>
        </div>

        <div id="preview-zone">
            <h3>Preview Result</h3>
            <span class="preview-hint">Review the cut below.</span>
            <audio id="preview-player" controls></audio>
            <div class="preview-actions">
                <button class="btn-replace" onclick="replaceOriginal()">Replace Original (Keep Metadata)</button>
                <button class="btn-discard" onclick="discardCut()">Discard</button>
            </div>
        </div>
        
        <div id="status"></div>
    </div>

    <script>
        let fileData = {};
        let activeProxyFile = "";
        let activeCutFile = "";
        let originalMp3File = "";

        const player = document.getElementById('player');
        const previewPlayer = document.getElementById('preview-player');
        const previewZone = document.getElementById('preview-zone');
        const folderSelect = document.getElementById('folderList');
        const fileSelect = document.getElementById('fileList');
        const statusDiv = document.getElementById('status');
        const loading = document.getElementById('loading-overlay');

        window.onload = function() { refreshLibrary(); };

        player.onloadedmetadata = function() {
            if(player.duration && player.duration !== Infinity) {
                document.getElementById('endTime').value = formatTime(player.duration);
            }
        };

        document.addEventListener('keydown', function(event) {
            if(event.target.tagName === "INPUT") return;
            switch(event.code) {
                case "Space": 
                    event.preventDefault(); 
                    if (previewZone.style.display === 'block' && !previewPlayer.paused) previewPlayer.pause();
                    else if (previewZone.style.display === 'block' && previewPlayer.paused) previewPlayer.play();
                    else player.paused ? player.play() : player.pause();
                    break;
                case "KeyI": setStart(); break;
                case "KeyO": setEnd(); break;
            }
        });

        async function refreshLibrary(keepSelection = false) {
            const currentFolder = folderSelect.value;
            const currentFile = fileSelect.value;

            try {
                const response = await fetch('/scan');
                fileData = await response.json();
                
                folderSelect.innerHTML = '<option value="" disabled selected>Select Folder...</option>';
                for (const folder in fileData) {
                    const option = document.createElement('option');
                    option.value = folder;
                    option.text = folder;
                    folderSelect.add(option);
                }

                if (keepSelection && currentFolder && fileData[currentFolder]) {
                    folderSelect.value = currentFolder;
                    onFolderChange(currentFile);
                }
            } catch (e) { console.error(e); }
        }

        function onFolderChange(preselectFile = null) {
            const folder = folderSelect.value;
            fileSelect.innerHTML = '<option value="" disabled selected>Select File...</option>';
            
            if (fileData[folder]) {
                fileData[folder].forEach(file => {
                    const option = document.createElement('option');
                    option.value = file;
                    option.text = file;
                    fileSelect.add(option);
                });
            }
            
            if (preselectFile) {
                fileSelect.value = preselectFile;
            } else {
                player.src = ""; 
                hidePreview();
                document.getElementById('startTime').value = "00:00:00.00";
            }
        }

        async function loadTrack() {
            // 1. CLEANUP PREVIOUS PROXY IF EXISTS
            if (activeProxyFile) {
                fetch('/delete', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ proxy: activeProxyFile }) 
                });
                activeProxyFile = "";
            }

            const folder = folderSelect.value;
            const file = fileSelect.value;
            if (!folder || !file) return;
            const fullPath = folder === "Root" ? file : folder + "/" + file;
            
            originalMp3File = fullPath;
            hidePreview();
            
            loading.style.display = 'flex';
            document.getElementById('loading-msg').innerText = "Loading & Sanitizing...";

            try {
                const res = await fetch('/prepare', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ filename: fullPath })
                });
                const json = await res.json();

                if (json.success) {
                    activeProxyFile = json.proxy_filename;
                    player.src = "/stream/" + encodeURIComponent(activeProxyFile) + "?t=" + Date.now();
                    document.getElementById('edit-mode-label').innerText = "Editing: " + file;
                    document.getElementById('edit-mode-label').style.color = "#333";
                } else {
                    alert("Error: " + json.message);
                }
            } catch (e) { alert("Network Error"); } 
            finally { loading.style.display = 'none'; }
            
            statusDiv.style.display = 'none';
            document.getElementById('startTime').value = "00:00:00.00";
        }

        function hidePreview() {
            previewZone.style.display = 'none';
            previewPlayer.pause();
            previewPlayer.src = "";
            activeCutFile = "";
        }

        function formatTime(seconds) {
            const date = new Date(seconds * 1000);
            return date.toISOString().substr(11, 11); 
        }
        function timeToSeconds(timeStr) {
            const parts = timeStr.split(':');
            return (+parts[0]) * 3600 + (+parts[1]) * 60 + (+parts[2]);
        }
        function setStart() { document.getElementById('startTime').value = formatTime(player.currentTime); }
        function setEnd() { document.getElementById('endTime').value = formatTime(player.currentTime); }
        function nudge(elementId, amount) {
            const el = document.getElementById(elementId);
            let newT = Math.max(0, timeToSeconds(el.value) + amount);
            el.value = formatTime(newT);
            player.currentTime = newT;
        }

        async function cutFile() {
            if (!activeProxyFile) return alert("No file loaded!");
            
            // STOP MAIN PLAYER
            player.pause();

            const start = document.getElementById('startTime').value;
            const end = document.getElementById('endTime').value;
            
            if (timeToSeconds(end) <= timeToSeconds(start)) return alert("End Time must be after Start Time.");

            loading.style.display = 'flex';
            document.getElementById('loading-msg').innerText = "Cutting...";

            try {
                const response = await fetch('/cut', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ proxy: activeProxyFile, start: start, end: end })
                });
                const result = await response.json();
                
                if (result.success) {
                    activeCutFile = result.cut_filename;
                    previewPlayer.src = "/stream/" + encodeURIComponent(activeCutFile) + "?t=" + Date.now();
                    previewZone.style.display = 'block';
                    previewPlayer.play(); 
                } else {
                    showStatus("Error: " + result.message, "error");
                }
            } catch (err) { showStatus("Network Error", "error"); }
            finally { loading.style.display = 'none'; }
        }

        async function replaceOriginal() {
            if (!activeCutFile || !originalMp3File) return;
            if(!confirm("Overwrite original file?")) return;

            loading.style.display = 'flex';
            document.getElementById('loading-msg').innerText = "Saving...";

            try {
                const response = await fetch('/replace', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ original: originalMp3File, cut_wav: activeCutFile, proxy: activeProxyFile })
                });
                const result = await response.json();

                if (result.success) {
                    showStatus("Success!", "success");
                    hidePreview();
                    activeProxyFile = ""; 
                    await refreshLibrary(true);
                } else {
                    showStatus("Error: " + result.message, "error");
                }
            } catch (err) { showStatus("Network Error", "error"); }
            finally { loading.style.display = 'none'; }
        }

        async function discardCut() { hidePreview(); }

        async function deleteFile() {
            if (!originalMp3File) return alert("Select file!");
            if (!confirm("Delete this file?")) return;

            try {
                const res = await fetch('/delete', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ filename: originalMp3File, proxy: activeProxyFile })
                });
                const json = await res.json();
                if (json.success) {
                    showStatus("Deleted.", "success");
                    hidePreview();
                    await refreshLibrary(true);
                }
            } catch (err) { showStatus("Network Error", "error"); }
        }

        function showStatus(msg, type) {
            statusDiv.innerText = msg;
            statusDiv.style.display = 'block';
            statusDiv.className = type;
        }
    </script>
</body>
</html>
"""

# --- BACKEND ---

def cleanup_orphans():
    # Auto-delete any leftover proxy/cut wavs in the whole library
    for root, dirs, files in os.walk(MUSIC_DIR):
        for f in files:
            if f.endswith('_proxy.wav') or f.endswith('_cut.wav') or f.startswith('temp_'):
                try:
                    os.remove(os.path.join(root, f))
                except: pass

def get_library_structure():
    # Run cleanup every time we list the library to catch stragglers
    cleanup_orphans()
    
    tree = {}
    for root, dirs, files in os.walk(MUSIC_DIR, followlinks=True):
        rel_folder = os.path.relpath(root, MUSIC_DIR)
        if rel_folder == ".": rel_folder = "Root"
        files.sort(key=lambda s: s.lower())
        # Support MP3 and OPUS
        audio_files = [f for f in files if (f.lower().endswith('.mp3') or f.lower().endswith('.opus')) and not 'temp_' in f]
        if audio_files: tree[rel_folder] = audio_files
    return dict(sorted(tree.items(), key=lambda item: item[0].lower()))

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/scan')
def scan_library(): 
    return jsonify(get_library_structure())

@app.route('/stream/<path:filename>')
def stream(filename):
    response = make_response(send_from_directory(MUSIC_DIR, filename))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

def parse_time(t):
    try:
        parts = t.split(':')
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except: return 0.0

@app.route('/prepare', methods=['POST'])
def prepare_proxy():
    data = request.json
    mp3_path = os.path.join(MUSIC_DIR, data['filename'])
    base, ext = os.path.splitext(data['filename'])
    proxy_filename = f"{base}_proxy.wav"
    proxy_path = os.path.join(MUSIC_DIR, proxy_filename)

    cmd = ['ffmpeg', '-y', '-i', mp3_path, '-vn', '-ac', '2', '-ar', '44100', '-f', 'wav', proxy_path]
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        return jsonify({"success": True, "proxy_filename": proxy_filename})
    except Exception as e: return jsonify({"success": False, "message": str(e)})

@app.route('/cut', methods=['POST'])
def cut_file():
    data = request.json
    proxy_filename = data['proxy']
    start_sec = parse_time(data['start'])
    end_sec = parse_time(data['end'])
    duration = end_sec - start_sec
    
    input_path = os.path.join(MUSIC_DIR, proxy_filename)
    base, ext = os.path.splitext(proxy_filename)
    cut_filename = f"{base}_cut.wav"
    cut_path = os.path.join(MUSIC_DIR, cut_filename)

    if duration <= 0: return jsonify({"success": False, "message": "Time Error"})

    cmd = ['ffmpeg', '-y', '-i', input_path, '-ss', str(start_sec), '-t', str(duration), '-c', 'copy', cut_path]
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        return jsonify({"success": True, "cut_filename": cut_filename})
    except Exception as e: return jsonify({"success": False, "message": str(e)})

@app.route('/replace', methods=['POST'])
def replace_file():
    data = request.json
    original_rel = data['original']
    cut_wav_rel = data['cut_wav']
    proxy_rel = data.get('proxy')

    original_path = os.path.join(MUSIC_DIR, original_rel)
    cut_wav_path = os.path.join(MUSIC_DIR, cut_wav_rel)
    
    base_name, ext = os.path.splitext(original_path)
    ext = ext.lower()
    
    temp_id = uuid.uuid4().hex
    temp_out_path = os.path.join(MUSIC_DIR, f"temp_{temp_id}{ext}")
    
    try:
        if os.path.exists(cut_wav_path):
            # MERGE: Cut Audio + Original Metadata
            cmd = [
                'ffmpeg', '-y',
                '-i', cut_wav_path,
                '-i', original_path,
                '-map', '0:a',
                '-map_metadata', '1',
            ]

            # Codec Selection based on extension
            if ext == '.opus':
                # Opus container (Ogg) usually doesn't support video streams for art in this way
                cmd.extend(['-c:a', 'libopus', '-b:a', '128k'])
            else:
                # Default to MP3/LAME for .mp3 or others
                # Copy album art if exists (treated as video stream in MP3)
                cmd.extend(['-map', '1:v?', '-c:v', 'copy', '-c:a', 'libmp3lame', '-b:a', '256k', '-id3v2_version', '3'])

            cmd.append(temp_out_path)

            subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
            
            os.remove(original_path)
            os.rename(temp_out_path, original_path)
            
            # Cleanup
            os.remove(cut_wav_path)
            if proxy_rel:
                p = os.path.join(MUSIC_DIR, proxy_rel)
                if os.path.exists(p): os.remove(p)
            
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Cut file missing"})
    except Exception as e:
        if os.path.exists(temp_out_path): os.remove(temp_out_path)
        return jsonify({"success": False, "message": str(e)})

@app.route('/delete', methods=['POST'])
def delete_file():
    data = request.json
    try:
        if 'filename' in data and data['filename']: 
            os.remove(os.path.join(MUSIC_DIR, data['filename']))
        if 'proxy' in data and data['proxy']:
            p = os.path.join(MUSIC_DIR, data['proxy'])
            if os.path.exists(p): os.remove(p)
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)