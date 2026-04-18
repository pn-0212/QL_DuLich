from __future__ import annotations

from dataclasses import dataclass


TOUR_STATE_DRAFT = "draft"
TOUR_STATE_OPEN = "open"
TOUR_STATE_FULL = "full"
TOUR_STATE_ONGOING = "ongoing"
TOUR_STATE_COMPLETED = "completed"
TOUR_STATE_CANCELLED = "cancelled"

BOOKING_STATE_PENDING = "pending"
BOOKING_STATE_CONFIRMED = "confirmed"
BOOKING_STATE_PAID = "paid"
BOOKING_STATE_CANCELLED = "cancelled"
BOOKING_STATE_COMPLETED = "completed"
BOOKING_STATE_REFUNDED = "refunded"

GUIDE_STATE_AVAILABLE = "available"
GUIDE_STATE_ASSIGNED = "assigned"
GUIDE_STATE_BUSY = "busy"
GUIDE_STATE_INACTIVE = "inactive"


TOUR_STATE_BY_STATUS = {
    "nhap": TOUR_STATE_DRAFT,
    "nháp": TOUR_STATE_DRAFT,
    "giu cho": TOUR_STATE_OPEN,
    "giữ chỗ": TOUR_STATE_OPEN,
    "mo ban": TOUR_STATE_OPEN,
    "mở bán": TOUR_STATE_OPEN,
    "cho khoi hanh": TOUR_STATE_OPEN,
    "chờ khởi hành": TOUR_STATE_OPEN,
    "da chot doan": TOUR_STATE_FULL,
    "đã chốt đoàn": TOUR_STATE_FULL,
    "dang di": TOUR_STATE_ONGOING,
    "đang đi": TOUR_STATE_ONGOING,
    "hoan tat": TOUR_STATE_COMPLETED,
    "hoàn tất": TOUR_STATE_COMPLETED,
    "da huy": TOUR_STATE_CANCELLED,
    "đã hủy": TOUR_STATE_CANCELLED,
    "tam hoan": TOUR_STATE_CANCELLED,
    "tạm hoãn": TOUR_STATE_CANCELLED,
}

BOOKING_STATE_BY_STATUS = {
    "moi tao": BOOKING_STATE_PENDING,
    "mới tạo": BOOKING_STATE_PENDING,
    "da coc": BOOKING_STATE_CONFIRMED,
    "đã cọc": BOOKING_STATE_CONFIRMED,
    "da thanh toan": BOOKING_STATE_PAID,
    "đã thanh toán": BOOKING_STATE_PAID,
    "da huy": BOOKING_STATE_CANCELLED,
    "đã hủy": BOOKING_STATE_CANCELLED,
    "cho hoan tien": BOOKING_STATE_CANCELLED,
    "chờ hoàn tiền": BOOKING_STATE_CANCELLED,
    "hoan tien": BOOKING_STATE_REFUNDED,
    "hoàn tiền": BOOKING_STATE_REFUNDED,
    "da hoan thanh": BOOKING_STATE_COMPLETED,
    "đã hoàn thành": BOOKING_STATE_COMPLETED,
}

GUIDE_STATE_BY_STATUS = {
    "san sang": GUIDE_STATE_AVAILABLE,
    "sẵn sàng": GUIDE_STATE_AVAILABLE,
    "da phan cong": GUIDE_STATE_ASSIGNED,
    "đã phân công": GUIDE_STATE_ASSIGNED,
    "dang dan tour": GUIDE_STATE_BUSY,
    "đang dẫn tour": GUIDE_STATE_BUSY,
    "tam nghi": GUIDE_STATE_INACTIVE,
    "tạm nghỉ": GUIDE_STATE_INACTIVE,
}

DISPLAY_GUIDE_STATUS = {
    GUIDE_STATE_AVAILABLE: "Sẵn sàng",
    GUIDE_STATE_ASSIGNED: "Đã phân công",
    GUIDE_STATE_BUSY: "Đang dẫn tour",
    GUIDE_STATE_INACTIVE: "Tạm nghỉ",
}

DISPLAY_BOOKING_STATUS_COMPLETED = "Đã hoàn thành"
DISPLAY_BOOKING_STATUS_CANCELLED = "Đã hủy"
DISPLAY_BOOKING_STATUS_REFUND_PENDING = "Chờ hoàn tiền"
DISPLAY_BOOKING_STATUS_REFUNDED = "Hoàn tiền"


