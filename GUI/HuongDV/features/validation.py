from __future__ import annotations

from core.validation import (
    is_valid_email as core_is_valid_email,
    is_valid_password as core_is_valid_password,
    is_valid_phone as core_is_valid_phone,
)


def is_valid_phone(phone):
    """
    Mục đích:
        Kiểm tra số điện thoại của HDV theo rule validation lõi.
    Tham số:
        phone: Chuỗi số điện thoại đầu vào.
    Giá trị trả về:
        `True` nếu hợp lệ, ngược lại `False`.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Rule đồng bộ với màn admin và khách để tránh sai lệch dữ liệu.
    """
    return core_is_valid_phone(phone)


def is_valid_email(email):
    """
    Mục đích:
        Kiểm tra định dạng email cho hồ sơ hướng dẫn viên.
    Tham số:
        email: Giá trị email đầu vào.
    Giá trị trả về:
        `True` nếu email hợp lệ, ngược lại `False`.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Hàm ủy quyền sang tầng lõi để giữ quy tắc chung.
    """
    return core_is_valid_email(email)


def is_valid_password(password):
    """
    Mục đích:
        Kiểm tra mật khẩu đầu vào cho tài khoản HDV.
    Tham số:
        password: Mật khẩu người dùng nhập.
    Giá trị trả về:
        `True` nếu đạt chuẩn, ngược lại `False`.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Điều kiện tối thiểu hiện do `core.validation` quản lý.
    """
    return core_is_valid_password(password)


def safe_int(value):
    """
    Mục đích:
        Ép kiểu an toàn sang số nguyên cho các trường số trên UI.
    Tham số:
        value: Giá trị cần ép kiểu.
    Giá trị trả về:
        Số nguyên tương ứng, hoặc `0` nếu không hợp lệ.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Tránh phát sinh exception làm gián đoạn thao tác form.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
