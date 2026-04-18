from __future__ import annotations

import base64
import math
import os
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from urllib.request import urlopen

import tkinter as tk

from GUI.Khach.features.validation import safe_int

TRANSFER_QR_CONFIG = {
    "bank_id": os.getenv("TRAVEL_BANK_ID", "ACB"),
    "account_no": os.getenv("TRAVEL_BANK_ACCOUNT", "41389377"),
    "account_name": os.getenv("TRAVEL_BANK_NAME", "VIETNAM TRAVEL"),
    "template": os.getenv("TRAVEL_QR_TEMPLATE", "compact"),
}


def build_cash_policy_notice(ngay_khoi_hanh):
    """
    Mục đích:
        Tạo thông báo chính sách thanh toán tiền mặt cho booking.
    Tham số:
        ngay_khoi_hanh: Ngày khởi hành của tour (định dạng `dd/mm/YYYY`).
    Giá trị trả về:
        Chuỗi thông báo tiếng Việt cho giao diện khách.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Deadline thanh toán/đặt cọc bằng tiền mặt là trước ngày khởi hành 15 ngày.
    """
    base_msg = "Tiền mặt: nếu chưa đặt cọc/thanh toán trước hạn, booking sẽ bị hủy tự động."
    try:
        depart_date = datetime.strptime(str(ngay_khoi_hanh or "").strip(), "%d/%m/%Y")
        deadline = (depart_date - timedelta(days=15)).strftime("%d/%m/%Y")
        return f"Tiền mặt: hạn chót đặt cọc/thanh toán là {deadline}. Booking quá hạn sẽ bị hủy."
    except ValueError:
        return base_msg


def short_ui_error(exc, fallback="Không thể gọi API QR. Vui lòng thử lại sau."):
    """
    Mục đích:
        Rút gọn thông báo lỗi kỹ thuật để hiển thị gọn trên UI.
    Tham số:
        exc: Exception gốc.
        fallback: Nội dung mặc định khi không có thông điệp lỗi.
    Giá trị trả về:
        Chuỗi lỗi đã chuẩn hóa độ dài.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Tránh hiển thị stack trace dài gây khó hiểu cho người dùng cuối.
    """
    text = " ".join(str(exc or "").split())
    if not text:
        return fallback
    return f"{text[:96]}..." if len(text) > 96 else text


def build_transfer_qr_url(amount, transfer_content):
    """
    Mục đích:
        Dựng URL QR chuyển khoản theo cấu hình ngân hàng hiện tại.
    Tham số:
        amount: Số tiền cần thanh toán.
        transfer_content: Nội dung chuyển khoản.
    Giá trị trả về:
        URL ảnh QR từ dịch vụ VietQR.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Thiếu mã ngân hàng hoặc số tài khoản sẽ chặn thanh toán chuyển khoản.
    """
    bank_id = str(TRANSFER_QR_CONFIG.get("bank_id", "")).strip()
    account_no = str(TRANSFER_QR_CONFIG.get("account_no", "")).strip()
    account_name = str(TRANSFER_QR_CONFIG.get("account_name", "")).strip()
    template = str(TRANSFER_QR_CONFIG.get("template", "compact2")).strip() or "compact2"

    if not bank_id or not account_no:
        raise ValueError("Thiếu cấu hình ngân hàng nhận chuyển khoản.")

    amount_value = max(0, safe_int(amount))
    add_info = quote_plus(str(transfer_content or "").strip())
    account_name_q = quote_plus(account_name)
    return (
        f"https://img.vietqr.io/image/{bank_id}-{account_no}-{template}.png"
        f"?amount={amount_value}&addInfo={add_info}&accountName={account_name_q}"
    )


def scale_photo_to_square(photo, max_size_px=220):
    """
    Mục đích:
        Thu nhỏ ảnh QR theo khung vuông tối đa để hiển thị ổn định trên UI.
    Tham số:
        photo: Đối tượng `tk.PhotoImage`.
        max_size_px: Kích thước tối đa theo pixel.
    Giá trị trả về:
        Ảnh đã scale (hoặc ảnh gốc nếu đã nhỏ hơn ngưỡng).
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Hàm dùng subsample để giảm tải render khi popup thanh toán mở nhiều lần.
    """
    max_size = max(80, safe_int(max_size_px))
    width = max(1, photo.width())
    height = max(1, photo.height())
    ratio = max(width / max_size, height / max_size)
    step = max(1, math.ceil(ratio))
    if step > 1:
        return photo.subsample(step, step)
    return photo


def fetch_transfer_qr_photo(qr_url, max_size_px=220):
    """
    Mục đích:
        Tải ảnh QR từ URL và chuyển thành `tk.PhotoImage` để hiển thị.
    Tham số:
        qr_url: Đường dẫn QR cần tải.
        max_size_px: Kích thước tối đa cho ảnh sau khi scale.
    Giá trị trả về:
        Đối tượng `tk.PhotoImage` đã sẵn sàng hiển thị.
    Tác dụng phụ:
        Gọi mạng ra ngoài để tải dữ liệu ảnh.
    Lưu ý nghiệp vụ:
        Nếu API QR trả payload rỗng thì xem như lỗi nghiệp vụ thanh toán.
    """
    with urlopen(qr_url, timeout=10) as response:
        payload = response.read()
    if not payload:
        raise ValueError("API QR không trả dữ liệu ảnh.")
    raw_photo = tk.PhotoImage(data=base64.b64encode(payload).decode("ascii"))
    return scale_photo_to_square(raw_photo, max_size_px)
