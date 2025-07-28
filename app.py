# app.py
import os
import json
import subprocess
import uuid
import requests
import gevent
import time
import zipfile
import io
from flask import Flask, jsonify, request, render_template, abort
from flask_cors import CORS
from flask_sockets import Sockets
from bs4 import BeautifulSoup

# --- 1. App Setup ---
app = Flask(__name__, template_folder='frontend', static_folder='frontend')
CORS(app)
sockets = Sockets(app)

# --- 2. Configuration & State ---
SERVERS_DIR = "servers"
os.makedirs(SERVERS_DIR, exist_ok=True)
servers_db = {}
running_processes = {}

# --- 3. Helper Functions ---
def get_server_path(server_id): return os.path.join(SERVERS_DIR, server_id)

def save_server_config(server_id, server_data):
    server_dir = get_server_path(server_id)
    os.makedirs(server_dir, exist_ok=True)
    with open(os.path.join(server_dir, 'config.json'), 'w') as f:
        json.dump(server_data, f, indent=4)

def load_servers_from_disk():
    for server_id in os.listdir(SERVERS_DIR):
        config_path = os.path.join(SERVERS_DIR, server_id, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                try:
                    servers_db[server_id] = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode config for server {server_id}")

def update_server_status(server_id):
    if server_id in running_processes:
        process = running_processes[server_id]
        if process.poll() is None:
            servers_db[server_id]['status'] = "running"
        else:
            servers_db[server_id]['status'] = "stopped"
            del running_processes[server_id]
    else:
        servers_db[server_id]['status'] = "stopped"
    save_server_config(server_id, servers_db[server_id])

def read_properties(server_id):
    props = {}
    props_path = os.path.join(get_server_path(server_id), 'server.properties')
    if not os.path.exists(props_path): return {}
    with open(props_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                props[key.replace('-', '_')] = value
    return props

def write_properties(server_id, properties):
    props_path = os.path.join(get_server_path(server_id), 'server.properties')
    current_props = read_properties(server_id)
    for key, value in properties.items():
        py_key = key.replace('-', '_')
        if isinstance(value, bool):
            current_props[py_key] = str(value).lower()
        else:
            current_props[py_key] = str(value)

    with open(props_path, 'w') as f:
        for key, value in current_props.items():
            f.write(f"{key.replace('_', '-')}={value}\n")

# --- 4. Flask Routes ---
load_servers_from_disk()

@app.route('/')
def index(): return render_template('index.html')

@app.route('/server.html')
def server_page(): return render_template('server.html')

@app.route("/versions", methods=['GET'])
def get_versions():
    versions = {"java": [], "bedrock": []}
    try:
        # Fetch Java versions (more reliable)
        java_manifest = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json").json()
        versions["java"] = [v for v in java_manifest['versions'] if v['type'] == 'release']
    except Exception as e:
        print(f"Could not fetch Java versions: {e}")

    try:
        # Scrape Bedrock version (less reliable, wrapped in try-except)
        bedrock_page = requests.get("https://www.minecraft.net/en-us/download/server/bedrock")
        soup = BeautifulSoup(bedrock_page.content, 'html.parser')
        download_link = soup.find('a', {'data-platform': 'serverBedrockLinux'})
        if download_link and download_link.has_attr('href'):
            bedrock_version_id = "latest-bedrock"
            bedrock_url = download_link['href']
            versions["bedrock"] = [{"id": bedrock_version_id, "url": bedrock_url}]
    except Exception as e:
        print(f"Could not fetch Bedrock version (this is common): {e}")

    return jsonify(versions)


@app.route("/servers", methods=['GET'])
def get_servers():
    for server_id in list(servers_db.keys()): update_server_status(server_id)
    return jsonify(list(servers_db.values()))

@app.route("/servers/<server_id>", methods=['GET'])
def get_server(server_id):
    if server_id not in servers_db: abort(404)
    update_server_status(server_id)
    return jsonify(servers_db[server_id])

@app.route("/servers/<server_id>/properties", methods=['GET'])
def get_server_properties(server_id):
    if server_id not in servers_db: abort(404)
    return jsonify(read_properties(server_id))

@app.route("/servers/<server_id>/properties", methods=['PUT'])
def update_server_properties(server_id):
    if server_id not in servers_db: abort(404)
    new_props = request.get_json()
    write_properties(server_id, new_props)
    return jsonify({"message": "Properties updated. Restart server to apply."})

@app.route("/servers/<server_id>/start", methods=['POST'])
def start_server(server_id):
    if server_id not in servers_db: abort(404)
    if server_id in running_processes and running_processes[server_id].poll() is None:
        return jsonify({"message": "Server is already running"}), 409
    
    server = servers_db[server_id]
    server_dir = get_server_path(server_id)
    
    if server['type'] == 'java':
        jar_path = os.path.join(server_dir, 'server.jar')
        if not os.path.exists(jar_path): abort(500, description="server.jar not found.")
        cmd = ["java", f"-Xmx{server['ram']}G", f"-Xms{server['ram']}G", "-jar", jar_path, "nogui"]
        process = subprocess.Popen(cmd, cwd=server_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    elif server['type'] == 'bedrock':
        executable = os.path.join(server_dir, 'bedrock_server')
        if not os.path.exists(executable): abort(500, description="bedrock_server executable not found.")
        os.chmod(executable, 0o755)
        cmd = [f"./{os.path.basename(executable)}"]
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = server_dir
        process = subprocess.Popen(cmd, cwd=server_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env, shell=True)
    else:
        abort(400, description="Unknown server type")

    running_processes[server_id] = process
    update_server_status(server_id)
    return jsonify({"message": "Server started"})

@app.route("/servers/<server_id>/stop", methods=['POST'])
def stop_server(server_id):
    if server_id not in running_processes or running_processes[server_id].poll() is not None:
        return jsonify({"message": "Server is not running"}), 409
    
    process = running_processes[server_id]
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    
    del running_processes[server_id]
    update_server_status(server_id)
    return jsonify({"message": "Server stopped"})

@app.route("/servers/<server_id>/restart", methods=['POST'])
def restart_server(server_id):
    if server_id in running_processes and running_processes[server_id].poll() is None:
        stop_server(server_id)
        time.sleep(2)
    start_server(server_id)
    return jsonify({"message": "Server restarted"})

# --- 5. WebSocket Routes ---
@sockets.route('/ws/create_status')
def create_status_socket(ws):
    data = json.loads(ws.receive())
    server_id = str(uuid.uuid4())
    server_dir = get_server_path(server_id)
    os.makedirs(server_dir, exist_ok=True)
    
    try:
        ws.send(json.dumps({"status": "downloading", "message": f"Downloading server version {data['version']}..."}))
        if data['type'] == 'java':
            manifest = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json").json()
            version_url = next(v['url'] for v in manifest['versions'] if v['id'] == data['version'])
            version_data = requests.get(version_url).json()
            jar_url = version_data['downloads']['server']['url']
            jar_path = os.path.join(server_dir, 'server.jar')
            with requests.get(jar_url, stream=True) as r:
                r.raise_for_status()
                with open(jar_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        elif data['type'] == 'bedrock':
            bedrock_url = data['version_url']
            zip_path = os.path.join(server_dir, 'bedrock.zip')
            with requests.get(bedrock_url, stream=True) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            ws.send(json.dumps({"status": "extracting", "message": "Extracting server files..."}))
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(server_dir)
            os.remove(zip_path)

        ws.send(json.dumps({"status": "configuring", "message": "Accepting EULA and configuring..."}))
        if data['type'] == 'java':
            with open(os.path.join(server_dir, 'eula.txt'), 'w') as f: f.write('eula=true\n')
            with open(os.path.join(server_dir, 'server.properties'), 'w') as f: f.write('motd=A new O2Craft Server\n')

        ws.send(json.dumps({"status": "finalizing", "message": "Saving server configuration..."}))
        server = {
            "id": server_id, "name": data['name'], "type": data['type'],
            "version": data['version'], "ram": data['ram'], "status": "stopped", "properties": {}
        }
        servers_db[server_id] = server
        save_server_config(server_id, server)
        
        ws.send(json.dumps({"status": "complete", "message": "Server created successfully!"}))
    except Exception as e:
        ws.send(json.dumps({"status": "error", "message": str(e)}))
    finally:
        if not ws.closed: ws.close()

@sockets.route('/ws/servers/<server_id>/console')
def console_socket(ws, server_id):
    if server_id not in running_processes or running_processes[server_id].poll() is not None:
        ws.send("[O₂Craft] Server is not running.")
        return

    process = running_processes[server_id]
    
    def read_logs():
        try:
            for line in iter(process.stdout.readline, ''):
                if not ws.closed:
                    ws.send(line.strip())
                else: break
        except Exception as e: print(f"Log reading error: {e}")

    log_thread = gevent.spawn(read_logs)
    try:
        while not ws.closed: gevent.sleep(1)
    except Exception as e: print(f"WebSocket Error: {e}")
    finally:
        log_thread.kill()
        print(f"WebSocket for server {server_id} closed.")

if __name__ == '__main__':
    print("Run with Gunicorn for WebSocket support: gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 app:app")
    app.run(host='0.0.0.0', port=8000, debug=True)
