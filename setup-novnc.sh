#!/bin/bash

# Terminate any existing processes
pkill -f Xvfb || true
pkill -f x11vnc || true
pkill -f fluxbox || true
pkill -f websockify || true
pkill -f vncserver || true

# Remove old lock files
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1

# Ensure packages are installed
sudo apt-get update
sudo apt-get install -y \
  tigervnc-standalone-server \
  tigervnc-common \
  fluxbox \
  websockify

# Set up a password for x11vnc
mkdir -p ~/.vnc
echo "mypassword" | vncpasswd -f > ~/.vnc/passwd
chmod 600 ~/.vnc/passwd

# Launch Xvfb
export DISPLAY=:1
Xvfb :1 -screen 0 1280x800x24 &
sleep 2

# Launch fluxbox on that display
fluxbox &

# Start x11vnc server on port 5901, with password
x11vnc -display :1 -rfbauth ~/.vnc/passwd -forever -shared -rfbport 5901 &
sleep 2

# Use websockify to provide a websocket-based VNC connection on port 6080
# For noVNC web files, we can use /usr/share/novnc if present, else fallback to simple websockify
sudo mkdir -p /usr/share/novnc
# If you already have noVNC locally, point --web to that path; otherwise this will just serve a blank page
websockify --web /usr/share/novnc 6080 localhost:5901 &
sleep 2

echo "======================================================="
echo "VNC server running on port 5901."
echo "Websocket-based VNC on port 6080 via websockify."
echo "Try http://localhost:6080/vnc.html (if no files exist in /usr/share/novnc, please copy or clone them)."
echo "VNC password: mypassword"
echo "======================================================="