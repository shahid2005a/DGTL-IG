#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================
# SHAHID - Flask Server Starter
# Contains functions to start Flask server and find ports
# ============================================================

import socket
import random
import threading
from Aryan import app, logger

def find_free_port():
    """Find a free port to run the server on"""
    for port in range(5000, 5010):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:
            return port
    return random.randint(8080, 9000)

def start_flask(port):
    """Start the Flask server on the given port"""
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

def run_flask_thread(port):
    """Run Flask in a background thread"""
    flask_thread = threading.Thread(target=start_flask, args=(port,), daemon=True)
    flask_thread.start()
    return flask_thread