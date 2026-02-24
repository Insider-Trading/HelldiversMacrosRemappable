"""
Reusable widgets for Helldivers Remappable Macros
"""

import time
import winsound
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QDrag
from PyQt6.QtCore import QMimeData

import keyboard
from ..config.config import find_svg_path


class Comm(QObject):
    update_test_display = pyqtSignal(str, list, str)


comm = Comm()


class DraggableIcon(QWidget):
    """Draggable stratagem icon widget for sidebar"""
    
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.setProperty("role", "icon")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.svg_view = QSvgWidget()
        path = find_svg_path(name)
        if path:
            self.svg_view.load(path)
        
        layout.addWidget(self.svg_view)
        self.setToolTip(name)

    def mousePressEvent(self, event):
        """Handle mouse press for drag operation"""
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.name)
            mime.setData("source", b"sidebar")
            drag.setMimeData(mime)
            drag.setPixmap(self.grab())
            drag.exec(Qt.DropAction.MoveAction)


class NumpadSlot(QWidget):
    """Numpad slot widget for assigning stratagems"""
    
    def __init__(self, slot_id, scan_code, label_text, parent_app):
        super().__init__()
        self.slot_id = slot_id
        self.scan_code = int(scan_code)
        self.label_text = label_text
        self.parent_app = parent_app
        self.assigned_stratagem = None
        self.is_remapping = False
        
        self.setProperty("role", "numpad-slot")
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        
        self.layout = QVBoxLayout(self)
        self.label = QLabel(label_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
        
        self.svg_display = QSvgWidget()
        self.layout.addWidget(self.svg_display, alignment=Qt.AlignmentFlag.AlignCenter)
        self.svg_display.hide()
        
        self.update_style(False)

    def update_style(self, assigned):
        """Update visual style based on whether slot is assigned or remapping"""
        if self.is_remapping:
            border_style, color, bg = "solid", "#3ddc84", "#102010"
            cursor = Qt.CursorShape.WaitCursor
            hover_border, hover_bg = "#3ddc84", "#102010"
        elif assigned:
            border_style, color, bg = "solid", "#ffcc00", "#151515"
            cursor = Qt.CursorShape.PointingHandCursor
            hover_border, hover_bg = "#ff4444", "#201010"
        else:
            border_style, color, bg = "dashed", "#444", "#0a0a0a"
            cursor = Qt.CursorShape.ArrowCursor
            hover_border, hover_bg = "#ffcc00", "#151515"
        
        self.setCursor(cursor)
        self.setStyleSheet(
            f"QWidget {{ border: 2px {border_style} {color}; background: {bg}; "
            f"color: #888; border-radius: 8px; font-weight: bold; }} "
            f"QWidget:hover {{ border: 2px solid {hover_border}; background: {hover_bg}; }}"
        )

    def mousePressEvent(self, event):
        """Handle mouse press for clearing, dragging, or remapping"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.start_remapping()
            return

        if event.button() == Qt.MouseButton.RightButton:
            if self.assigned_stratagem:
                self.clear_slot()
            return

        if event.button() == Qt.MouseButton.LeftButton and self.assigned_stratagem:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.assigned_stratagem)
            mime.setData("source_slot", str(self.slot_id).encode())
            drag.setMimeData(mime)
            drag.setPixmap(self.grab())
            drag.exec(Qt.DropAction.MoveAction)

    def start_remapping(self):
        """Enter remapping mode"""
        self.is_remapping = True
        self.label.setText("Press any key...")
        self.label.show()
        self.svg_display.hide()
        self.update_style(False)
        self.setFocus()

    def keyPressEvent(self, event):
        """Capture key press for remapping"""
        if self.is_remapping:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self.cancel_remapping()
                return

            # Get scan code and key name
            scan_code = event.nativeScanCode()
            key_name = event.text().upper()
            if not key_name or ord(key_name[0]) < 32:
                # Fallback for special keys
                key_name = self._get_key_name(key)

            self.scan_code = scan_code
            self.label_text = key_name
            self.is_remapping = False
            
            if self.assigned_stratagem:
                self.assign(self.assigned_stratagem)
            else:
                self.label.setText(self.label_text)
                self.update_style(False)
            
            self.parent_app.on_change()
            self.parent_app.show_status(f"Bound to {key_name}")
        else:
            super().keyPressEvent(event)

    def cancel_remapping(self):
        """Cancel remapping mode"""
        self.is_remapping = False
        if self.assigned_stratagem:
            self.assign(self.assigned_stratagem)
        else:
            self.label.setText(self.label_text)
            self.update_style(False)

    def _get_key_name(self, key):
        """Get a human-readable name for special keys"""
        key_map = {
            Qt.Key.Key_Return: "ENT",
            Qt.Key.Key_Enter: "ENT",
            Qt.Key.Key_Space: "SPC",
            Qt.Key.Key_Tab: "TAB",
            Qt.Key.Key_Backspace: "BS",
            Qt.Key.Key_Delete: "DEL",
            Qt.Key.Key_Insert: "INS",
            Qt.Key.Key_Home: "HOME",
            Qt.Key.Key_End: "END",
            Qt.Key.Key_PageUp: "PGUP",
            Qt.Key.Key_PageDown: "PGDN",
            Qt.Key.Key_Left: "LEFT",
            Qt.Key.Key_Right: "RGHT",
            Qt.Key.Key_Up: "UP",
            Qt.Key.Key_Down: "DOWN",
            Qt.Key.Key_CapsLock: "CAPS",
            Qt.Key.Key_Shift: "SHFT",
            Qt.Key.Key_Control: "CTRL",
            Qt.Key.Key_Alt: "ALT",
        }
        return key_map.get(key, "KEY")
    
    def mouseDoubleClickEvent(self, event):
        """Double click to start remapping"""
        self.start_remapping()
        event.accept()

    def dragEnterEvent(self, event):
        """Accept drag enter events"""
        event.accept()

    def dropEvent(self, event):
        """Handle drop events for swapping or assigning stratagems"""
        incoming_strat = event.mimeData().text()
        source_slot_code = event.mimeData().data("source_slot").data().decode()

        if source_slot_code:
            source_slot = self.parent_app.slots.get(source_slot_code)
            if source_slot and source_slot != self:
                existing_strat = self.assigned_stratagem
                if existing_strat:
                    source_slot.assign(existing_strat)
                else:
                    source_slot.clear_slot()
                self.assign(incoming_strat)
        else:
            self.assign(incoming_strat)
        
        event.accept()

    def clear_slot(self):
        """Clear the slot assignment"""
        self.assigned_stratagem = None
        self.svg_display.hide()
        self.label.show()
        self.update_style(False)
        self.parent_app.on_change()

    def assign(self, strat_name):
        """Assign a stratagem to this slot"""
        self.assigned_stratagem = strat_name
        path = find_svg_path(strat_name)
        if path:
            self.label.hide()
            self.svg_display.load(path)
            self.svg_display.show()
            self.update_style(True)
        self.parent_app.on_change()

    def run_macro(self, name, sequence, key_label):
        """Execute the macro for this slot"""
        comm.update_test_display.emit(name, sequence, key_label)
        delay = self.parent_app.speed_slider.value() / 1000.0
        
        for move in sequence:
            actual_key = self.parent_app.map_direction_to_key(move)
            keyboard.press(actual_key)
            time.sleep(delay)
            keyboard.release(actual_key)
            time.sleep(delay)
        
        if self.parent_app.global_settings.get("sound_enabled", True):
            try:
                winsound.Beep(1000, 200)
            except:
                pass
        
        if self.parent_app.global_settings.get("visual_enabled", True):
            self.parent_app.show_status(f"✓ {name} executed", 1500)


class CollapsibleDepartmentHeader(QWidget):
    """Clickable department header that can be collapsed/expanded"""
    
    def __init__(self, department_name, parent_app=None):
        super().__init__()
        self.department_name = department_name
        self.parent_app = parent_app
        self.is_expanded = True
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header_label = QLabel()
        self.header_label.setObjectName("department_header")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.update_header_display()
        
        layout.addWidget(self.header_label)
        self.setLayout(layout)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def update_header_display(self):
        """Update the header display with expand/collapse arrow"""
        arrow = "▼" if self.is_expanded else "▶"
        self.header_label.setText(f"{arrow} {self.department_name}")
    
    def mousePressEvent(self, event):
        """Handle click to toggle collapse/expand"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_collapse()
            event.accept()
    
    def toggle_collapse(self):
        """Toggle the collapse/expand state"""
        self.is_expanded = not self.is_expanded
        self.update_header_display()
        
        # Notify parent app to update visibility
        if self.parent_app and hasattr(self.parent_app, 'update_department_visibility'):
            self.parent_app.update_department_visibility(self.department_name, self.is_expanded)
