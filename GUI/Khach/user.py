# -*- coding: utf-8 -*-
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import threading
from urllib.error import URLError

from GUI.Khach.features.payment import (
    build_cash_policy_notice as feature_build_cash_policy_notice,
    build_transfer_qr_url as feature_build_transfer_qr_url,
    fetch_transfer_qr_photo as feature_fetch_transfer_qr_photo,
    short_ui_error as feature_short_ui_error,
)
from GUI.Khach.features.tour_visibility import (
    is_tour_visible_to_user as feature_is_tour_visible_to_user,
    parse_ddmmyyyy as feature_parse_ddmmyyyy,
)
from GUI.Khach.features.validation import (
    booking_payment_status as feature_booking_payment_status,
    is_valid_fullname as feature_is_valid_fullname,
    is_valid_password as feature_is_valid_password,
    is_valid_phone as feature_is_valid_phone,
    safe_int as feature_safe_int,
)
from core.booking_pricing import calculate_age_discount, normalize_passenger_breakdown
from core.booking_service import (
    apply_payment as service_apply_payment,
    cancel_booking as service_cancel_booking,
    create_booking as service_create_booking,
)
from core.datastore import SQLiteDataStore
from core.normalizers import (
    normalize_notification_item as core_normalize_notification_item,
    normalize_review_item as core_normalize_review_item,
)
from core.review_service import create_review as service_create_review
from core.security import prepare_password_for_storage
from core.state_machine import BOOKING_STATE_COMPLETED, booking_state_from_status
from core.tk_text import fix_mojibake
from core.voucher_service import build_voucher_quote as service_build_voucher_quote

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

def is_valid_fullname(name):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_fullname` (is valid fullname).
    Tham số:
        name: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_is_valid_fullname(name)

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


def booking_payment_status(total_amount, paid_amount):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `booking_payment_status` (booking payment status).
    Tham số:
        total_amount: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        paid_amount: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_booking_payment_status(total_amount, paid_amount)


def build_cash_policy_notice(ngay_khoi_hanh):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `build_cash_policy_notice` (build cash policy notice).
    Tham số:
        ngay_khoi_hanh: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_build_cash_policy_notice(ngay_khoi_hanh)


def short_ui_error(exc, fallback="Không thể gọi API QR. Vui lòng thử lại sau."):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `short_ui_error` (short ui error).
    Tham số:
        exc: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fallback: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_short_ui_error(exc, fallback=fallback)


def parse_ddmmyyyy(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `parse_ddmmyyyy` (parse ddmmyyyy).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_parse_ddmmyyyy(value)


def is_tour_visible_to_user(tour):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_tour_visible_to_user` (is tour visible to user).
    Tham số:
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_is_tour_visible_to_user(tour)


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

TOUR_BOOKABLE_STATUSES = ["Giữ chỗ", "Mở bán"]
TOUR_LOCK_CANCEL_STATUSES = ["Đã chốt đoàn", "Chờ khởi hành", "Đang đi", "Hoàn tất"]
BOOKING_CANCEL_STATUSES = ["Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]
PAYMENT_METHODS = [
    "Tiền mặt",
    "Chuyển khoản"
]

def build_transfer_qr_url(amount, transfer_content):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `build_transfer_qr_url` (build transfer qr url).
    Tham số:
        amount: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        transfer_content: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_build_transfer_qr_url(amount, transfer_content)


def fetch_transfer_qr_photo(qr_url, max_size_px=220):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `fetch_transfer_qr_photo` (fetch transfer qr photo).
    Tham số:
        qr_url: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        max_size_px: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return feature_fetch_transfer_qr_photo(qr_url, max_size_px=max_size_px)

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
            "problem_solving_score": 0
        }
    ],
    "tours": [],
    "bookings": [],
    "users": [],
    "admin": {"username": "admin", "password": "123"}
}


# =========================
# DATA STORE
# =========================

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
        content_keys=("content", "noiDung", "thongBao", "message", "moTa"),
    )

