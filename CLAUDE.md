# CLAUDE.md - Project Guide for AI Assistants

## Project Overview

**Ariel** is a live Mermaid diagram viewer that provides real-time visualization of `.mmd` (Mermaid) diagram files. It watches a Mermaid file for changes and automatically updates the rendered diagram in the browser without manual refresh.

**Purpose**: Enable rapid iteration on diagram creation by providing instant visual feedback during editing.

## Architecture

### Core Components

1. **ariel.py** - Flask backend server
   - Exposes two endpoints: `/` (main page) and `/mermaid` (diagram content as plain text)
   - Implements ETag-based caching using MD5 hashes
   - Returns HTTP 304 for unchanged content
   - Returns raw `.mmd` file content with proper Content-Type header

2. **templates/index.html** - Frontend interface
   - Polls `/mermaid` endpoint every 1 second
   - Uses Mermaid.js 11.12.1 for client-side rendering
   - Displays status indicators (green=connected, red=error)
   - Maintains scroll position and container height during updates

3. **start_ariel.sh** - Bash launcher script
   - Detects and activates Python virtual environments
   - Auto-installs Flask if missing
   - Opens browser automatically (cross-platform)
   - Accepts CLI arguments for configuration

### Data Flow

```
User edits .mmd file
    ↓
Browser polls /mermaid every 1s
    ↓
Server computes ETag, checks modification time
    ↓
If unchanged → 304 response (no re-render)
If changed → Plain text content + ETag
    ↓
Mermaid.js renders updated SVG
    ↓
User sees updated diagram
```

## Key Files

- `ariel.py` - Main Flask application (core logic)
- `templates/index.html` - Single-page frontend
- `start_ariel.sh` - Convenience launcher
- `requirements.txt` - Python dependencies (Flask 2.3.0+, Werkzeug 2.3.0+)
- `diagram.mmd` - Sample Mermaid diagram
- `README.md` - User-facing documentation

## Code Conventions

### Python (ariel.py)
- Uses Flask application factory pattern implicitly
- Global `config` dictionary stores runtime configuration
- ETag generation: MD5 hash of file content
- Logging disabled for Flask to reduce console noise
- File path validation and error handling at endpoint level

### Frontend (index.html)
- Polling interval: 1000ms (1 second)
- Error display: Shows "Error occurred" text and error message alert (no checkerboard pattern)
- Status indicator: Green dot (success) / Red dot (error)
- Page title: Shows filename dynamically (e.g., "diagram.mmd - Ariel")
- Mermaid initialization: `mermaid.initialize({ startOnLoad: false })`
- Dynamic rendering: `mermaid.run({ nodes: [container] })`

### Shell Script (start_ariel.sh)
- Detects virtual environment by checking for `venv/` directory
- Uses `python3` explicitly
- Platform detection for browser opening: `uname -s` → Darwin/Linux/Windows
- Default port: 5000

## Common Tasks

### Adding a New Endpoint
1. Add route decorator in `ariel.py`
2. Implement handler function
3. Return appropriate response (JSON, HTML template, or status code)
4. Update error handling if needed

### Modifying the Frontend
1. Edit `templates/index.html`
2. Changes are immediately visible on page refresh
3. Preserve ETag-based polling logic for performance
4. Test with various diagram types and error states

### Changing Polling Behavior
- Modify `setInterval` in `index.html` (currently 1000ms)
- Consider server load and file system performance
- Test with large diagram files

### Adding New CLI Arguments
1. Update `parse_arguments()` in `start_ariel.sh`
2. Pass new argument to `ariel.py`
3. Add corresponding argument parser in `ariel.py`
4. Store in `config` dictionary
5. Update README.md usage section

## Important Patterns

### ETag Caching
The application uses ETag-based caching to minimize bandwidth and unnecessary re-renders:
- Server computes MD5 hash of file content
- Client sends `If-None-Match` header with previous ETag
- Server returns 304 if ETag matches (no body)
- Client only re-renders on 200 response with new content

### Error Handling
- File not found: Returns plain text error message with appropriate status code
- Invalid Mermaid syntax: Client displays error message below diagram area
- Server errors: Caught and displayed with status indicator
- Missing dependencies: Launcher script attempts auto-install

### Virtual Environment Support
The launcher script automatically detects and activates Python virtual environments:
```bash
if [ -d "venv" ]; then
    source venv/bin/activate
fi
```

## Technologies

- **Backend**: Python 3.9+, Flask 2.3.0+, Werkzeug 2.3.0+
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3.0
- **Rendering**: Mermaid.js 11.12.1
- **Platform**: Cross-platform (macOS, Linux, Windows)

## Development Workflow

### Running Locally
```bash
./start_ariel.sh diagram.mmd
# Or with options:
./start_ariel.sh --host 0.0.0.0 --port 8080 --debug --no-browser diagram.mmd
```

### Manual Python Execution
```bash
python3 ariel.py diagram.mmd --host 127.0.0.1 --port 5000 --debug
```

### Testing Changes
1. Modify code (ariel.py or templates/index.html)
2. Restart server (Ctrl+C, then re-run start script)
3. Refresh browser (or it auto-refreshes on next poll)
4. Edit diagram.mmd to test live update functionality

## Gotchas and Important Notes

1. **File Argument Required**: The diagram file path is mandatory (not optional)
2. **Single File Watching**: Only watches one file at a time (specified as argument)
3. **Port Conflicts**: Default port 5000 may conflict with other services
4. **Browser Auto-Open**: Timing-sensitive; may open before server is ready on slow systems
5. **Flask Logging Disabled**: Reduces console noise; re-enable for debugging
6. **ETag MD5 Computation**: Done on every request; could be optimized with file watcher for very large files
7. **No WebSocket**: Uses HTTP polling instead of WebSocket for simplicity
8. **Bootstrap CDN**: Requires internet connection for styling
9. **Mermaid Version**: Pinned to 11.12.1; update `<script>` tag to upgrade

## Recent Changes

- Changed `/mermaid` endpoint to return raw plain text instead of JSON (simpler API)
- Updated page title to show filename dynamically (e.g., "diagram.mmd - Ariel")
- Removed checkerboard pattern on errors for cleaner error display
- Fixed README documentation: using ETag (If-None-Match) not If-Modified-Since
- Added diagram.mmd example to README
- Replaced title with navbar showing filename and status
- Added safety checks for None config values
- Upgraded Mermaid.js to 11.12.1
- Disabled Flask logging for cleaner output
- Refactored HTML to use Flask template system
- Made file argument required instead of optional

## Security Considerations

- **Path Traversal**: Validate file paths to prevent directory traversal attacks
- **Local Network Only**: Default binding to 127.0.0.1 (localhost)
- **No Authentication**: Intended for local development use only
- **Open Browser**: Automatically opens browser with localhost URL (low risk)

## Future Enhancement Ideas

- Support multiple file watching (tabs or dropdown)
- WebSocket-based updates instead of polling
- Dark mode theme support
- Export rendered diagrams (SVG, PNG)
- Diagram history/versioning
- Collaborative editing support
- Configuration file support (.arielrc)
