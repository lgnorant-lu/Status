# mypy: disable-error-code="attr-defined,unused-ignore,no-redef,unreachable,method-assign"
# tests/_qt_mock_definitions.py
"""
---------------------------------------------------------------
File name:                  _qt_mock_definitions.py
Author:                     Ignorant-lu
Date created:               2025/05/16 (Adapted from mocks.py)
Description:                纯粹的Qt模拟类定义，用于测试。
----------------------------------------------------------------
"""
from typing import Type, Any, List, Optional, cast
from enum import Enum, auto
import sys # For QApplication's argv default

class QObject:
    """模拟的QObject基类"""
    def __init__(self) -> None:
        pass

    def parent(self) -> Optional['QObject']: # Common method
        return None

    def deleteLater(self) -> None: # Common method
        pass

class Signal:
    """模拟的Signal类，用于测试"""
    def __init__(self, *args: Any) -> None: # Accept any signature for signal declaration
        self._callbacks: List[Any] = []
    
    def connect(self, callback: Any) -> None:
        if callback not in self._callbacks: # Avoid duplicate connections for simplicity
            self._callbacks.append(callback)
    
    def disconnect(self, callback: Any = None) -> None:
        if callback is None:
            self._callbacks.clear()
        elif callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def emit(self, *args: Any) -> None:
        # Iterate over a copy in case a callback modifies the list during emission
        for cb in list(self._callbacks):
            cb(*args)

pyqtSignal: Type[Signal] = Signal # In this file, pyqtSignal is always the mock Signal

# Define QIcon and QMenu before QAction if QAction uses them directly in __init__ type hints
# or use string forward references consistently.

class QIcon:
    """模拟的QIcon类"""
    def __init__(self, icon_path_or_theme: Optional[str] = None) -> None:
        self.path: Optional[str] = None
        self.theme_name: Optional[str] = None
        
        if icon_path_or_theme:
            # Corrected string literal for checking file path characters
            if any(c in icon_path_or_theme for c in '/.\\'): # Added backslash for windows paths
                self.path = icon_path_or_theme
            else: 
                self.theme_name = icon_path_or_theme
        
        self._null: bool = not (self.path or self.theme_name)

    def isNull(self) -> bool:
        return self._null

    @staticmethod
    def fromTheme(theme_name: str, fallback: Optional['QIcon'] = None) -> 'QIcon':
        icon = QIcon() # Recursive static method call, ensure mypy is ok or ignore if truly needed
        icon.theme_name = theme_name
        icon._null = False 
        return icon

    def name(self) -> str: 
        return self.theme_name or self.path or ""

class QMenu(QObject): 
    """模拟的QMenu类"""
    aboutToShow = Signal()
    aboutToHide = Signal()
    # The triggered signal of QMenu emits the QAction that was triggered.
    # So its type should be Signal(QAction) - needs QAction to be defined or forward referenced.
    # triggered = Signal(QAction) # This needs QAction to be defined first or use 'QAction' string

    def __init__(self, title_or_parent: Any = None, parent: Optional[QObject] = None) -> None:
        super().__init__()
        self._title_str: str
        self._parent_widget_obj: Optional[QObject]

        if isinstance(title_or_parent, str) and parent is None:
            self._title_str = title_or_parent
            self._parent_widget_obj = None 
        elif isinstance(title_or_parent, QObject): 
            self._title_str = ""
            self._parent_widget_obj = title_or_parent
        else: 
            self._title_str = ""
            self._parent_widget_obj = parent

        self._actions_list: List['QAction'] = [] # Use string literal for QAction
        self.object_name: str = ""
        # Add triggered signal after QAction is defined or ensure consistent forward reference
        self.triggered = Signal('QAction')

    def parent(self) -> Optional[QObject]: return self._parent_widget_obj

    def title(self) -> str: return self._title_str
    def setTitle(self, title: str) -> None: self._title_str = title

    def addAction(self, action_or_text_or_icon: Any, triggered_slot: Optional[Any] = None, shortcut: Optional[str] = None) -> 'QAction':
        action: 'QAction' # Use string literal
        if isinstance(action_or_text_or_icon, QAction): # QAction here refers to the class
            action = action_or_text_or_icon
        elif isinstance(action_or_text_or_icon, str):
            action = QAction(action_or_text_or_icon, self)
        elif isinstance(action_or_text_or_icon, QIcon):
            # 创建一个带图标的动作，使用空字符串作为文本
            icon_action = QAction("", self)
            icon_action._icon = action_or_text_or_icon
            action = icon_action
        else: 
            action = QAction(str(action_or_text_or_icon), self)

        if triggered_slot:
            action.triggered.connect(triggered_slot)
        if shortcut:
            action.setShortcut(shortcut)
            
        self._actions_list.append(action)
        return action

    def addMenu(self, menu_or_title_or_icon: Any) -> 'QMenu':
        menu: 'QMenu' # Use string literal
        if isinstance(menu_or_title_or_icon, QMenu):
            menu = menu_or_title_or_icon
            # Check if menuAction (which returns a QAction) is in _actions_list
            # This requires menuAction to be callable and return a QAction instance
            menu_act = menu.menuAction()
            if menu_act not in self._actions_list:
                 self._actions_list.append(menu_act)
        elif isinstance(menu_or_title_or_icon, QIcon):
            menu = QMenu(parent=self)
            # 创建一个带图标的动作
            action_for_menu = QAction("", self)
            action_for_menu._icon = menu_or_title_or_icon
            action_for_menu._text = menu.title() or "Submenu"
            action_for_menu.setMenu(menu)
            self._actions_list.append(action_for_menu)
        else: 
            menu = QMenu(str(menu_or_title_or_icon), self)
            action_for_menu = QAction(menu.title(), self)
            action_for_menu.setMenu(menu)
            self._actions_list.append(action_for_menu)
        return menu
    
    def menuAction(self) -> 'QAction': 
        if not hasattr(self, '_menu_action_instance_attr'): 
            # 创建一个菜单的Action
            self._menu_action_instance_attr = QAction(self.title(), self._parent_widget_obj)
            self._menu_action_instance_attr.setMenu(self)
        return self._menu_action_instance_attr

    def addSeparator(self) -> 'QAction':
        action = QAction("", self)
        setattr(action, '_is_separator', True)
        self._actions_list.append(action)
        return action

    def clear(self) -> None:
        self._actions_list.clear()

    def actions(self) -> List['QAction']:
        return list(self._actions_list)

    def exec(self, pos: Optional[Any] = None, at: Optional['QAction'] = None) -> Optional['QAction']:
        self.aboutToShow.emit()
        print(f"Mock QMenu '{self.title()}' exec() called. Simulating user selecting first action if available.")
        selected_action: Optional['QAction'] = None
        if self._actions_list:
            current_action = self._actions_list[0]
            if not getattr(current_action, '_is_separator', False) and current_action.isEnabled():
                 action_menu = current_action.menu()
                 if action_menu: 
                     action_menu.exec() 
                 else:
                     current_action.triggered.emit() 
                 # self.triggered is Signal(QAction), so it expects a QAction instance.
                 self.triggered.emit(current_action)
                 selected_action = current_action
            else:
                selected_action = None 
        self.aboutToHide.emit()
        return selected_action

    def isEmpty(self) -> bool:
        return not bool(self._actions_list)

    def popup(self, pos: Any, action: Optional['QAction'] = None) -> None:
        self.exec(pos, at=action)

