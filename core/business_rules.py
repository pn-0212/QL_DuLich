from __future__ import annotations

from core.state_machine import (
    BOOKING_STATE_CANCELLED,
    BOOKING_STATE_COMPLETED,
    BOOKING_STATE_CONFIRMED,
    BOOKING_STATE_PENDING,
    BOOKING_STATE_PAID,
    DISPLAY_BOOKING_STATUS_CANCELLED,
    DISPLAY_BOOKING_STATUS_COMPLETED,
    DISPLAY_BOOKING_STATUS_REFUND_PENDING,
    DISPLAY_GUIDE_STATUS,
    GUIDE_STATE_ASSIGNED,
    GUIDE_STATE_AVAILABLE,
    GUIDE_STATE_BUSY,
    GUIDE_STATE_INACTIVE,
    TOUR_STATE_CANCELLED,
    TOUR_STATE_COMPLETED,
    booking_state_from_status,
    guide_state_from_status,
    tour_state_from_status,
)


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


def normalize_business_state(data: dict) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_business_state` (normalize business state).
    Tham số:
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not isinstance(data, dict):
        return data

    data.setdefault("tours", [])
    data.setdefault("bookings", [])
    data.setdefault("hdv", [])

    tours_by_code = {}
    for tour in data["tours"]:
        ma_tour = str(tour.get("ma", "")).strip()
        if not ma_tour:
            continue
        tour["tourState"] = tour_state_from_status(str(tour.get("trangThai", "")).strip())
        tours_by_code[ma_tour] = tour

    for booking in data["bookings"]:
        booking_state = booking_state_from_status(
            str(booking.get("trangThai", "")).strip(),
            str(booking.get("trangThaiHoanTien", "")).strip(),
        )
        tour = tours_by_code.get(str(booking.get("maTour", "")).strip())
        if tour:
            tour_state = tour.get("tourState", "")
            paid_amount = max(0, _safe_int(booking.get("daThanhToan", 0)))

            if tour_state == TOUR_STATE_CANCELLED and booking_state in {
                BOOKING_STATE_PENDING,
                BOOKING_STATE_CONFIRMED,
                BOOKING_STATE_PAID,
                BOOKING_STATE_COMPLETED,
            }:
                if paid_amount > 0:
                    booking["trangThai"] = DISPLAY_BOOKING_STATUS_REFUND_PENDING
                    booking["trangThaiHoanTien"] = "Chờ duyệt"
                    booking["soTienHoan"] = max(_safe_int(booking.get("soTienHoan", 0)), paid_amount)
                else:
                    booking["trangThai"] = DISPLAY_BOOKING_STATUS_CANCELLED
                    booking["trangThaiHoanTien"] = ""
                    booking["soTienHoan"] = 0
            elif tour_state == TOUR_STATE_COMPLETED and booking_state in {
                BOOKING_STATE_CONFIRMED,
                BOOKING_STATE_PAID,
            }:
                booking["trangThai"] = DISPLAY_BOOKING_STATUS_COMPLETED
                booking["trangThaiHoanTien"] = ""
                booking["soTienHoan"] = 0
        booking["bookingState"] = booking_state_from_status(
            str(booking.get("trangThai", "")).strip(),
            str(booking.get("trangThaiHoanTien", "")).strip(),
        )

    assignments: dict[str, str] = {}
    for tour in data["tours"]:
        ma_hdv = str(tour.get("hdvPhuTrach", "")).strip()
        if not ma_hdv:
            continue
        tour_state = tour.get("tourState", tour_state_from_status(tour.get("trangThai", "")))
        if tour_state in {TOUR_STATE_CANCELLED, TOUR_STATE_COMPLETED}:
            continue
        current = assignments.get(ma_hdv, GUIDE_STATE_AVAILABLE)
        if tour_state == "ongoing":
            assignments[ma_hdv] = GUIDE_STATE_BUSY
        elif current != GUIDE_STATE_BUSY:
            assignments[ma_hdv] = GUIDE_STATE_ASSIGNED

    for guide in data["hdv"]:
        ma_hdv = str(guide.get("maHDV", "")).strip()
        existing_state = guide_state_from_status(str(guide.get("trangThai", "")).strip())
        if existing_state == GUIDE_STATE_INACTIVE:
            guide_state = GUIDE_STATE_INACTIVE
        else:
            guide_state = assignments.get(ma_hdv, GUIDE_STATE_AVAILABLE)

        guide["guideState"] = guide_state
        guide["trangThai"] = DISPLAY_GUIDE_STATUS.get(guide_state, guide.get("trangThai", "Sẵn sàng"))

    for tour in data["tours"]:
        if "tourState" not in tour:
            tour["tourState"] = tour_state_from_status(str(tour.get("trangThai", "")).strip())

    return data