@dataclass(frozen=True)
class TransitionRule:
    state_from: str
    state_to: str


TOUR_TRANSITIONS = {
    TransitionRule(TOUR_STATE_DRAFT, TOUR_STATE_OPEN),
    TransitionRule(TOUR_STATE_OPEN, TOUR_STATE_FULL),
    TransitionRule(TOUR_STATE_OPEN, TOUR_STATE_ONGOING),
    TransitionRule(TOUR_STATE_OPEN, TOUR_STATE_CANCELLED),
    TransitionRule(TOUR_STATE_FULL, TOUR_STATE_ONGOING),
    TransitionRule(TOUR_STATE_FULL, TOUR_STATE_CANCELLED),
    TransitionRule(TOUR_STATE_ONGOING, TOUR_STATE_COMPLETED),
    TransitionRule(TOUR_STATE_ONGOING, TOUR_STATE_CANCELLED),
}

BOOKING_TRANSITIONS = {
    TransitionRule(BOOKING_STATE_PENDING, BOOKING_STATE_CONFIRMED),
    TransitionRule(BOOKING_STATE_PENDING, BOOKING_STATE_PAID),
    TransitionRule(BOOKING_STATE_PENDING, BOOKING_STATE_CANCELLED),
    TransitionRule(BOOKING_STATE_CONFIRMED, BOOKING_STATE_PAID),
    TransitionRule(BOOKING_STATE_CONFIRMED, BOOKING_STATE_CANCELLED),
    TransitionRule(BOOKING_STATE_PAID, BOOKING_STATE_COMPLETED),
    TransitionRule(BOOKING_STATE_PAID, BOOKING_STATE_CANCELLED),
    TransitionRule(BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED),
}

GUIDE_TRANSITIONS = {
    TransitionRule(GUIDE_STATE_AVAILABLE, GUIDE_STATE_ASSIGNED),
    TransitionRule(GUIDE_STATE_ASSIGNED, GUIDE_STATE_BUSY),
    TransitionRule(GUIDE_STATE_BUSY, GUIDE_STATE_AVAILABLE),
    TransitionRule(GUIDE_STATE_AVAILABLE, GUIDE_STATE_INACTIVE),
    TransitionRule(GUIDE_STATE_ASSIGNED, GUIDE_STATE_INACTIVE),
    TransitionRule(GUIDE_STATE_BUSY, GUIDE_STATE_INACTIVE),
    TransitionRule(GUIDE_STATE_INACTIVE, GUIDE_STATE_AVAILABLE),
}


def _normalize_key(value: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_key` ( normalize key).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return " ".join(str(value or "").strip().lower().split())


def tour_state_from_status(status: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `tour_state_from_status` (tour state from status).
    Tham số:
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return TOUR_STATE_BY_STATUS.get(_normalize_key(status), TOUR_STATE_OPEN)


def booking_state_from_status(status: str, refund_status: str = "") -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `booking_state_from_status` (booking state from status).
    Tham số:
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        refund_status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = _normalize_key(status)
    if normalized in BOOKING_STATE_BY_STATUS:
        return BOOKING_STATE_BY_STATUS[normalized]

    if _normalize_key(refund_status) in {"da hoan tien", "đã hoàn tiền"}:
        return BOOKING_STATE_REFUNDED
    return BOOKING_STATE_PENDING


def guide_state_from_status(status: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `guide_state_from_status` (guide state from status).
    Tham số:
        status: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return GUIDE_STATE_BY_STATUS.get(_normalize_key(status), GUIDE_STATE_AVAILABLE)


def can_tour_transition(state_from: str, state_to: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `can_tour_transition` (can tour transition).
    Tham số:
        state_from: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        state_to: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return TransitionRule(state_from, state_to) in TOUR_TRANSITIONS or state_from == state_to


def can_booking_transition(state_from: str, state_to: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `can_booking_transition` (can booking transition).
    Tham số:
        state_from: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        state_to: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return TransitionRule(state_from, state_to) in BOOKING_TRANSITIONS or state_from == state_to


def can_guide_transition(state_from: str, state_to: str) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `can_guide_transition` (can guide transition).
    Tham số:
        state_from: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        state_to: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return TransitionRule(state_from, state_to) in GUIDE_TRANSITIONS or state_from == state_to

