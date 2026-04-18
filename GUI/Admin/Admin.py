# -*- coding: utf-8 -*-
import os
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
import copy

from GUI.Admin.tabs import get_admin_tab_definitions, get_admin_tab_handler
from core.booking_pricing import calculate_age_discount, normalize_passenger_breakdown
from core.booking_service import (
# =============================================================================
# FILE ADMIN QUẢN TRỊ HỆ THỐNG TOUR
# -----------------------------------------------------------------------------
# Nội dung chính gồm: dashboard, quản lý HDV, khách hàng, tour, booking,
# phản hồi/thông báo, voucher và hàm khởi tạo giao diện admin.
# =============================================================================

    approve_refund as service_approve_refund,
    reject_refund as service_reject_refund,
    summarize_bookings_by_tour,
)
from core.crud_logging import collect_changed_fields, write_crud_log
from core.datastore import SQLiteDataStore
from core.normalizers import (
    normalize_notification_item as core_normalize_notification_item,
    normalize_review_item as core_normalize_review_item,
)
from core.reporting import build_revenue_report
from core.security import mask_password, prepare_password_for_storage
from core.tk_text import enable_tk_text_autofix
from core.validation import is_valid_email as core_is_valid_email
from core.validation import is_valid_phone as core_is_valid_phone
from core.voucher_service import (
    build_voucher_scope_label,
    normalize_tour_scope,
    validate_voucher_payload,
)

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
    "status_bg": "#e8eef8",
    "header_bg": "#ffffff",
    "heading_bg": "#e2e8f0",
    "note_bg": "#fff7ed",
    "note_fg": "#9a3412",
    "zebra_even": "#f8fbff",
    "zebra_odd": "#ffffff",
}

TOUR_STATUSES = ["Giữ chỗ", "Mở bán", "Đã chốt đoàn", "Chờ khởi hành", "Đang đi", "Hoàn tất", "Đã hủy", "Tạm hoãn"]
BOOKING_STATUSES = ["Mới tạo", "Đã cọc", "Đã thanh toán", "Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]
HDV_STATUSES = ["Sẵn sàng", "Đã phân công", "Đang dẫn tour", "Tạm nghỉ"]

# =========================
# PATH DỮ LIỆU
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Admin", "data")
DATA_FILE = os.path.join(DATA_DIR, "vietnam_travel_data.json")
REVIEWS_FILE = os.path.join(DATA_DIR, "vietnam_travel_reviews.json")
NOTIF_FILE = os.path.join(DATA_DIR, "vietnam_travel_notifications.json")

DEFAULT_DATA = {
    "admin": {"username": "admin", "password": "123"}
}

# =========================
# DATA STORE
# =========================
# -----------------------------------------------------------------------------
# Hàm bọc (wrapper) cho bộ chuẩn hóa dữ liệu đánh giá.
# Mục đích: đồng nhất cấu trúc review trước khi lưu/hiển thị trong hệ thống.
# Hàm này không tự xử lý logic mới mà ủy quyền sang core.normalizers.
# -----------------------------------------------------------------------------
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
    return core_normalize_review_item(r)


# -----------------------------------------------------------------------------
# Hàm bọc để chuẩn hóa một bản ghi thông báo.
# Có truyền kèm datastore khi cần đối chiếu dữ liệu liên quan trong quá trình chuẩn hóa.
# -----------------------------------------------------------------------------
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
    return core_normalize_notification_item(n, datastore=datastore)
# =============================================================================
# Lớp kho dữ liệu chính của màn hình Admin.
# Kế thừa SQLiteDataStore để tái sử dụng logic load/save dữ liệu,
# đồng thời truyền vào các hàm chuẩn hóa review/thông báo đặc thù của module này.
# =============================================================================
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
        )


