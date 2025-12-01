#!/bin/bash
#
# Ariel Startup Script
# Starts the Ariel Mermaid diagram viewer server
#

set -e

# Default values
FILE="diagram.mmd"
HOST="127.0.0.1"
PORT="5000"
DEBUG=""

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [FILE] [OPTIONS]

Starts the Ariel Mermaid diagram viewer server.

ARGUMENTS:
    FILE                    Path to the .mmd file to watch (default: diagram.mmd)

OPTIONS:
    -h, --host HOST         Host to bind to (default: 127.0.0.1)
    -p, --port PORT         Port to bind to (default: 5000)
    -d, --debug             Enable debug mode
    --help                  Show this help message

EXAMPLES:
    # Start with default settings
    $0

    # Watch a specific file
    $0 my_diagram.mmd

    # Watch a specific file on custom port
    $0 my_diagram.mmd -p 8080

    # Enable debug mode
    $0 diagram.mmd -d

EOF
    exit 1
}

# Parse command line arguments
# Check if first argument is the file (doesn't start with -)
if [[ $# -gt 0 && ! "$1" =~ ^- ]]; then
    FILE="$1"
    shift
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG="--debug"
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if ariel.py exists
if [ ! -f "$SCRIPT_DIR/ariel.py" ]; then
    echo -e "${RED}Error: ariel.py not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Check for and activate virtual environment
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source "$SCRIPT_DIR/venv/bin/activate"
    PYTHON_CMD="$SCRIPT_DIR/venv/bin/python3"
else
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 is not installed${NC}"
        exit 1
    fi
    PYTHON_CMD="python3"

    # Check if Flask is installed
    if ! python3 -c "import flask" 2>/dev/null; then
        echo -e "${YELLOW}Warning: Flask is not installed${NC}"
        echo -e "Install it with: pip install flask"
        echo -e "Or create a virtual environment: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        echo -e "Attempting to install Flask..."
        pip install flask || {
            echo -e "${RED}Error: Failed to install Flask${NC}"
            echo -e "Please install Flask manually: pip install flask"
            exit 1
        }
    fi
fi

# Build command
CMD="$PYTHON_CMD $SCRIPT_DIR/ariel.py \"$FILE\" --host $HOST --port $PORT"

if [ -n "$DEBUG" ]; then
    CMD="$CMD $DEBUG"
fi

# Display startup information
echo -e "${GREEN}Starting Ariel Mermaid Diagram Viewer...${NC}"
echo -e "File: $FILE"
echo -e "Server: http://$HOST:$PORT"
echo ""

# Create a sample diagram if the file doesn't exist
if [ ! -f "$FILE" ]; then
    echo -e "${YELLOW}Warning: $FILE not found. Creating a sample diagram...${NC}"
    cat > "$FILE" << 'DIAGRAM'
graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Check the logs]
    C --> E[Edit this file to see changes]
    D --> E
    E --> F[Save the file]
    F --> G[Watch it update automatically!]
DIAGRAM
    echo -e "${GREEN}Sample diagram created: $FILE${NC}"
    echo ""
fi

# Run the server
eval $CMD
