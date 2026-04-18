# -*- coding: utf-8 -*-
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

from GUI.HuongDV.features.ui_helpers import (
    apply_zebra as feature_apply_zebra,
    auto_fit_treeview_columns as feature_auto_fit_treeview_columns,
    configure_ui_fonts as feature_configure_ui_fonts,
    create_scrollable_frame as feature_create_scrollable_frame,
    responsive_wraplength as feature_responsive_wraplength,
    style_button as feature_style_button,
)
from GUI.HuongDV.features.validation import (
    is_valid_email as feature_is_valid_email,
    is_valid_password as feature_is_valid_password,
    is_valid_phone as feature_is_valid_phone,
    safe_int as feature_safe_int,
)
from core.datastore import SQLiteDataStore
from core.normalizers import (
    normalize_notification_item as core_normalize_notification_item,
    normalize_review_item as core_normalize_review_item,
)
from core.security import prepare_password_for_storage
from core.tk_text import fix_mojibake

# =========================
# VALIDATION
# =========================
def is_valid_phone(phone):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_phone` (is valid phone).
    Tham số:
        phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_is_valid_phone(phone)

def is_valid_email(email):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_email` (is valid email).
    Tham số:
        email: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_is_valid_email(email)

def is_valid_password(pwd):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_password` (is valid password).
    Tham số:
        pwd: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_is_valid_password(pwd)

def safe_int(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `safe_int` (safe int).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_safe_int(value)


# =========================
# THEME
# =========================
THEME = {
    "bg": "#f1f5f9",
    "surface": "#ffffff",
    "sidebar": "#0b1220",
    "sidebar_hover": "#16233b",
    "sidebar_active": "#1e3a8a",
    "primary": "#2563eb",
    "success": "#059669",
    "danger": "#dc2626",
    "warning": "#d97706",
    "text": "#0f172a",
    "muted": "#64748b",
    "border": "#d2dae6",
    "header_bg": "#ffffff",
    "status_bg": "#e8eef8",
    "heading_bg": "#e2e8f0",
    "note_bg": "#fff7ed",
    "note_fg": "#9a3412",
    "zebra_even": "#f8fbff",
    "zebra_odd": "#ffffff",
}

HDV_STATUSES = ["Sẵn sàng", "Đã phân công", "Đang dẫn tour", "Tạm nghỉ"]
TOUR_FINISHED_STATUSES = ["Hoàn tất", "Đã hủy"]
BOOKING_CANCEL_STATUSES = ["Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]

# =========================
# PATH DỮ LIỆU
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Admin", "data")
DATA_FILE = os.path.join(DATA_DIR, "vietnam_travel_data.json")
REVIEWS_FILE = os.path.join(DATA_DIR, "vietnam_travel_reviews.json")
NOTIF_FILE = os.path.join(DATA_DIR, "vietnam_travel_notifications.json")

DEFAULT_DATA = {
    "hdv": [
        {
            "maHDV": "HDV01",
            "tenHDV": "Nguyễn Văn Anh",
            "sdt": "0901234567",
            "email": "anh@travel.com",
            "kn": "5",
            "gioiTinh": "Nam",
            "khuVuc": "Miền Bắc",
            "trangThai": "Sẵn sàng",
            "password": "123",
            "total_reviews": 0,
            "avg_rating": 0,
            "skill_score": 0,
            "attitude_score": 0,
            "problem_solving_score": 0,
        }
    ],
    "tours": [],
    "bookings": [],
    "users": [],
    "admin": {"username": "admin", "password": "123"},
}


# =========================
# DATA STORE
# =========================
def normalize_review_item(r, datastore=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_review_item` (normalize review item).
    Tham số:
        r: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return core_normalize_review_item(
        r,
        fullname_keys=("fullname", "tenKhach", "hoTen", "tenNguoiDanhGia"),
        content_keys=("content", "comment", "noiDung", "danhGia"),
        include_rating=True,
    )