# =========================
# HELPERS
# =========================
# Xóa toàn bộ widget con trong vùng nội dung trung tâm để chuẩn bị render tab mới.
def clear_container(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `clear_container` (clear container).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    for widget in app["container"].winfo_children():
        widget.destroy()

# Cập nhật nội dung thanh trạng thái phía dưới giao diện.
# Nếu có truyền màu, đồng thời đổi màu chữ để nhấn mạnh trạng thái hiện tại.
def set_status(app, text, color=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `set_status` (set status).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
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
    if color:
        app["status_label"].config(fg=color)


# Tải lại dữ liệu từ datastore, sau đó render lại đúng tab admin đang mở.
# Dùng khi cần làm mới giao diện sau khi CRUD hoặc sau khi dữ liệu thay đổi từ nơi khác.
def reload_admin_current_tab(app, success_message="Đã tải lại dữ liệu"):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `reload_admin_current_tab` (reload admin current tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        success_message: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    app["ql"].load()
    current_tab = app.get("current_tab", "dashboard")
    handler = get_admin_tab_handler(current_tab)
    handler(app)
    set_status(app, success_message, THEME["success"])

# Tạo nhanh một nút theo bộ giao diện thống nhất của toàn module admin.
# Việc gom style vào một hàm giúp các nút đồng nhất màu sắc, font và hành vi.
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


# Thiết lập font mặc định cho toàn bộ ứng dụng Tkinter và cho các widget ttk.
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

# Tô màu xen kẽ từng dòng của Treeview để bảng dữ liệu dễ nhìn hơn.
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

# Hàm chuyển tiếp sang validator lõi để kiểm tra số điện thoại hợp lệ.
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
    return core_is_valid_phone(phone)

# Hàm chuyển tiếp sang validator lõi để kiểm tra email hợp lệ.
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
    return core_is_valid_email(email)


# Chuyển chuỗi ngày theo định dạng dd/mm/yyyy sang đối tượng datetime; lỗi thì trả về None.
def parse_ddmmyyyy(date_text):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `parse_ddmmyyyy` (parse ddmmyyyy).
    Tham số:
        date_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return datetime.strptime(str(date_text or "").strip(), "%d/%m/%Y")
    except ValueError:
        return None

# Kiểm tra chuỗi ngày có đúng định dạng dd/mm/yyyy hay không.
def is_valid_date(date_text):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_date` (is valid date).
    Tham số:
        date_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        datetime.strptime(date_text, "%d/%m/%Y")
        return True
    except ValueError:
        return False

# Ép kiểu sang số nguyên an toàn; nếu lỗi thì trả về 0 để tránh làm hỏng luồng xử lý.
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
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


# Định dạng số tiền theo kiểu hiển thị Việt Nam, ví dụ: 1000000 -> 1.000.000đ.
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


# Lấy username admin hiện tại để ghi log thao tác CRUD và các hành động nghiệp vụ.
def get_admin_actor(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `get_admin_actor` (get admin actor).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return str(app["ql"].data.get("admin", {}).get("username", "admin")).strip() or "admin"


# Chuẩn hóa họ tên: bỏ khoảng trắng thừa và viết hoa chữ cái đầu từng từ.
def normalize_name_case(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_name_case` (normalize name case).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    text = " ".join(str(value or "").strip().split())
    if not text:
        return ""
    return " ".join(part[:1].upper() + part[1:].lower() if part else "" for part in text.split(" "))


# Chuyển đối tượng được đánh giá (HDV/Tour/Công ty) sang chuỗi hiển thị thân thiện.
# Nếu có thể, hàm sẽ tra cứu thêm tên thật từ datastore để tránh chỉ hiện mã.
def format_review_target(datastore, review, include_code=False):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `format_review_target` (format review target).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        review: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        include_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    target = str(review.get("target", "") or review.get("doiTuong", "") or "Công ty").strip()
    target_id = str(review.get("target_id", "") or review.get("maHDV", "") or review.get("maTour", "")).strip()

    if target == "HDV":
        hdv = datastore.find_hdv(target_id) if target_id else None
        hdv_name = str(hdv.get("tenHDV", "")).strip() if hdv else ""
        if hdv_name and include_code and target_id:
            return f"HDV: {hdv_name} ({target_id})"
        if hdv_name:
            return f"HDV: {hdv_name}"
        return f"HDV: {target_id}" if target_id else "HDV"

    if target == "Tour":
        tour = datastore.find_tour(target_id) if target_id else None
        tour_name = str(tour.get("ten", "")).strip() if tour else ""
        if tour_name and include_code and target_id:
            return f"Tour: {tour_name} ({target_id})"
        if tour_name:
            return f"Tour: {tour_name}"
        return f"Tour: {target_id}" if target_id else "Tour"

    return target or "Công ty"

# Tạo một form có thể cuộn theo trục dọc.
# Rất hữu ích cho các cửa sổ nhập liệu dài như HDV, tour, booking, voucher.
def create_scrollable_form(parent, bg):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `create_scrollable_form` (create scrollable form).
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
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)

    v_scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    content = tk.Frame(canvas, bg=bg)
    win = canvas.create_window((0, 0), window=content, anchor="nw")

    def on_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_configure` (on configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_canvas_configure` (on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfig(win, width=event.width)

    content.bind("<Configure>", on_configure)
    canvas.bind("<Configure>", on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
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
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    parent.after(200, lambda: content.bind_all("<MouseWheel>", _on_mousewheel))
    return outer, content


# =========================
# DASHBOARD
# =========================
# Render tab Dashboard của admin.
# Tab này tổng hợp số liệu nhanh, tác vụ nhanh và các ghi chú điều hành dựa trên dữ liệu hiện tại.
def dashboard_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `dashboard_tab` (dashboard tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)
    ql = app["ql"]

    tk.Label(
        app["container"],
        text="HỆ THỐNG VIETNAM TRAVEL",
        font=("Times New Roman", 22, "bold"),
        bg=THEME["bg"],
        fg=THEME["text"],
    ).pack(anchor="w", pady=(0, 20))

    stats = tk.Frame(app["container"], bg=THEME["bg"])
    stats.pack(fill="x", pady=(0, 18))

    revenue = sum(safe_int(t.get("gia", 0)) * ql.get_occupied_seats(t["ma"]) for t in ql.list_tours)
    stat_items = [
        ("Doanh thu tạm tính", f"{revenue:,}đ".replace(",", "."), THEME["primary"]),
        ("Tổng tour", str(len(ql.list_tours)), THEME["warning"]),
        ("Tổng HDV", str(len(ql.list_hdv)), THEME["success"]),
        ("Tổng booking", str(len(ql.list_bookings)), THEME["danger"]),
    ]

    for title, value, color in stat_items:
        card = tk.Frame(stats, bg=THEME["surface"], bd=1, relief="solid")
        card.pack(side="left", expand=True, fill="both", padx=8)
        tk.Label(card, text=title, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 13, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
        tk.Label(card, text=value, bg=THEME["surface"], fg=color, font=("Times New Roman", 22, "bold")).pack(anchor="w", padx=16, pady=(0, 16))

    lower = tk.Frame(app["container"], bg=THEME["bg"])
    lower.pack(fill="both", expand=True)

    left = tk.LabelFrame(lower, text="Tác vụ quản trị nhanh", font=("Times New Roman", 14, "bold"), bg=THEME["surface"], bd=1, relief="solid", padx=15, pady=15)
    left.pack(side="left", fill="both", expand=True, padx=(0, 8))
    style_button(left, "Thêm HDV mới", THEME["success"], lambda: open_hdv_form(app)).pack(fill="x", pady=5)
    style_button(left, "Tạo tour mới", THEME["warning"], lambda: open_tour_form(app)).pack(fill="x", pady=5)
    style_button(left, "Tổng hợp theo tour", "#7c3aed", lambda: open_booking_summary_window(app)).pack(fill="x", pady=5)
    style_button(left, "Báo cáo doanh thu", "#0f766e", lambda: open_revenue_report_window(app)).pack(fill="x", pady=5)
    style_button(left, "Làm mới Dashboard", "#0ea5e9", lambda: dashboard_tab(app)).pack(fill="x", pady=5)

    right = tk.LabelFrame(lower, text="Ghi chú điều hành", font=("Times New Roman", 14, "bold"), bg=THEME["note_bg"], fg=THEME["note_fg"], bd=1, relief="solid", padx=15, pady=15)
    right.pack(side="left", fill="both", expand=True, padx=(8, 0))

    dynamic_notes = []

    for t in ql.list_tours:
        occupied = ql.get_occupied_seats(t["ma"])
        total = safe_int(t["khach"])

        if t["trangThai"] == "Đã chốt đoàn":
            dynamic_notes.append(f"• Tour {t['ten']} đã chốt danh sách khách.")
        elif occupied >= total and total > 0:
            dynamic_notes.append(f"• Tour {t['ten']} đã đủ khách.")
        else:
            dynamic_notes.append(f"• Tour {t['ten']} còn {max(total - occupied, 0)} chỗ trống.")
            if total > 0 and occupied < total / 2 and t["trangThai"] in ["Mở bán", "Giữ chỗ"]:
                dynamic_notes.append(f"• Tour {t['ten']} có nguy cơ hủy nếu không đủ khách (mới có {occupied} khách).")

    for t in ql.list_tours:
        if t.get("hdvPhuTrach"):
            hdv = ql.find_hdv(t["hdvPhuTrach"])
            if hdv:
                dynamic_notes.append(f"• HDV {hdv['tenHDV']} phụ trách tour {t['ten']} từ {t['ngay']}.")
        else:
            dynamic_notes.append(f"• Cần phân công HDV cho tour {t['ten']} ({t['ngay']}).")

    for h in ql.list_hdv:
        if h["trangThai"] == "Tạm nghỉ":
            dynamic_notes.append(f"• HDV {h['tenHDV']} hiện đang tạm nghỉ.")

    note_text = "\n".join(dynamic_notes[:7]) if dynamic_notes else "• Hiện không có ghi chú điều hành mới."

    tk.Label(
        right,
        text=note_text,
        justify="left",
        anchor="nw",
        bg=THEME["note_bg"],
        fg=THEME["note_fg"],
        font=("Times New Roman", 13),
        wraplength=480
    ).pack(anchor="w", fill="both", expand=True)

    set_status(app, "Đang ở Dashboard", THEME["primary"])


# =========================
# HDV MANAGEMENT
# =========================
# Kiểm tra dữ liệu đầu vào của hướng dẫn viên trước khi lưu.
# Bao gồm: bắt buộc trường, định dạng mã, độ dài tên/mật khẩu, trùng số điện thoại/email,
# phạm vi năm kinh nghiệm và ràng buộc giới tính.
def validate_hdv(app, form_data, old_ma=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_hdv` (validate hdv).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        form_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_ma: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    required = ["maHDV", "tenHDV", "sdt", "email", "kn", "gioiTinh", "khuVuc", "trangThai"]
    if old_ma is None:
        required.append("password")

    if not all(form_data.get(k, "").strip() for k in required):
        return False, "Vui lòng nhập đầy đủ thông tin HDV."

    if not re.fullmatch(r"HDV\d{2,}", form_data["maHDV"]):
        return False, "Mã HDV phải theo dạng HDV01, HDV02..."

    if len(form_data["tenHDV"].strip()) < 3:
        return False, "Tên HDV quá ngắn."
    if form_data.get("password") and len(form_data["password"].strip()) < 3:
        return False, "Mật khẩu quá ngắn."

    if not is_valid_phone(form_data["sdt"]):
        return False, "Số điện thoại không hợp lệ."
    if not is_valid_email(form_data["email"]):
        return False, "Email không hợp lệ."

    if not form_data["kn"].isdigit() or not (0 <= int(form_data["kn"]) <= 50):
        return False, "Kinh nghiệm phải là số từ 0 đến 50."

    if form_data.get("gioiTinh") not in {"Nam", "Nữ"}:
        return False, "Giới tính chỉ hỗ trợ Nam hoặc Nữ."

    for h in app["ql"].list_hdv:
        if h["maHDV"] == form_data["maHDV"] and form_data["maHDV"] != old_ma:
            return False, "Mã HDV đã tồn tại."
        if h["sdt"] == form_data["sdt"] and h["maHDV"] != old_ma:
            return False, "Số điện thoại đã tồn tại."
        if str(h["email"]).lower() == form_data["email"].lower() and h["maHDV"] != old_ma:
            return False, "Email đã tồn tại."

    return True, ""


# Nạp lại danh sách hướng dẫn viên lên Treeview.
# Nếu có từ khóa thì lọc theo mã, tên, khu vực hoặc trạng thái.
def refresh_hdv(app, keyword=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_hdv` (refresh hdv).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tree = app.get("tv_hdv")
    if not tree:
        return

    for item in tree.get_children():
        tree.delete(item)

    rows = app["ql"].list_hdv
    if keyword:
        kw = keyword.lower().strip()
        rows = [h for h in rows if kw in h["maHDV"].lower() or kw in h["tenHDV"].lower() or kw in h["khuVuc"].lower() or kw in h["trangThai"].lower()]

    for h in rows:
        tree.insert("", "end", values=(h["maHDV"], h["tenHDV"], h["sdt"], h["email"], h["kn"], h["khuVuc"], h["trangThai"]))
    apply_zebra(tree)
    set_status(app, f"Hiển thị {len(rows)} HDV", THEME["primary"])


# Mở form thêm mới / cập nhật hướng dẫn viên.
# Logic bên trong chỉ thay đổi dữ liệu khi bấm Lưu; trước đó dữ liệu chỉ nằm ở widget giao diện.
def open_hdv_form(app, data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_hdv_form` (open hdv form).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    top = tk.Toplevel(app["root"])
    top.title("Thông tin hướng dẫn viên")
    top.geometry("620x520")
    top.minsize(560, 420)
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()
    top.resizable(True, True)

    card = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(card, text="THÔNG TIN HƯỚNG DẪN VIÊN", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 18, "bold")).pack(pady=(14, 10))

    scroll_outer, form = create_scrollable_form(card, THEME["surface"])
    scroll_outer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    password_label = "Mật khẩu mới" if data else "Mật khẩu"
    fields = [
        ("Mã HDV", "maHDV", "entry"),
        ("Tên HDV", "tenHDV", "entry"),
        (password_label, "password", "entry"),
        ("Số điện thoại", "sdt", "entry"),
        ("Email", "email", "entry"),
        ("Kinh nghiệm (năm)", "kn", "entry"),
        ("Giới tính", "gioiTinh", "combo", ["Nam", "Nữ"]),
        ("Khu vực", "khuVuc", "combo", ["Miền Bắc", "Miền Trung", "Miền Nam"]),
        ("Trạng thái", "trangThai", "combo", HDV_STATUSES),
    ]

    widgets = {}
    for label, key, kind, *extra in fields:
        row = tk.Frame(form, bg=THEME["surface"])
        row.pack(fill="x", pady=7)
        tk.Label(row, text=label, width=16, anchor="w", bg=THEME["surface"], font=("Times New Roman", 13, "bold")).pack(side="left")

        if kind == "entry":
            w = tk.Entry(row, font=("Times New Roman", 13), relief="solid", bd=1, show="*" if key == "password" else "")
            w.pack(side="left", fill="x", expand=True, ipady=5)
        else:
            w = ttk.Combobox(row, font=("Times New Roman", 12), values=extra[0], state="readonly")
            w.pack(side="left", fill="x", expand=True, ipady=5)

        widgets[key] = w
        if data:
            if kind == "entry" and key != "password":
                widgets[key].insert(0, data.get(key, ""))
            elif kind != "entry":
                value = data.get(key, "")
                if key == "gioiTinh" and value not in {"Nam", "Nữ"}:
                    value = ""
                widgets[key].set(value)

    if data:
        widgets["maHDV"].config(state="disabled")

    def sync_hdv_name_case(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `sync_hdv_name_case` (sync hdv name case).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        name_widget = widgets.get("tenHDV")
        if not name_widget:
            return

        current_value = name_widget.get()
        normalized_value = normalize_name_case(current_value)
        if normalized_value == current_value:
            return

        cursor = name_widget.index(tk.INSERT)
        name_widget.delete(0, "end")
        name_widget.insert(0, normalized_value)
        name_widget.icursor(min(cursor, len(normalized_value)))

    widgets["tenHDV"].bind("<FocusOut>", sync_hdv_name_case)

    def save_hdv():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save_hdv` (save hdv).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        new_data = {}
        before_data = copy.deepcopy(data) if data else None
        for _, key, kind, *extra in fields:
            if data and key == "maHDV":
                new_data[key] = data["maHDV"]
            else:
                new_data[key] = widgets[key].get().strip()

        new_data["tenHDV"] = normalize_name_case(new_data.get("tenHDV", ""))

        raw_password = new_data.get("password", "")
        if data and not raw_password:
            new_data["password"] = data.get("password", "")

        ok, msg = validate_hdv(app, new_data, data["maHDV"] if data else None)
        if not ok:
            messagebox.showwarning("Thông báo", msg, parent=top)
            return

        if data and raw_password:
            new_data["password"] = prepare_password_for_storage(raw_password)
        if not data:
            new_data["password"] = prepare_password_for_storage(raw_password)

        if data:
            for field in ["total_reviews", "avg_rating", "skill_score", "attitude_score", "problem_solving_score"]:
                new_data[field] = data.get(field, 0)
            for i, h in enumerate(app["ql"].list_hdv):
                if h["maHDV"] == data["maHDV"]:
                    app["ql"].list_hdv[i] = new_data
                    break
        else:
            new_data.update({
                "total_reviews": 0,
                "avg_rating": 0,
                "skill_score": 0,
                "attitude_score": 0,
                "problem_solving_score": 0
            })
            app["ql"].list_hdv.append(new_data)

        app["ql"].save()
        if data:
            changed_fields = [field for field in collect_changed_fields(before_data, new_data) if field != "password"]
            if raw_password:
                changed_fields.append("password")
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="hdv",
                operation="update",
                target=new_data["maHDV"],
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="hdv",
                operation="create",
                target=new_data["maHDV"],
                detail=f"Tạo HDV {new_data.get('tenHDV', '')} | Khu vực: {new_data.get('khuVuc', '')} | Trạng thái: {new_data.get('trangThai', '')}",
            )
        top.destroy()
        refresh_hdv(app, app["search_hdv_var"].get())
        set_status(app, "Đã lưu HDV thành công", THEME["success"])

    btns = tk.Frame(card, bg=THEME["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))
    style_button(btns, "Lưu thông tin", THEME["success"], save_hdv).pack(side="left", fill="x", expand=True, padx=(0, 8))
    style_button(btns, "Hủy bỏ", THEME["danger"], top.destroy).pack(side="left", fill="x", expand=True)


# Lấy dòng HDV đang chọn và mở form chỉnh sửa cho bản ghi đó.
def edit_hdv(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_hdv` (edit hdv).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_hdv"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn hướng dẫn viên cần sửa.")
        return
    ma = app["tv_hdv"].item(sel[0])["values"][0]
    hdv = app["ql"].find_hdv(ma)
    if hdv:
        open_hdv_form(app, hdv)


# Xóa HDV được chọn sau khi kiểm tra ràng buộc.
# Không cho xóa nếu HDV vẫn đang được phân công cho tour.
def delete_hdv(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_hdv` (delete hdv).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_hdv"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn hướng dẫn viên cần xóa.")
        return
    ma = app["tv_hdv"].item(sel[0])["values"][0]

    if any(t.get("hdvPhuTrach") == ma for t in app["ql"].list_tours):
        messagebox.showwarning("Không thể xóa", "HDV này đang được phân công phụ trách tour. Hãy thay đổi HDV của tour đó trước.")
        return

    if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa HDV {ma}?"):
        app["ql"].data["hdv"] = [h for h in app["ql"].list_hdv if h["maHDV"] != ma]
        app["ql"].save()
        write_crud_log(
            datastore=app["ql"],
            actor=get_admin_actor(app),
            role="admin",
            entity="hdv",
            operation="delete",
            target=ma,
            detail="Xóa hồ sơ hướng dẫn viên",
        )
        refresh_hdv(app, app["search_hdv_var"].get())
        set_status(app, f"Đã xóa HDV {ma}", THEME["danger"])

# Mở cửa sổ xem chi tiết hướng dẫn viên theo kiểu chỉ đọc.
# Hiển thị cả hồ sơ, điểm đánh giá và các tour HDV đang/đã phụ trách.
def open_hdv_detail(app, ma_hdv):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_hdv_detail` (open hdv detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    hdv = app["ql"].find_hdv(ma_hdv)
    if not hdv:
        messagebox.showerror("Lỗi", "Không tìm thấy thông tin HDV.")
        return

    assigned_tours = [
        t for t in app["ql"].list_tours
        if t.get("hdvPhuTrach") == ma_hdv
    ]

    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }

    top = tk.Toplevel(app["root"])
    top.title(f"Chi tiết HDV - {ma_hdv}")
    top.geometry("860x620")
    top.minsize(860, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(
        content_shell,
        bg=PASTEL_DETAIL["bg"],
        highlightthickness=0,
        bd=0
    )
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)

    v_scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    outer = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=outer, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    outer.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
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
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    # ===== HEADER =====
    header = tk.Frame(outer, bg=PASTEL_DETAIL["surface"])
    header.pack(fill="x", padx=24, pady=(22, 14))

    tk.Label(
        header,
        text="CHI TIẾT HƯỚNG DẪN VIÊN",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 24, "bold")
    ).pack()

    tk.Label(
        header,
        text=hdv.get("tenHDV", ""),
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 20, "bold")
    ).pack(pady=(4, 6))

    tk.Label(
        header,
        text=f"Mã HDV: {hdv.get('maHDV', '')}",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack()

    def create_section(parent, title, bg_color):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `create_section` (create section).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        wrapper = tk.Frame(
            parent,
            bg=bg_color,
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        wrapper.pack(fill="x", padx=20, pady=(0, 14))

        tk.Label(
            wrapper,
            text=title,
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 15, "bold")
        ).pack(anchor="w", padx=16, pady=(12, 8))

        body = tk.Frame(wrapper, bg=bg_color)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return body

    def create_info_row(parent, label_text, value, bg_color, wraplength=320):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `create_info_row` (create info row).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            label_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            wraplength: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        row = tk.Frame(parent, bg=bg_color)
        row.pack(fill="x", pady=4)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=18,
            anchor="w",
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")

        tk.Label(
            row,
            text=value if str(value).strip() else "Chưa cập nhật",
            anchor="w",
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12),
            wraplength=wraplength,
            justify="left"
        ).pack(side="left", fill="x", expand=True)

    # ===== THÔNG TIN TỔNG QUAN =====
    info_body = create_section(outer, "Thông tin tổng quan", PASTEL_DETAIL["section_bg"])

    left = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
    left.pack(side="left", fill="both", expand=True, padx=(0, 18))

    right = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
    right.pack(side="left", fill="both", expand=True)

    avg_rating = float(hdv.get("avg_rating", 0) or 0)

    info_left = [
        ("Mã HDV", hdv.get("maHDV", "")),
        ("Tên HDV", hdv.get("tenHDV", "")),
        ("Giới tính", hdv.get("gioiTinh", "")),
        ("Ngày sinh", hdv.get("ngaySinh", "")),
        ("CCCD", hdv.get("cccd", "")),
        ("SĐT", hdv.get("sdt", "")),
        ("Email", hdv.get("email", "")),
        ("Địa chỉ", hdv.get("diaChi", "")),
    ]

    info_right = [
        ("Khu vực", hdv.get("khuVuc", "")),
        ("Ngoại ngữ", hdv.get("ngoaiNgu", "")),
        ("Chuyên môn", hdv.get("chuyenMon", "")),
        ("Chứng chỉ", hdv.get("chungChi", "")),
        ("Số tour đã dẫn", hdv.get("soTourDaDan", 0)),
        ("Trạng thái", hdv.get("trangThai", "")),
    ]

    for label_text, value in info_left:
        create_info_row(left, label_text, value, PASTEL_DETAIL["section_bg"], 300)

    for label_text, value in info_right:
        create_info_row(right, label_text, value, PASTEL_DETAIL["section_bg"], 320)

    # ===== ĐÁNH GIÁ & HIỆU SUẤT =====
    ops_body = create_section(outer, "Đánh giá & hiệu suất", PASTEL_DETAIL["section_bg_2"])

    ops_rows = [
        ("Kiến thức chuyên môn", f"{hdv.get('skill_score', 0)}%"),
        ("Thái độ phục vụ", f"{hdv.get('attitude_score', 0)}%"),
        ("Xử lý tình huống", f"{hdv.get('problem_solving_score', 0)}%"),
    ]

    for label_text, value in ops_rows:
        row = tk.Frame(ops_body, bg=PASTEL_DETAIL["section_bg_2"])
        row.pack(fill="x", pady=6)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=18,
            anchor="nw",
            bg=PASTEL_DETAIL["section_bg_2"],
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")

        tk.Label(
            row,
            text=value,
            anchor="w",
            bg=PASTEL_DETAIL["section_bg_2"],
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12),
            wraplength=760,
            justify="left"
        ).pack(side="left", fill="x", expand=True)

    # ===== CÁC TOUR ĐANG / ĐÃ PHỤ TRÁCH =====
    tours_body = create_section(outer, "Các tour hướng dẫn viên phụ trách", PASTEL_DETAIL["section_bg_3"])

    if assigned_tours:
        for idx, tour in enumerate(assigned_tours, 1):
            row = tk.Frame(tours_body, bg=PASTEL_DETAIL["section_bg_3"])
            row.pack(fill="x", pady=5)

            occupied = app["ql"].get_occupied_seats(tour["ma"])

            text = (
                f"{idx}. {tour.get('ten', '')} "
                f"({tour.get('ma', '')}) | "
                f"Khởi hành: {tour.get('ngay', '')} | "
                f"Trạng thái: {tour.get('trangThai', '')} | "
                f"Khách: {occupied}/{tour.get('khach', '')}"
            )

            tk.Label(
                row,
                text=text,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg_3"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12),
                wraplength=820,
                justify="left"
            ).pack(side="left", fill="x", expand=True)
    else:
        tk.Label(
            tours_body,
            text="Hiện tại HDV này chưa được phân công tour nào.",
            anchor="w",
            bg=PASTEL_DETAIL["section_bg_3"],
            fg=PASTEL_DETAIL["muted"],
            font=("Times New Roman", 12, "italic")
        ).pack(fill="x")

    tk.Frame(outer, bg=PASTEL_DETAIL["surface"], height=10).pack(fill="x")

    # ===== FOOTER =====
    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    footer_inner.pack(fill="x", padx=16, pady=10)

    style_button(
        footer_inner,
        "Cập nhật",
        THEME["primary"],
        lambda: [top.destroy(), open_hdv_form(app, hdv)]
    ).pack(side="left", padx=(0, 8))

    style_button(
        footer_inner,
        "Thoát",
        THEME["danger"],
        top.destroy
    ).pack(side="right")

    set_status(app, f"Đã mở chi tiết HDV {hdv['maHDV']}", THEME["primary"])

# Render tab quản lý hướng dẫn viên của admin.
def admin_hdv_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_hdv_tab` (admin hdv tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)

    tk.Label(
        app["container"],
        text="QUẢN LÝ NHÂN SỰ HƯỚNG DẪN VIÊN",
        font=("Times New Roman", 20, "bold"),
        bg=THEME["bg"],
        fg=THEME["text"]
    ).pack(anchor="w", pady=(0, 10))

    top = tk.Frame(app["container"], bg=THEME["bg"])
    top.pack(fill="x", pady=(0, 10))

    style_button(top, "Thêm HDV", THEME["success"], lambda: open_hdv_form(app)).pack(side="left", padx=(0, 8))
    style_button(top, "Cập nhật", THEME["primary"], lambda: edit_hdv(app)).pack(side="left", padx=(0, 8))
    style_button(
        top,
        "Xem chi tiết",
        THEME["warning"],
        lambda: open_hdv_detail(
            app,
            app["tv_hdv"].item(app["tv_hdv"].selection()[0])["values"][0]
        ) if app["tv_hdv"].selection() else messagebox.showwarning("Thông báo", "Vui lòng chọn HDV cần xem.")
    ).pack(side="left", padx=(0, 8))
    style_button(top, "Xóa", THEME["danger"], lambda: delete_hdv(app)).pack(side="left", padx=(0, 20))
    style_button(top, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 20))

    tk.Label(top, text="Tìm kiếm:", bg=THEME["bg"], font=("Times New Roman", 12, "bold")).pack(side="left")
    search_entry = tk.Entry(top, textvariable=app["search_hdv_var"], font=("Times New Roman", 12), relief="solid", bd=1)
    search_entry.pack(side="left", fill="x", expand=True, ipady=4)
    search_entry.bind("<Return>", lambda e: refresh_hdv(app, app["search_hdv_var"].get()))
    style_button(top, "Lọc", THEME["primary"], lambda: refresh_hdv(app, app["search_hdv_var"].get())).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="both", expand=True)
   

    cols = ("ma", "ten", "sdt", "email", "kn", "kv", "tt")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=14)
    app["tv_hdv"] = tv

    config = [
        ("ma", "Mã HDV", 90),
        ("ten", "Họ tên", 180),
        ("sdt", "SĐT", 120),
        ("email", "Email", 180),
        ("kn", "KN (Năm)", 80),
        ("kv", "Khu vực", 110),
        ("tt", "Trạng thái", 130),
    ]

    for c, t, w in config:
        tv.heading(c, text=t)
        tv.column(c, anchor="center", width=w)

    def on_double_click(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click` (on double click).
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
        open_hdv_detail(app, ma)

    tv.bind("<Double-1>", on_double_click)

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sy.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")

    refresh_hdv(app, app["search_hdv_var"].get())

# =========================
# USER MANAGEMENT
# =========================
# Nạp lại danh sách khách hàng lên bảng, có hỗ trợ lọc theo từ khóa.
def refresh_users(app, keyword=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_users` (refresh users).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tree = app.get("tv_users")
    if not tree:
        return

    for item in tree.get_children():
        tree.delete(item)

    rows = app["ql"].list_users
    if keyword:
        kw = keyword.lower().strip()
        rows = [
            u for u in rows
            if kw in u["username"].lower()
            or kw in u["fullname"].lower()
            or kw in str(u.get("sdt", "")).lower()
        ]

    for u in rows:
        tree.insert(
            "",
            "end",
            values=(u["username"], u["fullname"], u.get("sdt", ""), mask_password(u.get("password", ""))),
        )
    apply_zebra(tree)
    set_status(app, f"Hiển thị {len(rows)} khách hàng", THEME["primary"])

# Hàm dựng cửa sổ chi tiết dùng chung theo phong cách pastel.
# Các tab khác chỉ cần truyền tiêu đề, phụ đề và danh sách section là có thể tái sử dụng.
def create_detail_window(app, title_text, subtitle_text, sections):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `create_detail_window` (create detail window).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        title_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        subtitle_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        sections: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }

    top = tk.Toplevel(app["root"])
    top.title(subtitle_text)
    top.geometry("860x620")
    top.minsize(860, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(content_shell, bg=PASTEL_DETAIL["bg"], highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)

    v_scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    outer = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=outer, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    outer.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
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
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    header = tk.Frame(outer, bg=PASTEL_DETAIL["surface"])
    header.pack(fill="x", padx=24, pady=(22, 14))

    tk.Label(
        header,
        text=title_text,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 24, "bold")
    ).pack()

    tk.Label(
        header,
        text=subtitle_text,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 20, "bold")
    ).pack(pady=(4, 6))

    def create_section(parent, title, bg_color):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `create_section` (create section).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        wrapper = tk.Frame(
            parent,
            bg=bg_color,
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        wrapper.pack(fill="x", padx=20, pady=(0, 14))

        tk.Label(
            wrapper,
            text=title,
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 15, "bold")
        ).pack(anchor="w", padx=16, pady=(12, 8))

        body = tk.Frame(wrapper, bg=bg_color)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return body

    section_colors = [
        PASTEL_DETAIL["section_bg"],
        PASTEL_DETAIL["section_bg_2"],
        PASTEL_DETAIL["section_bg_3"],
    ]

    for idx, section in enumerate(sections):
        body = create_section(
            outer,
            section["title"],
            section_colors[idx % len(section_colors)]
        )
        bg_color = section_colors[idx % len(section_colors)]

        for label_text, value in section["rows"]:
            row = tk.Frame(body, bg=bg_color)
            row.pack(fill="x", pady=5)

            tk.Label(
                row,
                text=f"{label_text}:",
                width=18,
                anchor="nw",
                bg=bg_color,
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=str(value) if value is not None else "",
                anchor="w",
                justify="left",
                wraplength=720,
                bg=bg_color,
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12)
            ).pack(side="left", fill="x", expand=True)

    tk.Frame(outer, bg=PASTEL_DETAIL["surface"], height=10).pack(fill="x")

    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    footer_inner.pack(fill="x", padx=16, pady=10)

    style_button(footer_inner, "Thoát", THEME["danger"], top.destroy).pack(side="right")

# Mở cửa sổ xem chi tiết khách hàng và thống kê booking liên quan.
def open_user_detail(app, username):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_user_detail` (open user detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    user = app["ql"].find_user(username)
    if not user:
        messagebox.showerror("Lỗi", "Không tìm thấy khách hàng.")
        return

    user_bookings = [b for b in app["ql"].list_bookings if b.get("usernameDat") == username]
    total_bookings = len(user_bookings)
    total_people = sum(safe_int(b.get("soNguoi", 0)) for b in user_bookings)
    total_paid = sum(safe_int(b.get("daThanhToan", 0)) for b in user_bookings)

    booking_lines = []
    for i, b in enumerate(user_bookings[:10], 1):
        booking_lines.append(
            f"{i}. {b.get('maBooking', '')} | Tour: {b.get('maTour', '')} | "
            f"SL: {b.get('soNguoi', '')} | TT: {b.get('trangThai', '')}"
        )

    if not booking_lines:
        booking_lines = ["Khách hàng này chưa có booking nào."]

    sections = [
        {
            "title": "Thông tin tổng quan",
            "rows": [
                ("Tên đăng nhập", user.get("username", "")),
                ("Họ và tên", user.get("fullname", "")),
                ("Số điện thoại", user.get("sdt", "")),
                ("Mật khẩu", mask_password(user.get("password", ""))),
            ],
        },
        {
            "title": "Thống kê booking",
            "rows": [
                ("Số booking", total_bookings),
                ("Tổng số người đã đặt", total_people),
                ("Tổng tiền đã thanh toán", f"{total_paid:,} đ".replace(",", ".")),
            ],
        },
        {
            "title": "Danh sách booking liên quan",
            "rows": [
                ("Booking", "\n".join(booking_lines)),
            ],
        },
    ]

    create_detail_window(
        app,
        "CHI TIẾT KHÁCH HÀNG",
        f"{user.get('fullname', '')} ({user.get('username', '')})",
        sections
    )

    set_status(app, f"Đã mở chi tiết khách hàng {username}", THEME["primary"])


# Mở form thêm mới / chỉnh sửa khách hàng.
# Khi sửa, username bị khóa để tránh làm hỏng khóa liên kết dữ liệu.
def open_user_form(app, data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_user_form` (open user form).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    top = tk.Toplevel(app["root"])
    top.title("Thông tin Khách hàng")
    top.geometry("520x420")
    top.minsize(480, 360)
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()
    top.resizable(True, True)

    card = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(card, text="QUẢN LÝ KHÁCH HÀNG", bg=THEME["surface"], font=("Times New Roman", 16, "bold")).pack(pady=15)

    fields = [("Tên đăng nhập", "username"), ("Mật khẩu", "password"), ("Họ và tên", "fullname"), ("Số điện thoại", "sdt")]
    widgets = {}

    for label, key in fields:
        row = tk.Frame(card, bg=THEME["surface"])
        row.pack(fill="x", padx=20, pady=5)
        tk.Label(row, text=label, width=15, anchor="w", bg=THEME["surface"], font=("Times New Roman", 12)).pack(side="left")
        show_char = "*" if key == "password" else ""
        e = tk.Entry(row, font=("Times New Roman", 12), relief="solid", bd=1, show=show_char)
        e.pack(side="left", fill="x", expand=True, ipady=3)
        if data and key != "password":
            e.insert(0, data.get(key, ""))
        widgets[key] = e

    if data:
        widgets["username"].config(state="disabled")

    tk.Label(card, text="SĐT phải có 10 số và dùng đầu số di động Việt Nam hợp lệ, ví dụ: 032, 038, 070, 081, 090...", bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 10, "italic")).pack(anchor="w", padx=20, pady=(5, 0))
    tk.Label(card, text="Để trống mật khẩu nếu không muốn thay đổi.", bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 11, "italic")).pack(anchor="w", padx=20, pady=(3, 0))

    def save():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save` (save).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        before_user = copy.deepcopy(data) if data else None
        username = data["username"] if data else widgets["username"].get().strip()
        password = widgets["password"].get().strip()
        fullname = widgets["fullname"].get().strip()
        sdt = widgets["sdt"].get().strip()

        if not username or not fullname:
            return messagebox.showwarning("Lỗi", "Vui lòng nhập đủ các trường bắt buộc!", parent=top)

        if not is_valid_phone(sdt):
            return messagebox.showwarning(
                "Lỗi",
                "Số điện thoại phải có 10 số, bắt đầu bằng 0 và dùng đầu số di động Việt Nam hợp lệ.",
                parent=top
            )

        if data:
            for u in app["ql"].list_users:
                if u["username"] != username and u.get("sdt") == sdt:
                    return messagebox.showwarning("Lỗi", "Số điện thoại đã tồn tại!", parent=top)
            for i, u in enumerate(app["ql"].list_users):
                if u["username"] == username:
                    app["ql"].list_users[i]["fullname"] = fullname
                    app["ql"].list_users[i]["sdt"] = sdt
                    if password:
                        if len(password) < 3:
                            return messagebox.showwarning("Lỗi", "Mật khẩu phải có ít nhất 3 ký tự.", parent=top)
                        app["ql"].list_users[i]["password"] = prepare_password_for_storage(password)
                    break
        else:
            if not password or len(password) < 3:
                return messagebox.showwarning("Lỗi", "Mật khẩu phải có ít nhất 3 ký tự.", parent=top)
            if app["ql"].find_user(username):
                return messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại!", parent=top)
            if any(u.get("sdt") == sdt for u in app["ql"].list_users):
                return messagebox.showwarning("Lỗi", "Số điện thoại đã tồn tại!", parent=top)

            app["ql"].list_users.append({
                "username": username,
                "password": prepare_password_for_storage(password),
                "fullname": fullname,
                "sdt": sdt
            })

        app["ql"].save()
        if data:
            updated_user = app["ql"].find_user(username)
            changed_fields = [field for field in collect_changed_fields(before_user, updated_user) if field != "password"]
            if password:
                changed_fields.append("password")
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="user",
                operation="update",
                target=username,
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="user",
                operation="create",
                target=username,
                detail=f"Tạo khách hàng {fullname} | SĐT: {sdt}",
            )
        keyword = app["search_user_var"].get().strip() if app.get("search_user_var") else ""
        refresh_users(app, keyword)
        top.destroy()
        set_status(app, "Đã lưu khách hàng thành công", THEME["success"])

    style_button(card, "Lưu thông tin", THEME["success"], save).pack(pady=20)


# Mở form chỉnh sửa cho khách hàng đang được chọn trong bảng.
def edit_user(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_user` (edit user).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_users"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn khách hàng cần sửa.")
        return

    username = app["tv_users"].item(sel[0])["values"][0]
    user = app["ql"].find_user(username)
    if not user:
        messagebox.showerror("Lỗi", "Không tìm thấy thông tin khách hàng.")
        return

    open_user_form(app, user)