class QAction(QObject):
    """模拟的QAction类"""
    triggered = Signal()
    toggled = Signal(bool) # Common signal with a boolean payload
    hovered = Signal()

    def __init__(self, text_or_icon: Any = "", parent: Optional[QObject] = None) -> None:
        super().__init__()
        self._icon: Optional[QIcon]
        self._text: str

        if isinstance(text_or_icon, QIcon): # Can be initialized with QIcon too
            self._icon = text_or_icon
            self._text = ""
        else:
            self._icon = None
            self._text = str(text_or_icon)
        
        self._parent_obj: Optional[QObject] = parent # Renamed to avoid clash with method
        self.object_name: str = ""
        self._data: Any = None
        self._enabled: bool = True
        self._checkable: bool = False
        self._checked: bool = False
        self._visible: bool = True
        self._tooltip: str = ""
        self._shortcut: str = ""
        self._menu: Optional[QMenu] = None

    def text(self) -> str: return self._text
    def setText(self, text: str) -> None: self._text = text
    
    def parent(self) -> Optional[QObject]: return self._parent_obj

    def setObjectName(self, name: str) -> None: self.object_name = name
    def objectName(self) -> str: return self.object_name
    
    def setData(self, data: Any) -> None: self._data = data
    def data(self) -> Any: return self._data
    
    def setEnabled(self, enabled: bool) -> None: self._enabled = enabled
    def isEnabled(self) -> bool: return self._enabled
    
    def setCheckable(self, checkable: bool) -> None: self._checkable = checkable
    def isCheckable(self) -> bool: return self._checkable
    
    def setChecked(self, checked: bool) -> None:
        if self._checkable:
            self._checked = checked
            self.toggled.emit(self._checked) # Emit toggled when checked state changes
    def isChecked(self) -> bool: return self._checked

    def setVisible(self, visible: bool) -> None: self._visible = visible
    def isVisible(self) -> bool: return self._visible

    def setToolTip(self, tip: str) -> None: self._tooltip = tip
    def toolTip(self) -> str: return self._tooltip

    def setShortcut(self, shortcut: str) -> None: self._shortcut = shortcut # QKeySequence usually
    def shortcut(self) -> str: return self._shortcut

    def setMenu(self, menu: QMenu) -> None: self._menu = menu
    def menu(self) -> Optional[QMenu]: return self._menu


