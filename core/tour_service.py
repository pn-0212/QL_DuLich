from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.crud_logging import write_crud_log
from core.notification_service import (
    notify_guide_assigned,
    notify_tour_cancelled,
    notify_tour_completed,
)
from core.state_machine import (
    BOOKING_STATE_CANCELLED,
    BOOKING_STATE_COMPLETED,
    BOOKING_STATE_CONFIRMED,
    BOOKING_STATE_PAID,
    BOOKING_STATE_REFUNDED,
    booking_state_from_status,
)


@dataclass(slots=True)
class TourResult:
    success: bool
    message: str
    tour: dict | None = None
    level: str = "info"


def _safe_int(value, default: int = 0) -> int:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_safe_int` ( safe int).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _parse_ddmmyyyy(value: str | None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_parse_ddmmyyyy` ( parse ddmmyyyy).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def _is_overlapped(tour_a: dict, tour_b: dict) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_is_overlapped` ( is overlapped).
    Tham số:
        tour_a: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour_b: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    start_a = _parse_ddmmyyyy(tour_a.get("ngay"))
    end_a = _parse_ddmmyyyy(tour_a.get("ngayKetThuc")) or start_a
    start_b = _parse_ddmmyyyy(tour_b.get("ngay"))
    end_b = _parse_ddmmyyyy(tour_b.get("ngayKetThuc")) or start_b
    if not start_a or not end_a or not start_b or not end_b:
        return False
    return start_a <= end_b and start_b <= end_a


def _bookings(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_bookings` ( bookings).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return getattr(datastore, "list_bookings", datastore.data.get("bookings", []))


def assign_guide(datastore, ma_tour: str, ma_hdv: str, actor: str = "admin") -> TourResult:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `assign_guide` (assign guide).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return TourResult(False, "Không tìm thấy tour cần phân công.", level="error")

    guide = datastore.find_hdv(ma_hdv) if hasattr(datastore, "find_hdv") else None
    if not isinstance(guide, dict):
        return TourResult(False, "Không tìm thấy hướng dẫn viên.", level="error")

    if str(guide.get("trangThai", "")).strip() == "Tạm nghỉ":
        return TourResult(False, "Hướng dẫn viên đang tạm nghỉ, không thể phân công.", level="warning")

    active_statuses = {"Giữ chỗ", "Mở bán", "Đã chốt đoàn", "Chờ khởi hành", "Đang đi"}
    for other_tour in getattr(datastore, "list_tours", datastore.data.get("tours", [])):
        if str(other_tour.get("ma", "")).strip() == str(ma_tour or "").strip():
            continue
        if str(other_tour.get("hdvPhuTrach", "")).strip() != str(ma_hdv or "").strip():
            continue
        if str(other_tour.get("trangThai", "")).strip() not in active_statuses:
            continue
        if _is_overlapped(tour, other_tour):
            return TourResult(
                False,
                f"HDV {ma_hdv} đang có tour trùng lịch ({other_tour.get('ma', '')}).",
                level="warning",
            )

    tour["hdvPhuTrach"] = str(ma_hdv or "").strip()
    notify_guide_assigned(datastore, tour, guide, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=str(actor or "admin").strip() or "admin",
        role="admin",
        entity="tour",
        operation="assign_guide",
        target=str(tour.get("ma", "")),
        detail=f"Gán HDV {ma_hdv} cho tour",
    )
    return TourResult(True, f"Đã phân công HDV {ma_hdv} cho tour {tour.get('ma', '')}.", tour=tour)


def cancel_tour(datastore, ma_tour: str, actor: str = "admin", reason: str = "") -> TourResult:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `cancel_tour` (cancel tour).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        reason: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return TourResult(False, "Không tìm thấy tour cần hủy.", level="error")

    tour["trangThai"] = "Đã hủy"
    if str(reason or "").strip():
        old_note = str(tour.get("ghiChuDieuHanh", "") or "").strip()
        tour["ghiChuDieuHanh"] = f"{old_note} [HỦY TOUR] {reason}".strip()

    pending_refunds = 0
    cancelled_free = 0
    for booking in _bookings(datastore):
        if str(booking.get("maTour", "")).strip() != str(ma_tour or "").strip():
            continue
        booking_state = booking_state_from_status(
            str(booking.get("trangThai", "")).strip(),
            str(booking.get("trangThaiHoanTien", "")).strip(),
        )
        if booking_state in {BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED}:
            continue

        paid = max(0, _safe_int(booking.get("daThanhToan", 0)))
        if paid > 0:
            booking["trangThai"] = "Chờ hoàn tiền"
            booking["trangThaiHoanTien"] = "Chờ duyệt"
            booking["soTienHoan"] = max(_safe_int(booking.get("soTienHoan", 0)), paid)
            booking["ngayYeuCauHoanTien"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            pending_refunds += 1
        else:
            booking["trangThai"] = "Đã hủy"
            booking["trangThaiHoanTien"] = ""
            booking["soTienHoan"] = 0
            cancelled_free += 1

    notify_tour_cancelled(datastore, tour, reason=reason, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=str(actor or "admin").strip() or "admin",
        role="admin",
        entity="tour",
        operation="cancel",
        target=str(tour.get("ma", "")),
        detail=f"Hủy tour | Chờ hoàn: {pending_refunds} | Hủy không hoàn: {cancelled_free}",
    )

    return TourResult(
        True,
        f"Đã hủy tour {tour.get('ma', '')}. Booking chờ hoàn: {pending_refunds}, booking hủy thẳng: {cancelled_free}.",
        tour=tour,
    )


def complete_tour(datastore, ma_tour: str, actor: str = "guide", note: str = "") -> TourResult:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `complete_tour` (complete tour).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return TourResult(False, "Không tìm thấy tour cần hoàn tất.", level="error")

    tour["trangThai"] = "Hoàn tất"
    if str(note or "").strip():
        old_note = str(tour.get("ghiChuDieuHanh", "") or "").strip()
        tour["ghiChuDieuHanh"] = f"{old_note} [HOÀN TẤT] {note}".strip()

    completed_count = 0
    for booking in _bookings(datastore):
        if str(booking.get("maTour", "")).strip() != str(ma_tour or "").strip():
            continue
        booking_state = booking_state_from_status(
            str(booking.get("trangThai", "")).strip(),
            str(booking.get("trangThaiHoanTien", "")).strip(),
        )
        if booking_state not in {BOOKING_STATE_CONFIRMED, BOOKING_STATE_PAID}:
            continue
        booking["trangThai"] = "Đã hoàn thành"
        booking["trangThaiHoanTien"] = ""
        booking["soTienHoan"] = 0
        completed_count += 1

    notify_tour_completed(datastore, tour, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=str(actor or "system").strip() or "system",
        role="guide" if actor != "admin" else "admin",
        entity="tour",
        operation="complete",
        target=str(tour.get("ma", "")),
        detail=f"Đóng tour, đánh dấu completed {completed_count} booking",
    )
    return TourResult(True, f"Đã hoàn tất tour {tour.get('ma', '')}.", tour=tour)
