#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================
# TUNNEL - Tunnel Management
# Contains functions to manage tunnels (ngrok, cloudflared, etc.)
# ============================================================

import subprocess
import os
import time
import threading

def start_tunnel(port, method='cloudflared'):
    """Start a tunnel to expose the server"""
    if method == 'cloudflared':
        return start_cloudflared(port)
    elif method == 'ngrok':
        return start_ngrok(port)
    else:
        print(f"⚠️ Unknown tunnel method: {method}")
        return None

def start_cloudflared(port):
    """Start cloudflared tunnel"""
    time.sleep(2)
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
        
        print(f"\n🚇 Starting cloudflared tunnel on port {port}...")
        process = subprocess.Popen([cloudflared_cmd, 'tunnel', '--url', f'http://localhost:{port}'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=1)
        
        def print_urls():
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
        
        threading.Thread(target=print_urls, daemon=True).start()
        return process
    except Exception as e:
        print(f"⚠️ Tunnel error: {e}")
        return None

def start_ngrok(port):
    """Start ngrok tunnel"""
    try:
        print(f"\n🚇 Starting ngrok tunnel on port {port}...")
        process = subprocess.Popen(['ngrok', 'http', str(port)],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, bufsize=1)
        
        def print_urls():
            for line in process.stdout:
                if 'https://' in line and 'ngrok.io' in line:
                    for word in line.split():
                        if 'https://' in word and 'ngrok.io' in word:
                            url = word.strip()
                            print("\n" + "="*60)
                            print("✅ TUNNEL ACTIVE!")
                            print(f"📱 PUBLIC URL: {url}")
                            print("="*60 + "\n")
                            break
                    break
        
        threading.Thread(target=print_urls, daemon=True).start()
        return process
    except Exception as e:
        print(f"⚠️ Ngrok error: {e}")
        return None