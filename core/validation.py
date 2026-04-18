from __future__ import annotations

import re

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_.-]{3,30}")
PHONE_PATTERN = re.compile(r"0\d{9}")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
VIETNAM_MOBILE_PREFIXES = {
    "032", "033", "034", "035", "036", "037", "038", "039",
    "052", "055", "056", "058", "059",
    "070", "076", "077", "078", "079",
    "081", "082", "083", "084", "085", "086", "087", "088", "089",
    "090", "091", "092", "093", "094", "096", "097", "098", "099",
}


def normalize_username(username: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_username` (normalize username).
    Tham số:
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return str(username or "").strip()


def normalize_fullname(fullname: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_fullname` (normalize fullname).
    Tham số:
        fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return " ".join(str(fullname or "").strip().split())


def normalize_phone(phone: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_phone` (normalize phone).
    Tham số:
        phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return str(phone or "").strip()


def is_valid_username(username: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_username` (is valid username).
    Tham số:
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return bool(USERNAME_PATTERN.fullmatch(normalize_username(username)))


def is_valid_password(password: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_password` (is valid password).
    Tham số:
        password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return len(str(password or "").strip()) >= 3


def is_valid_fullname(fullname: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_fullname` (is valid fullname).
    Tham số:
        fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return len(normalize_fullname(fullname)) >= 3


def is_valid_phone(phone: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_phone` (is valid phone).
    Tham số:
        phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    value = normalize_phone(phone)
    if not value:
        return True
    if not PHONE_PATTERN.fullmatch(value):
        return False
    return value[:3] in VIETNAM_MOBILE_PREFIXES


def is_valid_email(email: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_valid_email` (is valid email).
    Tham số:
        email: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return bool(EMAIL_PATTERN.fullmatch(str(email or "").strip()))
