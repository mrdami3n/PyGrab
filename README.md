# PyGrab - A Simple Screenshot Tool for Linux

PyGrab is a lightweight, background screenshot utility for Linux desktops, built with Python and PyQt6. It is designed to be unobtrusive, activating with a global hotkey and providing simple controls through a system tray icon.

![688c7cb210460_download](https://github.com/user-attachments/assets/757a7f7e-5978-4db4-8813-704e77357b02)

## Features
Global Hotkey: Press the Print Screen key at any time to activate the snipping tool.

System Tray Integration: The application runs in the background and is accessible via a system tray icon.

Tray Menu: Right-click the tray icon to open a menu with options to "Take Screenshot" or "Exit" the application.

Region Snapping: Click and drag to select any part of your screen.

Safe Capture: Automatically avoids capturing protected areas like the taskbar, preventing crashes on Linux.

Cancel Actions: Press the Escape key or right-click while snipping to cancel the action.

## Installation
To run PyGrab from the source, you'll need Python 3 and the required libraries.

Clone the repository:

```
git clone [https://github.com/mrdami3n/pygrab.git](https://github.com/mrrdami3n/pygrab.git)
cd pygrab
```

Create and activate a virtual environment (recommended):

```
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:
The project uses a requirements.txt file to manage its dependencies. Install them with pip:

```
pip install -r requirements.txt
```

Usage
Once the dependencies are installed, you can run the application directly from the terminal:

```
python pygrab.py
```

The application will start in the background. You can now use the Print Screen key to take a screenshot or right-click the icon in your system tray for more options.