# Xóa khách hàng được chọn, sau đó lưu dữ liệu và ghi log thao tác.
def delete_user(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_user` (delete user).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_users"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn khách hàng cần xóa.")
        return
    username = app["tv_users"].item(sel[0])["values"][0]
    if messagebox.askyesno("Xác nhận", f"Xóa khách hàng {username}?"):
        app["ql"].data["users"] = [u for u in app["ql"].list_users if u["username"] != username]
        app["ql"].save()
        write_crud_log(
            datastore=app["ql"],
            actor=get_admin_actor(app),
            role="admin",
            entity="user",
            operation="delete",
            target=username,
            detail="Xóa khách hàng khỏi hệ thống",
        )
        keyword = app["search_user_var"].get().strip() if app.get("search_user_var") else ""
        refresh_users(app, keyword)
        set_status(app, f"Đã xóa khách hàng {username}", THEME["danger"])


# Render tab quản lý khách hàng của admin.
def admin_user_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_user_tab` (admin user tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)
    tk.Label(app["container"], text="QUẢN LÝ DANH SÁCH KHÁCH HÀNG", font=("Times New Roman", 20, "bold"), bg=THEME["bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=10)
    style_button(toolbar, "Thêm khách mới", THEME["success"], lambda: open_user_form(app)).pack(side="left", padx=5)
    style_button(toolbar, "Sửa thông tin", THEME["primary"], lambda: edit_user(app)).pack(side="left", padx=5)
    style_button(
        toolbar,
        "Xem chi tiết",
        THEME["warning"],
        lambda: open_user_detail(
            app,
            app["tv_users"].item(app["tv_users"].selection()[0])["values"][0]
        ) if app["tv_users"].selection() else messagebox.showwarning("Thông báo", "Vui lòng chọn khách hàng cần xem.")
    ).pack(side="left", padx=5)
    style_button(toolbar, "Xóa khách", THEME["danger"], lambda: delete_user(app)).pack(side="left", padx=5)
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 16))

    tk.Label(toolbar, text="Tìm kiếm:", bg=THEME["bg"], font=("Times New Roman", 12, "bold")).pack(side="left", padx=(16, 4))
    search_entry = tk.Entry(toolbar, textvariable=app["search_user_var"], font=("Times New Roman", 12), relief="solid", bd=1)
    search_entry.pack(side="left", fill="x", expand=True, ipady=4)
    search_entry.bind("<Return>", lambda e: refresh_users(app, app["search_user_var"].get()))
    style_button(toolbar, "Lọc", THEME["primary"], lambda: refresh_users(app, app["search_user_var"].get())).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="both", expand=True)

    cols = ("user", "name", "sdt", "pass")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings")
    app["tv_users"] = tv

    headers = [("user", "Tên đăng nhập"), ("name", "Họ và tên"), ("sdt", "Số điện thoại"), ("pass", "Mật khẩu")]
    for cid, txt in headers:
        tv.heading(cid, text=txt)
        tv.column(cid, anchor="center", width=150)

    tv.pack(side="left", fill="both", expand=True)
    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sy.set)
    sy.pack(side="right", fill="y")
    refresh_users(app, app["search_user_var"].get())

    def on_double_click_user(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click_user` (on double click user).
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
        username = tv.item(sel[0])["values"][0]
        open_user_detail(app, username)

    tv.bind("<Double-1>", on_double_click_user)

# =========================
# TOUR MANAGEMENT
# =========================
# Kiểm tra dữ liệu tour trước khi lưu.
# Bao gồm: định dạng mã tour, ngày đi/ngày về, sức chứa, giá, điểm đi/đến,
# chi phí, HDV tồn tại hay không và xung đột lịch HDV.
def validate_tour(app, form_data, old_ma=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_tour` (validate tour).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        form_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_ma: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    required = ["ma", "ten", "ngay", "ngayKetThuc", "soNgay", "khach", "gia", "diemDi", "diemDen", "trangThai", "hdvPhuTrach"]

    if not all(form_data.get(k, "").strip() for k in required):
        return False, "Vui lòng nhập đầy đủ thông tin tour."

    if not re.fullmatch(r"T\d{2,}", form_data["ma"]):
        return False, "Mã tour phải theo dạng T01, T02..."

    if len(form_data["ten"].strip()) < 5:
        return False, "Tên tour quá ngắn."

    if not is_valid_date(form_data["ngay"]) or not is_valid_date(form_data["ngayKetThuc"]):
        return False, "Ngày khởi hành / kết thúc không đúng định dạng dd/mm/yyyy."

    try:
        ngay_di = datetime.strptime(form_data["ngay"], "%d/%m/%Y")
        ngay_ve = datetime.strptime(form_data["ngayKetThuc"], "%d/%m/%Y")
        if ngay_ve < ngay_di:
            return False, "Ngày kết thúc không được nhỏ hơn ngày khởi hành."
    except ValueError:
        return False, "Ngày tour không hợp lệ."

    if not form_data["khach"].isdigit() or not (1 <= int(form_data["khach"]) <= 500):
        return False, "Sức chứa tối đa phải từ 1 đến 500 khách."

    if not form_data["gia"].isdigit() or int(form_data["gia"]) <= 0:
        return False, "Giá tour phải là số dương."

    if form_data["diemDi"].strip().lower() == form_data["diemDen"].strip().lower():
        return False, "Điểm đi và điểm đến không được trùng nhau."

    chi_phi_du_kien = str(form_data.get("chiPhiDuKien", "")).strip()
    if chi_phi_du_kien and (not chi_phi_du_kien.isdigit() or int(chi_phi_du_kien) < 0):
        return False, "Chi phí dự kiến phải là số >= 0."

    chi_phi_thuc_te = str(form_data.get("chiPhiThucTe", "")).strip()
    if chi_phi_thuc_te and (not chi_phi_thuc_te.isdigit() or int(chi_phi_thuc_te) < 0):
        return False, "Chi phí thực tế phải là số >= 0."

    hdv = app["ql"].find_hdv(form_data["hdvPhuTrach"])
    if not hdv:
        return False, "Hướng dẫn viên phụ trách không tồn tại."
    if hdv.get("trangThai") == "Tạm nghỉ":
        return False, "Không thể phân công HDV đang ở trạng thái tạm nghỉ."

    for t in app["ql"].list_tours:
        if t.get("ma") == old_ma:
            continue
        if str(t.get("hdvPhuTrach", "")).strip() != str(form_data["hdvPhuTrach"]).strip():
            continue
        if str(t.get("trangThai", "")).strip() in ["Hoàn tất", "Đã hủy", "Tạm hoãn"]:
            continue

        other_start = parse_ddmmyyyy(t.get("ngay"))
        other_end = parse_ddmmyyyy(t.get("ngayKetThuc")) or other_start
        if not other_start or not other_end:
            continue

        if max(ngay_di, other_start) <= min(ngay_ve, other_end):
            return False, f"HDV {form_data['hdvPhuTrach']} đã có tour {t.get('ma', '')} bị trùng lịch trong khoảng thời gian này."

    for t in app["ql"].list_tours:
        if t["ma"] == form_data["ma"] and t["ma"] != old_ma:
            return False, "Mã tour đã tồn tại."

    existing_booked = app["ql"].get_occupied_seats(old_ma or form_data["ma"])
    if int(form_data["khach"]) < existing_booked:
        return False, f"Không thể giảm sức chứa vì đã có {existing_booked} chỗ được đặt."

    return True, ""


# Nạp lại bảng tour; đồng thời tính số chỗ đã đặt / tổng sức chứa để hiển thị.
def refresh_tours(app, keyword=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_tours` (refresh tours).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tree = app.get("tv_tour")
    if not tree:
        return

    for item in tree.get_children():
        tree.delete(item)

    rows = app["ql"].list_tours
    if keyword:
        kw = keyword.lower().strip()
        rows = [t for t in rows if kw in t["ma"].lower() or kw in t["ten"].lower() or kw in t["diemDen"].lower() or kw in t["trangThai"].lower()]

    for t in rows:
        booked = app["ql"].get_occupied_seats(t["ma"])
        tree.insert("", "end", values=(
            t["ma"], t["ten"], t["ngay"], f"{booked}/{t['khach']}",
            f"{safe_int(t['gia']):,}".replace(",", "."),
            t.get("hdvPhuTrach", ""), t["trangThai"]
        ))
    apply_zebra(tree)
    set_status(app, f"Hiển thị {len(rows)} tour", THEME["primary"])


# Mở form thêm mới / chỉnh sửa tour.
# Khi lưu, hàm còn cập nhật trạng thái HDV phụ trách tương ứng với trạng thái tour.
def open_tour_form(app, data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_tour_form` (open tour form).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    top = tk.Toplevel(app["root"])
    top.title("Thông tin tour du lịch")
    top.geometry("760x560")
    top.minsize(680, 460)
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()
    top.resizable(True, True)

    card = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(card, text="THÔNG TIN CHI TIẾT TOUR", bg=THEME["surface"], fg=THEME["text"], font=("Times New Roman", 18, "bold")).pack(pady=(14, 10))

    scroll_outer, form = create_scrollable_form(card, THEME["surface"])
    scroll_outer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    hdv_codes = [h["maHDV"] for h in app["ql"].list_hdv]

    fields = [
        ("Mã tour", "ma", "entry"),
        ("Tên tour", "ten", "entry"),
        ("Ngày khởi hành", "ngay", "entry"),
        ("Ngày kết thúc", "ngayKetThuc", "entry"),
        ("Số ngày", "soNgay", "entry"),
        ("Sức chứa tối đa", "khach", "entry"),
        ("Giá tour (VNĐ)", "gia", "entry"),
        ("Điểm xuất phát", "diemDi", "entry"),
        ("Điểm đến", "diemDen", "entry"),
        ("Chi phí dự kiến", "chiPhiDuKien", "entry"),
        ("Chi phí thực tế", "chiPhiThucTe", "entry"),
        ("Ghi chú điều hành", "ghiChuDieuHanh", "entry"),
        ("Trạng thái", "trangThai", "combo", TOUR_STATUSES),
        ("HDV phụ trách", "hdvPhuTrach", "combo", hdv_codes),
    ]

    widgets = {}
    for label, key, kind, *extra in fields:
        row = tk.Frame(form, bg=THEME["surface"])
        row.pack(fill="x", pady=7)
        tk.Label(row, text=label, width=16, anchor="w", bg=THEME["surface"], font=("Times New Roman", 13, "bold")).pack(side="left")

        if kind == "entry":
            w = tk.Entry(row, font=("Times New Roman", 13), relief="solid", bd=1)
            w.pack(side="left", fill="x", expand=True, ipady=5)
        else:
            w = ttk.Combobox(row, font=("Times New Roman", 12), values=extra[0], state="readonly")
            w.pack(side="left", fill="x", expand=True, ipady=5)

        widgets[key] = w
        if data:
            val = data.get(key, "")
            if kind == "entry":
                w.insert(0, str(val))
            else:
                w.set(val)

    if data:
        widgets["ma"].config(state="disabled")

    def save_tour():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save_tour` (save tour).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        before_tour = copy.deepcopy(data) if data else None
        form_data = {}
        for _, key, kind, *extra in fields:
            if data and key == "ma":
                form_data[key] = data["ma"]
            else:
                form_data[key] = widgets[key].get().strip()

        if form_data["trangThai"] == "Đã hủy" and (not data or data["trangThai"] != "Đã hủy"):
            booked = app["ql"].get_occupied_seats(form_data["ma"])
            if booked > 0:
                if not messagebox.askyesno("Xác nhận hủy", f"Tour '{form_data['ten']}' hiện đang có {booked} khách đặt chỗ.\nBạn vẫn chắc chắn muốn hủy tour?"):
                    return

        ok, msg = validate_tour(app, form_data, data["ma"] if data else None)
        if not ok:
            messagebox.showwarning("Thông báo", msg, parent=top)
            return

        if data:
            for i, t in enumerate(app["ql"].list_tours):
                if t["ma"] == data["ma"]:
                    app["ql"].list_tours[i] = form_data
                    break
        else:
            app["ql"].list_tours.append(form_data)

        hdv = app["ql"].find_hdv(form_data["hdvPhuTrach"])
        if hdv:
            if form_data["trangThai"] in ["Giữ chỗ", "Mở bán", "Đã chốt đoàn", "Chờ khởi hành", "Đang đi"]:
                hdv["trangThai"] = "Đã phân công" if form_data["trangThai"] in ["Giữ chỗ", "Mở bán", "Đã chốt đoàn", "Chờ khởi hành"] else "Đang dẫn tour"

        app["ql"].save()
        if data:
            changed_fields = collect_changed_fields(before_tour, form_data)
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="tour",
                operation="update",
                target=form_data["ma"],
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="tour",
                operation="create",
                target=form_data["ma"],
                detail=f"Tạo tour {form_data.get('ten', '')} | Ngày đi: {form_data.get('ngay', '')} | HDV: {form_data.get('hdvPhuTrach', '')}",
            )
        top.destroy()
        refresh_tours(app, app["search_tour_var"].get())
        set_status(app, "Đã lưu thông tin tour thành công", THEME["success"])

    btns = tk.Frame(card, bg=THEME["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))
    style_button(btns, "Lưu tour", THEME["success"], save_tour).pack(side="left", fill="x", expand=True, padx=(0, 8))
    style_button(btns, "Hủy", THEME["danger"], top.destroy).pack(side="left", fill="x", expand=True)


# Mở form sửa tour đang chọn.
def edit_tour(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_tour` (edit tour).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_tour"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn tour cần sửa.")
        return
    ma = app["tv_tour"].item(sel[0])["values"][0]
    tour = app["ql"].find_tour(ma)
    if tour:
        open_tour_form(app, tour)


# Xóa tour nếu thỏa điều kiện nghiệp vụ.
# Không cho xóa tour đang chạy hoặc tour còn booking hiệu lực.
def delete_tour(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_tour` (delete tour).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_tour"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn tour cần xóa.")
        return
    ma = app["tv_tour"].item(sel[0])["values"][0]

    tour = app["ql"].find_tour(ma)
    if not tour:
        return

    if tour.get("trangThai") in ["Đã chốt đoàn", "Chờ khởi hành", "Đang đi"]:
        messagebox.showwarning("Không thể xóa", f"Tour '{tour['ten']}' hiện đang ở trạng thái '{tour['trangThai']}'.")
        return

    active_bookings = [b for b in app["ql"].get_bookings_by_tour(ma) if b.get("trangThai") not in ["Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]]
    if active_bookings:
        messagebox.showwarning("Không thể xóa", "Tour này đã có booking đang hiệu lực. Vui lòng xử lý booking trước.")
        return

    if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa tour {ma}?"):
        app["ql"].data["tours"] = [t for t in app["ql"].list_tours if t["ma"] != ma]
        app["ql"].save()
        write_crud_log(
            datastore=app["ql"],
            actor=get_admin_actor(app),
            role="admin",
            entity="tour",
            operation="delete",
            target=ma,
            detail=f"Xóa tour {tour.get('ten', '')}",
        )
        refresh_tours(app, app["search_tour_var"].get())
        set_status(app, f"Đã xóa tour {ma}", THEME["danger"])


# Render tab quản lý tour và khai báo thêm cửa sổ xem chi tiết tour bên trong tab này.
def admin_tour_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_tour_tab` (admin tour tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)

    tk.Label(app["container"], text="QUẢN LÝ DANH SÁCH TOUR DU LỊCH", font=("Times New Roman", 20, "bold"), bg=THEME["bg"], fg=THEME["text"]).pack(anchor="w", pady=(0, 10))

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))
    style_button(toolbar, "Thêm tour mới", THEME["success"], lambda: open_tour_form(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Cập nhật", THEME["primary"], lambda: edit_tour(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Xem chi tiết",THEME["warning"],lambda: open_tour_detail_window(app, app["tv_tour"].item(app["tv_tour"].selection()[0])["values"][0]) if app["tv_tour"].selection() else messagebox.showwarning("Thông báo", "Vui lòng chọn tour cần xem.") ).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Xóa tour", THEME["danger"], lambda: delete_tour(app)).pack(side="left", padx=(0, 20))
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 20))

    tk.Label(toolbar, text="Tìm kiếm:", bg=THEME["bg"], font=("Times New Roman", 12, "bold")).pack(side="left")
    search_entry = tk.Entry(toolbar, textvariable=app["search_tour_var"], font=("Times New Roman", 12), relief="solid", bd=1)
    search_entry.pack(side="left", fill="x", expand=True, ipady=4)
    search_entry.bind("<Return>", lambda e: refresh_tours(app, app["search_tour_var"].get()))
    style_button(toolbar, "Lọc", THEME["primary"], lambda: refresh_tours(app, app["search_tour_var"].get())).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="both", expand=True)

    cols = ("ma", "ten", "ngay", "khach", "gia", "hdv", "tt")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=10)
    app["tv_tour"] = tv

    cfg = [
        ("ma", "Mã Tour", 80),
        ("ten", "Tên tour du lịch", 240),
        ("ngay", "Khởi hành", 110),
        ("khach", "Đã đặt/Tổng", 100),
        ("gia", "Giá tour", 110),
        ("hdv", "Mã HDV", 90),
        ("tt", "Trạng thái", 130),
    ]
    for c, t, w in cfg:
        tv.heading(c, text=t)
        tv.column(c, anchor="center", width=w)

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sy.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")

   
    def open_tour_detail_window(app, ma_tour):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `open_tour_detail_window` (open tour detail window).
        Tham số:
            app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        tour = app["ql"].find_tour(ma_tour)
        if not tour:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin tour.")
            return

        hdv = app["ql"].find_hdv(tour.get("hdvPhuTrach", ""))
        guest_count = app["ql"].get_occupied_seats(ma_tour)

        PASTEL_DETAIL = {
            "bg": "#edf6f9",
            "surface": "#ffffff",
            "title": "#1d3557",
            "muted": "#6c7a89",
            "border": "#cbd5e1",
            "section_bg": "#fff1e6",
            "section_bg_2": "#e8f6f0",
            "section_bg_3": "#f3ecff",
            "text": "#1f2937",
        }

        dia_diem_tham_quan = tour.get("diaDiemThamQuan", [])
        if isinstance(dia_diem_tham_quan, str):
            dia_diem_tham_quan = [x.strip() for x in dia_diem_tham_quan.split(",") if x.strip()]
        if not dia_diem_tham_quan:
            dia_diem_tham_quan = [tour.get("diemDen", "Chưa cập nhật")]

        top = tk.Toplevel(app["root"])
        top.title(f"Chi tiết tour - {tour['ma']}")
        top.geometry("860x620")
        top.minsize(860, 620)
        top.configure(bg=PASTEL_DETAIL["bg"])
        top.transient(app["root"])
        top.grab_set()

        outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
        outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

        content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
        content_shell.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            content_shell,
            bg=PASTEL_DETAIL["bg"],
            highlightthickness=0,
            bd=0
        )
        v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        outer = tk.Frame(
            canvas,
            bg=PASTEL_DETAIL["surface"],
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        canvas_window = canvas.create_window((0, 0), window=outer, anchor="nw")

        def _on_frame_configure(event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
            Tham số:
                event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
            Tham số:
                event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            canvas.itemconfigure(canvas_window, width=event.width)

        outer.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
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
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except (tk.TclError, ValueError, AttributeError):
                pass

        def _bind_mousewheel(_event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
            Tham số:
                _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(_event=None):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
            Tham số:
                _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            canvas.unbind_all("<MouseWheel>")

        top.bind("<Enter>", _bind_mousewheel)
        top.bind("<Leave>", _unbind_mousewheel)

        # ===== HEADER =====
        header = tk.Frame(outer, bg=PASTEL_DETAIL["surface"])
        header.pack(fill="x", padx=24, pady=(22, 14))

        tk.Label(
            header,
            text="CHI TIẾT TOUR",
            bg=PASTEL_DETAIL["surface"],
            fg=PASTEL_DETAIL["title"],
            font=("Times New Roman", 24, "bold")
        ).pack()

        tk.Label(
            header,
            text=tour.get("ten", ""),
            bg=PASTEL_DETAIL["surface"],
            fg=PASTEL_DETAIL["title"],
            font=("Times New Roman", 20, "bold")
        ).pack(pady=(4, 6))

        tk.Label(
            header,
            text=f"Mã tour: {tour.get('ma', '')}",
            bg=PASTEL_DETAIL["surface"],
            fg=PASTEL_DETAIL["muted"],
            font=("Times New Roman", 11, "italic")
        ).pack()

        def create_section(parent, title, bg_color):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `create_section` (create section).
            Tham số:
                parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            wrapper = tk.Frame(
                parent,
                bg=bg_color,
                highlightbackground=PASTEL_DETAIL["border"],
                highlightthickness=1
            )
            wrapper.pack(fill="x", padx=20, pady=(0, 14))

            tk.Label(
                wrapper,
                text=title,
                bg=bg_color,
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 15, "bold")
            ).pack(anchor="w", padx=16, pady=(12, 8))

            body = tk.Frame(wrapper, bg=bg_color)
            body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
            return body

        # ===== THÔNG TIN TỔNG QUAN =====
        info_body = create_section(outer, "Thông tin tổng quan", PASTEL_DETAIL["section_bg"])

        left = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 18))

        right = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
        right.pack(side="left", fill="both", expand=True)

        info_left = [
            ("Tên tour", tour.get("ten", "")),
            ("Mã tour", tour.get("ma", "")),
            ("Ngày khởi hành", tour.get("ngay", "")),
            ("Ngày kết thúc", tour.get("ngayKetThuc", "")),
            ("Số ngày", tour.get("soNgay", "")),
            ("Trạng thái", tour.get("trangThai", "")),
        ]

        info_right = [
            ("Điểm đi", tour.get("diemDi", "")),
            ("Điểm đến", tour.get("diemDen", "")),
            ("Sức chứa", str(tour.get("khach", ""))),
            ("Đã đặt", str(guest_count)),
            ("Giá tour", f"{safe_int(tour.get('gia', 0)):,} đ".replace(",", ".")),
            ("HDV phụ trách", f"{tour.get('hdvPhuTrach', '')} - {hdv.get('tenHDV', '') if hdv else 'Chưa xác định'}"),
        ]

        for label_text, value in info_left:
            row = tk.Frame(left, bg=PASTEL_DETAIL["section_bg"])
            row.pack(fill="x", pady=4)

            tk.Label(
                row,
                text=f"{label_text}:",
                width=16,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=value,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12)
            ).pack(side="left", fill="x", expand=True)

        for label_text, value in info_right:
            row = tk.Frame(right, bg=PASTEL_DETAIL["section_bg"])
            row.pack(fill="x", pady=4)

            tk.Label(
                row,
                text=f"{label_text}:",
                width=16,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=value,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12),
                wraplength=320,
                justify="left"
            ).pack(side="left", fill="x", expand=True)

        # ===== ĐIỀU HÀNH & CHI PHÍ =====
        ops_body = create_section(outer, "Điều hành & chi phí", PASTEL_DETAIL["section_bg_2"])

        ops_rows = [
            ("Chi phí dự kiến", f"{safe_int(tour.get('chiPhiDuKien', 0)):,} đ".replace(",", ".")),
            ("Chi phí thực tế", f"{safe_int(tour.get('chiPhiThucTe', 0)):,} đ".replace(",", ".")),
            ("Ghi chú điều hành", tour.get("ghiChuDieuHanh", "") or "Không có"),
        ]

        for label_text, value in ops_rows:
            row = tk.Frame(ops_body, bg=PASTEL_DETAIL["section_bg_2"])
            row.pack(fill="x", pady=6)

            tk.Label(
                row,
                text=f"{label_text}:",
                width=16,
                anchor="nw",
                bg=PASTEL_DETAIL["section_bg_2"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=value,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg_2"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12),
                wraplength=760,
                justify="left"
            ).pack(side="left", fill="x", expand=True)

        # ===== CÁC ĐỊA ĐIỂM SẼ ĐI =====
        places_body = create_section(outer, "Các địa điểm sẽ đi trong tour", PASTEL_DETAIL["section_bg_3"])

        for idx, place in enumerate(dia_diem_tham_quan, 1):
            row = tk.Frame(places_body, bg=PASTEL_DETAIL["section_bg_3"])
            row.pack(fill="x", pady=5)

            tk.Label(
                row,
                text=f"{idx}.",
                width=4,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg_3"],
                fg=PASTEL_DETAIL["title"],
                font=("Times New Roman", 12, "bold")
            ).pack(side="left")

            tk.Label(
                row,
                text=place,
                anchor="w",
                bg=PASTEL_DETAIL["section_bg_3"],
                fg=PASTEL_DETAIL["text"],
                font=("Times New Roman", 12)
            ).pack(side="left", fill="x", expand=True)

        # khoảng trắng cuối nội dung
        tk.Frame(outer, bg=PASTEL_DETAIL["surface"], height=10).pack(fill="x")

        # ===== FOOTER =====
        footer = tk.Frame(
            top,
            bg=PASTEL_DETAIL["surface"],
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        footer.pack(side="bottom", fill="x", padx=14, pady=14)

        footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
        footer_inner.pack(fill="x", padx=16, pady=10)

        style_button(
            footer_inner,
            "Cập nhật",
            THEME["primary"],
            lambda: open_tour_form(app, tour)
        ).pack(side="left", padx=(0, 8))

        style_button(
            footer_inner,
            "Thoát",
            THEME["danger"],
            top.destroy
        ).pack(side="right")

        set_status(app, f"Đã mở chi tiết tour {tour['ma']}", THEME["primary"])


    def on_double_click(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click` (on double click).
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
        open_tour_detail_window(app, ma)

    tv.bind("<Double-1>", on_double_click)
    refresh_tours(app, app["search_tour_var"].get())

# =========================
# BOOKING MANAGEMENT
# =========================
# Mở cửa sổ xem chi tiết booking.
# Hiển thị đầy đủ thông tin khách, tour, thanh toán, hoàn tiền và danh sách khách đi cùng.
def open_booking_detail(app, ma_booking):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_booking_detail` (open booking detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = next((b for b in app["ql"].list_bookings if b.get("maBooking") == ma_booking), None)
    if not booking:
        messagebox.showerror("Lỗi", "Không tìm thấy booking.")
        return

    tour = app["ql"].find_tour(booking.get("maTour", ""))
    user = app["ql"].find_user(booking.get("usernameDat", "")) if booking.get("usernameDat") else None

    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }

    guest_list = booking.get("danhSachKhach", [])
    guest_lines = []
    for guest in guest_list:
        guest_lines.append(
            f"{guest.get('hoTen', '')} | {guest.get('gioiTinh', '')} | {guest.get('namSinh', '')}"
        )
    if not guest_lines:
        guest_lines = ["Chưa có danh sách khách chi tiết"]

    top = tk.Toplevel(app["root"])
    top.title(f"Chi tiết booking - {booking.get('maBooking', '')}")
    top.geometry("860x620")
    top.minsize(860, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(content_shell, bg=PASTEL_DETAIL["bg"], highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)

    v_scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    outer = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=outer, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    outer.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
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
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    header = tk.Frame(outer, bg=PASTEL_DETAIL["surface"])
    header.pack(fill="x", padx=24, pady=(22, 14))

    tk.Label(
        header,
        text="CHI TIẾT BOOKING",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 24, "bold")
    ).pack()

    tk.Label(
        header,
        text=f"{booking.get('maBooking', '')} - {booking.get('tenKhach', '')}",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 20, "bold")
    ).pack(pady=(4, 6))

    tk.Label(
        header,
        text=f"Tour liên quan: {booking.get('maTour', '')}",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack()

    def create_section(parent, title, bg_color):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `create_section` (create section).
        Tham số:
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            bg_color: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        wrapper = tk.Frame(
            parent,
            bg=bg_color,
            highlightbackground=PASTEL_DETAIL["border"],
            highlightthickness=1
        )
        wrapper.pack(fill="x", padx=20, pady=(0, 14))

        tk.Label(
            wrapper,
            text=title,
            bg=bg_color,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 15, "bold")
        ).pack(anchor="w", padx=16, pady=(12, 8))

        body = tk.Frame(wrapper, bg=bg_color)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return body

    # ===== THÔNG TIN BOOKING =====
    info_body = create_section(outer, "Thông tin booking", PASTEL_DETAIL["section_bg"])

    left = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
    left.pack(side="left", fill="both", expand=True, padx=(0, 18))

    right = tk.Frame(info_body, bg=PASTEL_DETAIL["section_bg"])
    right.pack(side="left", fill="both", expand=True)

    info_left = [
        ("Mã booking", booking.get("maBooking", "")),
        ("Mã tour", booking.get("maTour", "")),
        ("Tên khách", booking.get("tenKhach", "")),
        ("Số điện thoại", booking.get("sdt", "")),
        ("Số người", booking.get("soNguoi", "")),
        ("Trạng thái", booking.get("trangThai", "")),
    ]

    info_right = [
        ("Ngày đặt", booking.get("ngayDat", "")),
        ("Username đặt", booking.get("usernameDat", "")),
        ("Khách hàng hệ thống", user.get("fullname", "") if user else "Không liên kết"),
        ("Tour", f"{tour.get('ma', '')} - {tour.get('ten', '')}" if tour else "Không tìm thấy"),
        ("Điểm đến", tour.get("diemDen", "") if tour else ""),
        ("HDV phụ trách", tour.get("hdvPhuTrach", "") if tour else ""),
    ]

    for label_text, value in info_left:
        row = tk.Frame(left, bg=PASTEL_DETAIL["section_bg"])
        row.pack(fill="x", pady=4)
        tk.Label(
            row, text=f"{label_text}:", width=16, anchor="w",
            bg=PASTEL_DETAIL["section_bg"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")
        tk.Label(
            row, text=value, anchor="w",
            bg=PASTEL_DETAIL["section_bg"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True)

    for label_text, value in info_right:
        row = tk.Frame(right, bg=PASTEL_DETAIL["section_bg"])
        row.pack(fill="x", pady=4)
        tk.Label(
            row, text=f"{label_text}:", width=16, anchor="w",
            bg=PASTEL_DETAIL["section_bg"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")
        tk.Label(
            row, text=value, anchor="w",
            bg=PASTEL_DETAIL["section_bg"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12), wraplength=320, justify="left"
        ).pack(side="left", fill="x", expand=True)

    # ===== THANH TOÁN =====
    payment_body = create_section(outer, "Thanh toán & ghi chú", PASTEL_DETAIL["section_bg_2"])

    age_breakdown = booking.get("coCauDoTuoi", {}) if isinstance(booking.get("coCauDoTuoi"), dict) else {}
    age_breakdown_text = (
        f"Trẻ em: {safe_int(age_breakdown.get('treEm', 0))} | "
        f"Trung niên: {safe_int(age_breakdown.get('trungNien', 0))} | "
        f"Người cao tuổi: {safe_int(age_breakdown.get('nguoiCaoTuoi', 0))}"
    )
    payment_rows = [
        ("Tổng gốc", format_currency(booking.get("tongTienGoc", 0))),
        ("Giảm đối tượng", format_currency(booking.get("giamGiaDoiTuong", 0))),
        ("Cơ cấu độ tuổi", age_breakdown_text),
        ("Mã voucher", booking.get("maVoucher", "") or "Không có"),
        ("Tên voucher", booking.get("tenVoucher", "") or "Không có"),
        ("Giảm voucher", format_currency(booking.get("giamGiaVoucher", 0))),
        ("Tổng tiền", f"{safe_int(booking.get('tongTien', 0)):,} đ".replace(",", ".")),
        ("Tiền cọc", f"{safe_int(booking.get('tienCoc', 0)):,} đ".replace(",", ".")),
        ("Đã thanh toán", f"{safe_int(booking.get('daThanhToan', 0)):,} đ".replace(",", ".")),
        ("Còn nợ", f"{safe_int(booking.get('conNo', 0)):,} đ".replace(",", ".")),
        ("Trạng thái hoàn", booking.get("trangThaiHoanTien", "") or "Không có"),
        ("Số tiền hoàn", f"{safe_int(booking.get('soTienHoan', 0)):,} đ".replace(",", ".")),
        ("Ngày yêu cầu hoàn", booking.get("ngayYeuCauHoanTien", "") or "Không có"),
        ("Ngày xử lý hoàn", booking.get("ngayXuLyHoanTien", "") or "Không có"),
        ("Người xử lý", booking.get("nguoiXuLyHoanTien", "") or "Không có"),
        ("Ghi chú hoàn tiền", booking.get("ghiChuHoanTien", "") or "Không có"),
        ("Hình thức thanh toán", booking.get("hinhThucThanhToan", "")),
        ("Nguồn khách", booking.get("nguonKhach", "")),
        ("Ghi chú", booking.get("ghiChu", "") or "Không có"),
    ]

    for label_text, value in payment_rows:
        row = tk.Frame(payment_body, bg=PASTEL_DETAIL["section_bg_2"])
        row.pack(fill="x", pady=6)
        tk.Label(
            row, text=f"{label_text}:", width=18, anchor="nw",
            bg=PASTEL_DETAIL["section_bg_2"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")
        tk.Label(
            row, text=value, anchor="w",
            bg=PASTEL_DETAIL["section_bg_2"], fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12), wraplength=760, justify="left"
        ).pack(side="left", fill="x", expand=True)

    # ===== DANH SÁCH KHÁCH =====
    guest_body = create_section(outer, "Danh sách khách đi cùng", PASTEL_DETAIL["section_bg_3"])

    for idx, line in enumerate(guest_lines, 1):
        row = tk.Frame(guest_body, bg=PASTEL_DETAIL["section_bg_3"])
        row.pack(fill="x", pady=5)

        tk.Label(
            row, text=f"{idx}.", width=4, anchor="w",
            bg=PASTEL_DETAIL["section_bg_3"], fg=PASTEL_DETAIL["title"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")

        tk.Label(
            row, text=line if "Chưa có" not in line else line,
            anchor="w", bg=PASTEL_DETAIL["section_bg_3"],
            fg=PASTEL_DETAIL["text"], font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True)

    tk.Frame(outer, bg=PASTEL_DETAIL["surface"], height=10).pack(fill="x")

    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    footer_inner.pack(fill="x", padx=16, pady=10)

    style_button(
        footer_inner,
        "Cập nhật",
        THEME["primary"],
        lambda: open_booking_form(app, booking)
    ).pack(side="left", padx=(0, 8))

    if booking.get("trangThai") == "Chờ hoàn tiền":
        style_button(
            footer_inner,
            "Duyệt hoàn",
            "#16a34a",
            lambda: [top.destroy(), handle_refund_decision(app, True, booking.get("maBooking", ""))]
        ).pack(side="left", padx=(0, 8))
        style_button(
            footer_inner,
            "Từ chối hoàn",
            "#dc2626",
            lambda: [top.destroy(), handle_refund_decision(app, False, booking.get("maBooking", ""))]
        ).pack(side="left", padx=(0, 8))

    style_button(
        footer_inner,
        "Thoát",
        THEME["danger"],
        top.destroy
    ).pack(side="right")

    set_status(app, f"Đã mở chi tiết booking {booking.get('maBooking', '')}", THEME["primary"])


# Trả về mã booking đang được chọn trong bảng; nếu chưa chọn thì trả về chuỗi rỗng.
def _selected_booking_code(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_selected_booking_code` ( selected booking code).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tree = app.get("tv_booking")
    if not tree:
        return ""
    selection = tree.selection()
    if not selection:
        return ""
    return str(tree.item(selection[0])["values"][0]).strip()


# Mở cửa sổ tổng hợp booking theo từng tour để admin theo dõi sức chứa và doanh thu nhanh.
def open_booking_summary_window(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_booking_summary_window` (open booking summary window).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    rows = summarize_bookings_by_tour(app["ql"])

    top = tk.Toplevel(app["root"])
    top.title("Tổng hợp booking theo tour")
    top.geometry("1080x520")
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()

    header = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    header.pack(fill="x", padx=18, pady=(16, 10))
    tk.Label(
        header,
        text="TỔNG HỢP BOOKING THEO TOUR",
        bg=THEME["surface"],
        fg=THEME["text"],
        font=("Times New Roman", 18, "bold"),
    ).pack(anchor="w", padx=16, pady=(12, 2))
    tk.Label(
        header,
        text=f"Số dòng: {len(rows)} | Cập nhật lúc {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}",
        bg=THEME["surface"],
        fg=THEME["muted"],
        font=("Times New Roman", 11, "italic"),
    ).pack(anchor="w", padx=16, pady=(0, 12))

    wrapper = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    cols = ("ma", "ten", "booking", "khachhang", "hieuluc", "trong", "refund", "doanhthu", "dathu")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=14)

    headers = [
        ("ma", "Mã tour", 90),
        ("ten", "Tên tour", 240),
        ("booking", "Số booking", 90),
        ("khachhang", "Khách hàng", 95),
        ("hieuluc", "Khách hiệu lực", 100),
        ("trong", "Chỗ còn", 90),
        ("refund", "Chờ hoàn", 90),
        ("doanhthu", "Doanh thu", 130),
        ("dathu", "Đã thu", 130),
    ]
    numeric_cols = {"booking", "khachhang", "hieuluc", "trong", "refund", "doanhthu", "dathu"}
    for column, title, width in headers:
        tv.heading(column, text=title)
        tv.column(column, anchor=("e" if column in numeric_cols else "center"), width=width)

    for row in rows:
        tv.insert(
            "",
            "end",
            values=(
                row["maTour"],
                row["tenTour"],
                row["tongBooking"],
                row["tongKhachHang"],
                row["khachHieuLuc"],
                row["choConLai"],
                row["choHoanTien"],
                format_currency(row["doanhThu"]),
                format_currency(row["daThu"]),
            ),
        )

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tv.xview)
    tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")
    sx.pack(side="bottom", fill="x")
    apply_zebra(tv)

# Mở báo cáo doanh thu đa góc nhìn: theo tour, theo tháng và theo quý.
def open_revenue_report_window(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_revenue_report_window` (open revenue report window).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    report = build_revenue_report(app["ql"])
    overview = report["overview"]

    top = tk.Toplevel(app["root"])
    top.title("Báo cáo doanh thu")
    top.geometry("860x620")
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()

    header = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    header.pack(fill="x", padx=18, pady=(16, 10))
    tk.Label(
        header,
        text="BÁO CÁO DOANH THU",
        bg=THEME["surface"],
        fg=THEME["text"],
        font=("Times New Roman", 18, "bold"),
    ).pack(anchor="w", padx=16, pady=(12, 2))
    tk.Label(
        header,
        text=f"Tóm tắt booking, doanh thu và công nợ theo nhiều góc nhìn | Cập nhật {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}",
        bg=THEME["surface"],
        fg=THEME["muted"],
        font=("Times New Roman", 11, "italic"),
    ).pack(anchor="w", padx=16, pady=(0, 12))

    stats = tk.Frame(top, bg=THEME["bg"])
    stats.pack(fill="x", padx=18, pady=(0, 10))
    stat_items = [
        ("Booking hiệu lực", str(overview["bookingHieuLuc"]), THEME["primary"]),
        ("Doanh thu dự kiến", format_currency(overview["doanhThuDuKien"]), THEME["success"]),
        ("Đã thu", format_currency(overview["daThu"]), THEME["warning"]),
        ("Còn nợ", format_currency(overview["conNo"]), THEME["danger"]),
        ("Chờ hoàn tiền", f"{overview['dangChoHoan']} booking", "#7c3aed"),
        ("Tiền chờ hoàn", format_currency(overview["soTienChoHoan"]), "#7c3aed"),
    ]
    for title, value, color in stat_items:
        card = tk.Frame(stats, bg=THEME["surface"], bd=1, relief="solid")
        card.pack(side="left", fill="both", expand=True, padx=6)
        tk.Frame(card, bg=color, height=3).pack(fill="x")
        tk.Label(card, text=title, bg=THEME["surface"], fg=THEME["muted"], font=("Times New Roman", 10, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(card, text=value, bg=THEME["surface"], fg=color, font=("Times New Roman", 15, "bold")).pack(anchor="w", padx=12, pady=(0, 10))

    style = ttk.Style(top)
    style.configure("Report.TNotebook", background=THEME["bg"], borderwidth=0)
    style.configure(
        "Report.TNotebook.Tab",
        padding=(16, 8),
        font=("Times New Roman", 11, "bold"),
        background=THEME["heading_bg"],
        foreground=THEME["text"],
    )
    style.map(
        "Report.TNotebook.Tab",
        background=[("selected", THEME["surface"])],
        foreground=[("selected", THEME["primary"])],
    )

    notebook = ttk.Notebook(top, style="Report.TNotebook")
    notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def build_report_tab(title, rows, columns):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `build_report_tab` (build report tab).
        Tham số:
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            rows: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            columns: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        frame = tk.Frame(notebook, bg=THEME["surface"])
        notebook.add(frame, text=title)

        tab_head = tk.Frame(frame, bg=THEME["surface"])
        tab_head.pack(fill="x", padx=10, pady=(10, 6))
        tk.Label(
            tab_head,
            text=f"Dữ liệu {title.lower()}",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=("Times New Roman", 13, "bold"),
        ).pack(side="left")
        tk.Label(
            tab_head,
            text=f"{len(rows)} dòng",
            bg=THEME["surface"],
            fg=THEME["muted"],
            font=("Times New Roman", 11, "italic"),
        ).pack(side="right")

        wrapper = tk.Frame(frame, bg=THEME["surface"], bd=1, relief="solid")
        wrapper.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tree = ttk.Treeview(wrapper, columns=[column[0] for column in columns], show="headings", height=16)
        numeric_keywords = ("booking", "nguoi", "doanhthu", "dathu", "conno")
        for column, text, width in columns:
            tree.heading(column, text=text)
            anchor = "e" if any(key in column for key in numeric_keywords) else "center"
            tree.column(column, anchor=anchor, width=width)

        for row in rows:
            tree.insert("", "end", values=row)

        if not rows:
            tree.insert("", "end", values=tuple("Không có dữ liệu" if i == 0 else "" for i in range(len(columns))))

        sy = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        sx = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        tree.pack(side="left", fill="both", expand=True)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        apply_zebra(tree)

    build_report_tab(
        "Theo tour",
        [
            (
                row["maTour"],
                row["tenTour"],
                row["tongBooking"],
                row["tongNguoi"],
                format_currency(row["doanhThuDuKien"]),
                format_currency(row["daThu"]),
                format_currency(row["conNo"]),
            )
            for row in report["by_tour"]
        ],
        [
            ("ma", "Mã tour", 90),
            ("ten", "Tên tour", 260),
            ("booking", "Booking", 90),
            ("nguoi", "Số người", 90),
            ("doanhthu", "Doanh thu", 140),
            ("dathu", "Đã thu", 140),
            ("conno", "Còn nợ", 140),
        ],
    )
    build_report_tab(
        "Theo tháng",
        [
            (
                row["ky"],
                row["tongBooking"],
                row["tongNguoi"],
                format_currency(row["doanhThuDuKien"]),
                format_currency(row["daThu"]),
                format_currency(row["conNo"]),
            )
            for row in report["by_month"]
        ],
        [
            ("ky", "Tháng", 120),
            ("booking", "Booking", 90),
            ("nguoi", "Số người", 90),
            ("doanhthu", "Doanh thu", 160),
            ("dathu", "Đã thu", 160),
            ("conno", "Còn nợ", 160),
        ],
    )
    build_report_tab(
        "Theo quý",
        [
            (
                row["ky"],
                row["tongBooking"],
                row["tongNguoi"],
                format_currency(row["doanhThuDuKien"]),
                format_currency(row["daThu"]),
                format_currency(row["conNo"]),
            )
            for row in report["by_quarter"]
        ],
        [
            ("ky", "Quý", 120),
            ("booking", "Booking", 90),
            ("nguoi", "Số người", 90),
            ("doanhthu", "Doanh thu", 160),
            ("dathu", "Đã thu", 160),
            ("conno", "Còn nợ", 160),
        ],
    )

# Xử lý thao tác duyệt hoàn / từ chối hoàn tiền cho booking.
# Hàm này chỉ điều phối giao diện, còn nghiệp vụ chính được ủy quyền cho service ở core.booking_service.
def handle_refund_decision(app, approve=True, ma_booking=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `handle_refund_decision` (handle refund decision).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        approve: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    ma_booking = ma_booking or _selected_booking_code(app)
    if not ma_booking:
        messagebox.showwarning("Thông báo", "Vui lòng chọn booking cần xử lý hoàn tiền.")
        return

    prompt = "Ghi chú xử lý hoàn tiền (có thể để trống):" if approve else "Lý do từ chối hoàn tiền:"
    note = simpledialog.askstring("Xử lý hoàn tiền", prompt, parent=app["root"])
    if note is None and not approve:
        return

    action_label = "duyệt" if approve else "từ chối"
    if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn {action_label} hoàn tiền cho booking {ma_booking}?"):
        return

    if approve:
        result = service_approve_refund(app["ql"], ma_booking, actor=get_admin_actor(app), note=note or "")
    else:
        result = service_reject_refund(app["ql"], ma_booking, actor=get_admin_actor(app), note=note or "")

    if not result.success:
        messagebox.showwarning("Không thể xử lý", result.message)
        return

    refresh_bookings(app, app["search_booking_var"].get())
    if app.get("tv_tour"):
        refresh_tours(app, app["search_tour_var"].get())
    set_status(app, result.message, THEME["success"] if approve else THEME["warning"])
    messagebox.showinfo("Thành công", result.message)

# Kiểm tra dữ liệu booking trước khi lưu.
# Ràng buộc chính: mã booking, tour tồn tại, username đặt hợp lệ, đủ chỗ trống,
# và không cho đặt vào tour đã hủy / tạm hoãn / hoàn tất.
def validate_booking(app, form_data, old_ma=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_booking` (validate booking).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        form_data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_ma: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    required = ["maBooking", "maTour", "tenKhach", "sdt", "soNguoi", "trangThai"]

    if not all(str(form_data.get(k, "")).strip() for k in required):
        return False, "Vui lòng nhập đầy đủ thông tin booking."

    if not re.fullmatch(r"BK\d{2,}", str(form_data["maBooking"]).strip()):
        return False, "Mã booking phải theo dạng BK01, BK02..."

    if len(str(form_data["tenKhach"]).strip()) < 3:
        return False, "Tên khách hàng quá ngắn."

    if not is_valid_phone(form_data["sdt"]):
        return False, "Số điện thoại khách hàng không hợp lệ."

    if not str(form_data["soNguoi"]).isdigit() or int(form_data["soNguoi"]) <= 0:
        return False, "Số người đi phải là số nguyên dương."

    tour = app["ql"].find_tour(form_data["maTour"])
    if not tour:
        return False, "Tour được chọn không tồn tại."

    username_dat = str(form_data.get("usernameDat", "")).strip()
    if username_dat:
        linked_user = app["ql"].find_user(username_dat) or next(
            (
                u for u in app["ql"].list_users
                if str(u.get("username", "")).strip().lower() == username_dat.lower()
            ),
            None,
        )
        if not linked_user:
            return False, "Username đặt không tồn tại trong hệ thống."

    for b in app["ql"].list_bookings:
        if b.get("maBooking") == form_data["maBooking"] and b.get("maBooking") != old_ma:
            return False, "Mã booking này đã tồn tại."

    occupied = app["ql"].get_occupied_seats(form_data["maTour"])
    old_people = 0

    if old_ma:
        old_booking = next(
            (b for b in app["ql"].list_bookings if b.get("maBooking") == old_ma),
            None
        )
        if (
            old_booking
            and old_booking.get("maTour") == form_data["maTour"]
            and old_booking.get("trangThai") not in ["Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]
        ):
            old_people = safe_int(old_booking.get("soNguoi", 0))

    if form_data["trangThai"] not in ["Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]:
        if occupied - old_people + int(form_data["soNguoi"]) > int(tour["khach"]):
            return False, f"Tour này không đủ chỗ cho {form_data['soNguoi']} người."

    if tour.get("trangThai") in ["Hoàn tất", "Tạm hoãn", "Đã hủy"] and form_data["trangThai"] not in ["Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"]:
        return False, f"Không thể đặt chỗ cho tour đang ở trạng thái '{tour.get('trangThai')}'."

    return True, ""


# Nạp lại danh sách booking lên Treeview, có hỗ trợ lọc theo mã/tên/trạng thái/hoàn tiền.
def refresh_bookings(app, keyword=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_bookings` (refresh bookings).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tree = app.get("tv_booking")
    if not tree:
        return

    for item in tree.get_children():
        tree.delete(item)

    rows = app["ql"].list_bookings
    if keyword:
        kw = keyword.lower().strip()
        rows = [
            b for b in rows
            if kw in str(b.get("maBooking", "")).lower()
            or kw in str(b.get("tenKhach", "")).lower()
            or kw in str(b.get("maTour", "")).lower()
            or kw in str(b.get("trangThai", "")).lower()
            or kw in str(b.get("trangThaiHoanTien", "")).lower()
        ]

    for b in rows:
        tree.insert(
            "",
            "end",
            values=(
                b.get("maBooking", ""),
                b.get("maTour", ""),
                b.get("tenKhach", ""),
                b.get("sdt", ""),
                b.get("soNguoi", ""),
                b.get("trangThai", ""),
                b.get("trangThaiHoanTien", "") or "-",
            )
        )

    apply_zebra(tree)
    set_status(app, f"Hiển thị {len(rows)} booking", THEME["primary"])

# Mở form thêm mới / chỉnh sửa booking.
# Đây là form có logic phụ trợ khá nhiều: tự tính tổng tiền, tiền cọc, còn nợ,
# chuẩn hóa cơ cấu độ tuổi và suy ra trạng thái thanh toán.
def open_booking_form(app, data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_booking_form` (open booking form).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    top = tk.Toplevel(app["root"])
    top.title("Thông tin đặt chỗ (Booking)")
    top.geometry("760x680")
    top.minsize(680, 520)
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()
    top.resizable(True, True)

    card = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(
        card,
        text="THÔNG TIN ĐẶT CHỖ",
        bg=THEME["surface"],
        font=("Times New Roman", 18, "bold")
    ).pack(pady=(14, 10))

    scroll_outer, form = create_scrollable_form(card, THEME["surface"])
    scroll_outer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    tour_codes = [t["ma"] for t in app["ql"].list_tours]

    fields = [
        ("Mã booking", "maBooking", "entry"),
        ("Mã tour", "maTour", "combo", tour_codes),
        ("Tên khách hàng", "tenKhach", "entry"),
        ("Số điện thoại", "sdt", "entry"),
        ("Số người đi", "soNguoi", "entry"),
        ("Trẻ em (<12)", "treEm", "entry"),
        ("Trung niên", "trungNien", "entry"),
        ("Người cao tuổi (>65)", "nguoiCaoTuoi", "entry"),
        ("Tổng tiền", "tongTien", "entry"),
        ("Tiền cọc", "tienCoc", "entry"),
        ("Đã thanh toán", "daThanhToan", "entry"),
        ("Còn nợ", "conNo", "entry"),
        ("Hình thức thanh toán", "hinhThucThanhToan", "combo", ["Chưa thanh toán", "Tiền mặt", "Chuyển khoản", "Thẻ", "Momo", "ZaloPay", "VNPay"]),
        ("Nguồn khách", "nguonKhach", "combo", ["Khách lẻ", "Khách đoàn", "Khách quen", "Facebook", "Fanpage", "Zalo", "Website", "Tiktok", "Đại lý"]),
        ("Username đặt", "usernameDat", "entry"),
        ("Ghi chú", "ghiChu", "entry"),
        ("Trạng thái", "trangThai", "combo", BOOKING_STATUSES),
    ]

    widgets = {}
    for label, key, kind, *extra in fields:
        row = tk.Frame(form, bg=THEME["surface"])
        row.pack(fill="x", pady=7)

        tk.Label(
            row,
            text=label,
            width=18,
            anchor="w",
            bg=THEME["surface"],
            font=("Times New Roman", 13, "bold")
        ).pack(side="left")

        if kind == "entry":
            w = tk.Entry(row, font=("Times New Roman", 13), relief="solid", bd=1)
            w.pack(side="left", fill="x", expand=True, ipady=5)
        else:
            w = ttk.Combobox(row, font=("Times New Roman", 12), values=extra[0], state="readonly")
            w.pack(side="left", fill="x", expand=True, ipady=5)

        widgets[key] = w
        if data:
            if key in {"treEm", "trungNien", "nguoiCaoTuoi"}:
                age_cfg = data.get("coCauDoTuoi", {}) if isinstance(data.get("coCauDoTuoi"), dict) else {}
                val = age_cfg.get(key, 0)
            else:
                val = data.get(key, "")
            if kind == "entry":
                w.insert(0, str(val))
            else:
                w.set(val)

    if not data:
        widgets["soNguoi"].insert(0, "1")
        widgets["treEm"].insert(0, "0")
        widgets["trungNien"].insert(0, "1")
        widgets["nguoiCaoTuoi"].insert(0, "0")
        widgets["tongTien"].insert(0, "0")
        widgets["tienCoc"].insert(0, "0")
        widgets["daThanhToan"].insert(0, "0")
        widgets["conNo"].insert(0, "0")
        widgets["hinhThucThanhToan"].set("Chưa thanh toán")
        widgets["nguonKhach"].set("Khách lẻ")
        widgets["trangThai"].set("Mới tạo")

    tk.Label(
        form,
        text="Hệ thống sẽ tự tính lại tổng gốc, giảm theo độ tuổi, công nợ và trạng thái theo tour + thanh toán hiện có.",
        bg=THEME["surface"],
        fg=THEME["muted"],
        font=("Times New Roman", 11, "italic"),
        wraplength=520,
        justify="left",
    ).pack(anchor="w", pady=(6, 0))

    calc_summary_var = tk.StringVar(value="")
    calc_summary_lbl = tk.Label(
        form,
        textvariable=calc_summary_var,
        bg=THEME["surface"],
        fg=THEME["success"],
        font=("Times New Roman", 11, "bold"),
        wraplength=540,
        justify="left",
    )
    calc_summary_lbl.pack(anchor="w", pady=(8, 0))

    readonly_fields = {"tongTien", "conNo"}

    def set_entry_value(key, value):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `set_entry_value` (set entry value).
        Tham số:
            key: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        widget = widgets[key]
        if key in readonly_fields:
            widget.config(state="normal")
        widget.delete(0, "end")
        widget.insert(0, str(value))
        if key in readonly_fields:
            widget.config(state="readonly", readonlybackground="#f8fafc")

    def build_payment_status(total_amount, paid_amount):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `build_payment_status` (build payment status).
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
        if paid_amount <= 0:
            return BOOKING_STATUSES[0]
        if total_amount > 0 and paid_amount < total_amount:
            return BOOKING_STATUSES[1]
        return BOOKING_STATUSES[2]

    def refresh_booking_quote():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `refresh_booking_quote` (refresh booking quote).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        people = max(1, safe_int(widgets["soNguoi"].get() or 1))
        age_breakdown = normalize_passenger_breakdown(
            {
                "treEm": widgets["treEm"].get(),
                "trungNien": widgets["trungNien"].get(),
                "nguoiCaoTuoi": widgets["nguoiCaoTuoi"].get(),
            },
            people,
        )
        if age_breakdown is None:
            calc_summary_var.set("Cơ cấu độ tuổi đang vượt quá số người đi.")
            calc_summary_lbl.config(fg=THEME["danger"])
            return None

        set_entry_value("soNguoi", people)
        set_entry_value("treEm", age_breakdown["treEm"])
        set_entry_value("trungNien", age_breakdown["trungNien"])
        set_entry_value("nguoiCaoTuoi", age_breakdown["nguoiCaoTuoi"])

        tour = app["ql"].find_tour(widgets["maTour"].get().strip())
        price_per_person = max(0, safe_int(tour.get("gia", 0))) if tour else 0
        gross_total = price_per_person * people
        age_discount = min(calculate_age_discount(price_per_person, age_breakdown), gross_total)
        voucher_discount = max(0, safe_int(data.get("giamGiaVoucher", 0) if data else 0))
        voucher_discount = min(voucher_discount, max(gross_total - age_discount, 0))
        total_amount = max(gross_total - age_discount - voucher_discount, 0)

        tien_coc = max(0, safe_int(widgets["tienCoc"].get()))
        da_thanh_toan = max(max(0, safe_int(widgets["daThanhToan"].get())), tien_coc)
        da_thanh_toan = min(da_thanh_toan, total_amount)
        tien_coc = min(tien_coc, da_thanh_toan)
        con_no = max(total_amount - da_thanh_toan, 0)

        set_entry_value("tienCoc", tien_coc)
        set_entry_value("daThanhToan", da_thanh_toan)
        set_entry_value("tongTien", total_amount)
        set_entry_value("conNo", con_no)

        current_method = widgets["hinhThucThanhToan"].get().strip()
        default_paid_method = "Tiền mặt"
        if data and str(data.get("hinhThucThanhToan", "")).strip() and str(data.get("hinhThucThanhToan", "")).strip() != "Chưa thanh toán":
            default_paid_method = str(data.get("hinhThucThanhToan")).strip()
        if da_thanh_toan <= 0:
            widgets["hinhThucThanhToan"].set("Chưa thanh toán")
        elif current_method == "Chưa thanh toán":
            widgets["hinhThucThanhToan"].set(default_paid_method)

        if widgets["trangThai"].get().strip() not in set(BOOKING_STATUSES[3:]):
            widgets["trangThai"].set(build_payment_status(total_amount, da_thanh_toan))

        if not tour:
            calc_summary_var.set("Chọn tour hợp lệ để hệ thống tính lại tổng tiền.")
            calc_summary_lbl.config(fg=THEME["warning"])
        else:
            calc_summary_var.set(
                f"Giá gốc: {format_currency(gross_total)} | "
                f"Giảm độ tuổi: {format_currency(age_discount)} | "
                f"Voucher giữ nguyên: {format_currency(voucher_discount)} | "
                f"Cần thu: {format_currency(total_amount)}"
            )
            calc_summary_lbl.config(fg=THEME["success"])

        return {
            "people": people,
            "age_breakdown": age_breakdown,
            "tour": tour,
            "price_per_person": price_per_person,
            "tong_tien_goc": gross_total,
            "giam_gia_doi_tuong": age_discount,
            "giam_gia_voucher": voucher_discount,
            "tong_tien": total_amount,
            "tien_coc": tien_coc,
            "da_thanh_toan": da_thanh_toan,
            "con_no": con_no,
        }

    if data:
        widgets["maBooking"].config(state="disabled")

    refresh_booking_quote()
    for key in ["maTour", "trangThai"]:
        widgets[key].bind("<<ComboboxSelected>>", lambda _event: refresh_booking_quote())
    for key in ["soNguoi", "treEm", "trungNien", "nguoiCaoTuoi", "tienCoc", "daThanhToan"]:
        widgets[key].bind("<KeyRelease>", lambda _event: refresh_booking_quote())
        widgets[key].bind("<FocusOut>", lambda _event: refresh_booking_quote())

    def save_booking():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save_booking` (save booking).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        form_data = {}
        before_booking = copy.deepcopy(data) if data else None
        for _, key, kind, *extra in fields:
            if data and key == "maBooking":
                form_data[key] = data["maBooking"]
            else:
                form_data[key] = widgets[key].get().strip()

        if not form_data.get("trangThai"):
            form_data["trangThai"] = "Mới tạo"

        if safe_int(form_data.get("soNguoi", 0)) <= 0:
            messagebox.showwarning("Thông báo", "Số người đi phải là số nguyên dương.", parent=top)
            return

        snapshot = refresh_booking_quote()
        if snapshot is None:
            messagebox.showwarning("Thông báo", "Cơ cấu độ tuổi không hợp lệ so với số người đi.", parent=top)
            return

        people = snapshot["people"]
        age_breakdown = snapshot["age_breakdown"]
        giam_gia_voucher = snapshot["giam_gia_voucher"]

        form_data.pop("treEm", None)
        form_data.pop("trungNien", None)
        form_data.pop("nguoiCaoTuoi", None)
        form_data["soNguoi"] = str(people)
        form_data["tongTienGoc"] = snapshot["tong_tien_goc"]
        form_data["giamGiaDoiTuong"] = snapshot["giam_gia_doi_tuong"]
        form_data["coCauDoTuoi"] = age_breakdown
        form_data["tongTien"] = snapshot["tong_tien"]
        form_data["daThanhToan"] = snapshot["da_thanh_toan"]
        form_data["tienCoc"] = snapshot["tien_coc"]
        form_data["conNo"] = snapshot["con_no"]

        form_data["ngayDat"] = data.get("ngayDat", datetime.now().strftime("%d/%m/%Y")) if data else datetime.now().strftime("%d/%m/%Y")
        form_data["danhSachKhach"] = data.get("danhSachKhach", []) if data else []
        form_data["maVoucher"] = data.get("maVoucher", "") if data else ""
        form_data["tenVoucher"] = data.get("tenVoucher", "") if data else ""
        form_data["giamGiaVoucher"] = giam_gia_voucher
        form_data["trangThaiHoanTien"] = data.get("trangThaiHoanTien", "") if data else ""
        form_data["soTienHoan"] = data.get("soTienHoan", 0) if data else 0
        form_data["ngayYeuCauHoanTien"] = data.get("ngayYeuCauHoanTien", "") if data else ""
        form_data["ngayXuLyHoanTien"] = data.get("ngayXuLyHoanTien", "") if data else ""
        form_data["nguoiXuLyHoanTien"] = data.get("nguoiXuLyHoanTien", "") if data else ""
        form_data["ghiChuHoanTien"] = data.get("ghiChuHoanTien", "") if data else ""
        if form_data["trangThai"] not in set(BOOKING_STATUSES[3:]):
            form_data["trangThai"] = build_payment_status(form_data["tongTien"], form_data["daThanhToan"])
        if form_data["daThanhToan"] <= 0:
            form_data["hinhThucThanhToan"] = "Chưa thanh toán"
        elif form_data["hinhThucThanhToan"] == "Chưa thanh toán":
            form_data["hinhThucThanhToan"] = "Tiền mặt"

        ok, msg = validate_booking(app, form_data, data["maBooking"] if data else None)
        if not ok:
            messagebox.showwarning("Thông báo", msg, parent=top)
            return

        if data:
            for i, b in enumerate(app["ql"].list_bookings):
                if b["maBooking"] == data["maBooking"]:
                    app["ql"].list_bookings[i] = form_data
                    break
        else:
            app["ql"].list_bookings.append(form_data)

        app["ql"].save()
        if data:
            changed_fields = collect_changed_fields(before_booking, form_data)
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="booking",
                operation="update",
                target=form_data["maBooking"],
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="booking",
                operation="create",
                target=form_data["maBooking"],
                detail=f"Tạo booking cho tour {form_data.get('maTour', '')} | Khách: {form_data.get('tenKhach', '')}",
            )
        top.destroy()

        refresh_bookings(app, app["search_booking_var"].get())
        if app.get("tv_tour"):
            refresh_tours(app, app["search_tour_var"].get())

        set_status(app, "Đã lưu booking thành công", THEME["success"])

    btns = tk.Frame(card, bg=THEME["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))

    style_button(btns, "Lưu booking", THEME["success"], save_booking).pack(
        side="left", fill="x", expand=True, padx=(0, 8)
    )
    style_button(btns, "Hủy bỏ", THEME["danger"], top.destroy).pack(
        side="left", fill="x", expand=True
    )


# Mở form sửa booking đang chọn.
def edit_booking(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_booking` (edit booking).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_booking"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn booking cần sửa.")
        return

    ma = app["tv_booking"].item(sel[0])["values"][0]
    booking = next((b for b in app["ql"].list_bookings if b["maBooking"] == ma), None)
    if booking:
        open_booking_form(app, booking)


# Xóa booking được chọn sau khi xác nhận và kiểm tra các cảnh báo liên quan đến tour.
def delete_booking(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_booking` (delete booking).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    sel = app["tv_booking"].selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn booking cần xóa.")
        return

    ma = app["tv_booking"].item(sel[0])["values"][0]
    booking = next((b for b in app["ql"].list_bookings if b["maBooking"] == ma), None)

    if booking:
        tour = app["ql"].find_tour(booking["maTour"])
        if tour and tour.get("trangThai") in ["Đã chốt đoàn", "Chờ khởi hành", "Đang đi"]:
            if not messagebox.askyesno(
                "Cảnh báo",
                f"Tour '{tour['ten']}' hiện đang ở trạng thái '{tour['trangThai']}'.\nBạn vẫn chắc chắn muốn xóa?"
            ):
                return

    if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa booking {ma}?"):
        app["ql"].data["bookings"] = [b for b in app["ql"].list_bookings if b["maBooking"] != ma]
        app["ql"].save()
        write_crud_log(
            datastore=app["ql"],
            actor=get_admin_actor(app),
            role="admin",
            entity="booking",
            operation="delete",
            target=ma,
            detail="Xóa booking khỏi hệ thống",
        )

        refresh_bookings(app, app["search_booking_var"].get())
        if app.get("tv_tour"):
            refresh_tours(app, app["search_tour_var"].get())

        set_status(app, f"Đã xóa booking {ma}", THEME["danger"])


# Render tab quản lý booking, hoàn tiền và báo cáo liên quan.
def admin_booking_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_booking_tab` (admin booking tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)

    tk.Label(
        app["container"],
        text="QUẢN LÝ ĐẶT CHỖ & KHÁCH HÀNG",
        font=("Times New Roman", 20, "bold"),
        bg=THEME["bg"],
        fg=THEME["text"]
    ).pack(anchor="w", pady=(0, 10))

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))

    style_button(toolbar, "Thêm booking", "#16a34a", lambda: open_booking_form(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Cập nhật", "#2563eb", lambda: edit_booking(app)).pack(side="left", padx=(0, 8))
    style_button(
        toolbar,
        "Xem chi tiết",
        "#f59e0b",
        lambda: open_booking_detail(
            app,
            app["tv_booking"].item(app["tv_booking"].selection()[0])["values"][0]
        ) if app["tv_booking"].selection() else messagebox.showwarning("Thông báo", "Vui lòng chọn booking cần xem.")
    ).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Duyệt hoàn", "#16a34a", lambda: handle_refund_decision(app, True)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Từ chối hoàn", "#dc2626", lambda: handle_refund_decision(app, False)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Xóa booking", "#991b1b", lambda: delete_booking(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Tổng hợp theo tour", "#7c3aed", lambda: open_booking_summary_window(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Báo cáo doanh thu", "#0f766e", lambda: open_revenue_report_window(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 20))

    tk.Label(toolbar, text="Tìm kiếm:", bg=THEME["bg"], font=("Times New Roman", 12, "bold")).pack(side="left")
    search_entry = tk.Entry(toolbar, textvariable=app["search_booking_var"], font=("Times New Roman", 12), relief="solid", bd=1)
    search_entry.pack(side="left", fill="x", expand=True, ipady=4)
    search_entry.bind("<Return>", lambda e: refresh_bookings(app, app["search_booking_var"].get()))
    style_button(toolbar, "Lọc", THEME["primary"], lambda: refresh_bookings(app, app["search_booking_var"].get())).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="both", expand=True)

    cols = ("ma", "tour", "ten", "sdt", "songuoi", "tt", "refund")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=13)
    app["tv_booking"] = tv

    cfg = [
        ("ma", "Mã Booking", 100),
        ("tour", "Mã Tour", 90),
        ("ten", "Tên khách hàng", 190),
        ("sdt", "Số điện thoại", 120),
        ("songuoi", "Số người", 90),
        ("tt", "Trạng thái", 130),
        ("refund", "Hoàn tiền", 120),
    ]
    for c, t, w in cfg:
        tv.heading(c, text=t)
        tv.column(c, anchor="center", width=w)

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sy.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")

    def on_double_click(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click` (on double click).
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
        open_booking_detail(app, ma)

    tv.bind("<Double-1>", on_double_click)

    refresh_bookings(app, app["search_booking_var"].get())

# =========================
# FEEDBACK / NOTIFICATION
# =========================


# Mở popup xem nhanh chi tiết một phản hồi / thông báo.
def open_feedback_detail(app, mode, data):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_feedback_detail` (open feedback detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        mode: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }
    section_bg = PASTEL_DETAIL["section_bg_3"] if mode == "review" else PASTEL_DETAIL["section_bg_2"]

    top = tk.Toplevel(app["root"])
    top.title("Chi tiết")
    top.geometry("760x480")
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    card = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        bd=1,
        relief="solid",
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    title = "CHI TIẾT ĐÁNH GIÁ" if mode == "review" else "CHI TIẾT THÔNG BÁO"

    tk.Label(
        card,
        text=title,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 22, "bold")
    ).pack(pady=(14, 10))

    tk.Label(
        card,
        text="Đánh giá khách hàng" if mode == "review" else "Thông báo hướng dẫn viên",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack(pady=(0, 12))

    body = tk.Frame(
        card,
        bg=section_bg,
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    body.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    tk.Label(
        body,
        text="Thông tin chi tiết",
        bg=section_bg,
        fg=PASTEL_DETAIL["text"],
        font=("Times New Roman", 15, "bold")
    ).pack(anchor="w", padx=16, pady=(12, 8))

    body_inner = tk.Frame(body, bg=section_bg)
    body_inner.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    if mode == "review":
        rows = [
            ("Khách hàng", f"{data.get('fullname', '')} ({data.get('username', '')})"),
            ("Đối tượng", format_review_target(app["ql"], data)),
            ("Điểm", data.get("rating", "")),
            ("Ngày gửi", data.get("date", "")),
            ("Nội dung", data.get("content", "")),
        ]
    else:
        rows = [
            ("Mã HDV", data.get("maHDV", "")),
            ("Tên HDV", data.get("tenHDV", "")),
            ("Tour", f"{data.get('maTour', '')} - {data.get('tenTour', '')}"),
            ("Ngày gửi", data.get("date", "")),
            ("Nội dung", data.get("content", "")),
        ]

    for label_text, value in rows:
        row = tk.Frame(body_inner, bg=section_bg, bd=0)
        row.pack(fill="x", pady=5)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=16,
            anchor="nw",
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            row,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=480,
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True, padx=(12, 12), pady=10)

    style_button(
        card,
        "Đóng",
        THEME["danger"],
        top.destroy,
        fg="white"
    ).pack(padx=20, pady=(8, 16), fill="x")

# Mở phiên bản chi tiết đầy đủ hơn cho phản hồi / thông báo.
def open_feedback_detail_full(app, mode, data):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_feedback_detail_full` (open feedback detail full).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        mode: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }
    section_bg = PASTEL_DETAIL["section_bg_3"] if mode == "review" else PASTEL_DETAIL["section_bg_2"]

    top = tk.Toplevel(app["root"])
    top.title("Chi tiết")
    top.geometry("860x620")
    top.minsize(840, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(content_shell, bg=PASTEL_DETAIL["bg"], highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)
    v_scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    card = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=card, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    card.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
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
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    title = "CHI TIẾT ĐÁNH GIÁ" if mode == "review" else "CHI TIẾT THÔNG BÁO"
    subtitle = "Đánh giá khách hàng" if mode == "review" else "Thông báo hướng dẫn viên"

    tk.Label(
        card,
        text=title,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 22, "bold")
    ).pack(pady=(16, 8))

    tk.Label(
        card,
        text=subtitle,
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack(pady=(0, 12))

    body = tk.Frame(
        card,
        bg=section_bg,
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    body.pack(fill="both", expand=True, padx=20, pady=(0, 14))

    tk.Label(
        body,
        text="Thông tin chi tiết",
        bg=section_bg,
        fg=PASTEL_DETAIL["text"],
        font=("Times New Roman", 15, "bold")
    ).pack(anchor="w", padx=16, pady=(12, 8))

    body_inner = tk.Frame(body, bg=section_bg)
    body_inner.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    if mode == "review":
        rows = [
            ("Khách hàng", f"{data.get('fullname', '')} ({data.get('username', '')})"),
            ("Username", data.get("username", "") or "Không có"),
            ("Đối tượng", format_review_target(app["ql"], data, include_code=True) or "Không có"),
            ("Mã đối tượng", data.get("target_id", "") or "Không có"),
            ("Điểm đánh giá", data.get("rating", "") or "Không có"),
            ("Ngày gửi", data.get("date", "") or "Không có"),
            ("Nội dung", data.get("content", "") or "Không có"),
        ]
    else:
        rows = [
            ("Mã HDV", data.get("maHDV", "") or "Không có"),
            ("Tên HDV", data.get("tenHDV", "") or "Không có"),
            ("Mã tour", data.get("maTour", "") or "Không có"),
            ("Tên tour", data.get("tenTour", "") or "Không có"),
            ("Tour", f"{data.get('maTour', '')} - {data.get('tenTour', '')}".strip(" -") or "Không có"),
            ("Ngày gửi", data.get("date", "") or "Không có"),
            ("Nội dung", data.get("content", "") or "Không có"),
        ]

    for label_text, value in rows:
        row = tk.Frame(body_inner, bg=section_bg)
        row.pack(fill="x", pady=5)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=18,
            anchor="nw",
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            row,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=640,
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True, padx=(12, 12), pady=10)

    tk.Frame(card, bg=PASTEL_DETAIL["surface"], height=90).pack(fill="x")

    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    footer_inner = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    footer_inner.pack(fill="x", padx=16, pady=10)

    style_button(footer_inner, "Đóng", THEME["danger"], top.destroy).pack(fill="x")


# Render tab quản lý phản hồi và thông báo của admin.
def admin_feedback_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_feedback_tab` (admin feedback tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)

    tk.Label(
        app["container"],
        text="ĐÁNH GIÁ TỪ KHÁCH HÀNG",
        font=("Times New Roman", 18, "bold"),
        bg=THEME["bg"],
        fg=THEME["text"]
    ).pack(anchor="w", pady=(0, 10))

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left")

    rev_wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    rev_wrapper.pack(fill="both", expand=True, pady=(0, 20))

    rev_tv = ttk.Treeview(rev_wrapper, columns=("user", "target", "content", "date"), show="headings", height=8)
    rev_tv.heading("user", text="Khách hàng")
    rev_tv.heading("target", text="Đối tượng")
    rev_tv.heading("content", text="Nội dung đánh giá")
    rev_tv.heading("date", text="Ngày gửi")

    rev_tv.column("user", width=280, minwidth=180, anchor="w", stretch=False)
    rev_tv.column("target", width=160, minwidth=120, anchor="center", stretch=False)
    rev_tv.column("content", width=500, minwidth=320, anchor="w", stretch=True)
    rev_tv.column("date", width=140, minwidth=120, anchor="center", stretch=False)

    rev_sy = ttk.Scrollbar(rev_wrapper, orient="vertical", command=rev_tv.yview)
    rev_sx = ttk.Scrollbar(rev_wrapper, orient="horizontal", command=rev_tv.xview)
    rev_tv.configure(yscrollcommand=rev_sy.set, xscrollcommand=rev_sx.set)
    rev_sy.pack(side="right", fill="y")
    rev_sx.pack(side="bottom", fill="x")
    rev_tv.pack(side="left", fill="both", expand=True)

    review_rows = []
    for r in app["ql"].list_reviews:
        target_display = format_review_target(app["ql"], r)

        review_rows.append(r)
        rev_tv.insert("", "end", values=(
            f"{r.get('fullname', '')} ({r.get('username', '')})",
            target_display,
            r.get("content", ""),
            r.get("date", "")
        ))

    def on_double_click_review(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click_review` (on double click review).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        sel = rev_tv.selection()
        if not sel:
            return
        idx = rev_tv.index(sel[0])
        if 0 <= idx < len(review_rows):
            open_feedback_detail_full(app, "review", review_rows[idx])

    rev_tv.bind("<Double-1>", on_double_click_review)

    apply_zebra(rev_tv)

    tk.Label(
        app["container"],
        text="THÔNG BÁO TỪ HƯỚNG DẪN VIÊN",
        font=("Times New Roman", 18, "bold"),
        bg=THEME["bg"],
        fg=THEME["text"]
    ).pack(anchor="w", pady=(0, 10))

    notif_wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    notif_wrapper.pack(fill="both", expand=True)

    notif_tv = ttk.Treeview(notif_wrapper, columns=("ma", "ten", "tour", "content", "date"), show="headings", height=8)
    notif_tv.heading("ma", text="Mã HDV")
    notif_tv.heading("ten", text="Tên HDV")
    notif_tv.heading("tour", text="Đoàn (Tour)")
    notif_tv.heading("content", text="Nội dung thông báo")
    notif_tv.heading("date", text="Ngày gửi")

    notif_tv.column("ma", width=90, minwidth=80, anchor="center", stretch=False)
    notif_tv.column("ten", width=180, minwidth=130, anchor="w", stretch=False)
    notif_tv.column("tour", width=220, minwidth=180, anchor="w", stretch=False)
    notif_tv.column("content", width=500, minwidth=300, anchor="w", stretch=True)
    notif_tv.column("date", width=150, minwidth=130, anchor="center", stretch=False)

    notif_sy = ttk.Scrollbar(notif_wrapper, orient="vertical", command=notif_tv.yview)
    notif_sx = ttk.Scrollbar(notif_wrapper, orient="horizontal", command=notif_tv.xview)
    notif_tv.configure(yscrollcommand=notif_sy.set, xscrollcommand=notif_sx.set)
    notif_sy.pack(side="right", fill="y")
    notif_sx.pack(side="bottom", fill="x")
    notif_tv.pack(side="left", fill="both", expand=True)

    notif_rows = []
    for n in app["ql"].list_notifications:
        notif_rows.append(n)
        tour_info = f"{n.get('maTour', 'N/A')} - {n.get('tenTour', '')}"
        notif_tv.insert("", "end", values=(
            n.get("maHDV", ""),
            n.get("tenHDV", ""),
            tour_info,
            n.get("content", ""),
            n.get("date", "")
        ))

    def on_double_click_notif(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click_notif` (on double click notif).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        sel = notif_tv.selection()
        if not sel:
            return
        idx = notif_tv.index(sel[0])
        if 0 <= idx < len(notif_rows):
            open_feedback_detail_full(app, "notify", notif_rows[idx])

    notif_tv.bind("<Double-1>", on_double_click_notif)

    apply_zebra(notif_tv)

    set_status(app, "Đang xem Đánh giá & Thông báo", THEME["primary"])

# =========================
# Voucher 
# =========================

# Kiểm tra chuỗi ngày có đúng định dạng dd/mm/yyyy hay không.
def is_valid_date(date_text):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_date` (is valid date).
    Tham số:
        date_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        datetime.strptime(date_text, "%d/%m/%Y")
        return True
    except ValueError:
        return False


# Kiểm tra tính hợp lệ của dữ liệu voucher trước khi lưu.
def validate_voucher(app, data, old_code=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_voucher` (validate voucher).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = copy.deepcopy(data)
    normalized["maVoucher"] = str(normalized.get("maVoucher", "")).strip().upper()
    normalized["tourApDung"] = normalize_tour_scope(normalized.get("tourApDung", ""))
    return validate_voucher_payload(app["ql"], normalized, old_code=old_code)


# Nạp lại bảng voucher để phản ánh dữ liệu mới nhất trên giao diện.
def refresh_vouchers(app, keyword=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_vouchers` (refresh vouchers).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tv = app.get("tv_voucher")
    if not tv:
        return

    for item in tv.get_children():
        tv.delete(item)

    rows = app["ql"].list_vouchers
    if keyword:
        kw = keyword.lower().strip()
        rows = [
            v for v in rows
            if kw in str(v.get("maVoucher", "")).lower()
            or kw in str(v.get("tenVoucher", "")).lower()
            or kw in str(v.get("trangThai", "")).lower()
            or kw in str(v.get("moTa", "")).lower()
            or kw in str(v.get("tourApDung", "")).lower()
        ]

    for v in rows:
        ma = str(v.get("maVoucher", "")).strip()
        ten = str(v.get("tenVoucher", "")).strip()
        tt = str(v.get("trangThai", "")).strip()
        loai = str(v.get("loaiGiam", "")).strip()
        giam = str(v.get("giamGiaVoucher", "")).strip()

        if loai == "Tiền mặt" and giam.isdigit():
            giam_hien = f"{int(giam):,}đ".replace(",", ".")
        else:
            giam_hien = giam

        sl_hien = f"{v.get('daSuDung', '0')}/{v.get('soLuong', '0')}"

        item = tv.insert("", "end", values=(ma, ten, giam_hien, sl_hien, tt))

        if "Đang áp dụng" in tt:
            tv.item(item, tags=("active",))
        elif "Ngừng" in tt:
            tv.item(item, tags=("inactive",))
        elif "Hết" in tt:
            tv.item(item, tags=("expired",))

    apply_zebra(tv)
    set_status(app, f"Hiển thị {len(rows)} voucher", THEME["primary"])


# Mở form thêm mới / chỉnh sửa voucher và kiểm tra dữ liệu trước khi lưu.
def open_voucher_form(app, data=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_voucher_form` (open voucher form).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    top = tk.Toplevel(app["root"])
    top.title("Thông tin mã giảm giá")
    top.geometry("720x620")
    top.configure(bg=THEME["bg"])
    top.transient(app["root"])
    top.grab_set()

    card = tk.Frame(top, bg=THEME["surface"], bd=1, relief="solid")
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(
        card,
        text="THÔNG TIN MÃ GIẢM GIÁ",
        bg=THEME["surface"],
        fg=THEME["text"],
        font=("Times New Roman", 18, "bold")
    ).pack(pady=(14, 10))

    form_wrap, form = create_scrollable_form(card, THEME["surface"])
    form_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    fields = [
        ("Mã voucher", "maVoucher", "entry"),
        ("Tên voucher", "tenVoucher", "entry"),
        ("Loại giảm", "loaiGiam", "combo", ["Phần trăm", "Tiền mặt"]),
        ("Giảm giá", "giamGiaVoucher", "entry"),
        ("Đơn tối thiểu", "donToiThieu", "entry"),
        ("Số lượng", "soLuong", "entry"),
        ("Đã sử dụng", "daSuDung", "entry"),
        ("Giới hạn / user", "gioiHanMoiUser", "entry"),
        ("Tour áp dụng", "tourApDung", "entry"),
        ("Ngày bắt đầu", "ngayBatDau", "entry"),
        ("Ngày kết thúc", "ngayKetThuc", "entry"),
        ("Trạng thái", "trangThai", "combo", ["Đang áp dụng", "Ngừng áp dụng", "Hết lượt"]),
        ("Mô tả", "moTa", "text"),
    ]

    widgets = {}

    for label, key, kind, *extra in fields:
        row = tk.Frame(form, bg=THEME["surface"])
        row.pack(fill="x", pady=7)

        tk.Label(
            row,
            text=label,
            width=16,
            anchor="w",
            bg=THEME["surface"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left")

        if kind == "entry":
            w = tk.Entry(row, font=("Times New Roman", 12), relief="solid", bd=1)
            w.pack(side="left", fill="x", expand=True, ipady=4)
        elif kind == "combo":
            w = ttk.Combobox(row, values=extra[0], state="readonly", font=("Times New Roman", 11))
            w.pack(side="left", fill="x", expand=True, ipady=4)
        else:
            w = tk.Text(row, height=4, font=("Times New Roman", 12), relief="solid", bd=1)
            w.pack(side="left", fill="both", expand=True)

        widgets[key] = w

        if data:
            value = data.get(key, "")
            if kind == "text":
                w.insert("1.0", value)
            else:
                w.insert(0, value) if kind == "entry" else w.set(value)

    if data:
        widgets["maVoucher"].config(state="disabled")

    hint_var = tk.StringVar(value="Ví dụ: 10% hoặc 50000 | Giới hạn / user: 0 = không giới hạn | Tour áp dụng: T01, T02")
    tk.Label(
        card,
        textvariable=hint_var,
        bg=THEME["surface"],
        fg=THEME["muted"],
        font=("Times New Roman", 10, "italic")
    ).pack(anchor="w", padx=20, pady=(0, 8))

    def on_discount_type_change(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_discount_type_change` (on discount type change).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        loai = widgets["loaiGiam"].get().strip()
        if loai == "Phần trăm":
            hint_var.set("Nhập giảm giá dạng phần trăm, ví dụ: 10%")
        else:
            hint_var.set("Nhập giảm giá dạng tiền mặt, ví dụ: 50000")

    if isinstance(widgets["loaiGiam"], ttk.Combobox):
        widgets["loaiGiam"].bind("<<ComboboxSelected>>", on_discount_type_change)

    def save_voucher():
        """
        Mục đích:
            Thực hiện xử lý cho hàm `save_voucher` (save voucher).
        Tham số:
            Không có.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        new_data = {}
        before_voucher = copy.deepcopy(data) if data else None
        for _, key, kind, *extra in fields:
            if kind == "text":
                new_data[key] = widgets[key].get("1.0", "end").strip()
            elif data and key == "maVoucher":
                new_data[key] = data["maVoucher"]
            else:
                new_data[key] = widgets[key].get().strip()

        new_data["maVoucher"] = new_data["maVoucher"].upper()
        new_data["tourApDung"] = normalize_tour_scope(new_data.get("tourApDung", ""))
        if not new_data.get("gioiHanMoiUser"):
            new_data["gioiHanMoiUser"] = "0"

        ok, msg = validate_voucher(app, new_data, data["maVoucher"] if data else None)
        if not ok:
            messagebox.showwarning("Thông báo", msg, parent=top)
            return

        if data:
            for i, v in enumerate(app["ql"].list_vouchers):
                if str(v.get("maVoucher", "")).upper() == str(data["maVoucher"]).upper():
                    app["ql"].list_vouchers[i] = new_data
                    break
        else:
            app["ql"].list_vouchers.append(new_data)

        app["ql"].save()
        if data:
            changed_fields = collect_changed_fields(before_voucher, new_data)
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="voucher",
                operation="update",
                target=new_data["maVoucher"],
                detail="Trường thay đổi: " + (", ".join(changed_fields) if changed_fields else "Không đổi dữ liệu"),
            )
        else:
            write_crud_log(
                datastore=app["ql"],
                actor=get_admin_actor(app),
                role="admin",
                entity="voucher",
                operation="create",
                target=new_data["maVoucher"],
                detail=f"Tạo voucher {new_data.get('tenVoucher', '')} | Phạm vi: {new_data.get('tourApDung', 'Tất cả tour') or 'Tất cả tour'}",
            )
        refresh_vouchers(app)
        top.destroy()
        set_status(app, "Đã lưu voucher thành công", THEME["success"])

    btns = tk.Frame(card, bg=THEME["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))

    style_button(btns, "Lưu voucher", THEME["success"], save_voucher).pack(side="left", fill="x", expand=True, padx=(0, 8))
    style_button(btns, "Hủy", THEME["danger"], top.destroy).pack(side="left", fill="x", expand=True)


# Mở form sửa voucher đang chọn.
def edit_voucher(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `edit_voucher` (edit voucher).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tv = app.get("tv_voucher")
    if not tv:
        return

    sel = tv.selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn voucher cần sửa.")
        return

    code = tv.item(sel[0])["values"][0]
    voucher = next((v for v in app["ql"].list_vouchers if v.get("maVoucher") == code), None)
    if not voucher:
        messagebox.showerror("Lỗi", "Không tìm thấy voucher.")
        return

    open_voucher_form(app, voucher)


# Xóa voucher đang chọn sau khi xác nhận.
def delete_voucher(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `delete_voucher` (delete voucher).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tv = app.get("tv_voucher")
    if not tv:
        return

    sel = tv.selection()
    if not sel:
        messagebox.showwarning("Thông báo", "Vui lòng chọn voucher cần xóa.")
        return

    code = tv.item(sel[0])["values"][0]

    if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa voucher {code}?"):
        return

    app["ql"].data["maVoucher"] = [
        v for v in app["ql"].list_vouchers
        if str(v.get("maVoucher", "")).upper() != str(code).upper()
    ]
    app["ql"].save()
    write_crud_log(
        datastore=app["ql"],
        actor=get_admin_actor(app),
        role="admin",
        entity="voucher",
        operation="delete",
        target=code,
        detail="Xóa voucher khỏi hệ thống",
    )
    refresh_vouchers(app)
    set_status(app, f"Đã xóa voucher {code}", THEME["danger"])

# Mở cửa sổ xem nhanh chi tiết voucher.
def open_voucher_detail(app, code):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_voucher_detail` (open voucher detail).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    voucher = next((v for v in app["ql"].list_vouchers if v.get("maVoucher") == code), None)
    if not voucher:
        messagebox.showerror("Lỗi", "Không tìm thấy voucher.")
        return
    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }
    status = str(voucher.get("trangThai", "")).strip()
    section_bg = PASTEL_DETAIL["section_bg"]
    if "Đang áp dụng" in status:
        section_bg = PASTEL_DETAIL["section_bg_2"]
    elif "Hết" in status:
        section_bg = PASTEL_DETAIL["section_bg_3"]

    top = tk.Toplevel(app["root"])
    top.title(f"Chi tiết voucher - {code}")
    top.geometry("620x500")
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    card = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        bd=1,
        relief="solid",
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=16, pady=16)

    tk.Label(
        card,
        text="CHI TIẾT MÃ GIẢM GIÁ",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 22, "bold")
    ).pack(pady=(14, 12))

    tk.Label(
        card,
        text=voucher.get("maVoucher", ""),
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack(pady=(0, 12))

    body = tk.Frame(
        card,
        bg=section_bg,
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    body.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    tk.Label(
        body,
        text="Thông tin voucher",
        bg=section_bg,
        fg=PASTEL_DETAIL["text"],
        font=("Times New Roman", 15, "bold")
    ).pack(anchor="w", padx=16, pady=(12, 8))

    body_inner = tk.Frame(body, bg=section_bg)
    body_inner.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    rows = [
        ("Mã voucher", voucher.get("maVoucher", "")),
        ("Tên voucher", voucher.get("tenVoucher", "")),
        ("Loại giảm", voucher.get("loaiGiam", "")),
        ("Giảm giá", voucher.get("giamGiaVoucher", "")),
        ("Đơn tối thiểu", f"{safe_int(voucher.get('donToiThieu', 0)):,}đ".replace(",", ".")),
        ("Số lượng", voucher.get("soLuong", "")),
        ("Đã sử dụng", voucher.get("daSuDung", "")),
        ("Giới hạn / user", voucher.get("gioiHanMoiUser", "0") or "0"),
        ("Phạm vi tour", build_voucher_scope_label(voucher)),
        ("Ngày bắt đầu", voucher.get("ngayBatDau", "")),
        ("Ngày kết thúc", voucher.get("ngayKetThuc", "")),
        ("Trạng thái", voucher.get("trangThai", "")),
        ("Mô tả", voucher.get("moTa", "")),
    ]

    for label_text, value in rows:
        row = tk.Frame(body_inner, bg=section_bg, bd=0)
        row.pack(fill="x", pady=5)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=16,
            anchor="w",
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            row,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=360,
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True, padx=(12, 12), pady=10)

    btns = tk.Frame(card, bg=PASTEL_DETAIL["surface"])
    btns.pack(fill="x", padx=20, pady=(8, 16))

    style_button(
        btns,
        "Sửa voucher",
        THEME["primary"],
        lambda: [top.destroy(), open_voucher_form(app, voucher)]
    ).pack(side="left", fill="x", expand=True, padx=(0, 8))

    style_button(
        btns,
        "Đóng",
        THEME["danger"],
        top.destroy
    ).pack(side="left", fill="x", expand=True)


# Mở cửa sổ chi tiết đầy đủ của voucher với thông tin mở rộng hơn.
def open_voucher_detail_full(app, code):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `open_voucher_detail_full` (open voucher detail full).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    voucher = next((v for v in app["ql"].list_vouchers if v.get("maVoucher") == code), None)
    if not voucher:
        messagebox.showerror("Lỗi", "Không tìm thấy voucher.")
        return

    PASTEL_DETAIL = {
        "bg": "#edf6f9",
        "surface": "#ffffff",
        "title": "#1d3557",
        "muted": "#6c7a89",
        "border": "#cbd5e1",
        "section_bg": "#fff1e6",
        "section_bg_2": "#e8f6f0",
        "section_bg_3": "#f3ecff",
        "text": "#1f2937",
    }

    status = str(voucher.get("trangThai", "")).strip()
    section_bg = PASTEL_DETAIL["section_bg"]
    if "Đang áp dụng" in status:
        section_bg = PASTEL_DETAIL["section_bg_2"]
    elif "Hết" in status:
        section_bg = PASTEL_DETAIL["section_bg_3"]

    top = tk.Toplevel(app["root"])
    top.title(f"Chi tiết voucher - {code}")
    top.geometry("820x620")
    top.minsize(820, 620)
    top.configure(bg=PASTEL_DETAIL["bg"])
    top.transient(app["root"])
    top.grab_set()

    outer_shell = tk.Frame(top, bg=PASTEL_DETAIL["bg"])
    outer_shell.pack(fill="both", expand=True, padx=14, pady=(14, 0))

    content_shell = tk.Frame(outer_shell, bg=PASTEL_DETAIL["bg"])
    content_shell.pack(fill="both", expand=True)

    canvas = tk.Canvas(content_shell, bg=PASTEL_DETAIL["bg"], highlightthickness=0, bd=0)
    v_scroll = ttk.Scrollbar(content_shell, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)
    v_scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    card = tk.Frame(
        canvas,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    canvas_window = canvas.create_window((0, 0), window=card, anchor="nw")

    def _on_frame_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_frame_configure` ( on frame configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_canvas_configure` ( on canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.itemconfigure(canvas_window, width=event.width)

    card.bind("<Configure>", _on_frame_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_mousewheel` ( on mousewheel).
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
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    def _bind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_bind_mousewheel` ( bind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_unbind_mousewheel` ( unbind mousewheel).
        Tham số:
            _event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        canvas.unbind_all("<MouseWheel>")

    top.bind("<Enter>", _bind_mousewheel)
    top.bind("<Leave>", _unbind_mousewheel)

    tk.Label(
        card,
        text="CHI TIẾT MÃ GIẢM GIÁ",
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["title"],
        font=("Times New Roman", 22, "bold")
    ).pack(pady=(16, 8))

    tk.Label(
        card,
        text=voucher.get("maVoucher", ""),
        bg=PASTEL_DETAIL["surface"],
        fg=PASTEL_DETAIL["muted"],
        font=("Times New Roman", 11, "italic")
    ).pack(pady=(0, 12))

    body = tk.Frame(
        card,
        bg=section_bg,
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    body.pack(fill="both", expand=True, padx=20, pady=(0, 14))

    tk.Label(
        body,
        text="Thông tin voucher",
        bg=section_bg,
        fg=PASTEL_DETAIL["text"],
        font=("Times New Roman", 15, "bold")
    ).pack(anchor="w", padx=16, pady=(12, 8))

    body_inner = tk.Frame(body, bg=section_bg)
    body_inner.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    loai = str(voucher.get("loaiGiam", "")).strip()
    giam = str(voucher.get("giamGiaVoucher", "")).strip()
    if loai == "Tiền mặt" and giam.isdigit():
        giam_hien = f"{int(giam):,}đ".replace(",", ".")
    else:
        giam_hien = giam

    rows = [
        ("Mã voucher", voucher.get("maVoucher", "") or "Không có"),
        ("Tên voucher", voucher.get("tenVoucher", "") or "Không có"),
        ("Loại giảm", loai or "Không có"),
        ("Giảm giá", giam_hien or "Không có"),
        ("Đơn tối thiểu", f"{safe_int(voucher.get('donToiThieu', 0)):,}đ".replace(",", ".")),
        ("Số lượng", voucher.get("soLuong", "") or "0"),
        ("Đã sử dụng", voucher.get("daSuDung", "") or "0"),
        ("Còn lại", max(0, safe_int(voucher.get("soLuong", 0)) - safe_int(voucher.get("daSuDung", 0)))),
        ("Giới hạn / user", voucher.get("gioiHanMoiUser", "0") or "0"),
        ("Phạm vi tour", build_voucher_scope_label(voucher)),
        ("Ngày bắt đầu", voucher.get("ngayBatDau", "") or "Không có"),
        ("Ngày kết thúc", voucher.get("ngayKetThuc", "") or "Không có"),
        ("Trạng thái", voucher.get("trangThai", "") or "Không có"),
        ("Mô tả", voucher.get("moTa", "") or "Không có"),
    ]

    for label_text, value in rows:
        row = tk.Frame(body_inner, bg=section_bg)
        row.pack(fill="x", pady=5)

        tk.Label(
            row,
            text=f"{label_text}:",
            width=18,
            anchor="nw",
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12, "bold")
        ).pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            row,
            text=str(value),
            anchor="w",
            justify="left",
            wraplength=620,
            bg=section_bg,
            fg=PASTEL_DETAIL["text"],
            font=("Times New Roman", 12)
        ).pack(side="left", fill="x", expand=True, padx=(12, 12), pady=10)

    tk.Frame(card, bg=PASTEL_DETAIL["surface"], height=90).pack(fill="x")

    footer = tk.Frame(
        top,
        bg=PASTEL_DETAIL["surface"],
        highlightbackground=PASTEL_DETAIL["border"],
        highlightthickness=1
    )
    footer.pack(side="bottom", fill="x", padx=14, pady=14)

    btns = tk.Frame(footer, bg=PASTEL_DETAIL["surface"])
    btns.pack(fill="x", padx=16, pady=10)

    style_button(
        btns,
        "Sửa voucher",
        THEME["primary"],
        lambda: [top.destroy(), open_voucher_form(app, voucher)]
    ).pack(side="left", fill="x", expand=True, padx=(0, 8))

    style_button(
        btns,
        "Đóng",
        THEME["danger"],
        top.destroy
    ).pack(side="left", fill="x", expand=True)


# Nạp lại bảng voucher để phản ánh dữ liệu mới nhất trên giao diện.
def refresh_vouchers(app, keyword=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `refresh_vouchers` (refresh vouchers).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keyword: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tv = app.get("tv_voucher")
    if not tv:
        return

    for item in tv.get_children():
        tv.delete(item)

    rows = app["ql"].list_vouchers
    if keyword:
        kw = keyword.lower().strip()
        rows = [
            v for v in rows
            if kw in str(v.get("maVoucher", "")).lower()
            or kw in str(v.get("tenVoucher", "")).lower()
            or kw in str(v.get("trangThai", "")).lower()
            or kw in str(v.get("moTa", "")).lower()
            or kw in str(v.get("tourApDung", "")).lower()
        ]

    for v in rows:
        ma = str(v.get("maVoucher", "")).strip()
        ten = str(v.get("tenVoucher", "")).strip()
        tt = str(v.get("trangThai", "")).strip()
        loai = str(v.get("loaiGiam", "")).strip()
        giam = str(v.get("giamGiaVoucher", "")).strip()

        if loai == "Tiền mặt" and giam.isdigit():
            giam_hien = f"{int(giam):,}đ".replace(",", ".")
        else:
            giam_hien = giam

        sl_hien = f"{v.get('daSuDung', '0')}/{v.get('soLuong', '0')}"

        item = tv.insert("", "end", values=(ma, ten, giam_hien, sl_hien, tt))

        if "Đang áp dụng" in tt:
            tv.item(item, tags=("active",))
        elif "Ngừng" in tt:
            tv.item(item, tags=("inactive",))
        elif "Hết" in tt:
            tv.item(item, tags=("expired",))

    apply_zebra(tv)
    set_status(app, f"Hiển thị {len(rows)} voucher", THEME["primary"])


# Render tab quản lý voucher của admin.
def admin_voucher_tab(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `admin_voucher_tab` (admin voucher tab).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    clear_container(app)

    tk.Label(
        app["container"],
        text="QUẢN LÝ MÃ GIẢM GIÁ",
        font=("Times New Roman", 20, "bold"),
        bg=THEME["bg"],
        fg=THEME["text"]
    ).pack(anchor="w", pady=(0, 10))

    toolbar = tk.Frame(app["container"], bg=THEME["bg"])
    toolbar.pack(fill="x", pady=(0, 10))

    style_button(toolbar, "Thêm mã", THEME["success"], lambda: open_voucher_form(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Sửa voucher", THEME["primary"], lambda: edit_voucher(app)).pack(side="left", padx=(0, 8))
    style_button(toolbar, "Xóa mã", THEME["danger"], lambda: delete_voucher(app)).pack(side="left", padx=(0, 20))
    style_button(toolbar, "Tải lại", "#0ea5e9", lambda: reload_admin_current_tab(app)).pack(side="left", padx=(0, 20))

    tk.Label(
        toolbar,
        text="Tìm kiếm:",
        bg=THEME["bg"],
        font=("Times New Roman", 12, "bold")
    ).pack(side="left")

    if "search_voucher_var" not in app:
        app["search_voucher_var"] = tk.StringVar()

    ent_search = tk.Entry(
        toolbar,
        textvariable=app["search_voucher_var"],
        font=("Times New Roman", 12),
        relief="solid",
        bd=1
    )
    ent_search.pack(side="left", fill="x", expand=True, ipady=4)
    ent_search.bind("<Return>", lambda e: refresh_vouchers(app, app["search_voucher_var"].get()))

    style_button(
        toolbar,
        "Lọc",
        THEME["primary"],
        lambda: refresh_vouchers(app, app["search_voucher_var"].get())
    ).pack(side="left", padx=(8, 0))

    wrapper = tk.Frame(app["container"], bg=THEME["surface"], bd=1, relief="solid")
    wrapper.pack(fill="both", expand=True)

    cols = ("ma", "ten", "giam", "sl", "tt")
    tv = ttk.Treeview(wrapper, columns=cols, show="headings", height=12)
    app["tv_voucher"] = tv

    headers = [
        ("ma", "Mã giảm giá", 140),
        ("ten", "Tên chương trình", 260),
        ("giam", "Giảm", 140),
        ("sl", "Đã dùng/Tổng", 120),
        ("tt", "Trạng thái", 140),
    ]

    for c, t, w in headers:
        tv.heading(c, text=t)
        tv.column(c, anchor="center", width=w)

    def on_double_click_voucher(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `on_double_click_voucher` (on double click voucher).
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
        code = tv.item(sel[0])["values"][0]
        open_voucher_detail_full(app, code)

    tv.bind("<Double-1>", on_double_click_voucher)

    sy = ttk.Scrollbar(wrapper, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sy.set)
    tv.pack(side="left", fill="both", expand=True)
    sy.pack(side="right", fill="y")

    refresh_vouchers(app, app["search_voucher_var"].get())
    set_status(app, "Đang ở Quản lý mã giảm giá", THEME["primary"])

# =========================
# SYSTEM
# =========================

# Đăng xuất khỏi giao diện admin và quay về màn hình đăng nhập / chọn vai trò.
def logout(app):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `logout` (logout).
    Tham số:
        app: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if messagebox.askyesno("Đăng xuất", "Bạn có chắc chắn muốn thoát khỏi hệ thống quản trị?"):
        for widget in app["root"].winfo_children():
            widget.destroy()
        try:
            from GUI.Login.login import set_root, show_role_selection
            set_root(app["root"])
            app["root"].configure(bg=THEME["bg"])
            show_role_selection()
        except (ImportError, RuntimeError, tk.TclError) as e:
            messagebox.showerror("Lỗi", f"Không thể quay lại màn hình đăng nhập.\n{e}")


# =========================
# MAIN
# =========================
# Hàm khởi tạo giao diện admin chính.
# Tạo root/window, datastore, sidebar, container nội dung, thanh trạng thái và gắn các tab chức năng.
def main(root=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `main` (main).
    Tham số:
        root: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    enable_tk_text_autofix()
    if root is None:
        root = tk.Tk()

    root.title("VIETNAM TRAVEL - QUẢN TRỊ HỆ THỐNG")
    root.geometry("1420x820")
    root.minsize(1220, 740)
    root.configure(bg=THEME["bg"])
    configure_ui_fonts(root)

    for widget in root.winfo_children():
        widget.destroy()

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        font=("Times New Roman", 12),
        rowheight=34,
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

    app = {
        "root": root,
        "ql": DataStore(),
        "container": None,
        "content_canvas": None,
        "tv_hdv": None,
        "tv_tour": None,
        "tv_booking": None,
        "tv_users": None,
        "status_var": tk.StringVar(value="Hệ thống đã sẵn sàng"),
        "status_label": None,
        "search_hdv_var": tk.StringVar(),
        "search_user_var": tk.StringVar(),
        "search_tour_var": tk.StringVar(),
        "search_booking_var": tk.StringVar(),
        "search_voucher_var": tk.StringVar(),
        "search_feedback_var": tk.StringVar(),
        "page_title_var": tk.StringVar(value="Tổng quan Dashboard"),
        "page_subtitle_var": tk.StringVar(value="Theo dõi nhanh hoạt động tour, nhân sự và booking của hệ thống."),
        "active_menu_btn": None,
        "current_tab": "dashboard",
        "status_badge": None,
        "login_time": datetime.now(),
        "login_time_var": tk.StringVar(),
    }

    app["login_time_var"].set(
        "Đăng nhập lúc: " + app["login_time"].strftime("%d/%m/%Y - %H:%M:%S")
    )

    sidebar = tk.Frame(root, bg="#071224", width=300)
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
        text="Admin Control Center",
        justify="left",
        anchor="w",
        bg="#071224",
        fg="#93c5fd",
        font=("Times New Roman", 11, "italic"),
    ).pack(fill="x", pady=(2, 0))

    admin_info = app["ql"].data.get("admin", {})
    account_card = tk.Frame(sidebar, bg="#111b30", highlightbackground="#243450", highlightthickness=1)
    account_card.pack(fill="x", padx=16, pady=(8, 12))
    tk.Label(
        account_card,
        text="TÀI KHOẢN QUẢN TRỊ",
        bg="#111b30",
        fg="#dbeafe",
        font=("Times New Roman", 11, "bold"),
    ).pack(fill="x", pady=(12, 2))
    tk.Label(
        account_card,
        text=f"{admin_info.get('fullname', 'Quản trị viên')}",
        bg="#111b30",
        fg="white",
        font=("Times New Roman", 13, "bold"),
        pady=4,
    ).pack(fill="x")
    tk.Label(
        account_card,
        text=f"Username: {admin_info.get('username', 'admin')}",
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

# Khung menu có thể cuộn
    menu_shell = tk.Frame(sidebar, bg="#071224")
    menu_shell.pack(fill="both", expand=True, padx=12, pady=(4, 0))

    menu_canvas = tk.Canvas(
        menu_shell,
        bg="#071224",
        highlightthickness=0,
        bd=0
    )
    menu_scroll = ttk.Scrollbar(menu_shell, orient="vertical", command=menu_canvas.yview)
    menu_canvas.configure(yscrollcommand=menu_scroll.set)

    menu_scroll.pack(side="right", fill="y")
    menu_canvas.pack(side="left", fill="both", expand=True)

    menu = tk.Frame(menu_canvas, bg="#071224")
    menu_window = menu_canvas.create_window((0, 0), window=menu, anchor="nw")

    def _on_menu_configure(event=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_menu_configure` ( on menu configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        menu_canvas.configure(scrollregion=menu_canvas.bbox("all"))

    def _on_menu_canvas_configure(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_menu_canvas_configure` ( on menu canvas configure).
        Tham số:
            event: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        menu_canvas.itemconfigure(menu_window, width=event.width)

    menu.bind("<Configure>", _on_menu_configure)
    menu_canvas.bind("<Configure>", _on_menu_canvas_configure)

    def _on_sidebar_mousewheel(event):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `_on_sidebar_mousewheel` ( on sidebar mousewheel).
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
            menu_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except (tk.TclError, ValueError, AttributeError):
            pass

    menu_canvas.bind("<Enter>", lambda _e: menu_canvas.bind_all("<MouseWheel>", _on_sidebar_mousewheel))
    menu_canvas.bind("<Leave>", lambda _e: menu_canvas.unbind_all("<MouseWheel>"))

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

    def set_page(title, subtitle, current_tab):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `set_page` (set page).
        Tham số:
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            subtitle: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            current_tab: Tham số đầu vào phục vụ nghiệp vụ của hàm.
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
        text="Trạng thái hệ thống",
        bg=THEME["header_bg"],
        fg=THEME["muted"],
        font=("Times New Roman", 10, "bold"),
    ).pack(anchor="e")
    header_badge = tk.Label(
        head_right,
        text="ADMIN",
        bg="#dbeafe",
        fg="#1d4ed8",
        font=("Times New Roman", 11, "bold"),
        padx=14,
        pady=7,
    )
    header_badge.pack(anchor="e", pady=(6, 8))

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

    def open_view(title, subtitle, current_tab, view_fn, button):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `open_view` (open view).
        Tham số:
            title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            subtitle: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            current_tab: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            view_fn: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            button: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        set_page(title, subtitle, current_tab)
        set_active_menu(button)
        view_fn()

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
        reload_admin_current_tab(app)

    style_button(head_right, "Tải lại", THEME["primary"], reload_current_page).pack(anchor="e")

    tab_definitions = get_admin_tab_definitions()
    nav_specs = [
        (
            tab_def.title,
            tab_def.subtitle,
            tab_def.key,
            (lambda key=tab_def.key: get_admin_tab_handler(key)(app)),
            tab_def.icon,
        )
        for tab_def in tab_definitions
    ]

    nav_buttons = []
    for idx, (title, subtitle, current_tab, fn, icon) in enumerate(nav_specs):
        btn = menu_btn(
            title,
            lambda t=title, s=subtitle, c=current_tab, f=fn, i=idx: open_view(t, s, c, f, nav_buttons[i]),
            icon=icon,
        )
        btn.pack(fill="x", pady=2)
        nav_buttons.append(btn)

    util = tk.Frame(sidebar, bg="#071224")
    util.pack(side="bottom", fill="x", padx=12, pady=14)
    style_button(util, "Đăng xuất hệ thống", "#7f1d1d", lambda: logout(app)).pack(fill="x")

    first_tab = tab_definitions[0]
    open_view(
        first_tab.title,
        first_tab.subtitle,
        first_tab.key,
        lambda: get_admin_tab_handler(first_tab.key)(app),
        nav_buttons[0],
    )

    if root is not None and not isinstance(root, tk.Tk):
        return
    root.mainloop()


if __name__ == "__main__":
    main()