class QApplication(QObject):
    """模拟的QApplication类"""
    _instance_attr: Optional['QApplication'] = None # Renamed
    aboutToQuit = Signal()
    focusChanged = Signal(Optional[Any], Optional[Any]) 

    def __init__(self, argv: Optional[List[str]] = None) -> None:
        super().__init__()
        self.argv_list: List[str] = argv or sys.argv # Renamed
        if QApplication._instance_attr is None:
            QApplication._instance_attr = self
        
        self._display_name_str: str = "MockApp" # Renamed
        self._quit_called_bool: bool = False # Renamed
        self._window_icon_obj: Optional[QIcon] = None # Renamed
        self._style_sheet_str: str = "" # Renamed
        self._font_obj: Optional[Any] = None # Renamed
        self._palette_obj: Optional[Any] = None # Renamed


    @staticmethod
    def instance() -> Optional['QApplication']:
        return QApplication._instance_attr

    def setApplicationDisplayName(self, name: str) -> None: self._display_name_str = name
    def applicationDisplayName(self) -> str: return self._display_name_str
    
    def applicationName(self) -> str: return self._display_name_str 
    def setApplicationName(self, name: str) -> None: self._display_name_str = name

    def setWindowIcon(self, icon: QIcon) -> None: self._window_icon_obj = icon
    def windowIcon(self) -> Optional[QIcon]: return self._window_icon_obj

    def setStyleSheet(self, style_sheet: str) -> None: self._style_sheet_str = style_sheet
    def styleSheet(self) -> str: return self._style_sheet_str

    def exec_(self) -> int:
        print("Mock QApplication.exec_() called. Entering simulated event loop.")
        return 0
    exec = exec_ 

    def quit(self) -> None:
        print("Mock QApplication.quit() called")
        self.aboutToQuit.emit()
        self._quit_called_bool = True

    def exit(self, retcode: int = 0) -> None: 
        print(f"Mock QApplication.exit({retcode}) called")
        self.quit()

    @staticmethod
    def desktop() -> Optional[Any]: 
        print("Mock QApplication.desktop() called")
        class MockDesktop:
            screenCount = 1
            def screenGeometry(self, screen:int = -1) -> Any: 
                class MockRect: width=1920; height=1080; x=0; y=0; left=0; top=0; right=1919; bottom=1079
                return MockRect()
            def availableGeometry(self, screen:int = -1) -> Any: 
                return self.screenGeometry(screen)
        return MockDesktop()

    @staticmethod
    def palette(widget: Optional[Any] = None) -> Any: 
        print("Mock QApplication.palette() called")
        class MockPalette: pass
        return MockPalette()

    @staticmethod
    def setFont(font: Any, className: Optional[str] = None) -> None: 
        print(f"Mock QApplication.setFont({font}) called")
        if QApplication._instance_attr:
            QApplication._instance_attr._font_obj = font

    @staticmethod
    def font() -> Any: 
        print("Mock QApplication.font() called")
        if QApplication._instance_attr and QApplication._instance_attr._font_obj:
            return QApplication._instance_attr._font_obj
        class MockFont: pass # Define it before use
        return MockFont()
        
class QSystemTrayIcon(QObject):
    """模拟的QSystemTrayIcon类"""
    activated = Signal(Any) 
    messageClicked = Signal()
    
    class ActivationReason(Enum):
        Trigger = auto()
        DoubleClick = auto()
        MiddleClick = auto()
        Context = auto()
        Unknown = auto()
    
    Information = 1 
    Warning = 2
    Critical = 3
    NoIcon = 0 

    Trigger = ActivationReason.Trigger
    DoubleClick = ActivationReason.DoubleClick
    MiddleClick = ActivationReason.MiddleClick
    Context = ActivationReason.Context
    Unknown = ActivationReason.Unknown

    def __init__(self, icon_or_parent: Any = None, parent: Optional[QObject] = None) -> None:
        super().__init__()
        self._icon_obj: Optional[QIcon]
        self._parent_obj_st: Optional[QObject]

        if isinstance(icon_or_parent, QIcon):
            self._icon_obj = icon_or_parent # Renamed
            self._parent_obj_st = parent # Renamed
        elif isinstance(icon_or_parent, QObject): 
            self._icon_obj = None
            self._parent_obj_st = icon_or_parent
        else: 
            self._icon_obj = None
            self._parent_obj_st = parent
            
        self._visible_bool: bool = False # Renamed
        self._tooltip_str: str = "" # Renamed
        self._context_menu_obj: Optional[QMenu] = None # Renamed

    def parent(self) -> Optional[QObject]: return self._parent_obj_st

    def show(self) -> None: self._visible_bool = True
    def hide(self) -> None: self._visible_bool = False
    def isVisible(self) -> bool: return self._visible_bool

    def setIcon(self, icon: QIcon) -> None: self._icon_obj = icon
    def icon(self) -> Optional[QIcon]: return self._icon_obj

    def setToolTip(self, tooltip: str) -> None: self._tooltip_str = tooltip
    def toolTip(self) -> str: return self._tooltip_str

    def setContextMenu(self, menu: QMenu) -> None: self._context_menu_obj = menu
    def contextMenu(self) -> Optional[QMenu]: return self._context_menu_obj

    def showMessage(self, title: str, message: str, icon: Any = Information, 
                    millisecsTimeoutHint: int = 10000) -> None:
        print(f"Mock QSystemTrayIcon.showMessage: Title='{title}', Message='{message}', Icon='{icon}'")
