#!/usr/bin/env python3
"""
Ariel - A Flask web server for live Mermaid diagram rendering
"""

import os
import sys
import argparse
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

        .status-checking {
            background-color: #ffc107;
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
                        <span id="status-indicator" class="status-checking"></span>
                        <span id="status-text">Initializing...</span>
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
        let lastModified = null;
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
                case 'checking':
                    statusIndicator.className = 'status-checking';
                    statusText.textContent = 'Checking...';
                    break;
            }
        }

        async function renderDiagram(mermaidCode) {
            const diagramContainer = document.getElementById('diagram-container');

            try {
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

                clearError();
                updateStatus('ok');
            } catch (error) {
                console.error('Mermaid rendering error:', error);
                showError('Failed to render diagram: ' + error.message);
            }
        }

        async function checkForUpdates() {
            updateStatus('checking');

            try {
                const headers = {};
                if (lastModified) {
                    headers['If-Modified-Since'] = lastModified;
                }

                const response = await fetch('/mermaid', { headers });

                if (response.status === 304) {
                    // Not modified
                    updateStatus('ok');
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                // Update last modified time
                lastModified = response.headers.get('Last-Modified');

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
    """
    mmd_path = Path(config['mmd_file'])

    # Check if file exists
    if not mmd_path.exists():
        return jsonify({
            'error': f'Mermaid file not found: {config["mmd_file"]}'
        }), 404

    # Get file modification time
    try:
        file_mtime = datetime.fromtimestamp(mmd_path.stat().st_mtime)
    except Exception as e:
        return jsonify({'error': f'Failed to read file stats: {str(e)}'}), 500

    # Check If-Modified-Since header
    if_modified_since = request.headers.get('If-Modified-Since')
    if if_modified_since:
        if_modified_since_dt = parse_date(if_modified_since)
        if if_modified_since_dt and file_mtime.timestamp() <= if_modified_since_dt.timestamp():
            # File hasn't been modified
            response = make_response('', 304)
            response.headers['Last-Modified'] = http_date(file_mtime.timestamp())
            return response

    # File has been modified or first request
    try:
        # Read the mermaid file
        with open(mmd_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update cache
        config['last_modified'] = file_mtime
        config['last_content'] = content

        # Return the content
        response = make_response(jsonify({
            'content': content,
            'modified': http_date(file_mtime.timestamp())
        }))
        response.headers['Last-Modified'] = http_date(file_mtime.timestamp())
        response.headers['Cache-Control'] = 'no-cache'

        return response

    except Exception as e:
        return jsonify({'error': f'Failed to read file: {str(e)}'}), 500


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Ariel - A Flask web server for live Mermaid diagram rendering'
    )
    parser.add_argument(
        'file',
        nargs='?',
        default='diagram.mmd',
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

    args = parser.parse_args()

    # Update global config
    config['mmd_file'] = args.file

    # Check if mermaid file exists
    if not Path(args.file).exists():
        print(f'Warning: Mermaid file not found: {args.file}', file=sys.stderr)
        print(f'The server will start but return 404 until the file is created.', file=sys.stderr)

    print(f'Starting Ariel server...')
    print(f'  Watching file: {args.file}')
    print(f'  Server: http://{args.host}:{args.port}')
    print()

    # Run the Flask app
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()
