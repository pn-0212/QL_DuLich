from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.booking_pricing import calculate_age_discount, normalize_passenger_breakdown
from core.crud_logging import write_crud_log
from core.notification_service import notify_booking_created, notify_payment_success
from core.state_machine import (
    BOOKING_STATE_CANCELLED,
    BOOKING_STATE_COMPLETED,
    BOOKING_STATE_REFUNDED,
    booking_state_from_status,
)
from core.system_rules import CANCEL_BOOKING_STATUSES
from core.voucher_service import build_voucher_quote, safe_int


TOUR_BOOKABLE_STATUSES = {"Giữ chỗ", "Mở bán"}
TOUR_LOCK_CANCEL_STATUSES = {"Đã chốt đoàn", "Chờ khởi hành", "Đang đi", "Hoàn tất"}


@dataclass(slots=True)
class BookingResult:
    success: bool
    message: str
    booking: dict | None = None
    level: str = "info"


def _get_bookings(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_get_bookings` ( get bookings).
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


def _find_tour(datastore, ma_tour):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_find_tour` ( find tour).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    finder = getattr(datastore, "find_tour", None)
    if callable(finder):
        result = finder(ma_tour)
        if result:
            return result

    return next(
        (
            tour
            for tour in getattr(datastore, "list_tours", datastore.data.get("tours", []))
            if str(tour.get("ma", "")).strip() == str(ma_tour or "").strip()
        ),
        None,
    )


def _find_booking(datastore, ma_booking):
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
    return next(
        (
            booking
            for booking in _get_bookings(datastore)
            if str(booking.get("maBooking", "")).strip() == str(ma_booking or "").strip()
        ),
        None,
    )


def _next_booking_code(datastore) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_next_booking_code` ( next booking code).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    existing_ids = []
    for booking in _get_bookings(datastore):
        ma_booking = str(booking.get("maBooking", "")).strip().upper()
        if not ma_booking.startswith("BK"):
            continue
        try:
            existing_ids.append(int(ma_booking[2:]))
        except ValueError:
            continue
    return f"BK{max(existing_ids, default=0) + 1:02d}"


def _payment_status(total_amount, paid_amount):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_payment_status` ( payment status).
    Tham số:
        total_amount: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        paid_amount: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    total = max(0, safe_int(total_amount))
    paid = max(0, safe_int(paid_amount))
    if paid <= 0:
        return "Mới tạo"
    if total > 0 and paid < total:
        return "Đã cọc"
    return "Đã thanh toán"


def _occupied_seats(datastore, ma_tour):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_occupied_seats` ( occupied seats).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    getter = getattr(datastore, "get_occupied_seats", None)
    if callable(getter):
        return max(0, safe_int(getter(ma_tour)))

    total = 0
    for booking in _get_bookings(datastore):
        refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
        if booking.get("maTour") != ma_tour:
            continue
        if booking.get("trangThai") in CANCEL_BOOKING_STATUSES and refund_status != "Từ chối":
            continue
        total += max(0, safe_int(booking.get("soNguoi", 0)))
    return total


def create_booking(
    datastore,
    *,
    ma_tour,
    num_people,
    pay_now,
    payment_method,
    username,
    fullname,
    phone,
    voucher_code="",
    danh_sach_khach=None,
    passenger_breakdown=None,
    source="Khách lẻ",
    note="",
    actor="",
    role="user",
):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `create_booking` (create booking).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        num_people: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        pay_now: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        payment_method: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fullname: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        phone: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        voucher_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        danh_sach_khach: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        passenger_breakdown: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        source: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour = _find_tour(datastore, ma_tour)
    if not tour:
        return BookingResult(False, "Không tìm thấy tour đã chọn.", level="error")

    people = max(0, safe_int(num_people))
    if people <= 0:
        return BookingResult(False, "Số người đi không hợp lệ.", level="warning")

    status = str(tour.get("trangThai", "")).strip()
    if status not in TOUR_BOOKABLE_STATUSES:
        return BookingResult(False, f"Tour đang ở trạng thái '{status}', chưa thể đăng ký.", level="warning")

    occupied = _occupied_seats(datastore, ma_tour)
    capacity = max(1, safe_int(tour.get("khach", 1)))
    available = max(capacity - occupied, 0)
    if people > available:
        return BookingResult(False, f"Tour này chỉ còn {available} chỗ trống.", level="error")

    price_per_person = max(0, safe_int(tour.get("gia", 0)))
    gross_total = max(0, price_per_person * people)
    normalized_breakdown = normalize_passenger_breakdown(passenger_breakdown, people)
    if normalized_breakdown is None:
        return BookingResult(False, "Cơ cấu độ tuổi không hợp lệ (vượt quá tổng số người).", level="warning")

    age_discount = calculate_age_discount(price_per_person, normalized_breakdown)
    age_discount = max(0, min(gross_total, safe_int(age_discount)))
    subtotal_after_age_discount = max(gross_total - age_discount, 0)

    voucher_quote = build_voucher_quote(
        datastore,
        voucher_code,
        subtotal_after_age_discount,
        username=username,
        ma_tour=ma_tour,
    )
    if not voucher_quote["ok"]:
        return BookingResult(False, voucher_quote["message"], level="warning")

    total_after_discount = max(subtotal_after_age_discount - voucher_quote["discount"], 0)
    paid_now = max(0, safe_int(pay_now))
    if paid_now > total_after_discount:
        return BookingResult(False, "Số tiền thanh toán ngay không được lớn hơn tổng tiền sau giảm giá.", level="warning")

    applied_voucher = voucher_quote["voucher"] if voucher_quote["code"] else None
    booking = {
        "maBooking": _next_booking_code(datastore),
        "maTour": str(ma_tour).strip(),
        "tenKhach": str(fullname or "").strip(),
        "sdt": str(phone or "").strip(),
        "soNguoi": str(people),
        "trangThai": _payment_status(total_after_discount, paid_now),
        "ngayDat": datetime.now().strftime("%d/%m/%Y"),
        "tongTienGoc": gross_total,
        "giamGiaDoiTuong": age_discount,
        "tongTien": total_after_discount,
        "tienCoc": paid_now,
        "daThanhToan": paid_now,
        "conNo": max(total_after_discount - paid_now, 0),
        "hinhThucThanhToan": str(payment_method or "Tiền mặt").strip() or "Tiền mặt",
        "nguonKhach": str(source or "Khách lẻ").strip() or "Khách lẻ",
        "ghiChu": str(note or "").strip(),
        "usernameDat": str(username or "").strip(),
        "danhSachKhach": danh_sach_khach if isinstance(danh_sach_khach, list) else [],
        "coCauDoTuoi": normalized_breakdown,
        "maVoucher": voucher_quote["code"],
        "tenVoucher": applied_voucher.get("tenVoucher", "") if applied_voucher else "",
        "giamGiaVoucher": voucher_quote["discount"],
        "trangThaiHoanTien": "",
        "soTienHoan": 0,
        "ngayYeuCauHoanTien": "",
        "ngayXuLyHoanTien": "",
        "nguoiXuLyHoanTien": "",
        "ghiChuHoanTien": "",
    }

    _get_bookings(datastore).append(booking)
    notify_booking_created(datastore, booking, tour, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or username or "system",
        role=role,
        entity="booking",
        operation="create",
        target=booking["maBooking"],
        detail=f"Tạo booking cho tour {booking['maTour']} | Số người: {booking['soNguoi']} | Voucher: {booking['maVoucher'] or 'Không'}",
    )
    return BookingResult(True, "Tạo booking thành công.", booking=booking)


def apply_payment(datastore, ma_booking, pay_more, method, actor="", role="user"):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `apply_payment` (apply payment).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        pay_more: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        method: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return BookingResult(False, "Không tìm thấy booking cần thanh toán.", level="error")

    booking_state = booking_state_from_status(
        str(booking.get("trangThai", "")).strip(),
        str(booking.get("trangThaiHoanTien", "")).strip(),
    )
    if booking_state in {BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED, BOOKING_STATE_COMPLETED}:
        return BookingResult(False, "Booking này không thể thanh toán thêm.", level="warning")

    amount = max(0, safe_int(pay_more))
    if amount <= 0:
        return BookingResult(False, "Số tiền thanh toán thêm phải lớn hơn 0.", level="warning")

    total_amount = max(0, safe_int(booking.get("tongTien", 0)))
    paid_amount = max(0, safe_int(booking.get("daThanhToan", 0)))
    debt = max(total_amount - paid_amount, 0)
    if amount > debt:
        return BookingResult(False, "Số tiền thanh toán thêm không được vượt quá công nợ.", level="warning")

    booking["daThanhToan"] = paid_amount + amount
    if safe_int(booking.get("tienCoc", 0)) <= 0:
        booking["tienCoc"] = amount
    booking["conNo"] = max(total_amount - safe_int(booking.get("daThanhToan", 0)), 0)
    booking["hinhThucThanhToan"] = str(method or "Tiền mặt").strip() or "Tiền mặt"
    booking["trangThai"] = _payment_status(total_amount, booking["daThanhToan"])
    booking["trangThaiHoanTien"] = ""
    booking["soTienHoan"] = 0

    notify_payment_success(datastore, booking, persist=False)
    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or booking.get("usernameDat", "") or "system",
        role=role,
        entity="booking",
        operation="update",
        target=str(ma_booking or ""),
        detail=f"Thanh toán thêm {amount:,}đ bằng {booking['hinhThucThanhToan']}".replace(",", "."),
    )
    return BookingResult(True, f"Đã cập nhật thanh toán cho booking {ma_booking}.", booking=booking)


def cancel_booking(datastore, ma_booking, actor="", role="user", note=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `cancel_booking` (cancel booking).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        role: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return BookingResult(False, "Không tìm thấy booking cần hủy.", level="error")

    tour = _find_tour(datastore, booking.get("maTour"))
    if role == "user" and tour and str(tour.get("trangThai", "")).strip() in TOUR_LOCK_CANCEL_STATUSES:
        return BookingResult(
            False,
            f"Tour '{tour.get('ten', '')}' đang ở trạng thái '{tour.get('trangThai', '')}', bạn không thể tự hủy booking này.",
            level="warning",
        )

    current_status = str(booking.get("trangThai", "")).strip()
    booking_state = booking_state_from_status(
        current_status,
        str(booking.get("trangThaiHoanTien", "")).strip(),
    )
    if booking_state in {BOOKING_STATE_CANCELLED, BOOKING_STATE_REFUNDED}:
        return BookingResult(False, "Booking này đã ở trạng thái hủy hoặc hoàn tiền.", level="warning")
    if booking_state == BOOKING_STATE_COMPLETED:
        return BookingResult(False, "Booking đã hoàn thành nên không thể hủy.", level="warning")

    paid_amount = max(0, safe_int(booking.get("daThanhToan", 0)))
    if paid_amount > 0:
        booking["trangThai"] = "Chờ hoàn tiền"
        booking["trangThaiHoanTien"] = "Chờ duyệt"
        booking["soTienHoan"] = paid_amount
        booking["ngayYeuCauHoanTien"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        booking["ghiChuHoanTien"] = str(note or booking.get("ghiChuHoanTien", "") or "").strip()
    else:
        booking["trangThai"] = "Đã hủy"
        booking["trangThaiHoanTien"] = ""
        booking["soTienHoan"] = 0

    if note:
        existing_note = str(booking.get("ghiChu", "") or "").strip()
        booking["ghiChu"] = f"{existing_note} {note}".strip()

    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or booking.get("usernameDat", "") or "system",
        role=role,
        entity="booking",
        operation="update",
        target=str(ma_booking or ""),
        detail=f"Hủy booking | Trạng thái mới: {booking['trangThai']}",
    )
    return BookingResult(True, f"Đã cập nhật trạng thái booking {ma_booking} thành '{booking['trangThai']}'.", booking=booking)


def approve_refund(datastore, ma_booking, actor="", note=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `approve_refund` (approve refund).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return BookingResult(False, "Không tìm thấy booking cần duyệt hoàn tiền.", level="error")

    if str(booking.get("trangThai", "")).strip() != "Chờ hoàn tiền":
        return BookingResult(False, "Booking này không ở trạng thái chờ hoàn tiền.", level="warning")

    refund_amount = max(
        safe_int(booking.get("soTienHoan", 0)),
        safe_int(booking.get("daThanhToan", 0)),
    )
    booking["soTienHoan"] = refund_amount
    booking["trangThai"] = "Hoàn tiền"
    booking["trangThaiHoanTien"] = "Đã hoàn tiền"
    booking["ngayXuLyHoanTien"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    booking["nguoiXuLyHoanTien"] = str(actor or "admin").strip() or "admin"
    booking["ghiChuHoanTien"] = str(note or booking.get("ghiChuHoanTien", "") or "").strip()
    booking["daThanhToan"] = 0
    booking["tienCoc"] = 0
    booking["conNo"] = 0

    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or "admin",
        role="admin",
        entity="refund",
        operation="approve",
        target=str(ma_booking or ""),
        detail=f"Duyệt hoàn {refund_amount:,}đ".replace(",", "."),
    )
    return BookingResult(True, f"Đã duyệt hoàn tiền cho booking {ma_booking}.", booking=booking)


def reject_refund(datastore, ma_booking, actor="", note=""):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `reject_refund` (reject refund).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        actor: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        note: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    booking = _find_booking(datastore, ma_booking)
    if not booking:
        return BookingResult(False, "Không tìm thấy booking cần từ chối hoàn tiền.", level="error")

    if str(booking.get("trangThai", "")).strip() != "Chờ hoàn tiền":
        return BookingResult(False, "Booking này không ở trạng thái chờ hoàn tiền.", level="warning")

    booking["trangThai"] = "Đã hủy"
    booking["trangThaiHoanTien"] = "Từ chối"
    booking["ngayXuLyHoanTien"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    booking["nguoiXuLyHoanTien"] = str(actor or "admin").strip() or "admin"
    booking["ghiChuHoanTien"] = str(note or booking.get("ghiChuHoanTien", "") or "").strip()
    booking["conNo"] = 0

    datastore.save()

    write_crud_log(
        datastore=datastore,
        actor=actor or "admin",
        role="admin",
        entity="refund",
        operation="reject",
        target=str(ma_booking or ""),
        detail=booking["ghiChuHoanTien"] or "Từ chối yêu cầu hoàn tiền",
    )
    return BookingResult(True, f"Đã từ chối hoàn tiền cho booking {ma_booking}.", booking=booking)


def summarize_bookings_by_tour(datastore) -> list[dict]:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `summarize_bookings_by_tour` (summarize bookings by tour).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    rows = []
    tours = getattr(datastore, "list_tours", datastore.data.get("tours", []))

    for tour in tours:
        ma_tour = str(tour.get("ma", "")).strip()
        tour_bookings = [booking for booking in _get_bookings(datastore) if str(booking.get("maTour", "")).strip() == ma_tour]
        customers = set()
        guest_total = 0
        active_guest_total = 0
        total_revenue = 0
        collected = 0
        pending_refunds = 0

        for booking in tour_bookings:
            customer_key = (
                str(booking.get("usernameDat", "")).strip().lower()
                or str(booking.get("sdt", "")).strip()
                or str(booking.get("tenKhach", "")).strip().lower()
            )
            if customer_key:
                customers.add(customer_key)

            guest_total += max(0, safe_int(booking.get("soNguoi", 0)))
            collected += max(0, safe_int(booking.get("daThanhToan", 0)))

            refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
            if booking.get("trangThai") == "Chờ hoàn tiền":
                pending_refunds += 1
            if booking.get("trangThai") in CANCEL_BOOKING_STATUSES and refund_status != "Từ chối":
                continue

            active_guest_total += max(0, safe_int(booking.get("soNguoi", 0)))
            total_revenue += max(0, safe_int(booking.get("tongTien", 0)))

        capacity = max(1, safe_int(tour.get("khach", 1)))
        rows.append(
            {
                "maTour": ma_tour,
                "tenTour": str(tour.get("ten", "")).strip(),
                "trangThai": str(tour.get("trangThai", "")).strip(),
                "tongBooking": len(tour_bookings),
                "tongKhachHang": len(customers),
                "tongNguoi": guest_total,
                "khachHieuLuc": active_guest_total,
                "choConLai": max(capacity - active_guest_total, 0),
                "doanhThu": total_revenue,
                "daThu": collected,
                "choHoanTien": pending_refunds,
            }
        )

    return sorted(rows, key=lambda row: (row["maTour"], row["tenTour"]))
