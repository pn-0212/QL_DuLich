from __future__ import annotations

from datetime import datetime


def parse_ddmmyyyy(value):
    """
    Mục đích:
        Parse chuỗi ngày định dạng `dd/mm/YYYY` sang đối tượng `date`.
    Tham số:
        value: Chuỗi ngày cần chuyển đổi.
    Giá trị trả về:
        `date` nếu parse thành công, hoặc `None` khi dữ liệu sai định dạng.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Dữ liệu ngày tour ở UI khách đang dùng chuẩn `dd/mm/YYYY`.
    """
    try:
        return datetime.strptime(str(value or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def is_tour_visible_to_user(tour):
    """
    Mục đích:
        Quyết định một tour có được hiển thị cho khách hàng hay không.
    Tham số:
        tour: Bản ghi tour dạng dictionary.
    Giá trị trả về:
        `True` nếu tour được phép hiển thị, ngược lại `False`.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Tour bị hủy/tạm hoãn/hoàn tất sẽ bị ẩn; tour quá ngày khởi hành cũng bị ẩn.
    """
    status = str(tour.get("trangThai", "")).strip()
    if status in {"Đã hủy", "Tạm hoãn", "Hoàn tất"}:
        return False

    depart_date = parse_ddmmyyyy(tour.get("ngay", ""))
    if depart_date is None:
        return True
    return depart_date >= datetime.now().date()
