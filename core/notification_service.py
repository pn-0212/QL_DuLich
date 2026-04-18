from __future__ import annotations

from datetime import datetime


EVENT_BOOKING_CREATED = "booking_created"
EVENT_PAYMENT_SUCCESS = "payment_success"
EVENT_TOUR_CANCELLED = "tour_cancelled"
EVENT_GUIDE_ASSIGNED = "guide_assigned"
EVENT_TOUR_COMPLETED = "tour_completed"


def _notifications(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_notifications` ( notifications).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return getattr(datastore, "list_notifications", datastore.notifications)


def _tour_name(datastore, ma_tour: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_tour_name` ( tour name).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
    if not isinstance(tour, dict):
        return ""
    return str(tour.get("ten", "")).strip()


def _guide_name(datastore, ma_hdv: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_guide_name` ( guide name).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    guide = datastore.find_hdv(ma_hdv) if hasattr(datastore, "find_hdv") else None
    if not isinstance(guide, dict):
        return ""
    return str(guide.get("tenHDV", "")).strip()


def emit_notification(
    datastore,
    *,
    event_type: str,
    content: str,
    ma_tour: str = "",
    ma_hdv: str = "",
    persist: bool = False,
) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `emit_notification` (emit notification).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        event_type: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        content: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    payload = {
        "eventType": str(event_type or "").strip(),
        "maHDV": str(ma_hdv or "").strip(),
        "tenHDV": _guide_name(datastore, ma_hdv),
        "maTour": str(ma_tour or "").strip(),
        "tenTour": _tour_name(datastore, ma_tour),
        "content": str(content or "").strip(),
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    _notifications(datastore).append(payload)
    if persist:
        datastore.save()
    return payload


def notify_booking_created(datastore, booking: dict, tour: dict, *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_booking_created` (notify booking created).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return emit_notification(
        datastore,
        event_type=EVENT_BOOKING_CREATED,
        ma_tour=str(booking.get("maTour", "")),
        ma_hdv=str(tour.get("hdvPhuTrach", "")),
        content=(
            f"Booking {booking.get('maBooking', '')} vừa được tạo cho tour "
            f"{tour.get('ten', booking.get('maTour', ''))}."
        ),
        persist=persist,
    )


def notify_payment_success(datastore, booking: dict, *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_payment_success` (notify payment success).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return emit_notification(
        datastore,
        event_type=EVENT_PAYMENT_SUCCESS,
        ma_tour=str(booking.get("maTour", "")),
        content=(
            f"Booking {booking.get('maBooking', '')} đã thanh toán "
            f"{int(booking.get('daThanhToan', 0)):,}đ.".replace(",", ".")
        ),
        persist=persist,
    )


def notify_tour_cancelled(datastore, tour: dict, reason: str = "", *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_tour_cancelled` (notify tour cancelled).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        reason: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    detail = f" Lý do: {reason.strip()}" if str(reason or "").strip() else ""
    return emit_notification(
        datastore,
        event_type=EVENT_TOUR_CANCELLED,
        ma_tour=str(tour.get("ma", "")),
        ma_hdv=str(tour.get("hdvPhuTrach", "")),
        content=f"Tour {tour.get('ten', tour.get('ma', ''))} đã bị hủy.{detail}",
        persist=persist,
    )


def notify_guide_assigned(datastore, tour: dict, guide: dict, *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_guide_assigned` (notify guide assigned).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        guide: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return emit_notification(
        datastore,
        event_type=EVENT_GUIDE_ASSIGNED,
        ma_tour=str(tour.get("ma", "")),
        ma_hdv=str(guide.get("maHDV", "")),
        content=(
            f"HDV {guide.get('tenHDV', guide.get('maHDV', ''))} được phân công cho "
            f"tour {tour.get('ten', tour.get('ma', ''))}."
        ),
        persist=persist,
    )


def notify_tour_completed(datastore, tour: dict, *, persist: bool = False) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `notify_tour_completed` (notify tour completed).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        persist: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return emit_notification(
        datastore,
        event_type=EVENT_TOUR_COMPLETED,
        ma_tour=str(tour.get("ma", "")),
        ma_hdv=str(tour.get("hdvPhuTrach", "")),
        content=f"Tour {tour.get('ten', tour.get('ma', ''))} đã hoàn tất.",
        persist=persist,
    )

