from __future__ import annotations

from core.system_rules import CANCEL_BOOKING_STATUSES
from core.voucher_service import safe_int


def _iter_bookings(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_iter_bookings` ( iter bookings).
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


def _iter_tours(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_iter_tours` ( iter tours).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    return getattr(datastore, "list_tours", datastore.data.get("tours", []))


def _find_tour_name(datastore, ma_tour):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_find_tour_name` ( find tour name).
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
        tour = finder(ma_tour)
        if tour:
            return str(tour.get("ten", "")).strip()

    for tour in _iter_tours(datastore):
        if str(tour.get("ma", "")).strip() == str(ma_tour or "").strip():
            return str(tour.get("ten", "")).strip()
    return ""


def _revenue_booking(booking) -> bool:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_revenue_booking` ( revenue booking).
    Tham số:
        booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    status = str(booking.get("trangThai", "")).strip()
    refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
    if status == "Hoàn tiền":
        return False
    if status == "Chờ hoàn tiền":
        return False
    if status == "Đã hủy" and refund_status != "Từ chối":
        return False
    return True


def _month_key(date_text):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_month_key` ( month key).
    Tham số:
        date_text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        _day, month, year = str(date_text or "").strip().split("/")
        return f"{year}-{month}"
    except ValueError:
        return "Không rõ"


def _quarter_key(month_key):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_quarter_key` ( quarter key).
    Tham số:
        month_key: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if month_key == "Không rõ":
        return month_key

    year_text, month_text = month_key.split("-")
    month = max(1, min(12, safe_int(month_text, 1)))
    quarter = ((month - 1) // 3) + 1
    return f"{year_text}-Q{quarter}"


def build_revenue_report(datastore) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `build_revenue_report` (build revenue report).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    by_tour = {}
    by_month = {}
    by_quarter = {}

    overview = {
        "tongBooking": 0,
        "bookingHieuLuc": 0,
        "doanhThuDuKien": 0,
        "daThu": 0,
        "conNo": 0,
        "dangChoHoan": 0,
        "soTienChoHoan": 0,
    }

    for booking in _iter_bookings(datastore):
        overview["tongBooking"] += 1

        month_key = _month_key(booking.get("ngayDat"))
        quarter_key = _quarter_key(month_key)
        ma_tour = str(booking.get("maTour", "")).strip()

        people = max(0, safe_int(booking.get("soNguoi", 0)))
        paid = max(0, safe_int(booking.get("daThanhToan", 0)))
        total = max(0, safe_int(booking.get("tongTien", 0)))
        debt = max(0, safe_int(booking.get("conNo", 0)))

        if str(booking.get("trangThai", "")).strip() == "Chờ hoàn tiền":
            overview["dangChoHoan"] += 1
            overview["soTienChoHoan"] += max(safe_int(booking.get("soTienHoan", 0)), paid)

        if not _revenue_booking(booking):
            continue

        tour_row = by_tour.setdefault(
            ma_tour or "Không rõ",
            {
                "maTour": ma_tour or "Không rõ",
                "tenTour": _find_tour_name(datastore, ma_tour),
                "tongBooking": 0,
                "tongNguoi": 0,
                "doanhThuDuKien": 0,
                "daThu": 0,
                "conNo": 0,
            },
        )
        month_row = by_month.setdefault(
            month_key,
            {
                "ky": month_key,
                "tongBooking": 0,
                "tongNguoi": 0,
                "doanhThuDuKien": 0,
                "daThu": 0,
                "conNo": 0,
            },
        )
        quarter_row = by_quarter.setdefault(
            quarter_key,
            {
                "ky": quarter_key,
                "tongBooking": 0,
                "tongNguoi": 0,
                "doanhThuDuKien": 0,
                "daThu": 0,
                "conNo": 0,
            },
        )

        overview["bookingHieuLuc"] += 1
        overview["doanhThuDuKien"] += total
        overview["daThu"] += paid
        overview["conNo"] += debt

        for row in (tour_row, month_row, quarter_row):
            row["tongBooking"] += 1
            row["tongNguoi"] += people
            row["doanhThuDuKien"] += total
            row["daThu"] += paid
            row["conNo"] += debt

    return {
        "overview": overview,
        "by_tour": sorted(by_tour.values(), key=lambda row: (row["maTour"], row["tenTour"])),
        "by_month": sorted(by_month.values(), key=lambda row: row["ky"]),
        "by_quarter": sorted(by_quarter.values(), key=lambda row: row["ky"]),
    }
