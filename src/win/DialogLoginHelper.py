import time
import win32gui
import win32api
import win32con


def _screen_to_client(hwnd, sx, sy):
    cx, cy = win32gui.ScreenToClient(hwnd, (sx, sy))
    return int(cx), int(cy)


def _post_click(hwnd, cx, cy, delay=0.05):
    lp = win32api.MAKELONG(cx, cy)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
    time.sleep(delay)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lp)
 
COMBO_LBOX_CLASS = "ComboLBox"
COMBO_LBOX_ITEM_HEIGHT = 44
COMBO_LBOX_WAIT_TIME = 2
COMBO_LBOX_TOLERANCE = 5

class ControlInfo:
    def __init__(self, hwnd, cls_name, text, rect):
        self.hwnd = hwnd
        self.cls_name = cls_name
        self.text = text
        self.rect = rect
        self.width = rect[2] - rect[0]
        self.height = rect[3] - rect[1]
        self.center_x = int(round((rect[0] + rect[2]) / 2))
        self.center_y = int(round((rect[1] + rect[3]) / 2))

def _get_child_controls(hwnd):
    controls = []
    def enum_child_cb(child_hwnd, extra):
        cls_name = win32gui.GetClassName(child_hwnd)
        text = win32gui.GetWindowText(child_hwnd) or "无文本"
        rect = win32gui.GetWindowRect(child_hwnd)
        controls.append(ControlInfo(child_hwnd, cls_name, text, rect))
        return True
    win32gui.EnumChildWindows(hwnd, enum_child_cb, None)
    return controls

def _find_control_at(controls, sx, sy, tolerance=5):
    for ctrl in controls:
        if (ctrl.rect[0] - tolerance <= sx <= ctrl.rect[2] + tolerance and
                ctrl.rect[1] - tolerance <= sy <= ctrl.rect[3] + tolerance):
            return ctrl
    return None


def _find_dialog():
    candidates = []

    def enum_cb(h, extra):
        if win32gui.GetClassName(h) == "#32770":
            extra.append(h)
        return True

    win32gui.EnumWindows(enum_cb, candidates)
    for h in candidates:
        if win32gui.IsWindowVisible(h):
            return h
    return None


def _get_rect(hwnd):
    try:
        return win32gui.GetWindowRect(hwnd)
    except Exception:
        return None

def _find_combo_lbox_by_lt(parent_rect):
    parent_left, parent_top, parent_right, parent_bottom = parent_rect
    candidate_hwnds = []
    def enum_top_cb(hwnd, extra):
        if win32gui.GetClassName(hwnd) == COMBO_LBOX_CLASS:
            extra.append(hwnd)
        return True
    win32gui.EnumWindows(enum_top_cb, candidate_hwnds)
    for hwnd in candidate_hwnds:
        lbox_left, lbox_top, lbox_right, lbox_bottom = win32gui.GetWindowRect(hwnd)
        if lbox_left >= parent_left - COMBO_LBOX_TOLERANCE and lbox_top >= parent_top - COMBO_LBOX_TOLERANCE:
            return hwnd
    return None

def _click_combo_lbox_item(hwnd, n):
    rect = win32gui.GetClientRect(hwnd)
    w = rect[2] - rect[0]
    client_x = int(round(w / 2))
    client_y = int(round(COMBO_LBOX_ITEM_HEIGHT * n))
    _post_click(hwnd, client_x, client_y, 0.05)
 
def _click_child_control(ctrl):
    hwnd = ctrl.hwnd
    if ctrl.cls_name == "Button":
        win32api.SendMessage(hwnd, win32con.BM_CLICK, 0, 0)
    else:
        cx = int(round(ctrl.width / 2))
        cy = int(round(ctrl.height / 2))
        _post_click(hwnd, cx, cy, 0.05)


def click_account_and_login(account_num):
    if not isinstance(account_num, int) or account_num < 1 or account_num > 4:
        return False
    dlg = _find_dialog()
    if not dlg:
        return False
    rect = _get_rect(dlg)
    if not rect:
        return False
    left, top, right, bottom = rect
    w = right - left
    h = bottom - top
    center_x = int(round(left + w / 2))
    open_y = int(round(top + h * 0.38))
    childs = _get_child_controls(dlg)
    base_ctrl = _find_control_at(childs, center_x, open_y)
    if base_ctrl:
        _click_child_control(base_ctrl)
    else:
        cx_open, cy_open = _screen_to_client(dlg, center_x, open_y)
        _post_click(dlg, cx_open, cy_open, 0.05)
    time.sleep(COMBO_LBOX_WAIT_TIME)
    lbox = _find_combo_lbox_by_lt(rect)
    if lbox:
        _click_combo_lbox_item(lbox, account_num)
    time.sleep(0.2)
    login_ctrl = _find_control_at(childs, center_x, int(round(open_y + 175)))
    if login_ctrl:
        _click_child_control(login_ctrl)
    else:
        login_y = int(round(top + h * 0.39 + 2 * 88))
        cx_login, cy_login = _screen_to_client(dlg, center_x, login_y)
        _post_click(dlg, cx_login, cy_login, 0.05)
    return True
