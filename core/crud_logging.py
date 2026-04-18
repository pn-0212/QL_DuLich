from __future__ import annotations

from core.activity_log import write_activity_log


def collect_changed_fields(before: dict | None, after: dict | None, keys: list[str] | None = None) -> list[str]:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `collect_changed_fields` (collect changed fields).
    Tham số:
        before: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        after: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    before = before or {}
    after = after or {}

    if keys is None:
        keys = sorted(set(before.keys()) | set(after.keys()))

    changes = []
    for key in keys:
        if before.get(key) != after.get(key):
            changes.append(key)
    return changes


def write_crud_log(
    *,
    datastore,
    actor: str,
    role: str,
    entity: str,
    operation: str,
    target: str = "",
    status: str = "SUCCESS",
    detail: str = "",
) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `write_crud_log` (write crud log).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        entity: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        operation: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        target: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        detail: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    entity_name = str(entity or "").strip().upper()
    operation_name = str(operation or "").strip().upper()
    target_name = str(target or "").strip()

    detail_parts = []
    if target_name:
        detail_parts.append(f"Mã đối tượng: {target_name}")
    if detail:
        detail_parts.append(str(detail).strip())

    write_activity_log(
        action=f"{operation_name}_{entity_name}",
        actor=str(actor or "system").strip() or "system",
        role=str(role or "system").strip() or "system",
        status=status,
        detail=" | ".join(detail_parts),
        datastore=datastore,
    )
