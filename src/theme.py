from PyQt5.QtCore import QObject, pyqtSignal, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt5.QtGui import QPalette, QColor, QPainter, QBrush
import json
import os
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QRect

class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.accent_color = "#1976d2"
        self.gradient = "None"
        self.load_theme_settings()
    
    def load_theme_settings(self):
        """Load theme settings from config file"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'theme.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                    self.current_theme = settings.get('theme', 'light')
                    self.accent_color = settings.get('accent_color', '#1976d2')
                    self.gradient = settings.get('gradient', 'None')
        except Exception:
            pass
    
    def save_theme_settings(self):
        """Save theme settings to config file"""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, 'theme.json')
        try:
            settings = {
                'theme': self.current_theme,
                'accent_color': self.accent_color,
                'gradient': self.gradient
            }
            with open(config_path, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass
    
    def set_theme(self, theme):
        """Set the current theme and emit change signal"""
        self.current_theme = theme
        self.save_theme_settings()
        self.theme_changed.emit(theme)
    
    def set_accent_color(self, color):
        """Set the accent color"""
        self.accent_color = color
        self.save_theme_settings()
    
    def set_gradient(self, gradient):
        """Set the background gradient"""
        self.gradient = gradient
        self.save_theme_settings()
    
    def get_button_stylesheet(self):
        """Get theme-aware button stylesheet with pressed state animation"""
        transition = "transition: background-color 0.2s, border-color 0.2s;"
        if self.current_theme == "dark":
            return f"""
                QPushButton {{
                    background-color: {self.accent_color};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    {transition}
                }}
                QPushButton:hover {{
                    background-color: {self._adjust_color(self.accent_color, 20)};
                    {transition}
                }}
                QPushButton:pressed {{
                    background-color: {self._adjust_color(self.accent_color, -20)};
                    {transition}
                }}
                QPushButton:disabled {{
                    background-color: #666;
                    color: #999;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {self.accent_color};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    {transition}
                }}
                QPushButton:hover {{
                    background-color: {self._adjust_color(self.accent_color, 20)};
                    {transition}
                }}
                QPushButton:pressed {{
                    background-color: {self._adjust_color(self.accent_color, -20)};
                    {transition}
                }}
                QPushButton:disabled {{
                    background-color: #ccc;
                    color: #666;
                }}
            """
    
    def get_section_title_stylesheet(self):
        """Get theme-aware section title stylesheet"""
        if self.current_theme == "dark":
            return f"""
                QLabel {{
                    color: {self.accent_color};
                    font-size: 18px;
                    font-weight: bold;
                    padding: 8px 0;
                }}
            """
        else:
            return f"""
                QLabel {{
                    color: {self.accent_color};
                    font-size: 18px;
                    font-weight: bold;
                    padding: 8px 0;
                }}
            """
    
    def get_bill_summary_total_stylesheet(self):
        """Get theme-aware bill total stylesheet"""
        if self.current_theme == "dark":
            return f"""
                QLabel {{
                    color: {self.accent_color};
                    font-size: 20px;
                    font-weight: bold;
                    padding: 8px;
                    background-color: #2a2a2a;
                    border-radius: 4px;
                }}
            """
        else:
            return f"""
                QLabel {{
                    color: {self.accent_color};
                    font-size: 20px;
                    font-weight: bold;
                    padding: 8px;
                    background-color: #f5f5f5;
                    border-radius: 4px;
                }}
            """
    
    def get_table_stylesheet(self):
        """Get theme-aware table stylesheet"""
        if self.current_theme == "dark":
            return f"""
                QTableWidget {{
                    background-color: #2a2a2a;
                    color: white;
                    gridline-color: #444;
                    border: 1px solid #444;
                }}
                QTableWidget::item {{
                    padding: 4px;
                }}
                QTableWidget::item:selected {{
                    background-color: {self.accent_color};
                }}
                QHeaderView::section {{
                    background-color: #3a3a3a;
                    color: white;
                    padding: 8px;
                    border: 1px solid #444;
                    font-weight: bold;
                }}
            """
        else:
            return f"""
                QTableWidget {{
                    background-color: white;
                    color: black;
                    gridline-color: #ddd;
                    border: 1px solid #ddd;
                }}
                QTableWidget::item {{
                    padding: 4px;
                }}
                QTableWidget::item:selected {{
                    background-color: {self.accent_color};
                    color: white;
                }}
                QHeaderView::section {{
                    background-color: #f5f5f5;
                    color: black;
                    padding: 8px;
                    border: 1px solid #ddd;
                    font-weight: bold;
                }}
            """
    
    def get_dialog_stylesheet(self):
        """Get theme-aware dialog stylesheet"""
        if self.current_theme == "dark":
            return f"""
                QDialog {{
                    background-color: #2a2a2a;
                    color: white;
                }}
                QLabel {{
                    color: white;
                }}
                QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                    background-color: #3a3a3a;
                    color: white;
                    border: 1px solid #555;
                    padding: 4px;
                    border-radius: 2px;
                }}
                QGroupBox {{
                    color: white;
                    font-weight: bold;
                    border: 1px solid #555;
                    margin-top: 8px;
                    padding-top: 8px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px 0 4px;
                }}
            """
        else:
            return f"""
                QDialog {{
                    background-color: white;
                    color: black;
                }}
                QLabel {{
                    color: black;
                }}
                QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                    padding: 4px;
                    border-radius: 2px;
                }}
                QGroupBox {{
                    color: black;
                    font-weight: bold;
                    border: 1px solid #ccc;
                    margin-top: 8px;
                    padding-top: 8px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px 0 4px;
                }}
            """
    
    def get_main_window_stylesheet(self):
        """Get theme-aware main window stylesheet"""
        base_style = self.get_dialog_stylesheet()
        if self.current_theme == "dark":
            base_style += """
                QMainWindow, QWidget {
                    background-color: #404040;
                    color: white;
                }
            """
        if self.gradient != "None":
            gradient_style = self._get_gradient_style()
            return base_style + gradient_style
        return base_style
    
    def _get_gradient_style(self):
        """Get gradient background style"""
        if self.gradient == "Blue to White":
            return f"""
                QWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self.accent_color}, stop:1 #ffffff);
                }}
            """
        elif self.gradient == "Purple to Pink":
            return """
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8e24aa, stop:1 #ff4081);
                }
            """
        elif self.gradient == "Green to Blue":
            return """
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #43cea2, stop:1 #185a9d);
                }
            """
        elif self.gradient == "Grey to Black":
            return """
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e0e0e0, stop:1 #212121);
                }
            """
        return ""
    
    def _adjust_color(self, color, amount):
        """Adjust color brightness by amount"""
        # Simple color adjustment - in production, use proper color manipulation
        if amount > 0:
            return self._lighten_color(color, amount)
        else:
            return self._darken_color(color, abs(amount))
    
    def _lighten_color(self, color, amount):
        """Lighten a color by amount"""
        # Simple implementation - in production, use proper color manipulation
        return color
    
    def _darken_color(self, color, amount):
        """Darken a color by amount"""
        # Simple implementation - in production, use proper color manipulation
        return color

# Remove AnimatedButton and revert to standard QPushButton with theme styling

def create_animated_button(text, parent=None, color=None, pressed_color=None, duration=150):
    from theme import theme_manager
    btn = QPushButton(text, parent)
    btn.setStyleSheet(theme_manager.get_button_stylesheet())
    return btn

# Global theme manager instance
theme_manager = ThemeManager()
