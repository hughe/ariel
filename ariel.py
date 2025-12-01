#!/usr/bin/env python3
"""
Ariel - A Flask web server for live Mermaid diagram rendering
"""

import os
import sys
import argparse
import subprocess
import threading
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, make_response
from werkzeug.http import http_date, parse_date

app = Flask(__name__)

# Disable Flask/Werkzeug logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.logger.disabled = True

# Global configuration
config = {
    'mmd_file': None,
    'last_modified': None,
    'last_content': None
}


@app.route('/')
def index():
    """Serve the main webpage"""
    if config['mmd_file']:
        filename = Path(config['mmd_file']).name
    else:
        filename = 'No file loaded'
    return render_template('index.html', filename=filename)


@app.route('/mermaid')
def mermaid():
    """
    Return the mermaid diagram content if the file has been modified.
    Returns 304 Not Modified if the file hasn't changed since last request.
    Uses ETag (content hash) for cache validation.
    """
    # Check if mmd_file is configured
    if config['mmd_file'] is None:
        return 'No mermaid file configured', 500

    mmd_path = Path(config['mmd_file'])

    # Check if file exists
    if not mmd_path.exists():
        return f'Mermaid file not found: {config["mmd_file"]}', 404

    # Read the mermaid file
    try:
        with open(mmd_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f'Failed to read file: {str(e)}', 500

    # Get file modification time
    try:
        file_mtime = datetime.fromtimestamp(mmd_path.stat().st_mtime)
    except Exception as e:
        return f'Failed to read file stats: {str(e)}', 500

    # Create ETag from content hash
    import hashlib
    etag = f'"{hashlib.md5(content.encode()).hexdigest()}"'

    # Check If-None-Match header (ETag validation)
    if_none_match = request.headers.get('If-None-Match')
    if if_none_match and if_none_match == etag:
        # Content hasn't changed
        response = make_response('', 304)
        response.headers['ETag'] = etag
        response.headers['Last-Modified'] = http_date(file_mtime.timestamp())
        return response

    # Update cache
    config['last_modified'] = file_mtime
    config['last_content'] = content

    # Return the raw content
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['ETag'] = etag
    response.headers['Last-Modified'] = http_date(file_mtime.timestamp())
    response.headers['Cache-Control'] = 'no-cache'

    return response


def open_browser(url, delay=1.5):
    """Open web browser using the system's open command"""
    import time
    time.sleep(delay)
    try:
        # Use platform-specific open command
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', url], check=False)
        elif sys.platform == 'linux':  # Linux
            subprocess.run(['xdg-open', url], check=False)
        elif sys.platform == 'win32':  # Windows
            subprocess.run(['start', url], shell=True, check=False)
    except Exception as e:
        print(f'Warning: Could not open browser: {e}', file=sys.stderr)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Ariel - A Flask web server for live Mermaid diagram rendering'
    )
    parser.add_argument(
        'file',
        help='Path to the mermaid (.mmd) file to watch'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        '-p',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not open browser automatically'
    )

    args = parser.parse_args()

    # Update global config
    config['mmd_file'] = args.file

    # Check if mermaid file exists
    if not Path(args.file).exists():
        print(f'Error: Mermaid file not found: {args.file}', file=sys.stderr)
        sys.exit(1)

    # Construct URL
    url = f'http://{args.host}:{args.port}'

    print(f'Starting Ariel server...')
    print(f'  Watching file: {args.file}')
    print(f'  Server: {url}')
    if not args.no_browser:
        print(f'  Opening browser...')
    print()

    # Open browser in background thread
    if not args.no_browser:
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # Run the Flask app
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        use_reloader=False,
        threaded=True
    )


if __name__ == '__main__':
    main()
