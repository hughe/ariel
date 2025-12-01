#!/usr/bin/env python3
"""
Ariel - A Flask web server for live Mermaid diagram rendering
"""

import os
import sys
import argparse
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request, make_response
from werkzeug.http import http_date, parse_date

app = Flask(__name__)

# Global configuration
config = {
    'mmd_file': 'diagram.mmd',
    'last_modified': None,
    'last_content': None
}

# HTML template for the main page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ariel - Mermaid Diagram Viewer</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Mermaid.js -->
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({ startOnLoad: false, theme: 'default' });
        window.mermaid = mermaid;
    </script>

    <style>
        .checkerboard {
            background-image:
                linear-gradient(45deg, #ccc 25%, transparent 25%),
                linear-gradient(-45deg, #ccc 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, #ccc 75%),
                linear-gradient(-45deg, transparent 75%, #ccc 75%);
            background-size: 20px 20px;
            background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
            background-color: #fff;
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px dashed #999;
        }

        #diagram-container {
            min-height: 400px;
            padding: 20px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .error-message {
            margin-top: 15px;
        }

        #status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-ok {
            background-color: #28a745;
        }

        .status-error {
            background-color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <h1 class="mb-4">
                    Ariel - Live Mermaid Diagram Viewer
                    <small class="text-muted fs-6">
                        <span id="status-indicator" class="status-ok"></span>
                        <span id="status-text">Connected</span>
                    </small>
                </h1>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div id="diagram-container">
                    <div class="checkerboard">
                        <span class="text-muted">Loading diagram...</span>
                    </div>
                </div>

                <div id="error-container" class="alert alert-danger error-message" style="display: none;" role="alert">
                    <strong>Error:</strong> <span id="error-message"></span>
                </div>
            </div>
        </div>
    </div>

    <script>
        let lastETag = null;
        let pollInterval = null;

        function showError(message) {
            const errorContainer = document.getElementById('error-container');
            const errorMessage = document.getElementById('error-message');
            const diagramContainer = document.getElementById('diagram-container');
            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');

            errorMessage.textContent = message;
            errorContainer.style.display = 'block';
            diagramContainer.innerHTML = '<div class="checkerboard"><span class="text-muted">Error occurred</span></div>';
            statusIndicator.className = 'status-error';
            statusText.textContent = 'Error';
        }

        function clearError() {
            const errorContainer = document.getElementById('error-container');
            errorContainer.style.display = 'none';
        }

        function updateStatus(status) {
            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');

            switch(status) {
                case 'ok':
                    statusIndicator.className = 'status-ok';
                    statusText.textContent = 'Connected';
                    break;
                case 'error':
                    statusIndicator.className = 'status-error';
                    statusText.textContent = 'Error';
                    break;
            }
        }

        async function renderDiagram(mermaidCode) {
            const diagramContainer = document.getElementById('diagram-container');

            try {
                // Save current scroll position and container height
                const scrollX = window.scrollX;
                const scrollY = window.scrollY;
                const currentHeight = diagramContainer.offsetHeight;

                // Preserve container height to prevent layout shift
                diagramContainer.style.minHeight = `${currentHeight}px`;

                // Clear previous content
                diagramContainer.innerHTML = '';

                // Create a div for mermaid to render into
                const mermaidDiv = document.createElement('div');
                mermaidDiv.className = 'mermaid';
                mermaidDiv.textContent = mermaidCode;
                diagramContainer.appendChild(mermaidDiv);

                // Render with mermaid
                await window.mermaid.run({
                    querySelector: '.mermaid',
                });

                // Remove min-height after rendering to allow natural sizing
                diagramContainer.style.minHeight = '';

                // Restore scroll position
                window.scrollTo(scrollX, scrollY);

                clearError();
                updateStatus('ok');
            } catch (error) {
                console.error('Mermaid rendering error:', error);
                showError('Failed to render diagram: ' + error.message);
            }
        }

        async function checkForUpdates() {
            try {
                const headers = {};
                if (lastETag) {
                    headers['If-None-Match'] = lastETag;
                }

                const response = await fetch('/mermaid', { headers });

                if (response.status === 304) {
                    // Not modified - keep status as is (should already be 'ok')
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                // Update ETag for next request
                lastETag = response.headers.get('ETag');

                // Render the new diagram
                if (data.content) {
                    await renderDiagram(data.content);
                } else {
                    throw new Error('No diagram content received');
                }

            } catch (error) {
                console.error('Error checking for updates:', error);
                showError('Failed to fetch diagram: ' + error.message);
            }
        }

        // Start polling when page loads
        document.addEventListener('DOMContentLoaded', function() {
            // Initial check
            checkForUpdates();

            // Poll every second
            pollInterval = setInterval(checkForUpdates, 1000);
        });

        // Clean up on page unload
        window.addEventListener('beforeunload', function() {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Serve the main webpage"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/mermaid')
def mermaid():
    """
    Return the mermaid diagram content if the file has been modified.
    Returns 304 Not Modified if the file hasn't changed since last request.
    Uses ETag (filename + mtime) for cache validation.
    """
    mmd_path = Path(config['mmd_file'])

    # Check if file exists
    if not mmd_path.exists():
        return jsonify({
            'error': f'Mermaid file not found: {config["mmd_file"]}'
        }), 404

    # Read the mermaid file
    try:
        with open(mmd_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {str(e)}'}), 500

    # Get file modification time
    try:
        file_mtime = datetime.fromtimestamp(mmd_path.stat().st_mtime)
    except Exception as e:
        return jsonify({'error': f'Failed to read file stats: {str(e)}'}), 500

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

    # Return the content
    response = make_response(jsonify({
        'content': content,
        'modified': http_date(file_mtime.timestamp())
    }))
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
        nargs=1,
        default=None,
        help='Path to the mermaid (.mmd) file to watch (default: diagram.mmd)'
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
        debug=args.debug
    )


if __name__ == '__main__':
    main()
