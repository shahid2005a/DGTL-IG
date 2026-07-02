#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================
# SERVER - Server Management
# Contains functions to run and manage the server
# ============================================================

import os
import threading
from Aryan import app, logger
from Shahid import find_free_port

def run_server(port=None):
    """Run the Flask server"""
    if port is None:
        port = find_free_port()
    print(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

def run_server_thread(port=None):
    """Run server in a background thread"""
    if port is None:
        port = find_free_port()
    thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    thread.start()
    return thread, port

def get_server_url(port):
    """Get the local server URL"""
    return f"http://localhost:{port}"

def get_public_url():
    """Get the public URL from the tunnel"""
    # This would need to be implemented to read from the tunnel output
    return None