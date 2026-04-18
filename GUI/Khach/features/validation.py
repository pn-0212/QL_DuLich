from __future__ import annotations

from core.validation import (
    is_valid_fullname as core_is_valid_fullname,
    is_valid_password as core_is_valid_password,
    is_valid_phone as core_is_valid_phone,
)


def is_valid_phone(phone):
    """
    Mục đích:
        Kiểm tra số điện thoại theo bộ quy tắc validation dùng chung.
    Tham số:
        phone: Giá trị số điện thoại người dùng nhập.
    Giá trị trả về:
        `True` nếu hợp lệ, ngược lại `False`.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Hàm chỉ ủy quyền sang tầng `core.validation` để đảm bảo đồng nhất rule.
    """
    return core_is_valid_phone(phone)


def is_valid_password(password):
    """
    Mục đích:
        Kiểm tra mật khẩu theo chuẩn tối thiểu của hệ thống.
    Tham số:
        password: Mật khẩu thô từ giao diện.
    Giá trị trả về:
        `True` nếu đạt chuẩn, ngược lại `False`.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Rule hiện tại được quản lý tập trung ở `core.validation`.
    """
    return core_is_valid_password(password)


def is_valid_fullname(fullname):
    """
    Mục đích:
        Kiểm tra họ tên khách hàng trước khi ghi dữ liệu.
    Tham số:
        fullname: Họ tên người dùng nhập.
    Giá trị trả về:
        `True` nếu hợp lệ, ngược lại `False`.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Hàm dùng chung rule với luồng đăng ký/đăng nhập ở các màn khác.
    """
    return core_is_valid_fullname(fullname)


def safe_int(value):
    """
    Mục đích:
        Chuyển giá trị bất kỳ sang số nguyên an toàn cho xử lý UI.
    Tham số:
        value: Giá trị đầu vào cần ép kiểu.
    Giá trị trả về:
        Số nguyên hợp lệ, hoặc `0` khi không chuyển được.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Dùng để tránh vỡ giao diện khi dữ liệu số bị rỗng/sai kiểu.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def booking_payment_status(total_amount, paid_amount):
    """
    Mục đích:
        Suy ra trạng thái thanh toán booking từ tổng tiền và số tiền đã thu.
    Tham số:
        total_amount: Tổng tiền booking.
        paid_amount: Số tiền đã thanh toán.
    Giá trị trả về:
        Chuỗi trạng thái thanh toán tiếng Việt.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Trạng thái trả về phải đồng bộ với màn quản lý booking.
    """
    total = max(0, safe_int(total_amount))
    paid = max(0, safe_int(paid_amount))
    if paid <= 0:
        return "Mới tạo"
    if total > 0 and paid < total:
        return "Đã cọc"
    return "Đã thanh toán"
