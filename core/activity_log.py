from __future__ import annotations

import json
import os
from datetime import datetime


def _resolve_log_file(datastore=None, log_file: str | None = None) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_resolve_log_file` ( resolve log file).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        log_file: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if log_file:
        return log_file
    if datastore is not None and getattr(datastore, "path", None):
        return os.path.join(os.path.dirname(datastore.path), "activity_logs.json")
    return os.path.join(os.getcwd(), "activity_logs.json")


def _load_entries(path: str) -> list[dict]:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_load_entries` ( load entries).
    Tham số:
        path: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []

    return data if isinstance(data, list) else []


def write_activity_log(
    action: str,
    actor: str,
    role: str,
    status: str,
    detail: str = "",
    datastore=None,
    log_file: str | None = None,
) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `write_activity_log` (write activity log).
    Tham số:
        action: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        detail: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        log_file: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    path = _resolve_log_file(datastore=datastore, log_file=log_file)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    entries = _load_entries(path)
    entries.append(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "actor": actor,
            "role": role,
            "action": action,
            "status": status,
            "detail": detail,
        }
    )

    with open(path, "w", encoding="utf-8") as file:
        json.dump(entries[-1000:], file, ensure_ascii=False, indent=2)
