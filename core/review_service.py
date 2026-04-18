from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.state_machine import BOOKING_STATE_COMPLETED, booking_state_from_status


@dataclass(slots=True)
class ReviewResult:
    success: bool
    message: str
    review: dict | None = None
    level: str = "info"


def _find_booking(datastore, ma_booking: str):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_find_booking` ( find booking).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    target = str(ma_booking or "").strip()
    for booking in getattr(datastore, "list_bookings", datastore.data.get("bookings", [])):
        if str(booking.get("maBooking", "")).strip() == target:
            return booking
    return None


def _safe_float(value, default: float = 0.0) -> float:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_safe_float` ( safe float).
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
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _update_guide_metrics(datastore, ma_hdv: str, rating: float) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_update_guide_metrics` ( update guide metrics).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        rating: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not ma_hdv:
        return
    guide = datastore.find_hdv(ma_hdv) if hasattr(datastore, "find_hdv") else None
    if not isinstance(guide, dict):
        return

    total = int(guide.get("total_reviews", 0) or 0)
    avg = _safe_float(guide.get("avg_rating", 0), 0.0)
    guide["avg_rating"] = round(((avg * total) + rating) / (total + 1), 2)
    guide["total_reviews"] = total + 1


def create_review(
    datastore,
    *,
    username: str,
    fullname: str,
    ma_booking: str,
    content: str,
    target: str = "Tour",
    target_id: str = "",
    rating: float | None = None,
) -> ReviewResult:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `create_review` (create review).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        content: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        target: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        target_id: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        rating: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return ReviewResult(False, "Không tìm thấy booking để đánh giá.", level="error")

    owner = str(booking.get("usernameDat", "")).strip().lower()
    if owner and owner != str(username or "").strip().lower():
        return ReviewResult(False, "Bạn không có quyền đánh giá booking này.", level="warning")

    booking_state = booking_state_from_status(
        str(booking.get("trangThai", "")).strip(),
        str(booking.get("trangThaiHoanTien", "")).strip(),
    )
    if booking_state != BOOKING_STATE_COMPLETED:
        return ReviewResult(False, "Chỉ booking đã hoàn thành mới được đánh giá.", level="warning")

    normalized_content = str(content or "").strip()
    if not normalized_content:
        return ReviewResult(False, "Nội dung đánh giá không được để trống.", level="warning")

    booking_code = str(ma_booking or "").strip()
    normalized_user = str(username or "").strip().lower()
    for existing in getattr(datastore, "list_reviews", datastore.reviews):
        existing_booking = str(existing.get("maBooking", "")).strip()
        existing_user = str(existing.get("username", "")).strip().lower()
        if existing_booking == booking_code and existing_user == normalized_user:
            return ReviewResult(False, "Mỗi booking chỉ được đánh giá một lần.", level="warning")

    ma_tour = str(booking.get("maTour", "")).strip()
    if str(target or "").strip().lower() == "hdv":
        final_target = "HDV"
        if not target_id:
            tour = datastore.find_tour(ma_tour) if hasattr(datastore, "find_tour") else None
            target_id = str(tour.get("hdvPhuTrach", "")).strip() if isinstance(tour, dict) else ""
        if not target_id:
            return ReviewResult(False, "Tour này chưa có HDV để đánh giá.", level="warning")
        ma_hdv = str(target_id).strip()
    else:
        final_target = "Tour"
        ma_hdv = ""
        target_id = ma_tour

    final_rating = float(rating) if rating is not None else ""
    review = {
        "username": str(username or "").strip(),
        "fullname": str(fullname or "").strip() or str(booking.get("tenKhach", "")).strip(),
        "target": final_target,
        "target_id": str(target_id or "").strip(),
        "content": normalized_content,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "rating": final_rating,
        "maBooking": booking_code,
        "maTour": ma_tour,
        "maHDV": ma_hdv,
    }
    getattr(datastore, "list_reviews", datastore.reviews).append(review)

    if final_target == "HDV" and isinstance(final_rating, float):
        _update_guide_metrics(datastore, ma_hdv, final_rating)

    datastore.save()
    return ReviewResult(True, "Đã ghi nhận đánh giá thành công.", review=review)