def normalize_review_item(r):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_review_item` (normalize review item).
    Tham số:
        r: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return core_normalize_review_item(r, include_rating=True, include_ma_hdv=True)



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
    tree.tag_configure("odd", background=THEME["zebra_odd"])
    tree.tag_configure("even", background=THEME["zebra_even"])
    for i, item in enumerate(tree.get_children()):
        tree.item(item, tags=(("even" if i % 2 == 0 else "odd"),))

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
    return tk.Button(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        activebackground=bg,
        activeforeground=fg,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Times New Roman", 11, "bold"),
        padx=14,
        pady=9,
        highlightthickness=1,
        highlightbackground=bg,
        highlightcolor=bg,
        command=command,
    )


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
    default_font = ("Times New Roman", 12)
    heading_font = ("Times New Roman", 12, "bold")
    root.option_add("*Font", default_font)
    root.option_add("*Label.Font", default_font)
    root.option_add("*Button.Font", default_font)
    root.option_add("*Entry.Font", default_font)
    root.option_add("*Text.Font", default_font)
    root.option_add("*Spinbox.Font", default_font)
    root.option_add("*TCombobox*Listbox*Font", default_font)

    style = ttk.Style(root)
    style.configure("TLabel", font=default_font)
    style.configure("TButton", font=heading_font)
    style.configure("TEntry", font=default_font)
    style.configure("TCombobox", font=default_font)


# =========================
# USER UI
# =========================

def khoi_tao_khach(root, user_data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `khoi_tao_khach` (khoi tao khach).
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
        user_data = {"username": "Khach", "name": "Khách hàng", "fullname": "Khách hàng", "sdt": ""}

    app = {
        "root": root,
        "ql": DataStore(),
        "user": user_data,
        "container": None,
        "content_canvas": None,
        "tv_tours": None,
        "detail_var": tk.StringVar(value="Chọn một tour để xem chi tiết và đăng ký."),
        "active_menu_btn": None,
        "page_title_var": tk.StringVar(value="Khách hàng"),
        "page_subtitle_var": tk.StringVar(value="Khám phá tour, theo dõi booking và quản lý thông tin tài khoản."),
        "status_var": tk.StringVar(value="Sẵn sàng"),
        "status_label": None,
        "header_badge": None,
        "login_time": datetime.now(),
        "login_time_var": tk.StringVar(),
        "current_tab": "tour",
        "current_view": None,
    }

    app["login_time_var"].set("Đăng nhập lúc: " + app["login_time"].strftime("%d/%m/%Y - %H:%M:%S"))

    for widget in root.winfo_children():
        widget.destroy()

    root.title("VIETNAM TRAVEL - KHÁCH HÀNG")
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

    username = user_data.get("username", "Khach")
    display_name = user_data.get("fullname") or user_data.get("name", "Khách hàng")

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
        text="Customer Service Center",
        justify="left",
        anchor="w",
        bg="#071224",
        fg="#93c5fd",
        font=("Times New Roman", 11, "italic"),
    ).pack(fill="x", pady=(2, 0))

    account_card = tk.Frame(sidebar, bg="#111b30", highlightbackground="#243450", highlightthickness=1)
    account_card.pack(fill="x", padx=16, pady=(0, 8))

    tk.Label(
        account_card,
        text="TÀI KHOẢN KHÁCH HÀNG",
        bg="#111b30",
        fg="#dbeafe",
        font=("Times New Roman", 11, "bold"),
    ).pack(fill="x", pady=(10, 0))

    tk.Label(
        account_card,
        text=f"Chào mừng, {display_name}",
        bg="#111b30",
        fg="white",
        font=("Times New Roman", 13, "bold"),
        pady=6,
    ).pack(fill="x")

    tk.Label(
        account_card,
        text=f"Username: {username}",
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
    ).pack(pady=(4, 10))

    menu = tk.Frame(sidebar, bg="#071224")
    menu.pack(fill="x", padx=12, pady=(2, 0))

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
    app["header_badge"] = tk.Label(
        head_right,
        text="KHÁCH HÀNG",
        bg="#dbeafe",
        fg="#1d4ed8",
        font=("Times New Roman", 11, "bold"),
        padx=14,
        pady=7,
    )
    app["header_badge"].pack(anchor="e", pady=(0, 8))

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

    def set_badge(text, bg="#dbeafe", fg="#1d4ed8"):
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
        if app.get("header_badge"):
            app["header_badge"].config(text=text, bg=bg, fg=fg)

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

    def get_current_user():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `get_current_user` (get current user).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return app["ql"].find_user(user_data.get("username", ""))

    def my_bookings():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `my_bookings` (my bookings).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        username_local = user_data.get("username", "")
        return [b for b in app["ql"].list_bookings if b.get("usernameDat") == username_local]

    def responsive_wraplength(base_offset=360, minimum=320):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `responsive_wraplength` (responsive wraplength).
        Tham số:
            base_offset: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            minimum: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        current_width = max(content_area.winfo_width(), right_panel.winfo_width(), root.winfo_width())
        return max(minimum, current_width - base_offset)

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
        return f"{safe_int(value):,}đ".replace(",", ".")

    def build_voucher_quote(voucher_code, gross_total, ma_tour=""):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `build_voucher_quote` (build voucher quote).
        Tham số:
            voucher_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            gross_total: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return service_build_voucher_quote(
            app["ql"],
            voucher_code,
            gross_total,
            username=user_data.get("username", ""),
            ma_tour=ma_tour,
        )

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
        app["current_tab"] = "tour"

        stats_wrap = tk.Frame(content_area, bg=THEME["bg"])
        stats_wrap.pack(fill="x", pady=(0, 14))

        visible_tours = [t for t in app["ql"].list_tours if is_tour_visible_to_user(t)]
        visible_tours.sort(key=lambda t: parse_ddmmyyyy(t.get("ngay", "")) or datetime.max.date())
        all_open_tours = [t for t in visible_tours if t.get("trangThai") in TOUR_BOOKABLE_STATUSES]
        total_open = len(all_open_tours)
        total_visible = len(visible_tours)
        total_available = 0
        for t in all_open_tours:
            occupied = app["ql"].get_occupied_seats(t.get("ma", ""))
            total_available += max(safe_int(t.get("khach", 0)) - occupied, 0)
        my_total_bookings = len(my_bookings())

        build_stat_card(stats_wrap, "Tour hiển thị", str(total_visible), "Các tour sắp diễn ra mà bạn có thể theo dõi trên hệ thống.", THEME["primary"])
        build_stat_card(stats_wrap, "Tour mở bán", str(total_open), "Các tour còn có thể đăng ký ngay lúc này.", THEME["success"])
        build_stat_card(stats_wrap, "Booking của bạn", str(my_total_bookings), "Số booking bạn đang theo dõi trong hệ thống.", THEME["warning"])

        _, body = make_section(
            content_area,
            "Khám phá các tour du lịch",
            "Xem lịch khởi hành, số chỗ còn trống và đăng ký tour trực tiếp ở ngay bên dưới.",
            accent="#2563eb",
        )

        wrapper = tk.Frame(body, bg=THEME["surface"], bd=1, relief="solid")
        wrapper.pack(fill="x")

        cols = ("ma", "ten", "ngay", "gia", "khach", "tt")
        tv_height = 5 if root.winfo_height() < 820 else 6
        tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=tv_height)
        app["tv_tours"] = tv

        tv.heading("ma", text="Mã")
        tv.heading("ten", text="Tên Tour Du Lịch")
        tv.heading("ngay", text="Khởi hành")
        tv.heading("gia", text="Giá vé")
        tv.heading("khach", text="Chỗ trống")
        tv.heading("tt", text="Trạng thái")

        tv.column("ma", width=60, anchor="center")
        tv.column("ten", width=300, anchor="w")
        tv.column("ngay", width=120, anchor="center")
        tv.column("gia", width=120, anchor="center")
        tv.column("khach", width=100, anchor="center")
        tv.column("tt", width=120, anchor="center")

        for t in visible_tours:
            occupied = app["ql"].get_occupied_seats(t["ma"])
            available = max(safe_int(t["khach"]) - occupied, 0)
            tv.insert("", "end", values=(
                t["ma"],
                t["ten"],
                t["ngay"],
                format_currency(t['gia']),
                f"{available} chỗ",
                t["trangThai"]
            ))

        apply_zebra(tv)
        sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
        sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
        tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)

        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        tv.pack(side="left", fill="both", expand=True)

        if not visible_tours:
            tv.insert("", "end", values=("", "Hiện chưa có tour phù hợp để hiển thị", "", "", "", ""))

        detail_section, detail_body_container = make_section(
            content_area,
            "Chi tiết tour và đăng ký",
            "Chọn tour ở bảng phía trên để xem chi tiết và thực hiện đăng ký ngay.",
            accent="#d97706",
        )

        detail_fr = tk.Frame(detail_body_container, bg=THEME["surface"])
        detail_fr.pack(fill="x")

        detail_fr.grid_rowconfigure(0, weight=1)
        detail_fr.grid_columnconfigure(0, weight=1)
        detail_fr.grid_columnconfigure(1, minsize=320)

        detail_body = tk.Frame(detail_fr, bg=THEME["surface"], bd=1, relief="solid")
        detail_body.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        detail_body.grid_rowconfigure(0, weight=1)
        detail_body.grid_columnconfigure(0, weight=1)

        detail_scroll = ttk.Scrollbar(detail_body, orient="vertical")
        detail_text = tk.Text(
            detail_body,
            wrap="word",
            font=("Times New Roman", 13),
            bg=THEME["surface"],
            fg=THEME["text"],
            relief="flat",
            bd=0,
            padx=10,
            pady=8,
            yscrollcommand=detail_scroll.set,
            height=6
        )
        detail_scroll.config(command=detail_text.yview)
        detail_text.grid(row=0, column=0, sticky="nsew")
        detail_scroll.grid(row=0, column=1, sticky="ns")

        def set_detail_content(content):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `set_detail_content` (set detail content).
            Tham số:
                content: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            app["detail_var"].set(content)
            detail_text.config(state="normal")
            detail_text.delete("1.0", "end")
            detail_text.insert("1.0", content)
            detail_text.config(state="disabled")

        set_detail_content(app["detail_var"].get())

        action_fr = tk.Frame(detail_fr, bg=THEME["surface"], bd=1, relief="solid", padx=12, pady=12)
        action_fr.grid(row=0, column=1, sticky="nsew")
        action_fr.grid_columnconfigure(0, weight=0, minsize=132)
        action_fr.grid_columnconfigure(1, weight=1)

        tk.Label(
            action_fr,
            text="ĐĂNG KÝ TOUR",
            font=("Times New Roman", 13, "bold"),
            bg=THEME["surface"],
            fg=THEME["success"],
            anchor="w"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(action_fr, text="Số người đi:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=1, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        spn_people = tk.Spinbox(action_fr, from_=1, to=50, font=("Times New Roman", 12), relief="solid", bd=1, justify="center")
        spn_people.grid(row=1, column=1, sticky="ew", ipady=4, pady=(0, 10))

        tk.Label(action_fr, text="Cơ cấu độ tuổi:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=2, column=0, sticky="nw", pady=(0, 10), padx=(0, 10))
        age_group_fr = tk.Frame(action_fr, bg=THEME["surface"])
        age_group_fr.grid(row=2, column=1, sticky="ew", pady=(0, 10))
        age_group_fr.grid_columnconfigure(1, weight=1)

        tk.Label(age_group_fr, text="Trẻ em (<12):", font=("Times New Roman", 11), bg=THEME["surface"]).grid(row=0, column=0, sticky="w")
        spn_child = tk.Spinbox(age_group_fr, from_=0, to=50, font=("Times New Roman", 11), relief="solid", bd=1, justify="center", width=8)
        spn_child.grid(row=0, column=1, sticky="e", pady=(0, 4))

        tk.Label(age_group_fr, text="Trung niên:", font=("Times New Roman", 11), bg=THEME["surface"]).grid(row=1, column=0, sticky="w")
        spn_middle = tk.Spinbox(age_group_fr, from_=0, to=50, font=("Times New Roman", 11), relief="solid", bd=1, justify="center", width=8)
        spn_middle.grid(row=1, column=1, sticky="e", pady=(0, 4))

        tk.Label(age_group_fr, text="Người cao tuổi (>65):", font=("Times New Roman", 11), bg=THEME["surface"]).grid(row=2, column=0, sticky="w")
        spn_senior = tk.Spinbox(age_group_fr, from_=0, to=50, font=("Times New Roman", 11), relief="solid", bd=1, justify="center", width=8)
        spn_senior.grid(row=2, column=1, sticky="e")

        tk.Label(action_fr, text="Thanh toán ngay (đ):", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=3, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        ent_pay_now = tk.Entry(action_fr, font=("Times New Roman", 12), relief="solid", bd=1, justify="right")
        ent_pay_now.insert(0, "0")
        ent_pay_now.grid(row=3, column=1, sticky="ew", ipady=4, pady=(0, 10))

        tk.Label(action_fr, text="Hình thức thanh toán:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=4, column=0, sticky="w", pady=(0, 10), padx=(0, 10))
        pay_method_var = tk.StringVar(value=PAYMENT_METHODS[0])
        cmb_pay_method = ttk.Combobox(action_fr, textvariable=pay_method_var, values=PAYMENT_METHODS, state="readonly", font=("Times New Roman", 11))
        cmb_pay_method.grid(row=4, column=1, sticky="ew", pady=(0, 10))

        tk.Label(action_fr, text="Mã giảm giá:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"], anchor="w").grid(row=5, column=0, sticky="w", pady=(0, 8), padx=(0, 10))
        voucher_var = tk.StringVar()
        ent_voucher = tk.Entry(action_fr, textvariable=voucher_var, font=("Times New Roman", 12), relief="solid", bd=1)
        ent_voucher.grid(row=5, column=1, sticky="ew", ipady=4, pady=(0, 8))

        voucher_feedback_var = tk.StringVar(value="Để trống nếu bạn chưa có mã giảm giá. Có thể thử: TRAVEL17 hoặc TRAVEL19.")
        voucher_feedback_lbl = tk.Label(
            action_fr,
            textvariable=voucher_feedback_var,
            font=("Times New Roman", 10, "italic"),
            bg=THEME["surface"],
            fg=THEME["muted"],
            justify="left",
            wraplength=260
        )
        voucher_feedback_lbl.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        booking_summary_var = tk.StringVar(value="Tổng tạm tính: 0đ | Giảm: 0đ | Cần thanh toán: 0đ")
        booking_summary_lbl = tk.Label(
            action_fr,
            textvariable=booking_summary_var,
            font=("Times New Roman", 10, "bold"),
            bg=THEME["surface"],
            fg=THEME["success"],
            justify="left",
            wraplength=260
        )
        booking_summary_lbl.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        info_note = tk.Label(
            action_fr,
            text="Chọn tour ở bảng phía trên, nhập cơ cấu độ tuổi. Trẻ em (<12) giảm 20%, người cao tuổi (>65) giảm 35%.",
            font=("Times New Roman", 10, "italic"),
            bg=THEME["surface"],
            fg=THEME["muted"],
            justify="left",
            wraplength=260
        )
        info_note.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(2, 10))

        cash_policy_var = tk.StringVar(value="")
        cash_policy_lbl = tk.Label(
            action_fr,
            textvariable=cash_policy_var,
            font=("Times New Roman", 10, "bold"),
            bg=THEME["surface"],
            fg=THEME["warning"],
            justify="left",
            wraplength=260
        )
        cash_policy_lbl.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        qr_box = tk.Frame(action_fr, bg=THEME["note_bg"], bd=1, relief="solid", padx=8, pady=8)
        qr_box.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        tk.Label(qr_box, text="QR Chuyển khoản", font=("Times New Roman", 12, "bold"), bg=THEME["note_bg"], fg=THEME["note_fg"]).pack(anchor="w")

        qr_image_lbl = tk.Label(qr_box, text="", bg=THEME["note_bg"], fg=THEME["muted"], justify="center", wraplength=240)
        qr_image_lbl.pack(anchor="center", pady=(6, 6))

        qr_status_var = tk.StringVar(value="")
        qr_status_lbl = tk.Label(qr_box, textvariable=qr_status_var, font=("Times New Roman", 10), bg=THEME["note_bg"], fg=THEME["note_fg"], justify="left", wraplength=260)
        qr_status_lbl.pack(anchor="w")

        qr_note_var = tk.StringVar(value="")
        qr_note_lbl = tk.Label(qr_box, textvariable=qr_note_var, font=("Times New Roman", 9, "italic"), bg=THEME["note_bg"], fg=THEME["muted"], justify="left", wraplength=260)
        qr_note_lbl.pack(anchor="w", pady=(3, 0))

        qr_box.grid_remove()
        qr_request_id = {"value": 0}

        action_btn_row = tk.Frame(action_fr, bg=THEME["surface"])
        action_btn_row.grid(row=11, column=0, columnspan=2, sticky="ew")

        def get_selected_tour_and_amount():
            """
            Mục đích:
                Thực hiện xử lý cho hàm `get_selected_tour_and_amount` (get selected tour and amount).
            Tham số:
                Không có.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            sel = tv.selection()
            if not sel:
                return None, 0, max(1, safe_int(spn_people.get()))
            ma = tv.item(sel[0])["values"][0]
            tour = app["ql"].find_tour(ma)
            num_people = max(1, safe_int(spn_people.get()))
            pay_now = max(0, safe_int(ent_pay_now.get()))
            return tour, pay_now, num_people

        def get_age_breakdown():
            """
            Mục đích:
                Thực hiện xử lý cho hàm `get_age_breakdown` (get age breakdown).
            Tham số:
                Không có.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            return {
                "treEm": max(0, safe_int(spn_child.get())),
                "trungNien": max(0, safe_int(spn_middle.get())),
                "nguoiCaoTuoi": max(0, safe_int(spn_senior.get())),
            }

        def normalize_age_breakdown(num_people):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `normalize_age_breakdown` (normalize age breakdown).
            Tham số:
                num_people: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            breakdown = normalize_passenger_breakdown(get_age_breakdown(), num_people)
            if breakdown is None:
                return None
            spn_middle.delete(0, "end")
            spn_middle.insert(0, str(breakdown["trungNien"]))
            return breakdown

        def refresh_booking_quote(show_error=False):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `refresh_booking_quote` (refresh booking quote).
            Tham số:
                show_error: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            tour, pay_now, num_people = get_selected_tour_and_amount()
            if not tour:
                voucher_feedback_var.set("Chọn tour để kiểm tra mã giảm giá.")
                voucher_feedback_lbl.config(fg=THEME["muted"])
                booking_summary_var.set("Tổng tạm tính: 0đ | Giảm: 0đ | Cần thanh toán: 0đ")
                booking_summary_lbl.config(fg=THEME["success"])
                return None

            breakdown = normalize_age_breakdown(num_people)
            if breakdown is None:
                booking_summary_var.set("Cơ cấu độ tuổi vượt quá số người đi. Vui lòng kiểm tra lại.")
                booking_summary_lbl.config(fg=THEME["danger"])
                return None

            price_per_person = max(0, safe_int(tour.get("gia", 0)))
            gross_total = max(0, price_per_person * num_people)
            age_discount = calculate_age_discount(price_per_person, breakdown)
            age_discount = max(0, min(gross_total, safe_int(age_discount)))
            subtotal_after_age = max(gross_total - age_discount, 0)
            normalized_code = str(voucher_var.get() or "").strip().upper()
            if normalized_code != voucher_var.get():
                voucher_var.set(normalized_code)
            quote = build_voucher_quote(normalized_code, subtotal_after_age, tour.get("ma", ""))
            final_total = max(subtotal_after_age - quote["discount"], 0)
            total_discount = age_discount + quote["discount"]

            booking_summary_var.set(
                "Tổng tạm tính: "
                f"{format_currency(gross_total)} | Giảm đối tượng: {format_currency(age_discount)}"
                f" | Voucher: {format_currency(quote['discount'])}"
                f" | Tổng giảm: {format_currency(total_discount)}"
                f" | Cần thanh toán: {format_currency(final_total)}"
            )
            booking_summary_lbl.config(fg=THEME["success"])

            if quote["ok"]:
                voucher_feedback_lbl.config(fg=THEME["success"] if quote["code"] else THEME["muted"])
            else:
                voucher_feedback_lbl.config(fg=THEME["danger"])
                if show_error and quote["code"]:
                    messagebox.showwarning("Mã giảm giá", quote["message"])

            voucher_feedback_var.set(quote["message"])

            return {
                "tour": tour,
                "pay_now": pay_now,
                "num_people": num_people,
                "breakdown": breakdown,
                "gross_total": gross_total,
                "age_discount": age_discount,
                "quote": quote,
                "final_total": final_total,
            }

        def update_transfer_qr():
            """
            Mục đích:
                Thực hiện xử lý cho hàm `update_transfer_qr` (update transfer qr).
            Tham số:
                Không có.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            booking_context = refresh_booking_quote()
            if pay_method_var.get().strip() != "Chuyển khoản":
                qr_request_id["value"] += 1
                qr_box.grid_remove()
                qr_image_lbl.config(image="", text="")
                qr_image_lbl.image = None
                qr_status_var.set("")
                qr_note_var.set("")
                tour = booking_context["tour"] if booking_context else None
                cash_policy_var.set(build_cash_policy_notice(tour.get("ngay", "")) if tour else build_cash_policy_notice(""))
                return

            cash_policy_var.set("")
            qr_box.grid()
            if not booking_context:
                qr_image_lbl.config(image="", text="Chọn tour để tạo QR")
                qr_image_lbl.image = None
                qr_status_var.set("Vui lòng chọn tour ở bảng phía trên.")
                qr_note_var.set("")
                return

            tour = booking_context["tour"]
            pay_now = booking_context["pay_now"]

            if pay_now <= 0:
                pay_now = booking_context["final_total"]

            if pay_now <= 0:
                qr_image_lbl.config(image="", text="Không đủ dữ liệu để tạo QR")
                qr_image_lbl.image = None
                qr_status_var.set("Số tiền thanh toán phải lớn hơn 0.")
                qr_note_var.set("")
                return

            transfer_content = f"{tour.get('ma', '')}-{user_data.get('username', 'KH')}-{pay_now}"
            qr_request_id["value"] += 1
            current_request_id = qr_request_id["value"]
            qr_image_lbl.config(image="", text="Đang tải QR...")
            qr_image_lbl.image = None
            qr_status_var.set("Đang tải mã chuyển khoản, vui lòng chờ...")
            qr_note_var.set("")

            def worker():
                """
                Mục đích:
                    Thực hiện xử lý cho hàm `worker` (worker).
                Tham số:
                    Không có.
                Giá trị trả về:
                    Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
                Tác dụng phụ:
                    Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
                Lưu ý nghiệp vụ:
                    Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
                """
                try:
                    qr_url = build_transfer_qr_url(pay_now, transfer_content)
                    qr_photo = fetch_transfer_qr_photo(qr_url, max_size_px=190)
                except (OSError, URLError, ValueError, tk.TclError) as exc:
                    error_message = short_ui_error(exc)

                    def apply_error():
                        """
                        Mục đích:
                            Thực hiện xử lý cho hàm `apply_error` (apply error).
                        Tham số:
                            Không có.
                        Giá trị trả về:
                            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
                        Tác dụng phụ:
                            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
                        Lưu ý nghiệp vụ:
                            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
                        """
                        if current_request_id != qr_request_id["value"] or pay_method_var.get().strip() != "Chuyển khoản":
                            return
                        qr_image_lbl.config(image="", text="(Không tải được QR)")
                        qr_image_lbl.image = None
                        qr_status_var.set("Không thể gọi API QR. Vui lòng thử lại sau.")
                        qr_note_var.set(error_message)

                    root.after(0, apply_error)
                    return

                def apply_success():
                    """
                    Mục đích:
                        Thực hiện xử lý cho hàm `apply_success` (apply success).
                    Tham số:
                        Không có.
                    Giá trị trả về:
                        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
                    Tác dụng phụ:
                        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
                    Lưu ý nghiệp vụ:
                        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
                    """
                    if current_request_id != qr_request_id["value"] or pay_method_var.get().strip() != "Chuyển khoản":
                        return
                    qr_image_lbl.config(image=qr_photo, text="")
                    qr_image_lbl.image = qr_photo
                    qr_status_var.set(f"Quét mã để chuyển khoản {pay_now:,}đ".replace(",", "."))
                    qr_note_var.set("Nội dung CK được tạo tự động theo mã tour và tài khoản khách.")

                root.after(0, apply_success)

            threading.Thread(target=worker, daemon=True).start()

        cmb_pay_method.bind("<<ComboboxSelected>>", lambda _e: update_transfer_qr())
        ent_pay_now.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        ent_voucher.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        ent_voucher.bind("<FocusOut>", lambda _e: update_transfer_qr())
        spn_people.config(command=update_transfer_qr)
        spn_people.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        spn_child.config(command=update_transfer_qr)
        spn_middle.config(command=update_transfer_qr)
        spn_senior.config(command=update_transfer_qr)
        spn_child.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        spn_middle.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        spn_senior.bind("<KeyRelease>", lambda _e: update_transfer_qr())
        update_transfer_qr()

        def sync_detail_layout(event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `sync_detail_layout` (sync detail layout).
            Tham số:
                event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            width = detail_fr.winfo_width()
            height = root.winfo_height()
            compact_mode = width < 1120 or height < 820
            tv.configure(height=5 if height < 820 else 6)

            if compact_mode:
                detail_body.grid_configure(row=0, column=0, padx=0, pady=(0, 10), sticky="nsew")
                action_fr.grid_configure(row=1, column=0, padx=0, pady=0, sticky="ew")
                detail_fr.grid_columnconfigure(0, weight=1, minsize=0)
                detail_fr.grid_columnconfigure(1, weight=0, minsize=0)
                detail_fr.grid_rowconfigure(0, weight=1)
                detail_fr.grid_rowconfigure(1, weight=0)
                detail_text.config(height=5)
                wrap_size = max(210, min(action_fr.winfo_width() - 32, width - 64))
            else:
                detail_body.grid_configure(row=0, column=0, padx=(0, 12), pady=0, sticky="nsew")
                action_fr.grid_configure(row=0, column=1, padx=0, pady=0, sticky="nsew")
                detail_fr.grid_columnconfigure(0, weight=1, minsize=0)
                detail_fr.grid_columnconfigure(1, weight=0, minsize=320)
                detail_fr.grid_rowconfigure(0, weight=1)
                detail_fr.grid_rowconfigure(1, weight=0)
                detail_text.config(height=6)
                wrap_size = max(240, min(action_fr.winfo_width() - 32, 340))

            info_note.config(wraplength=wrap_size)
            voucher_feedback_lbl.config(wraplength=wrap_size)
            booking_summary_lbl.config(wraplength=wrap_size)
            cash_policy_lbl.config(wraplength=wrap_size)
            qr_image_lbl.config(wraplength=wrap_size)
            qr_status_lbl.config(wraplength=wrap_size)
            qr_note_lbl.config(wraplength=wrap_size)

        detail_fr.bind("<Configure>", sync_detail_layout)
        sync_detail_layout()

        def on_select(event):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `on_select` (on select).
            Tham số:
                event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            sel = tv.selection()
            if not sel:
                return

            ma = tv.item(sel[0])["values"][0]
            t = app["ql"].find_tour(ma)
            if not t:
                return

            hdv = app["ql"].find_hdv(t.get("hdvPhuTrach"))
            occupied = app["ql"].get_occupied_seats(ma)
            available = max(safe_int(t["khach"]) - occupied, 0)
            spn_people.config(to=max(1, available))
            spn_child.config(to=max(0, available))
            spn_middle.config(to=max(0, available))
            spn_senior.config(to=max(0, available))
            spn_child.delete(0, "end")
            spn_child.insert(0, "0")
            spn_senior.delete(0, "end")
            spn_senior.insert(0, "0")
            spn_middle.delete(0, "end")
            spn_middle.insert(0, str(max(1, safe_int(spn_people.get()))))

            info = [
                f"TOUR: {t['ten']} ({t['ma']})",
                f"Lộ trình: {t.get('diemDi', '')} → {t.get('diemDen', '')}",
                f"Khởi hành: {t['ngay']} | Kết thúc: {t.get('ngayKetThuc', '')} | Số ngày: {t.get('soNgay', '')}",
                f"Giá: {format_currency(t['gia'])}",
                f"Hướng dẫn viên: {hdv['tenHDV'] if hdv else 'Chưa phân công'} - SĐT: {hdv['sdt'] if hdv else 'N/A'}",
                f"Trạng thái: {t['trangThai']} | Còn trống: {available} chỗ",
                f"Ghi chú điều hành: {t.get('ghiChuDieuHanh', '') or 'Không có'}"
            ]
            set_detail_content("\n".join(info))
            update_transfer_qr()

        tv.bind("<<TreeviewSelect>>", on_select)

        def dang_ky_tour():
            """
            Mục đích:
                Thực hiện xử lý cho hàm `dang_ky_tour` (dang ky tour).
            Tham số:
                Không có.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            sel = tv.selection()
            if not sel:
                return messagebox.showwarning("Chú ý", "Vui lòng chọn một tour để đăng ký!")

            num_people = safe_int(spn_people.get())
            if num_people <= 0:
                return messagebox.showwarning("Lỗi", "Số người đi không hợp lệ!")
            age_breakdown = normalize_age_breakdown(num_people)
            if age_breakdown is None:
                return messagebox.showwarning("Lỗi", "Cơ cấu độ tuổi vượt quá số người đi.")

            ma = tv.item(sel[0])["values"][0]
            t = app["ql"].find_tour(ma)
            if not t:
                return

            if t.get("trangThai") not in TOUR_BOOKABLE_STATUSES:
                return messagebox.showwarning("Không thể đăng ký", f"Tour đang ở trạng thái '{t.get('trangThai', '')}'.")

            occupied = app["ql"].get_occupied_seats(ma)
            available = max(safe_int(t["khach"]) - occupied, 0)
            if num_people > available:
                return messagebox.showerror("Hết chỗ", f"Rất tiếc, tour này chỉ còn {available} chỗ trống!")

            user_info = get_current_user()
            fullname = user_info.get("fullname", user_data.get("fullname", user_data.get("name", "Khách hàng"))) if user_info else user_data.get("fullname", "Khách hàng")
            sdt_khach = user_info.get("sdt", "Chưa cập nhật") if user_info else user_data.get("sdt", "Chưa cập nhật")

            pay_now = max(0, safe_int(ent_pay_now.get()))
            payment_method = pay_method_var.get().strip() or PAYMENT_METHODS[0]
            if payment_method == "Tiền mặt":
                messagebox.showinfo("Lưu ý thanh toán tiền mặt", build_cash_policy_notice(t.get("ngay", "")))

            result = service_create_booking(
                app["ql"],
                ma_tour=ma,
                num_people=num_people,
                pay_now=pay_now,
                payment_method=payment_method,
                username=user_data.get("username", ""),
                fullname=fullname,
                phone=sdt_khach,
                voucher_code=voucher_var.get(),
                passenger_breakdown=age_breakdown,
                actor=user_data.get("username", ""),
                role="user",
            )
            if not result.success:
                return messagebox.showwarning("Không thể đăng ký", result.message)

            created_booking = result.booking or {}

            discount_line = ""
            age_discount_line = ""
            if safe_int(created_booking.get("giamGiaDoiTuong", 0)) > 0:
                age_discount_line = (
                    f"\nGiảm theo độ tuổi: {format_currency(created_booking.get('giamGiaDoiTuong', 0))}"
                )
            if created_booking.get("maVoucher"):
                discount_line = (
                    f"\nMã giảm giá: {created_booking.get('maVoucher')}"
                    f"\nĐã giảm: {format_currency(created_booking.get('giamGiaVoucher', 0))}"
                )

            messagebox.showinfo(
                "Thành công",
                (
                    f"Bạn đã đăng ký tour {t['ten']} cho {num_people} người thành công!\n"
                    f"Mã đặt chỗ: {created_booking.get('maBooking', '')}\n"
                    f"Hình thức thanh toán: {payment_method}\n"
                    f"Cơ cấu độ tuổi: Trẻ em {age_breakdown.get('treEm', 0)} | Trung niên {age_breakdown.get('trungNien', 0)} | Cao tuổi {age_breakdown.get('nguoiCaoTuoi', 0)}"
                    f"{age_discount_line}\n"
                    f"Tổng thanh toán: {format_currency(created_booking.get('tongTien', 0))}"
                    f"{discount_line}\n"
                    f"Đã thanh toán: {format_currency(created_booking.get('daThanhToan', 0))}"
                ),
            )
            tab_danh_sach_tour()

        style_button(action_btn_row, "ĐĂNG KÝ NGAY", THEME["success"], dang_ky_tour).pack(fill="x", pady=(2, 0))
        set_status("Đang ở mục: Khám phá Tour", THEME["primary"])

    def tab_tour_da_dat():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `tab_tour_da_dat` (tab tour da dat).
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
        app["current_tab"] = "booked"

        bookings = my_bookings()

        stats_wrap = tk.Frame(content_area, bg=THEME["bg"])
        stats_wrap.pack(fill="x", pady=(0, 14))

        paid_total = sum(safe_int(b.get("daThanhToan", 0)) for b in bookings)
        debt_total = sum(safe_int(b.get("conNo", 0)) for b in bookings)
        active_total = len([b for b in bookings if b.get("trangThai") not in BOOKING_CANCEL_STATUSES])

        build_stat_card(stats_wrap, "Tổng booking", str(len(bookings)), "Số booking bạn đã tạo trong hệ thống.", THEME["primary"])
        build_stat_card(stats_wrap, "Booking còn hiệu lực", str(active_total), "Các booking chưa hủy hoặc chưa hoàn tiền.", THEME["success"])
        build_stat_card(stats_wrap, "Đã thanh toán", format_currency(paid_total), "Tổng số tiền bạn đã thanh toán.", THEME["warning"])
        build_stat_card(stats_wrap, "Còn nợ", format_currency(debt_total), "Số tiền còn lại của các booking.", "#7c3aed")

        _, body = make_section(
            content_area,
            "Lịch sử đặt tour của bạn",
            "Theo dõi trạng thái thanh toán, cập nhật công nợ và tự hủy booking khi còn được phép.",
            accent="#7c3aed",
        )

        if not bookings:
            tk.Label(body, text="Bạn chưa tham gia tour nào.", font=("Times New Roman", 13), bg=THEME["surface"], fg=THEME["muted"]).pack(pady=40)
            return

        list_area = tk.Frame(body, bg=THEME["surface"])
        list_area.pack(fill="both", expand=True)

        for b in bookings:
            t = app["ql"].find_tour(b["maTour"])
            if not t:
                continue

            card = tk.Frame(list_area, bg=THEME["surface"], bd=1, relief="solid", padx=15, pady=12)
            card.pack(fill="x", pady=6)

            left = tk.Frame(card, bg=THEME["surface"])
            left.pack(side="left", fill="both", expand=True)

            tk.Label(left, text=f"✅ {t['ten']}", font=("Times New Roman", 14, "bold"), bg=THEME["surface"], fg=THEME["primary"]).pack(anchor="w")

            voucher_text = ""
            if str(b.get("maVoucher", "")).strip():
                voucher_text = f" | Voucher: {b.get('maVoucher')} (-{format_currency(b.get('giamGiaVoucher', 0))})"
            age_discount_text = ""
            if safe_int(b.get("giamGiaDoiTuong", 0)) > 0:
                age_cfg = b.get("coCauDoTuoi", {}) if isinstance(b.get("coCauDoTuoi"), dict) else {}
                age_discount_text = (
                    f" | Độ tuổi: TE {safe_int(age_cfg.get('treEm', 0))}/TN {safe_int(age_cfg.get('trungNien', 0))}/CT {safe_int(age_cfg.get('nguoiCaoTuoi', 0))}"
                    f" (-{format_currency(b.get('giamGiaDoiTuong', 0))})"
                )
            refund_text = ""
            if str(b.get("trangThaiHoanTien", "")).strip():
                refund_text = f" | Hoàn tiền: {b.get('trangThaiHoanTien')}"

            booking_label = tk.Label(
                left,
                text=(
                    f"Mã: {b['maBooking']} | Ngày: {t['ngay']} | Số người: {b['soNguoi']} | "
                    f"Trạng thái: {b['trangThai']} | Hình thức TT: {b.get('hinhThucThanhToan', 'Tiền mặt')} | "
                    f"Đã thanh toán: {format_currency(b.get('daThanhToan', 0))} | Còn nợ: {format_currency(b.get('conNo', 0))}"
                    f"{age_discount_text}{voucher_text}{refund_text}"
                ),
                font=("Times New Roman", 12),
                bg=THEME["surface"],
                wraplength=responsive_wraplength(base_offset=420, minimum=300),
                justify="left"
            )
            booking_label.pack(anchor="w", pady=(4, 0))

            def sync_booking_wrap(event, label=booking_label):
                """
                Mục đích:
                    Thực hiện xử lý cho hàm `sync_booking_wrap` (sync booking wrap).
                Tham số:
                    event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                    label: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                Giá trị trả về:
                    Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
                Tác dụng phụ:
                    Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
                Lưu ý nghiệp vụ:
                    Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
                """
                label.config(wraplength=max(300, event.width - 230))

            card.bind("<Configure>", sync_booking_wrap)

            style_button(card, "Thanh toán", THEME["primary"], lambda m=b["maBooking"]: cap_nhat_thanh_toan(m)).pack(side="right", padx=(0, 8))
            style_button(card, "Hủy", THEME["danger"], lambda m=b["maBooking"]: huy_tour(m)).pack(side="right")

        set_status("Đang ở mục: Tour đã đặt", THEME["primary"])

    def cap_nhat_thanh_toan(ma_booking):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `cap_nhat_thanh_toan` (cap nhat thanh toan).
        Tham số:
            ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        booking = next((b for b in app["ql"].list_bookings if b["maBooking"] == ma_booking), None)
        if not booking:
            return

        if booking.get("trangThai") in BOOKING_CANCEL_STATUSES:
            return messagebox.showwarning("Không thể thanh toán", "Booking này đang ở trạng thái hủy/hoàn tiền.")

        tong_tien = safe_int(booking.get("tongTien", 0))
        tong_tien_goc = safe_int(booking.get("tongTienGoc", tong_tien))
        giam_doi_tuong = safe_int(booking.get("giamGiaDoiTuong", 0))
        giam_voucher = safe_int(booking.get("giamGiaVoucher", 0))
        da_thanh_toan = safe_int(booking.get("daThanhToan", 0))
        con_no = max(tong_tien - da_thanh_toan, 0)

        if con_no <= 0:
            return messagebox.showinfo("Đã hoàn tất", "Booking này đã thanh toán đủ.")

        top = tk.Toplevel(root)
        top.title(f"Thanh toán booking {ma_booking}")
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        popup_w = min(620, max(520, screen_w - 80))
        popup_h = min(760, max(560, screen_h - 120))
        top.geometry(f"{popup_w}x{popup_h}")
        top.configure(bg=THEME["bg"])
        top.transient(root)
        top.grab_set()
        top.resizable(True, True)

        card = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid", padx=20, pady=20)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(card, text=f"Booking: {ma_booking}", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 14, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(
            card,
            text=(
                f"Tổng gốc: {format_currency(tong_tien_goc)}\n"
                f"Giảm độ tuổi: {format_currency(giam_doi_tuong)}\n"
                f"Giảm voucher: {format_currency(giam_voucher)}"
                + (f" ({booking.get('maVoucher', '')})\n" if str(booking.get("maVoucher", "")).strip() else "\n")
                + f"Tổng tiền: {format_currency(tong_tien)}\n"
                f"Đã thanh toán: {format_currency(da_thanh_toan)}\n"
                f"Còn nợ: {format_currency(con_no)}"
            ),
            bg=THEME["surface"],
            fg=THEME["text"],
            justify="left",
            font=("Times New Roman", 12),
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(card, text="Hình thức thanh toán:", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 12, "bold")).pack(anchor="w")
        current_method = booking.get("hinhThucThanhToan", PAYMENT_METHODS[0])
        if current_method not in PAYMENT_METHODS:
            current_method = PAYMENT_METHODS[0]
        method_var = tk.StringVar(value=current_method)
        cmb_method = ttk.Combobox(card, textvariable=method_var, values=PAYMENT_METHODS, state="readonly", font=("Times New Roman", 11), width=28)
        cmb_method.pack(anchor="w", pady=(4, 12))

        tour_for_booking = app["ql"].find_tour(booking.get("maTour", ""))
        cash_policy_var = tk.StringVar(value="")
        cash_policy_lbl = tk.Label(card, textvariable=cash_policy_var, bg=THEME["surface"], fg=THEME["warning"], justify="left", font=("Times New Roman", 11, "bold"), wraplength=460)
        cash_policy_lbl.pack(anchor="w", pady=(0, 10))

        tk.Label(card, text="Số tiền thanh toán thêm:", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 12, "bold")).pack(anchor="w")
        amount_entry = tk.Entry(card, font=("Times New Roman", 12), relief="solid", bd=1)
        amount_entry.insert(0, str(con_no))
        amount_entry.pack(anchor="w", pady=(4, 10), fill="x")

        qr_box = tk.Frame(card, bg=THEME["note_bg"], bd=1, relief="solid", padx=8, pady=8)
        qr_box.pack(fill="x", pady=(0, 10))

        tk.Label(qr_box, text="QR Chuyển khoản", font=("Times New Roman", 12, "bold"), bg=THEME["note_bg"], fg=THEME["note_fg"]).pack(anchor="w")

        qr_image_lbl = tk.Label(qr_box, text="", bg=THEME["note_bg"], fg=THEME["muted"], justify="center", wraplength=240)
        qr_image_lbl.pack(anchor="center", pady=(6, 6))

        qr_status_var = tk.StringVar(value="")
        qr_status_lbl = tk.Label(qr_box, textvariable=qr_status_var, font=("Times New Roman", 10), bg=THEME["note_bg"], fg=THEME["note_fg"], justify="left", wraplength=420)
        qr_status_lbl.pack(anchor="w")

        qr_note_var = tk.StringVar(value="")
        qr_note_lbl = tk.Label(qr_box, textvariable=qr_note_var, font=("Times New Roman", 9, "italic"), bg=THEME["note_bg"], fg=THEME["muted"], justify="left", wraplength=420)
        qr_note_lbl.pack(anchor="w", pady=(3, 0))
        payment_qr_request_id = {"value": 0}

        def sync_payment_layout(_event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `sync_payment_layout` (sync payment layout).
            Tham số:
                _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            wrap_size = max(260, card.winfo_width() - 56)
            cash_policy_lbl.config(wraplength=wrap_size)
            qr_image_lbl.config(wraplength=wrap_size)
            qr_status_lbl.config(wraplength=wrap_size)
            qr_note_lbl.config(wraplength=wrap_size)

        card.bind("<Configure>", sync_payment_layout)
        sync_payment_layout()

        def update_payment_qr():
            """
            Mục đích:
                Thực hiện xử lý cho hàm `update_payment_qr` (update payment qr).
            Tham số:
                Không có.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            if method_var.get().strip() != "Chuyển khoản":
                payment_qr_request_id["value"] += 1
                qr_box.pack_forget()
                qr_image_lbl.config(image="", text="")
                qr_image_lbl.image = None
                qr_status_var.set("")
                qr_note_var.set("")
                cash_policy_var.set(build_cash_policy_notice(tour_for_booking.get("ngay", "")) if tour_for_booking else build_cash_policy_notice(""))
                return

            cash_policy_var.set("")
            qr_box.pack(fill="x", pady=(0, 10), before=btns)
            pay_more = max(0, safe_int(amount_entry.get()))
            if pay_more <= 0:
                qr_image_lbl.config(image="", text="Nhập số tiền để tạo QR")
                qr_image_lbl.image = None
                qr_status_var.set("Số tiền thanh toán thêm phải lớn hơn 0.")
                qr_note_var.set("")
                return

            transfer_content = f"{ma_booking}-{user_data.get('username', 'KH')}-{pay_more}"
            payment_qr_request_id["value"] += 1
            current_request_id = payment_qr_request_id["value"]
            qr_image_lbl.config(image="", text="Đang tải QR...")
            qr_image_lbl.image = None
            qr_status_var.set("Đang tải mã chuyển khoản, vui lòng chờ...")
            qr_note_var.set("")

            def worker():
                """
                Mục đích:
                    Thực hiện xử lý cho hàm `worker` (worker).
                Tham số:
                    Không có.
                Giá trị trả về:
                    Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
                Tác dụng phụ:
                    Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
                Lưu ý nghiệp vụ:
                    Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
                """
                try:
                    qr_url = build_transfer_qr_url(pay_more, transfer_content)
                    qr_photo = fetch_transfer_qr_photo(qr_url, max_size_px=220)
                except (OSError, URLError, ValueError, tk.TclError) as exc:
                    error_message = short_ui_error(exc)

                    def apply_error():
                        """
                        Mục đích:
                            Thực hiện xử lý cho hàm `apply_error` (apply error).
                        Tham số:
                            Không có.
                        Giá trị trả về:
                            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
                        Tác dụng phụ:
                            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
                        Lưu ý nghiệp vụ:
                            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
                        """
                        if current_request_id != payment_qr_request_id["value"] or method_var.get().strip() != "Chuyển khoản":
                            return
                        qr_image_lbl.config(image="", text="(Không tải được QR)")
                        qr_image_lbl.image = None
                        qr_status_var.set("Không thể gọi API QR. Vui lòng thử lại sau.")
                        qr_note_var.set(error_message)

                    root.after(0, apply_error)
                    return

                def apply_success():
                    """
                    Mục đích:
                        Thực hiện xử lý cho hàm `apply_success` (apply success).
                    Tham số:
                        Không có.
                    Giá trị trả về:
                        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
                    Tác dụng phụ:
                        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
                    Lưu ý nghiệp vụ:
                        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
                    """
                    if current_request_id != payment_qr_request_id["value"] or method_var.get().strip() != "Chuyển khoản":
                        return
                    qr_image_lbl.config(image=qr_photo, text="")
                    qr_image_lbl.image = qr_photo
                    qr_status_var.set(f"Quét mã để thanh toán thêm {pay_more:,}đ".replace(",", "."))
                    qr_note_var.set("Nội dung CK được tạo tự động theo mã booking.")

                root.after(0, apply_success)

            threading.Thread(target=worker, daemon=True).start()

        cmb_method.bind("<<ComboboxSelected>>", lambda _e: update_payment_qr())
        amount_entry.bind("<KeyRelease>", lambda _e: update_payment_qr())

        def submit_payment():
            """
            Mục đích:
                Thực hiện xử lý cho hàm `submit_payment` (submit payment).
            Tham số:
                Không có.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            result = service_apply_payment(
                app["ql"],
                ma_booking,
                amount_entry.get(),
                method_var.get().strip() or PAYMENT_METHODS[0],
                actor=user_data.get("username", ""),
                role="user",
            )
            if not result.success:
                return messagebox.showwarning("Lỗi", result.message, parent=top)

            top.destroy()
            messagebox.showinfo("Thành công", result.message)
            tab_tour_da_dat()

        btns = tk.Frame(card, bg=THEME["surface"])
        btns.pack(fill="x", pady=(8, 0))
        style_button(btns, "Xác nhận", THEME["success"], submit_payment).pack(side="left", fill="x", expand=True, padx=(0, 6))
        style_button(btns, "Đóng", THEME["muted"], top.destroy).pack(side="left", fill="x", expand=True)
        update_payment_qr()

    def huy_tour(ma_booking):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `huy_tour` (huy tour).
        Tham số:
            ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn hủy đặt chỗ {ma_booking}?"):
            result = service_cancel_booking(
                app["ql"],
                ma_booking,
                actor=user_data.get("username", ""),
                role="user",
            )
            if not result.success:
                return messagebox.showwarning("Không thể hủy", result.message)

            messagebox.showinfo("Thành công", result.message)
            tab_tour_da_dat()

    def tab_gui_danh_gia():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `tab_gui_danh_gia` (tab gui danh gia).
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
        app["current_tab"] = "review"

        _, body = make_section(
            content_area,
            "Gửi ý kiến phản hồi",
            "Góp ý chất lượng dịch vụ hoặc đánh giá riêng cho hướng dẫn viên đã đồng hành cùng bạn.",
            accent="#059669",
        )

        card = tk.Frame(body, bg=THEME["surface"], padx=25, pady=25)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Bạn muốn đánh giá cho đối tượng nào?", font=("Times New Roman", 13, "bold"), bg=THEME["surface"]).pack(anchor="w")

        target_var = tk.StringVar(value="Công ty")
        target_fr = tk.Frame(card, bg=THEME["surface"])
        target_fr.pack(fill="x", pady=(5, 15))

        tk.Radiobutton(target_fr, text="Công ty Vietnam Travel", variable=target_var, value="Công ty", bg=THEME["surface"], font=("Times New Roman", 12)).pack(side="left", padx=(0, 20))
        tk.Radiobutton(target_fr, text="Hướng dẫn viên", variable=target_var, value="HDV", bg=THEME["surface"], font=("Times New Roman", 12)).pack(side="left")

        my_hdvs = []
        for b in my_bookings():
            t = app["ql"].find_tour(b["maTour"])
            if t and t.get("hdvPhuTrach"):
                h = app["ql"].find_hdv(t["hdvPhuTrach"])
                if h and h not in my_hdvs:
                    my_hdvs.append(h)

        hdv_options = [f"{h['maHDV']} - {h['tenHDV']}" for h in my_hdvs]
        hdv_var = tk.StringVar()

        hdv_sel_fr = tk.Frame(card, bg=THEME["surface"])
        tk.Label(hdv_sel_fr, text="Chọn Hướng dẫn viên:", font=("Times New Roman", 12), bg=THEME["surface"]).pack(side="left", padx=(0, 10))
        hdv_cb = ttk.Combobox(hdv_sel_fr, textvariable=hdv_var, values=hdv_options, state="readonly", width=30, font=("Times New Roman", 11))
        hdv_cb.pack(side="left")

        score_fr = tk.Frame(card, bg=THEME["surface"])
        scores = {}

        criteria = [
            ("Kiến thức chuyên môn", "skill"),
            ("Thái độ phục vụ", "attitude"),
            ("Xử lý tình huống", "problem")
        ]

        for label, key in criteria:
            row = tk.Frame(score_fr, bg=THEME["surface"])
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label, width=20, anchor="w", bg=THEME["surface"], font=("Times New Roman", 12)).pack(side="left")
            s = tk.Scale(row, from_=0, to=100, orient="horizontal", bg=THEME["surface"], length=300, showvalue=True, highlightthickness=0)
            s.set(80)
            s.pack(side="left")
            scores[key] = s

        def update_ui(*args):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `update_ui` (update ui).
            Tham số:
                *args: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            if target_var.get() == "HDV":
                hdv_sel_fr.pack(fill="x", pady=(0, 15), before=txt_label)
                score_fr.pack(fill="x", pady=(0, 15), before=txt_label)
            else:
                hdv_sel_fr.pack_forget()
                score_fr.pack_forget()

        target_var.trace_add("write", update_ui)

        txt_label = tk.Label(card, text="Nội dung nhận xét chi tiết:", font=("Times New Roman", 12, "bold"), bg=THEME["surface"])
        txt_label.pack(anchor="w")

        txt = tk.Text(card, height=6, font=("Times New Roman", 13), relief="solid", bd=1, wrap="word")
        txt.pack(fill="both", expand=True, pady=(5, 20))

        def update_hdv_metrics(ma_hdv, review_data):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `update_hdv_metrics` (update hdv metrics).
            Tham số:
                ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                review_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            h = app["ql"].find_hdv(ma_hdv)
            if not h:
                return

            for f in ["total_reviews", "skill_score", "attitude_score", "problem_solving_score", "avg_rating"]:
                if f not in h:
                    h[f] = 0

            n = h["total_reviews"]
            h["skill_score"] = round((h["skill_score"] * n + review_data["skill"]) / (n + 1), 1)
            h["attitude_score"] = round((h["attitude_score"] * n + review_data["attitude"]) / (n + 1), 1)
            h["problem_solving_score"] = round((h["problem_solving_score"] * n + review_data["problem"]) / (n + 1), 1)
            h["total_reviews"] += 1
            h["avg_rating"] = round((h["skill_score"] + h["attitude_score"] + h["problem_solving_score"]) / 3, 1)

        def gui_review():
            """
            Mục đích:
                Thực hiện xử lý cho hàm `gui_review` (gui review).
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
            if not content:
                return messagebox.showwarning("Lỗi", "Vui lòng nhập nội dung đánh giá!")

            target = target_var.get()
            selected_hdv_code = ""

            if target == "HDV":
                if not hdv_var.get():
                    return messagebox.showwarning("Lỗi", "Vui lòng chọn Hướng dẫn viên muốn đánh giá!")
                selected_hdv_code = hdv_var.get().split(" - ")[0]

            fullname = user_data.get("fullname") or user_data.get("name", "Khách hàng")
            eligible_bookings = []
            for booking in my_bookings():
                booking_state = booking_state_from_status(
                    str(booking.get("trangThai", "")).strip(),
                    str(booking.get("trangThaiHoanTien", "")).strip(),
                )
                if booking_state != BOOKING_STATE_COMPLETED:
                    continue

                if any(
                    str(review.get("maBooking", "")).strip() == str(booking.get("maBooking", "")).strip()
                    and str(review.get("username", "")).strip().lower() == str(user_data.get("username", "")).strip().lower()
                    for review in app["ql"].list_reviews
                ):
                    continue

                if target == "HDV":
                    tour = app["ql"].find_tour(booking.get("maTour", ""))
                    if not tour or str(tour.get("hdvPhuTrach", "")).strip() != selected_hdv_code:
                        continue

                eligible_bookings.append(booking)

            if not eligible_bookings:
                return messagebox.showwarning(
                    "Lỗi",
                    "Bạn chỉ có thể đánh giá một lần cho booking đã hoàn thành và chưa đánh giá trước đó.",
                )

            booking_for_review = eligible_bookings[0]
            rating = ""
            if target == "HDV":
                rating = round(
                    (scores["skill"].get() + scores["attitude"].get() + scores["problem"].get()) / 60,
                    1,
                )

            result = service_create_review(
                app["ql"],
                username=str(user_data.get("username", "")).strip(),
                fullname=fullname,
                ma_booking=str(booking_for_review.get("maBooking", "")).strip(),
                content=content,
                target="HDV" if target == "HDV" else "Tour",
                target_id=selected_hdv_code if target == "HDV" else str(booking_for_review.get("maTour", "")).strip(),
                rating=rating if rating != "" else None,
            )
            if not result.success:
                return messagebox.showwarning("Lỗi", result.message)

            messagebox.showinfo("Cảm ơn", result.message)
            tab_danh_sach_tour()

        style_button(card, "GỬI NHẬN XÉT", THEME["primary"], gui_review).pack()
        update_ui()
        set_status("Đang ở mục: Gửi đánh giá", THEME["primary"])

    def tab_ho_so():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `tab_ho_so` (tab ho so).
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
        app["current_tab"] = "profile"

        user_info = get_current_user()

        _, body = make_section(
            content_area,
            "Thông tin hồ sơ cá nhân",
            "Cập nhật họ tên, số điện thoại và đổi mật khẩu nếu cần.",
            accent="#dc2626",
        )

        card = tk.Frame(body, bg=THEME["surface"], padx=25, pady=25)
        card.pack(fill="x")

        if not user_info:
            tk.Label(card, text="Lỗi: Không tìm thấy thông tin tài khoản!", fg=THEME["danger"], bg=THEME["surface"]).pack()
            return

        fields = [("Họ và tên", "fullname"), ("Số điện thoại", "sdt"), ("Mật khẩu mới", "password")]
        widgets = {}

        for label, key in fields:
            row = tk.Frame(card, bg=THEME["surface"])
            row.pack(fill="x", pady=8)
            tk.Label(row, text=label, width=15, anchor="w", bg=THEME["surface"], font=("Times New Roman", 12, "bold")).pack(side="left")

            show_char = "*" if key == "password" else ""
            e = tk.Entry(row, font=("Times New Roman", 12), relief="solid", bd=1, width=30, show=show_char)
            e.pack(side="left", fill="x", expand=True, ipady=4)
            if key != "password":
                e.insert(0, user_info.get(key, ""))
            widgets[key] = e

        tk.Label(card, text="Để trống mật khẩu nếu không muốn thay đổi.", bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 11, "italic")).pack(anchor="w", pady=(4, 10))

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
            new_fullname = widgets["fullname"].get().strip()
            new_phone = widgets["sdt"].get().strip()
            new_pass = widgets["password"].get().strip()

            if not is_valid_fullname(new_fullname):
                return messagebox.showwarning("Lỗi", "Họ tên quá ngắn (tối thiểu 3 ký tự).")
            if not is_valid_phone(new_phone):
                return messagebox.showwarning("Lỗi", "Số điện thoại không hợp lệ (10 số, bắt đầu bằng 0).")
            if new_pass and not is_valid_password(new_pass):
                return messagebox.showwarning("Lỗi", "Mật khẩu quá ngắn (tối thiểu 3 ký tự).")

            for u in app["ql"].list_users:
                if u.get("username") == user_info.get("username"):
                    continue
                if u.get("sdt") == new_phone:
                    return messagebox.showwarning("Lỗi", "Số điện thoại đã tồn tại ở tài khoản khác.")

            user_info["fullname"] = new_fullname
            user_info["sdt"] = new_phone
            if new_pass:
                user_info["password"] = prepare_password_for_storage(new_pass)

            user_data["fullname"] = new_fullname
            user_data["name"] = new_fullname
            user_data["sdt"] = new_phone

            app["ql"].save()
            messagebox.showinfo("Thành công", "Đã cập nhật thông tin cá nhân thành công!")
            khoi_tao_khach(root, user_data)

        style_button(card, "LƯU THÔNG TIN", THEME["success"], save_profile).pack(pady=20)
        set_status("Đang ở mục: Hồ sơ cá nhân", THEME["primary"])

    def tab_thong_bao():
       # 1. Thêm lệnh xóa container cũ và đặt trạng thái tab
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
       app["current_tab"] = "notification"

       # 2. Khởi tạo section giao diện (giống các tab khác)
       _, body = make_section(
           content_area,
           "Thông báo từ hệ thống",
           "Cập nhật các thông báo mới nhất từ các tour bạn đã đăng ký.",
           accent="#d97706",
       )

       # 3. Khởi tạo list_area để chứa danh sách thông báo
       list_area = tk.Frame(body, bg=THEME["surface"])
       list_area.pack(fill="both", expand=True)

       user_bookings = [
            b for b in app["ql"].list_bookings
            if str(b.get("usernameDat", "")).strip() == str(user_data.get("username", "")).strip()
        ]
       my_tour_codes = {str(b.get("maTour", "")).strip() for b in user_bookings if b.get("maTour")}

       # Lọc thông báo và loại bỏ các thông báo bị trùng lặp nội dung
       relevant_notifs = []
       seen_notifs = set()

       for n in app["ql"].list_notifications:
           ma_tour = str(n.get("maTour", "")).strip()
           if ma_tour in my_tour_codes:
               # Tạo một bộ "chữ ký" gồm Mã Tour + Nội dung + Ngày để kiểm tra trùng
               noi_dung = str(n.get("content", "")).strip()
               ngay_thang = str(n.get("date", "")).strip()
               notif_signature = (ma_tour, noi_dung, ngay_thang)
               
               # Nếu thông báo này chưa từng xuất hiện thì mới thêm vào danh sách hiển thị
               if notif_signature not in seen_notifs:
                   seen_notifs.add(notif_signature)
                   relevant_notifs.append(n)

       if not relevant_notifs:
            tk.Label(
                list_area,
                text="Bạn chưa có thông báo nào từ tour đã đăng ký.",
                bg=THEME["surface"],
                fg=THEME["muted"],
                font=("Times New Roman", 13, "italic")
            ).pack(anchor="w", pady=10)
       else:
            for n in relevant_notifs:
                tour_title = n.get("tenTour", "").strip() or n.get("maTour", "Thông báo")
                hdv = app["ql"].find_hdv(n.get("maHDV"))

                hdv_name = (
                    n.get("tenHDV")
                    or (hdv.get("tenHDV") if hdv else "")
                    or n.get("maHDV")
                    or "N/A"
                )
                notif_text  = (
                    str(n.get("content") or n.get("noiDung") or n.get("thongBao") or "").strip()
                    or "Chưa có nội dung thông báo."
                )
                notif_date = str(n.get("date") or n.get("thoiGian") or "").strip()

                card = tk.Frame(list_area, bg=THEME["surface"], bd=1, relief="solid", padx=20, pady=15)
                card.pack(fill="x", pady=8)

                header_fr = tk.Frame(card, bg=THEME["surface"])
                header_fr.pack(fill="x")

                tk.Label(
                    header_fr,
                    text=f"📢 {tour_title}",
                    font=("Times New Roman", 14, "bold"),
                    bg=THEME["surface"],
                    fg=THEME["danger"]
                ).pack(side="left")

                tk.Label(
                    header_fr,
                    text=notif_date,
                    font=("Times New Roman", 11),
                    bg=THEME["surface"],
                    fg=THEME["muted"]
                ).pack(side="right")

                tk.Label(
                    card,
                    text=f"HDV: {hdv_name}",
                    font=("Times New Roman", 12, "italic"),
                    bg=THEME["surface"],
                    fg=THEME["primary"]
                ).pack(anchor="w", pady=(5, 10))

                msg = tk.Label(
                    card,
                    text=notif_text,
                    font=("Times New Roman", 13),
                    bg=THEME["surface"],
                    justify="left",
                    wraplength=720
                )
                msg.pack(anchor="w")

                def sync_notif_wrap(event, label=msg):
                    """
                    Mục đích:
                        Thực hiện xử lý cho hàm `sync_notif_wrap` (sync notif wrap).
                    Tham số:
                        event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                        label: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                    Giá trị trả về:
                        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
                    Tác dụng phụ:
                        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
                    Lưu ý nghiệp vụ:
                        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
                    """
                    label.config(wraplength=max(320, event.width - 40))

                card.bind("<Configure>", sync_notif_wrap)

       set_status("Đang ở mục: Thông báo", THEME["primary"])

    def open_view(title, subtitle, current_tab, view_fn, menu_button, badge_text="KHÁCH HÀNG", badge_bg="#dbeafe", badge_fg="#1d4ed8"):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `open_view` (open view).
        Tham số:
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            subtitle: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            current_tab: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            view_fn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            menu_button: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            badge_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            badge_bg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            badge_fg: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        app["page_title_var"].set(title)
        app["page_subtitle_var"].set(subtitle)
        app["current_tab"] = current_tab
        app["current_view"] = {
            "title": title,
            "subtitle": subtitle,
            "current_tab": current_tab,
            "view_fn": view_fn,
            "menu_button": menu_button,
            "badge_text": badge_text,
            "badge_bg": badge_bg,
            "badge_fg": badge_fg,
        }
        set_badge(badge_text, badge_bg, badge_fg)
        set_active_menu(menu_button)
        view_fn()
        set_status(f"Đang ở mục: {title}", THEME["primary"])

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
        current_view = app.get("current_view")
        if current_view:
            open_view(
                current_view["title"],
                current_view["subtitle"],
                current_view["current_tab"],
                current_view["view_fn"],
                current_view["menu_button"],
                current_view["badge_text"],
                current_view["badge_bg"],
                current_view["badge_fg"],
            )
        set_status("Đã tải lại dữ liệu", THEME["success"])

    style_button(head_right, "↻ Tải lại", THEME["primary"], reload_current_page).pack(anchor="e")

    nav_buttons = []
    nav_views = [
        ("Khám phá Tour", "Xem danh sách tour mở bán và đăng ký nhanh.", "tour", tab_danh_sach_tour, "🗺", "DANH SÁCH TOUR", "#dbeafe", "#1d4ed8"),
        ("Tour đã đặt", "Theo dõi lịch sử booking và trạng thái thanh toán.", "booked", tab_tour_da_dat, "📄", "BOOKING", "#ede9fe", "#7c3aed"),
        ("Thông báo", "Cập nhật thông báo mới nhất từ đoàn và hướng dẫn viên.", "notification", tab_thong_bao, "🔔", "THÔNG BÁO", "#fef3c7", "#d97706"),
        ("Gửi đánh giá", "Góp ý dịch vụ và đánh giá chất lượng hướng dẫn viên.", "review", tab_gui_danh_gia, "⭐", "ĐÁNH GIÁ", "#dcfce7", "#059669"),
        ("Hồ sơ cá nhân", "Quản lý thông tin cá nhân và bảo mật tài khoản.", "profile", tab_ho_so, "⚙", "TÀI KHOẢN", "#fee2e2", "#dc2626"),
    ]

    for idx, (title, subtitle, current_tab, view_fn, icon, badge_text, badge_bg, badge_fg) in enumerate(nav_views):
        btn = menu_btn(
            title,
            lambda t=title, s=subtitle, c=current_tab, f=view_fn, b_idx=idx, bt=badge_text, bbg=badge_bg, bfg=badge_fg:
                open_view(t, s, c, f, nav_buttons[b_idx], bt, bbg, bfg),
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
        command=lambda: logout_user(root)
    ).pack(fill="x")

    if nav_buttons:
        first_title, first_subtitle, first_current_tab, first_view, _first_icon, first_badge, first_badge_bg, first_badge_fg = nav_views[0]
        open_view(first_title, first_subtitle, first_current_tab, first_view, nav_buttons[0], first_badge, first_badge_bg, first_badge_fg)

def logout_user(root):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `logout_user` (logout user).
    Tham số:
        root: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if messagebox.askyesno("Xác nhận", "Bạn có muốn đăng xuất?"):
        for widget in root.winfo_children():
            widget.destroy()
        try:
            from GUI.Login.login import set_root, show_role_selection
            set_root(root)
            root.configure(bg=THEME["bg"])
            show_role_selection()
        except (ImportError, RuntimeError, tk.TclError) as e:
            messagebox.showerror("Lỗi", f"Không thể quay lại màn hình đăng nhập.\n{e}")


if __name__ == "__main__":
    win = tk.Tk()
    win.title("Vietnam Travel 2026")
    win.geometry("1240x760")
    win.minsize(1040, 660)
    win.mainloop()