def normalize_notification_item(n, datastore=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_notification_item` (normalize notification item).
    Tham số:
        n: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return core_normalize_notification_item(
        n,
        datastore=datastore,
        content_keys=("content", "noiDung", "message", "thongBao"),
    )

def auto_fit_treeview_columns(tree, columns, min_widths=None, max_widths=None, padding=24):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `auto_fit_treeview_columns` (auto fit treeview columns).
    Tham số:
        tree: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        columns: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        min_widths: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        max_widths: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        padding: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_auto_fit_treeview_columns(
        tree,
        columns,
        min_widths=min_widths,
        max_widths=max_widths,
        padding=padding,
    )

class DataStore(SQLiteDataStore):
    def __init__(self, path=DATA_FILE, rev_path=REVIEWS_FILE, notif_path=NOTIF_FILE):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `__init__` (  init  ).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            rev_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            notif_path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        super().__init__(
            path=path,
            rev_path=rev_path,
            notif_path=notif_path,
            default_data=DEFAULT_DATA,
            normalize_review_item=normalize_review_item,
            normalize_notification_item=normalize_notification_item,
            text_normalizer=fix_mojibake,
        )


# =========================
# UI HELPER
# =========================
def apply_zebra(tree):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `apply_zebra` (apply zebra).
    Tham số:
        tree: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_apply_zebra(tree, THEME)


def style_button(parent, text, bg, command, fg="white"):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `style_button` (style button).
    Tham số:
        parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        bg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        command: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_style_button(parent, text, bg, command, fg=fg)


def configure_ui_fonts(root):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `configure_ui_fonts` (configure ui fonts).
    Tham số:
        root: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_configure_ui_fonts(root)

def create_scrollable_frame(parent, bg):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `create_scrollable_frame` (create scrollable frame).
    Tham số:
        parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        bg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_create_scrollable_frame(parent, bg)

def responsive_wraplength(widget, offset=80, min_width=260, fallback=760):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `responsive_wraplength` (responsive wraplength).
    Tham số:
        widget: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        offset: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        min_width: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fallback: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_responsive_wraplength(
        widget,
        offset=offset,
        min_width=min_width,
        fallback=fallback,
    )


# =========================
# GUIDE UI
# =========================
def khoi_tao_hdv(root, user_data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `khoi_tao_hdv` (khoi tao hdv).
    Tham số:
        root: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        user_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not user_data:
        user_data = {"maHDV": "HDV01", "tenHDV": "Hướng Dẫn Viên"}

    app = {
        "root": root,
        "ql": DataStore(),
        "user": user_data,
        "container": None,
        "content_canvas": None,
        "tv_tours": None,
        "detail_frame": None,
        "active_menu_btn": None,
        "page_title_var": tk.StringVar(value="Lịch trình tour"),
        "page_subtitle_var": tk.StringVar(value="Theo dõi các tour được phân công, danh sách khách và trạng thái vận hành."),
        "status_var": tk.StringVar(value="Sẵn sàng làm việc"),
        "status_label": None,
        "status_badge": None,
        "login_time": datetime.now(),
        "login_time_var": tk.StringVar(),
        "current_tab": "tour",
    }

    app["login_time_var"].set(
    "Đăng nhập lúc: " + app["login_time"].strftime("%d/%m/%Y - %H:%M:%S")
    )

    for widget in root.winfo_children():
        widget.destroy()

    root.title("VIETNAM TRAVEL - HƯỚNG DẪN VIÊN")
    root.geometry("1320x780")
    root.minsize(1120, 700)
    root.configure(bg=THEME["bg"])
    configure_ui_fonts(root)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        font=("Times New Roman", 12),
        rowheight=38,
        background=THEME["surface"],
        fieldbackground=THEME["surface"],
        foreground=THEME["text"],
        bordercolor=THEME["border"],
        relief="flat",
    )
    style.configure(
        "Treeview.Heading",
        font=("Times New Roman", 12, "bold"),
        background=THEME["heading_bg"],
        foreground=THEME["text"],
        relief="flat",
        padding=(8, 10),
    )
    style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", THEME["text"])])
    style.configure(
        "TScrollbar",
        bordercolor=THEME["border"],
        troughcolor="#eef2ff",
        background="#94a3b8",
        darkcolor="#94a3b8",
        lightcolor="#94a3b8",
        arrowsize=14,
    )

    sidebar = tk.Frame(root, bg="#071224", width=286)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    brand = tk.Frame(sidebar, bg="#071224")
    brand.pack(fill="x", padx=18, pady=(18, 10))
    tk.Label(
        brand,
        text="VIETNAM TRAVEL",
        justify="left",
        anchor="w",
        bg="#071224",
        fg="#34d399",
        font=("Times New Roman", 21, "bold"),
    ).pack(fill="x")
    tk.Label(
        brand,
        text="Guide Control Center",
        justify="left",
        anchor="w",
        bg="#071224",
        fg="#93c5fd",
        font=("Times New Roman", 11, "italic"),
    ).pack(fill="x", pady=(2, 0))


    ten_hdv = user_data.get("tenHDV", "Hướng Dẫn Viên")
    ma_hdv = user_data.get("maHDV", "HDV01")
    account_card = tk.Frame(sidebar, bg="#111b30", highlightbackground="#243450", highlightthickness=1)
    account_card.pack(fill="x", padx=16, pady=(0, 8))


    tk.Label(
        account_card,
        text="TÀI KHOẢN HƯỚNG DẪN VIÊN",
        bg="#111b30",
        fg="#dbeafe",
        font=("Times New Roman", 11, "bold"),
    ).pack(fill="x")

    tk.Label(
        account_card,
        text=f"Chào mừng, {ten_hdv}",
        bg="#111b30",
        fg="white",
        font=("Times New Roman", 13, "bold"),
        pady=6,
    ).pack(fill="x")

    tk.Label(
        account_card,
        text=f"Mã HDV: {user_data.get('maHDV', '')}",
        bg="#111b30",
        fg="#93c5fd",
        font=("Times New Roman", 10, "italic"),
    ).pack(fill="x")

    tk.Label(
        account_card,
        textvariable=app["login_time_var"],
        bg="#111b30",
        fg="#93c5fd",
        font=("Times New Roman", 10, "italic"),
        pady=8,
        wraplength=220,
        justify="center",
    ).pack(fill="x")

    tk.Label(
        account_card,
        text="Đang hoạt động",
        bg="#111b30",
        fg="#22c55e",
        font=("Times New Roman", 10, "bold"),
    ).pack(pady=(4, 0))

    menu = tk.Frame(sidebar, bg="#071224")
    menu.pack(fill="x", padx=12, pady=(2, 0))

    def reload_current_page():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `reload_current_page` (reload current page).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        app["ql"].load()

        current_tab = app.get("current_tab", "tour")

        if current_tab == "tour":
            tab_danh_sach_tour()
            set_status("Đã tải lại dữ liệu lịch trình tour", THEME["success"])
        elif current_tab == "stats":
            tab_thong_ke()
            set_status("Đã tải lại dữ liệu hiệu suất", THEME["success"])
        elif current_tab == "notify":
            tab_thong_bao()
            set_status("Đã tải lại dữ liệu thông báo", THEME["success"])
        elif current_tab == "settings":
            tab_cai_dat()
            set_status("Đã tải lại dữ liệu tài khoản", THEME["success"])
        else:
            tab_danh_sach_tour()
            set_status("Đã tải lại dữ liệu", THEME["success"])


    def set_status(text, color=THEME["primary"]):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `set_status` (set status).
        Tham số:
            text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        app["status_var"].set(text)
        if app.get("status_label"):
            app["status_label"].config(fg=color)

    def set_badge(text, bg="#123a5a", fg="#d1fae5"):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `set_badge` (set badge).
        Tham số:
            text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            fg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if app.get("status_badge"):
            app["status_badge"].config(text=text, bg=bg, fg=fg)

    def set_active_menu(button):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `set_active_menu` (set active menu).
        Tham số:
            button: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        prev = app.get("active_menu_btn")
        if prev and prev.winfo_exists() and prev is not button:
            prev.configure(bg="#071224", fg="#dbe4f5")
        app["active_menu_btn"] = button
        button.configure(bg="#1d4ed8", fg="white")

    def menu_btn(text, cmd, icon=""):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `menu_btn` (menu btn).
        Tham số:
            text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            cmd: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            icon: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        label = f"  {icon}  {text}" if icon else f"  {text}"
        btn = tk.Button(
            menu,
            text=label,
            bg="#071224",
            fg="#dbe4f5",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            anchor="w",
            font=("Times New Roman", 13, "bold"),
            padx=14,
            pady=13,
            command=cmd,
        )
        btn.bind("<Enter>", lambda _e, b=btn: b.configure(bg="#13213c") if app.get("active_menu_btn") is not b else None)
        btn.bind("<Leave>", lambda _e, b=btn: b.configure(bg="#071224") if app.get("active_menu_btn") is not b else None)
        return btn

    right_panel = tk.Frame(root, bg=THEME["bg"])
    right_panel.pack(side="left", fill="both", expand=True)

    header = tk.Frame(
        right_panel,
        bg=THEME["header_bg"],
        height=96,
        highlightbackground=THEME["border"],
        highlightthickness=1,
    )
    header.pack(side="top", fill="x", padx=18, pady=(18, 12))
    header.pack_propagate(False)

    head_left = tk.Frame(header, bg=THEME["header_bg"])
    head_left.pack(side="left", fill="both", expand=True, padx=18, pady=12)
    tk.Label(
        head_left,
        textvariable=app["page_title_var"],
        bg=THEME["header_bg"],
        fg=THEME["text"],
        font=("Times New Roman", 24, "bold"),
        anchor="w",
    ).pack(anchor="w")
    tk.Label(
        head_left,
        textvariable=app["page_subtitle_var"],
        bg=THEME["header_bg"],
        fg=THEME["muted"],
        font=("Times New Roman", 12, "italic"),
        anchor="w",
        wraplength=760,
        justify="left",
    ).pack(anchor="w", pady=(3, 0))

    head_right = tk.Frame(header, bg=THEME["header_bg"])
    head_right.pack(side="right", padx=18, pady=16)
    tk.Label(
        head_right,
        text="Trạng thái hôm nay",
        bg=THEME["header_bg"],
        fg=THEME["muted"],
        font=("Times New Roman", 10, "bold"),
    ).pack(anchor="e")
    header_badge = tk.Label(
        head_right,
        text="SẴN SÀNG DẪN TOUR",
        bg="#dbeafe",
        fg="#1d4ed8",
        font=("Times New Roman", 11, "bold"),
        padx=14,
        pady=7,
    )
    header_badge.pack(anchor="e", pady=(6, 0))

    style_button(
    head_right,
    "↻ Tải lại",
    THEME["primary"],
    reload_current_page
    ).pack(anchor="e")

    content_shell = tk.Frame(right_panel, bg=THEME["bg"])
    content_shell.pack(fill="both", expand=True, padx=18)

    content_canvas = tk.Canvas(content_shell, bg=THEME["bg"], highlightthickness=0, bd=0)
    outer_sy = ttk.Scrollbar(content_shell, orient="vertical", command=content_canvas.yview)
    content_canvas.configure(yscrollcommand=outer_sy.set)

    outer_sy.pack(side="right", fill="y")
    content_canvas.pack(side="left", fill="both", expand=True)

    content_area = tk.Frame(content_canvas, bg=THEME["bg"], padx=4, pady=4)
    canvas_window = content_canvas.create_window((0, 0), window=content_area, anchor="nw")

    def on_content_configure(_event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_content_configure` (on content configure).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        content_canvas.configure(scrollregion=content_canvas.bbox("all"))

    def on_canvas_resize(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_canvas_resize` (on canvas resize).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        content_canvas.itemconfigure(canvas_window, width=max(event.width - 2, 1))

    def on_outer_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_outer_mousewheel` (on outer mousewheel).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        try:
            content_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    content_area.bind("<Configure>", on_content_configure)
    content_canvas.bind("<Configure>", on_canvas_resize)
    content_canvas.bind("<Enter>", lambda _e: content_canvas.bind_all("<MouseWheel>", on_outer_mousewheel))
    content_canvas.bind("<Leave>", lambda _e: content_canvas.unbind_all("<MouseWheel>"))

    app["container"] = content_area
    app["content_canvas"] = content_canvas

    status_bar = tk.Frame(
        right_panel,
        bg=THEME["status_bg"],
        height=36,
        highlightbackground=THEME["border"],
        highlightthickness=1,
    )
    status_bar.pack(side="bottom", fill="x", padx=18, pady=(0, 16))
    status_bar.pack_propagate(False)
    app["status_label"] = tk.Label(
        status_bar,
        textvariable=app["status_var"],
        bg=THEME["status_bg"],
        fg=THEME["primary"],
        anchor="w",
        padx=14,
        font=("Times New Roman", 11, "italic"),
    )
    app["status_label"].pack(fill="both", expand=True)

    def clear_container():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `clear_container` (clear container).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        for widget in content_area.winfo_children():
            widget.destroy()
        if app.get("content_canvas"):
            app["content_canvas"].yview_moveto(0)

    def get_my_tours():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `get_my_tours` (get my tours).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return [t for t in app["ql"].list_tours if t.get("hdvPhuTrach") == ma_hdv]

    def get_active_tours():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `get_active_tours` (get active tours).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return [t for t in get_my_tours() if t.get("trangThai") not in TOUR_FINISHED_STATUSES]

    def format_currency(value):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `format_currency` (format currency).
        Tham số:
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return f"{safe_int(value):,} đ".replace(",", ".")

    def build_stat_card(parent, title, value, note, accent):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `build_stat_card` (build stat card).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            accent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        card = tk.Frame(parent, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=7)
        tk.Frame(card, bg=accent, height=4).pack(fill="x")
        body = tk.Frame(card, bg=THEME["surface"], padx=16, pady=14)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=title, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 11, "bold")).pack(anchor="w")
        tk.Label(body, text=value, bg=THEME["surface"], fg=accent, font=("Times New Roman", 22, "bold")).pack(anchor="w", pady=(6, 4))
        tk.Label(body, text=note, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 10, "italic"), wraplength=220, justify="left").pack(anchor="w")
        return card

    def info_pair(parent, left_items, right_items, bg):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `info_pair` (info pair).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            left_items: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            right_items: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        left = tk.Frame(parent, bg=bg)
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))
        right = tk.Frame(parent, bg=bg)
        right.pack(side="left", fill="both", expand=True)

        for label_text, value in left_items:
            row = tk.Frame(left, bg=bg)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{label_text}:", width=16, anchor="w", bg=bg, fg=THEME["text"], font=("Times New Roman", 12, "bold")).pack(side="left")
            tk.Label(row, text=str(value), anchor="w", bg=bg, fg=THEME["text"], font=("Times New Roman", 12)).pack(side="left", fill="x", expand=True)

        for label_text, value in right_items:
            row = tk.Frame(right, bg=bg)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{label_text}:", width=16, anchor="w", bg=bg, fg=THEME["text"], font=("Times New Roman", 12, "bold")).pack(side="left")
            tk.Label(row, text=str(value), anchor="w", bg=bg, fg=THEME["text"], font=("Times New Roman", 12), wraplength=360, justify="left").pack(side="left", fill="x", expand=True)

    def make_section(parent, title, subtitle="", accent=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `make_section` (make section).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            subtitle: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            accent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        section = tk.Frame(parent, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        section.pack(fill="x", pady=(0, 14))
        if accent:
            tk.Frame(section, bg=accent, height=4).pack(fill="x")
        head = tk.Frame(section, bg=THEME["surface"])
        head.pack(fill="x", padx=18, pady=(14, 8))
        tk.Label(head, text=title, bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 18, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(head, text=subtitle, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 11, "italic"), wraplength=920, justify="left").pack(anchor="w", pady=(2, 0))
        body = tk.Frame(section, bg=THEME["surface"])
        body.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        return section, body

    def hien_thi_chi_tiet(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `hien_thi_chi_tiet` (hien thi chi tiet).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        sel = app["tv_tours"].selection()
        if not sel:
            return

        ma_tour = app["tv_tours"].item(sel[0])["values"][0]
        tour = app["ql"].find_tour(ma_tour)
        bookings = app["ql"].get_bookings_by_tour(ma_tour)

        for w in app["detail_frame"].winfo_children():
            w.destroy()

        if not tour:
            tk.Label(app["detail_frame"], text="Không tìm thấy dữ liệu tour.", font=("Times New Roman", 13), bg=THEME["bg"], fg=THEME["danger"]).pack(pady=20)
            return

        occupied = app["ql"].get_occupied_seats(ma_tour)
        paid_total = sum(safe_int(b.get("daThanhToan", 0)) for b in bookings)
        remaining_total = sum(safe_int(b.get("conNo", 0)) for b in bookings)

        _, overview_body = make_section(
            app["detail_frame"],
            f"Chi tiết tour {tour.get('ma', '')}",
            "Toàn bộ thông tin điều hành, lịch trình và trạng thái khách theo tour đang chọn.",
            accent="#2563eb",
        )

        info_pair(
            overview_body,
            [
                ("Tên tour", tour.get("ten", "")),
                ("Khởi hành", tour.get("ngay", "")),
                ("Kết thúc", tour.get("ngayKetThuc", "")),
                ("Số ngày", tour.get("soNgay", "")),
                ("Điểm đi", tour.get("diemDi", "")),
            ],
            [
                ("Điểm đến", tour.get("diemDen", "")),
                ("Trạng thái", tour.get("trangThai", "")),
                ("Sức chứa", tour.get("khach", "")),
                ("Đã đặt", occupied),
                ("Ghi chú", tour.get("ghiChuDieuHanh", "Không có") or "Không có"),
            ],
            THEME["surface"],
        )

        stats_wrap = tk.Frame(app["detail_frame"], bg=THEME["bg"])
        stats_wrap.pack(fill="x", pady=(0, 14))
        build_stat_card(stats_wrap, "Booking hiệu lực", str(len([b for b in bookings if b.get("trangThai") not in BOOKING_CANCEL_STATUSES])), "Số booking còn hiệu lực trên tour này.", THEME["primary"])
        build_stat_card(stats_wrap, "Doanh thu đã thu", format_currency(paid_total), "Tổng tiền khách đã thanh toán cho tour.", THEME["success"])
        build_stat_card(stats_wrap, "Công nợ còn lại", format_currency(remaining_total), "Khoản cần tiếp tục theo dõi trước ngày khởi hành.", THEME["warning"])

        _, booking_body = make_section(
            app["detail_frame"],
            "Danh sách booking / khách hàng",
            "Theo dõi khách theo từng booking để chủ động chuẩn bị danh sách đoàn và hỗ trợ khi cần.",
            accent="#059669",
        )

        wrapper = tk.Frame(booking_body, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        wrapper.pack(fill="both", expand=True)
        wrapper.pack_propagate(False)
        wrapper.configure(height=250)

        cols = ("stt", "ten", "sdt", "sl", "tt", "thanhtoan")
        tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=7)

        headings = {
            "stt": "STT",
            "ten": "Tên khách hàng",
            "sdt": "Số điện thoại",
            "sl": "Số người",
            "tt": "Trạng thái",
            "thanhtoan": "Đã thanh toán",
        }
        for col, title in headings.items():
            tv.heading(col, text=title)

        tv.column("stt", width=60, minwidth=48, anchor="center", stretch=True)
        tv.column("ten", width=260, minwidth=170, anchor="w", stretch=True)
        tv.column("sdt", width=130, minwidth=100, anchor="center", stretch=True)
        tv.column("sl", width=90, minwidth=76, anchor="center", stretch=True)
        tv.column("tt", width=170, minwidth=120, anchor="center", stretch=True)
        tv.column("thanhtoan", width=150, minwidth=110, anchor="center", stretch=True)

        active_bookings = [b for b in bookings if b.get("trangThai") not in BOOKING_CANCEL_STATUSES]
        rows = active_bookings if active_bookings else bookings

        for i, b in enumerate(rows, 1):
            tv.insert(
                "",
                "end",
                values=(
                    i,
                    b.get("tenKhach", ""),
                    b.get("sdt", ""),
                    b.get("soNguoi", ""),
                    b.get("trangThai", ""),
                    format_currency(b.get("daThanhToan", 0)),
                ),
            )

        if not rows:
            tv.insert("", "end", values=("", "Chưa có booking nào cho tour này", "", "", "", ""))

        apply_zebra(tv)
        sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")
        tv.pack(side="left", fill="both", expand=True)
       

        def fit_booking_columns(event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `fit_booking_columns` (fit booking columns).
            Tham số:
                event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            width = max(520, wrapper.winfo_width() - 20)
            ratios = {"stt": 0.08, "ten": 0.32, "sdt": 0.16, "sl": 0.10, "tt": 0.19, "thanhtoan": 0.15}
            mins = {"stt": 48, "ten": 170, "sdt": 100, "sl": 76, "tt": 120, "thanhtoan": 110}
            for col in cols:
                tv.column(col, width=max(mins[col], int(width * ratios[col])))

        wrapper.bind("<Configure>", fit_booking_columns)
        fit_booking_columns()

        set_status(f"Đang xem chi tiết tour {ma_tour}", THEME["primary"])

    def tab_danh_sach_tour():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `tab_danh_sach_tour` (tab danh sach tour).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        clear_container()

        my_tours = get_my_tours()
        active_tours = get_active_tours()
        total_guests = sum(app["ql"].get_occupied_seats(t["ma"]) for t in my_tours)
        total_notifications = len([n for n in app["ql"].list_notifications if n.get("maHDV") == ma_hdv])

        stats_wrap = tk.Frame(content_area, bg=THEME["bg"])
        stats_wrap.pack(fill="x", pady=(0, 14))
        build_stat_card(stats_wrap, "Tour được phân công", str(len(my_tours)), "Tổng số tour HDV đang phụ trách trong hệ thống.", THEME["primary"])
        build_stat_card(stats_wrap, "Tour đang hoạt động", str(len(active_tours)), "Tour chưa kết thúc hoặc chưa bị hủy.", THEME["success"])
        build_stat_card(stats_wrap, "Tổng khách đang theo", str(total_guests), "Số khách hiện đang nằm trong các tour được phân công.", THEME["warning"])
        build_stat_card(stats_wrap, "Thông báo đã gửi", str(total_notifications), "Thông báo đã gửi cho các đoàn trong kỳ hiện tại.", "#7c3aed")

        _, table_body = make_section(
            content_area,
            "Danh sách tour được phân công",
            "Chọn một tour để xem nhanh lịch trình, trạng thái đoàn và danh sách khách hàng theo booking.",
            accent="#1d4ed8",
        )

        wrapper = tk.Frame(table_body, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        wrapper.pack(fill="x")

        cols = ("ma", "ten", "ngay", "khach", "tt")
        tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=8)
        app["tv_tours"] = tv

        tv.heading("ma", text="Mã tour")
        tv.heading("ten", text="Tên tour")
        tv.heading("ngay", text="Ngày khởi hành")
        tv.heading("khach", text="Đã đặt / Tổng")
        tv.heading("tt", text="Trạng thái")

        tv.column("ma", width=90, minwidth=78, anchor="center", stretch=True)
        tv.column("ten", width=380, minwidth=240, anchor="w", stretch=True)
        tv.column("ngay", width=150, minwidth=110, anchor="center", stretch=True)
        tv.column("khach", width=140, minwidth=100, anchor="center", stretch=True)
        tv.column("tt", width=150, minwidth=110, anchor="center", stretch=True)

        for t in my_tours:
            occupied = app["ql"].get_occupied_seats(t["ma"])
            tv.insert("", "end", values=(t["ma"], t["ten"], t["ngay"], f"{occupied}/{t['khach']}", t["trangThai"]))

        apply_zebra(tv)
        sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")
        tv.pack(side="left", fill="both", expand=True)

        def fit_tour_columns(event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `fit_tour_columns` (fit tour columns).
            Tham số:
                event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            width = max(560, wrapper.winfo_width() - 20)
            ratios = {"ma": 0.10, "ten": 0.44, "ngay": 0.18, "khach": 0.14, "tt": 0.14}
            mins = {"ma": 78, "ten": 240, "ngay": 110, "khach": 100, "tt": 110}
            for col in cols:
                tv.column(col, width=max(mins[col], int(width * ratios[col])))

        wrapper.bind("<Configure>", fit_tour_columns)
        fit_tour_columns()

        tv.bind("<<TreeviewSelect>>", hien_thi_chi_tiet)

        app["detail_frame"] = tk.Frame(content_area, bg=THEME["bg"])
        app["detail_frame"].pack(fill="both", expand=True, pady=(2, 0))
        app["current_tab"] = "tour"

        if my_tours:
            first = tv.get_children()
            if first:
                tv.selection_set(first[0])
                tv.focus(first[0])
                hien_thi_chi_tiet()
        else:
            _, empty_body = make_section(
                app["detail_frame"],
                "Chưa có tour được phân công",
                "Khi admin gán tour cho bạn, danh sách tour và khách hàng sẽ hiển thị tại đây.",
                accent="#dc2626",
            )
            tk.Label(empty_body, text="Hiện tại bạn chưa có tour nào được phân công.", font=("Times New Roman", 13), bg=THEME["surface"], fg=THEME["muted"]).pack(anchor="w")

    def tab_thong_ke():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `tab_thong_ke` (tab thong ke).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        clear_container()
        app["current_tab"] = "tour"
        _, top_body = make_section(
            content_area,
            "Hiệu suất & đánh giá của khách hàng",
            "Theo dõi nhanh mức độ hài lòng, điểm trung bình và năng lực chuyên môn của HDV.",
            accent="#7c3aed",
        )

        card_frame = tk.Frame(top_body, bg=THEME["surface"])
        card_frame.pack(fill="x", pady=(0, 8))

        h = app["ql"].find_hdv(ma_hdv) or {
            "avg_rating": 0,
            "skill_score": 0,
            "attitude_score": 0,
            "problem_solving_score": 0,
            "total_reviews": 0,
        }

        stats = [
            ("Điểm trung bình", f"{h.get('avg_rating', 0) / 20:.1f} / 5.0", THEME["warning"], "Tổng hợp từ tất cả đánh giá đã ghi nhận."),
            ("Tỷ lệ hài lòng", f"{h.get('avg_rating', 0):.1f}%", THEME["success"], "Mức độ hài lòng quy đổi theo thang phần trăm."),
            ("Số lượt đánh giá", str(h.get("total_reviews", 0)), THEME["primary"], "Số phản hồi từ khách hàng sau tour."),
        ]

        my_reviews = [
            r for r in app["ql"].list_reviews
            if str(r.get("target_id", "")).strip() == ma_hdv
            or str(r.get("maHDV", "")).strip() == ma_hdv
        ]

        for title, value, color, note in stats:
            build_stat_card(card_frame, title, value, note, color)

        _, chart_body = make_section(
            content_area,
            "Chỉ số đánh giá chuyên môn (%)",
            "Ba tiêu chí quan trọng phản ánh chất lượng dẫn đoàn và xử lý tình huống thực tế.",
            accent="#059669",
        )

        criteria = [
            ("Kiến thức chuyên môn", h.get("skill_score", 0), THEME["primary"]),
            ("Thái độ phục vụ", h.get("attitude_score", 0), THEME["success"]),
            ("Xử lý tình huống", h.get("problem_solving_score", 0), THEME["warning"]),
        ]

        for name, val, color in criteria:
            row = tk.Frame(chart_body, bg=THEME["surface"])
            row.pack(fill="x", pady=10)
            tk.Label(row, text=name, font=("Times New Roman", 12, "bold"), width=22, anchor="w", bg=THEME["surface"], fg=THEME["text"]).pack(side="left")
            p_bg = tk.Frame(row, bg="#e2e8f0", width=500, height=20)
            p_bg.pack(side="left", padx=16)
            p_bg.pack_propagate(False)
            fill_width = max(1, int(float(val) * 5)) if float(val) > 0 else 1
            tk.Frame(p_bg, bg=color, width=fill_width, height=20).pack(side="left")
            tk.Label(row, text=f"{float(val):.1f}%", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], fg=color).pack(side="left")

        _, review_body = make_section(
            content_area,
            "Đánh giá chi tiết từ khách hàng",
            "Danh sách phản hồi khách hàng dành cho hướng dẫn viên trong các tour đã hoàn tất.",
            accent="#7c3aed",
        )

        review_wrapper = tk.Frame(review_body, bg=THEME["surface"], highlightbackground=THEME["border"], highlightthickness=1)
        review_wrapper.pack(fill="both", expand=True)

        review_cols = ("khach", "tour", "rating", "content", "date")
        review_tv = ttk.Treeview(review_wrapper, columns=review_cols, show="headings", height=8)

        review_tv.heading("khach", text="Khách hàng")
        review_tv.heading("tour", text="Tour/Đối tượng")
        review_tv.heading("rating", text="Điểm")
        review_tv.heading("content", text="Nội dung đánh giá")
        review_tv.heading("date", text="Ngày gửi")

        review_tv.column("khach", width=260, anchor="w", stretch=False)
        review_tv.column("tour", width=180, anchor="center", stretch=False)
        review_tv.column("rating", width=80, anchor="center", stretch=False)
        review_tv.column("content", width=500, anchor="w", stretch=True)
        review_tv.column("date", width=130, anchor="center", stretch=False)

        review_sy = ttk.Scrollbar(review_wrapper, orient="vertical", command=review_tv.yview)
        review_sx = ttk.Scrollbar(review_wrapper, orient="horizontal", command=review_tv.xview)
        review_tv.configure(yscrollcommand=review_sy.set, xscrollcommand=review_sx.set)

        review_sy.pack(side="right", fill="y")
        review_sx.pack(side="bottom", fill="x")
        review_tv.pack(side="left", fill="both", expand=True)

        my_reviews = [
            r for r in app["ql"].list_reviews
            if str(r.get("target_id", "")).strip() == ma_hdv
            or str(r.get("maHDV", "")).strip() == ma_hdv
        ]

        for r in my_reviews:
            fullname = (
                str(r.get("fullname") or r.get("tenKhach") or r.get("hoTen") or "").strip()
            )
            username = str(r.get("username") or r.get("user") or "").strip()

            if fullname and username:
                customer_text = f"{fullname} ({username})"
            elif fullname:
                customer_text = fullname
            elif username:
                customer_text = username
            else:
                customer_text = "Ẩn danh"

            target_text = str(r.get("target") or r.get("doiTuong") or "HDV").strip()
            target_id = str(r.get("target_id") or r.get("maHDV") or "").strip()
            if target_text == "HDV" and target_id:
                target_text = f"HDV: {target_id}"

            review_content = (
                str(r.get("content") or r.get("comment") or r.get("noiDung") or r.get("danhGia") or "").strip()
            )

            review_date = (
                str(r.get("date") or r.get("ngayGui") or r.get("thoiGian") or r.get("ngay") or "").strip()
            )

            rating_value = r.get("rating", "")
            if rating_value == "":
                # fallback nếu file cũ không có rating riêng
                skill = safe_int(r.get("skill", 0))
                attitude = safe_int(r.get("attitude", 0))
                problem = safe_int(r.get("problem", r.get("problem_solving", 0)))
                scores = [x for x in [skill, attitude, problem] if x > 0]
                rating_value = round(sum(scores) / len(scores) / 20, 1) if scores else ""

            review_tv.insert("", "end", values=(
                customer_text,
                target_text,
                rating_value,
                review_content,
                review_date
            )
            )
    def tab_thong_bao():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `tab_thong_bao` (tab thong bao).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        clear_container()
        app["current_tab"] = "tour"
        _, body = make_section(
            content_area,
            "Gửi thông báo khẩn cấp",
            "Chủ động gửi thông báo quan trọng cho từng đoàn khách đang hoạt động để cập nhật lịch trình hoặc thay đổi phát sinh.",
            accent="#dc2626",
        )

        tk.Label(body, text="Chọn tour cần gửi thông báo", font=("Times New Roman", 13, "bold"), bg=THEME["surface"], fg=THEME["text"]).pack(anchor="w", pady=(0, 6))

        my_tours = get_my_tours()
        active_tours = [t for t in my_tours if t.get("trangThai") not in TOUR_FINISHED_STATUSES]
        tour_options = [f"{t['ma']} - {t['ten']}" for t in active_tours]

        tour_var = tk.StringVar()
        tour_cb = ttk.Combobox(body, textvariable=tour_var, values=tour_options, state="readonly", font=("Times New Roman", 12), width=58)
        tour_cb.pack(anchor="w", pady=(0, 18))
        if tour_options:
            tour_cb.current(0)

        tk.Label(body, text="Nội dung thông báo", font=("Times New Roman", 13, "bold"), bg=THEME["surface"], fg=THEME["text"]).pack(anchor="w", pady=(0, 8))
        txt = tk.Text(body, height=11, font=("Times New Roman", 13), relief="solid", bd=1, wrap="word")
        txt.pack(fill="both", expand=True, pady=(0, 18))

        def gui_thong_bao():
            """
            Mục đích:
                Thực hiện xử lý cho hàm `gui_thong_bao` (gui thong bao).
            Tham số:
                Không có.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            content = txt.get("1.0", "end").strip()
            if not tour_var.get():
                return messagebox.showwarning("Lỗi", "Vui lòng chọn đoàn khách muốn gửi thông báo!")
            if not content:
                return messagebox.showwarning("Lỗi", "Vui lòng nhập nội dung thông báo!")

            selected = tour_var.get().split(" - ", 1)
            selected_tour_ma = selected[0]
            selected_tour_ten = selected[1] if len(selected) > 1 else ""

            new_notif = {
                "maHDV": ma_hdv,
                "tenHDV": ten_hdv,
                "maTour": selected_tour_ma,
                "tenTour": selected_tour_ten,
                "content": content,
                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
            app["ql"].notifications.append(new_notif)
            app["ql"].save()
            messagebox.showinfo("Thành công", f"Đã gửi thông báo đến đoàn '{selected_tour_ten}'!")
            tab_danh_sach_tour()

        style_button(body, "XÁC NHẬN GỬI THÔNG BÁO", THEME["danger"], gui_thong_bao).pack(anchor="w")

    def tab_cai_dat():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `tab_cai_dat` (tab cai dat).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        clear_container()
        app["current_tab"] = "tour"
        _, body = make_section(
            content_area,
            "Cài đặt tài khoản cá nhân",
            "Quản lý thông tin liên hệ và mật khẩu để đảm bảo liên lạc vận hành luôn chính xác.",
            accent="#d97706",
        )

        hdv_data = app["ql"].find_hdv(ma_hdv)
        if not hdv_data:
            tk.Label(body, text="Lỗi: Không tìm thấy thông tin tài khoản!", fg=THEME["danger"], bg=THEME["surface"], font=("Times New Roman", 13, "bold")).pack(anchor="w")
            return

        form_card = tk.Frame(body, bg="#f8fbff", highlightbackground=THEME["border"], highlightthickness=1, padx=20, pady=18)
        form_card.pack(fill="x")

        fields = [("Họ và tên", "tenHDV"), ("Số điện thoại", "sdt"), ("Email", "email"), ("Mật khẩu mới", "password")]
        widgets = {}
        for label, key in fields:
            row = tk.Frame(form_card, bg="#f8fbff")
            row.pack(fill="x", pady=8)
            tk.Label(row, text=label, width=15, anchor="w", bg="#f8fbff", font=("Times New Roman", 12, "bold"), fg=THEME["text"]).pack(side="left")
            show_char = "*" if key == "password" else ""
            e = tk.Entry(row, font=("Times New Roman", 12), relief="solid", bd=1, width=40, show=show_char)
            e.pack(side="left", ipady=4)
            if key != "password":
                e.insert(0, hdv_data.get(key, ""))
            widgets[key] = e

        tk.Label(form_card, text="Để trống mật khẩu nếu bạn chưa muốn thay đổi.", bg="#f8fbff", fg=THEME["muted"], font=("Times New Roman", 11, "italic")).pack(anchor="w", pady=(4, 10))

        def save_profile():
            """
            Mục đích:
                Thực hiện xử lý cho hàm `save_profile` (save profile).
            Tham số:
                Không có.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            new_name = widgets["tenHDV"].get().strip()
            new_phone = widgets["sdt"].get().strip()
            new_email = widgets["email"].get().strip()
            new_pass = widgets["password"].get().strip()

            if len(new_name) < 3:
                return messagebox.showwarning("Lỗi", "Họ tên quá ngắn (tối thiểu 3 ký tự).")
            if not is_valid_phone(new_phone):
                return messagebox.showwarning("Lỗi", "Số điện thoại không hợp lệ.")
            if not is_valid_email(new_email):
                return messagebox.showwarning("Lỗi", "Định dạng email không hợp lệ.")
            if new_pass and not is_valid_password(new_pass):
                return messagebox.showwarning("Lỗi", "Mật khẩu quá ngắn (tối thiểu 3 ký tự).")

            for h in app["ql"].list_hdv:
                if h.get("maHDV") == ma_hdv:
                    continue
                if h.get("sdt") == new_phone:
                    return messagebox.showwarning("Lỗi", "Số điện thoại đã tồn tại ở HDV khác.")
                if str(h.get("email", "")).lower() == new_email.lower():
                    return messagebox.showwarning("Lỗi", "Email đã tồn tại ở HDV khác.")

            hdv_data["tenHDV"] = new_name
            hdv_data["sdt"] = new_phone
            hdv_data["email"] = new_email
            if new_pass:
                hdv_data["password"] = prepare_password_for_storage(new_pass)

            user_data["tenHDV"] = new_name
            app["ql"].save()
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin cá nhân thành công!")
            tab_cai_dat()

        style_button(form_card, "CẬP NHẬT THÔNG TIN", THEME["success"], save_profile).pack(anchor="w", pady=(8, 0))

    def open_view(title, subtitle, view_fn, button):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `open_view` (open view).
        Tham số:
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            subtitle: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            view_fn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            button: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        set_active_menu(button)
        app["page_title_var"].set(title)
        app["page_subtitle_var"].set(subtitle)
        view_fn()
        set_status(f"Đang ở mục: {title}", THEME["primary"])
        if title == "Lịch trình tour":
            set_badge("ĐANG THEO DÕI TOUR", "#123a5a", "#d1fae5")
            header_badge.config(text="LỊCH TRÌNH TOUR", bg="#dbeafe", fg="#1d4ed8")
        elif title == "Hiệu suất & đánh giá":
            set_badge("ĐANG XEM HIỆU SUẤT", "#3b0764", "#ede9fe")
            header_badge.config(text="BÁO CÁO CÁ NHÂN", bg="#ede9fe", fg="#7c3aed")
        elif title == "Gửi thông báo":
            set_badge("CHẾ ĐỘ THÔNG BÁO", "#7f1d1d", "#fee2e2")
            header_badge.config(text="THÔNG BÁO KHẨN", bg="#fee2e2", fg="#dc2626")
        else:
            set_badge("CẬP NHẬT TÀI KHOẢN", "#78350f", "#fef3c7")
            header_badge.config(text="CÀI ĐẶT CÁ NHÂN", bg="#fef3c7", fg="#d97706")

    nav_items = [
        ("Lịch trình tour", "Theo dõi các tour được phân công, danh sách khách và trạng thái vận hành.", tab_danh_sach_tour, "🗂"),
        ("Hiệu suất & đánh giá", "Tổng hợp điểm số, tỷ lệ hài lòng và năng lực chuyên môn của HDV.", tab_thong_ke, "📈"),
        ("Gửi thông báo", "Gửi thông báo khẩn cấp đến các đoàn khách đang hoạt động.", tab_thong_bao, "📢"),
        ("Cài đặt tài khoản", "Quản lý thông tin cá nhân và cập nhật mật khẩu bảo mật.", tab_cai_dat, "⚙"),
    ]

    nav_buttons = []
    for idx, (title, subtitle, view_fn, icon) in enumerate(nav_items):
        btn = menu_btn(
            title,
            lambda t=title, s=subtitle, f=view_fn, b_idx=idx: open_view(t, s, f, nav_buttons[b_idx]),
            icon=icon,
        )
        btn.pack(fill="x", pady=4)
        nav_buttons.append(btn)

    util = tk.Frame(sidebar, bg="#071224")
    util.pack(side="bottom", fill="x", padx=12, pady=16)
    tk.Frame(util, bg="#22365b", height=1).pack(fill="x", pady=(0, 12))
    tk.Button(
        util,
        text="  ⟵  Đăng xuất",
        bg="#b91c1c",
        fg="white",
        activebackground="#dc2626",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        anchor="w",
        font=("Times New Roman", 13, "bold"),
        padx=14,
        pady=12,
        command=lambda: logout_system(root),
    ).pack(fill="x")

    open_view(
        "Lịch trình tour",
        "Theo dõi các tour được phân công, danh sách khách và trạng thái vận hành.",
        tab_danh_sach_tour,
        nav_buttons[0],
    )


def logout_system(root):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `logout_system` (logout system).
    Tham số:
        root: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if messagebox.askyesno("Xác nhận", "Bạn có muốn đăng xuất khỏi hệ thống?"):
        for widget in root.winfo_children():
            widget.destroy()
        try:
            from GUI.Login.login import set_root, show_role_selection
            set_root(root)
            root.configure(bg=THEME["bg"])
            show_role_selection()
        except (ImportError, RuntimeError, tk.TclError) as e:
            messagebox.showerror("Lỗi", f"Không thể quay lại màn hình đăng nhập.\n{e}")
