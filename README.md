# O₂Craft - Your Cosmic Minecraft Server Manager  

<p align="center">  
  <img src="https://placehold.co/600x300/01000a/8b5cf6?text=O%E2%82%82Craft&font=raleway" alt="O₂Craft Banner">  
</p>  

<p align="center">  
  <em>A sleek, modern, and lightweight web interface for creating and managing Minecraft (Java & Bedrock) servers</em>  
</p>  

<p align="center">  
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python" alt="Python">  
  <img src="https://img.shields.io/badge/Flask-2.0+-black.svg?style=for-the-badge&logo=flask" alt="Flask">  
  <img src="https://img.shields.io/badge/License-Apache--2.0-green.svg?style=for-the-badge" alt="License">  
  <img src="https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge" alt="Status">  
</p>  

## ✨ Cosmic Features  

O₂Craft brings a stunning "glassmorphism" UI with cosmic aesthetics to make server management delightful:  

🌌 **Stunning Web UI**: Responsive interface built with Tailwind CSS  
🚀 **One-Click Creation**: Instant Minecraft server deployment  
☕ **Java & 🪨 Bedrock**: Dual-edition support in one dashboard  
📊 **Live Console**: Real-time monitoring via WebSockets  
⚙️ **Smart Config Editor**: Visual server.properties management  
🎮 **Core Controls**: Start/Stop/Restart with one click  
⬇️ **Auto-Updates**: Fetches latest server versions automatically  
🪶 **Lightweight**: Minimal footprint with Flask & Gevent  

## 🛠️ Tech Stack  

**Backend**: Python 3.10+, Flask, Flask-Sock  
**WSGI**: Gunicorn with Gevent workers  
**Frontend**: Tailwind CSS, Vanilla JS, WebSockets  
**Dependencies**: Requests, BeautifulSoup4  

## 🚀 Quick Start  

### Prerequisites  
- Python 3.10+  
- Java 17+ (for Java Edition)  
- Git  

```bash
git clone https://github.com/unknownmsv/oxygencraft.git
cd o2craft
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

### 🏃 Running  

**Development Mode**:  
```bash
python app.py
```

**Production Mode**:  
```bash
gunicorn --worker-class gevent -w 1 --bind 0.0.0.0:8000 app:app
```

Access at: `http://localhost:8000`

## 📖 User Guide  

1. **Create Server**:  
   - Click "+ New Server"  
   - Select type (Java/Bedrock), version, and RAM  
   - Watch automatic setup complete  

2. **Manage Servers**:  
   - Start/Stop/Restart with single clicks  
   - Live console streaming  
   - Edit server.properties visually  

## 📂 Project Structure  

```
o2craft/
├── app.py                  # Main application
├── servers/                # Server instances
│   └── [server_id]/
│       ├── config.json     # Server configuration
│       └── server.jar      # Java server binary
├── static/                 # Frontend assets
├── templates/              # HTML templates
├── LICENSE                 # Apache 2.0
└── README.md               # This file
```

## 🤝 Contributing  

We welcome contributions! Please:  
1. Fork the repository  
2. Create a feature branch  
3. Submit a PR  

## 📜 License  

Licensed under **[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)**  



---

<p align="center">
  <img src="https://img.shields.io/github/stars/username/o2craft?style=social" alt="Stars">  
  <img src="https://img.shields.io/github/forks/username/o2craft?style=social" alt="Forks">
</p>
