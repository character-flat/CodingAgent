#!/bin/bash

echo "Starting services..."

# Make sure we have the right directories
mkdir -p /workspaces/CodingAgent/agent/workspace
mkdir -p /workspaces/CodingAgent/agent/outputs
mkdir -p /workspaces/CodingAgent/agent/context

# Kill any existing processes
echo "Cleaning up any existing processes..."
pkill -f Xvfb || true
pkill -f x11vnc || true
pkill -f websockify || true
pkill -f xfce4 || true

# Set up display
echo "Setting up display..."
export DISPLAY=:1
Xvfb $DISPLAY -screen 0 1280x800x24 &
sleep 2  # Wait for Xvfb to start

# Check if Xvfb is running
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "ERROR: Xvfb failed to start."
    exit 1
fi

# Start XFCE desktop
echo "Starting XFCE desktop..."
startxfce4 &
sleep 3  # Give it time to start

# Start VNC server
echo "Starting VNC server..."
x11vnc -display $DISPLAY -forever -shared -rfbport 5900 &
sleep 2  # Wait for VNC server to start

# Check if x11vnc is running
if ! pgrep -x "x11vnc" > /dev/null; then
    echo "ERROR: x11vnc failed to start."
    exit 1
fi

# Download and setup noVNC if it doesn't exist
if [ ! -d "/opt/noVNC" ]; then
    echo "Setting up noVNC..."
    sudo mkdir -p /opt/noVNC
    sudo git clone https://github.com/novnc/noVNC.git /opt/noVNC
    sudo git clone https://github.com/novnc/websockify /opt/noVNC/utils/websockify
fi

# Start noVNC
echo "Starting noVNC..."
/opt/noVNC/utils/launch.sh --vnc localhost:5900 --listen 6080 &
sleep 2

# Verify ports are active
echo "Checking if ports are active..."
echo "VNC port 5900: $(netstat -tuln | grep 5900 || echo 'NOT ACTIVE')"
echo "noVNC port 6080: $(netstat -tuln | grep 6080 || echo 'NOT ACTIVE')"

echo "======================================"
echo "Services started!"
echo "VNC Web Interface: http://localhost:6080/vnc.html"
echo "API Server: http://localhost:8000"
echo "======================================"

# Keep script running to keep services active
tail -f /dev/null