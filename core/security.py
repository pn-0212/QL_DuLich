from __future__ import annotations

import os
import hashlib
import re

import bcrypt

SHA256_PATTERN = re.compile(r"[a-fA-F0-9]{64}")
MASKED_PASSWORD = "********"
BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def legacy_sha256_hash(raw_password: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `legacy_sha256_hash` (legacy sha256 hash).
    Tham số:
        raw_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return hashlib.sha256(str(raw_password or "").encode("utf-8")).hexdigest()


def hash_password(raw_password: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `hash_password` (hash password).
    Tham số:
        raw_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    raw = str(raw_password or "").strip()
    if not raw:
        return ""
    try:
        configured_rounds = int(os.getenv("TRAVEL_BCRYPT_ROUNDS", "12"))
    except ValueError:
        configured_rounds = 12
    rounds = max(4, min(15, configured_rounds))
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def looks_like_sha256(value: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `looks_like_sha256` (looks like sha256).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return bool(SHA256_PATTERN.fullmatch(str(value).strip()))


def is_bcrypt_hash(value: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `is_bcrypt_hash` (is bcrypt hash).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = str(value or "").strip()
    return normalized.startswith(BCRYPT_PREFIXES)


def prepare_password_for_storage(password: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `prepare_password_for_storage` (prepare password for storage).
    Tham số:
        password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = str(password or "").strip()
    if not normalized:
        return ""
    if is_bcrypt_hash(normalized):
        return normalized
    if looks_like_sha256(normalized):
        return normalized
    return hash_password(normalized)


def password_matches(stored_password: str, input_password: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `password_matches` (password matches).
    Tham số:
        stored_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        input_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    stored = str(stored_password or "").strip()
    provided = str(input_password or "").strip()
    if not stored:
        return False
    if is_bcrypt_hash(stored):
        try:
            return bcrypt.checkpw(provided.encode("utf-8"), stored.encode("utf-8"))
        except ValueError:
            return False
    if looks_like_sha256(stored):
        return legacy_sha256_hash(provided) == stored
    return stored == provided


def upgrade_password_hash(stored_password: str, input_password: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `upgrade_password_hash` (upgrade password hash).
    Tham số:
        stored_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        input_password: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    stored = str(stored_password or "").strip()
    provided = str(input_password or "").strip()
    if not stored or not provided:
        return stored
    if is_bcrypt_hash(stored):
        return stored
    if password_matches(stored, provided):
        return hash_password(provided)
    return stored


def mask_password(_: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `mask_password` (mask password).
    Tham số:
        _: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return MASKED_PASSWORD
