import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QFileDialog, QSystemTrayIcon
from PyQt6.QtGui import QPainter, QPen, QGuiApplication, QAction, QIcon, QCursor
from PyQt6.QtCore import Qt, QRect, QPoint, QObject, pyqtSignal, pyqtSlot
from pynput import keyboard
from PIL import Image
import mss

class SnippingWidget(QWidget):
    """
    A full-screen, transparent widget to select a screen region for capture.
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_snipping = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(Qt.GlobalColor.black)
        painter.setOpacity(0.3)
        painter.drawRect(self.rect())

        if self.is_snipping:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(QRect(self.begin, self.end).normalized(), Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.SolidLine))
            painter.drawRect(QRect(self.begin, self.end).normalized())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.close()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_snipping = True
            self.begin = event.pos()
            self.end = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_snipping:
            self.is_snipping = False
            self.hide()
            QApplication.processEvents()
            selection_rect = QRect(self.begin, self.end).normalized()
            if selection_rect.width() > 0 and selection_rect.height() > 0:
                self.capture_screen(selection_rect)
        self.close()

    def capture_screen(self, rect):
        """
        Captures the selected area, ensuring it does not include protected
        system UI like the taskbar to prevent crashes on Linux.
        """
        # Get the available screen geometry (this excludes taskbars/panels)
        available_geo = QGuiApplication.primaryScreen().availableGeometry()

        # Find the intersection of the user's selection and the available area.
        # This effectively crops the selection to a "safe" capturable zone.
        safe_capture_rect_qt = rect.intersected(available_geo)

        # If the resulting rectangle is invalid or has no area, do nothing.
        if not safe_capture_rect_qt.isValid() or safe_capture_rect_qt.isEmpty():
            print("Selection is outside the capturable area.")
            return

        # Adjust for device pixel ratio for high-DPI displays
        device_pixel_ratio = self.devicePixelRatioF()
        capture_rect = {
            "top": int(safe_capture_rect_qt.top() * device_pixel_ratio),
            "left": int(safe_capture_rect_qt.left() * device_pixel_ratio),
            "width": int(safe_capture_rect_qt.width() * device_pixel_ratio),
            "height": int(safe_capture_rect_qt.height() * device_pixel_ratio),
        }
        
        # Final check to ensure we have a valid capture size
        if capture_rect["width"] <= 0 or capture_rect["height"] <= 0:
            print("Selection is too small to capture.")
            return

        with mss.mss() as sct:
            # Wrap the grab call in a try...except block for maximum stability
            try:
                sct_img = sct.grab(capture_rect)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                self.save_image(img)
            except mss.exception.ScreenShotError as e:
                print(f"Could not capture the screen: {e}")


    def save_image(self, img):
        pictures_path = os.path.join(os.path.expanduser('~'), 'Pictures')
        if not os.path.exists(pictures_path):
            os.makedirs(pictures_path)
        filePath, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot", os.path.join(pictures_path, "screenshot.png"), "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        if filePath:
            img.save(filePath)

class ScreenshotApplication(QApplication):
    """
    The main application class, inheriting from QApplication for better
    compatibility on Linux systems. It manages the tray icon and hotkey listener.
    """
    # Using a signal is still good practice for thread safety with pynput
    start_snipping_signal = pyqtSignal()

    def __init__(self, args):
        super().__init__(args)
        # The app should run in the background without a main window.
        self.setQuitOnLastWindowClosed(False)
        
        self.snipping_widget = None

        # --- System Tray Icon Setup ---
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use a standard icon theme if available, with a fallback
        try:
            self.tray_icon.setIcon(QIcon.fromTheme("camera-photo"))
        except:
            pixmap = QGuiApplication.primaryScreen().grabWindow(0, 0, 0, 16, 16)
            self.tray_icon.setIcon(QIcon(pixmap))

        self.tray_icon.setToolTip("Screenshot App")

        # Create the context menu
        tray_menu = QMenu()
        take_screenshot_action = QAction("Take Screenshot", self)
        take_screenshot_action.triggered.connect(self.activate_snipping)
        tray_menu.addAction(take_screenshot_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit) # Connect to the app's quit method
        tray_menu.addAction(exit_action)
        
        # Assign the menu to the tray icon
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        # --- End of Tray Icon Setup ---

        # Connect signal for thread-safe GUI calls
        self.start_snipping_signal.connect(self.activate_snipping)

        # Start the keyboard listener
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        
        # Connect the cleanup function to run when the application is about to quit
        self.aboutToQuit.connect(self.cleanup)

    @pyqtSlot()
    def activate_snipping(self):
        """Creates and shows the snipping widget."""
        # Ensure only one snipping widget is active at a time
        if not self.snipping_widget or not self.snipping_widget.isVisible():
            self.snipping_widget = SnippingWidget()
            self.snipping_widget.show()
            self.snipping_widget.activateWindow()
            self.snipping_widget.raise_()

    def on_press(self, key):
        """Callback for the keyboard listener (runs in a separate thread)."""
        if key == keyboard.Key.print_screen:
            self.start_snipping_signal.emit()

    def cleanup(self):
        """Stops the keyboard listener thread when the app quits."""
        self.listener.stop()
        print("Keyboard listener stopped.")

if __name__ == "__main__":
    # Instantiate our custom application class
    app = ScreenshotApplication(sys.argv)
    
    print("Screenshot app is running in the background.")
    print("Press 'Print Screen' to capture or right-click the tray icon.")
    
    # Start the application's event loop
    sys.exit(app.exec())
