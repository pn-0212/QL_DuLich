from __future__ import annotations


def _first_text(data: dict, keys: tuple[str, ...], default: str = "") -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_first_text` ( first text).
    Tham số:
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def normalize_review_item(
    review: dict,
    *,
    fullname_keys: tuple[str, ...] = ("fullname", "tenKhach", "hoTen"),
    content_keys: tuple[str, ...] = ("content", "comment", "noiDung"),
    date_keys: tuple[str, ...] = ("date", "thoiGian", "ngayGui", "ngay"),
    include_rating: bool = False,
    include_ma_hdv: bool = False,
) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_review_item` (normalize review item).
    Tham số:
        review: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        fullname_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        content_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        date_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        include_rating: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        include_ma_hdv: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    username = _first_text(review, ("username", "user"))
    fullname = _first_text(review, fullname_keys)

    target = _first_text(review, ("target", "doiTuong"))
    if not target:
        if review.get("maHDV"):
            target = "HDV"
        elif review.get("maTour"):
            target = "Tour"
        else:
            target = "Công ty"

    normalized = {
        "username": username,
        "fullname": fullname,
        "target": target,
        "target_id": _first_text(review, ("target_id", "maHDV", "maTour")),
        "content": _first_text(review, content_keys),
        "date": _first_text(review, date_keys),
        "maBooking": _first_text(review, ("maBooking", "bookingCode", "booking_code")),
        "maTour": _first_text(review, ("maTour",)),
    }

    if include_rating:
        normalized["rating"] = review.get("rating", "")
    if include_ma_hdv:
        normalized["maHDV"] = _first_text(review, ("maHDV",))
    return normalized


def normalize_notification_item(
    notification: dict,
    datastore=None,
    *,
    content_keys: tuple[str, ...] = ("content", "noiDung", "message"),
    date_keys: tuple[str, ...] = ("date", "thoiGian", "ngayGui", "ngay"),
) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_notification_item` (normalize notification item).
    Tham số:
        notification: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        content_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        date_keys: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    ma_hdv = _first_text(notification, ("maHDV",))
    ma_tour = _first_text(notification, ("maTour",))

    ten_hdv = _first_text(notification, ("tenHDV",))
    ten_tour = _first_text(notification, ("tenTour",))

    if datastore is not None:
        if not ten_hdv and ma_hdv:
            guide = datastore.find_hdv(ma_hdv)
            if guide:
                ten_hdv = _first_text(guide, ("tenHDV",))
        if not ten_tour and ma_tour:
            tour = datastore.find_tour(ma_tour)
            if tour:
                ten_tour = _first_text(tour, ("ten",))

    return {
        "eventType": _first_text(notification, ("eventType", "loai")),
        "maHDV": ma_hdv,
        "tenHDV": ten_hdv,
        "maTour": ma_tour,
        "tenTour": ten_tour,
        "content": _first_text(notification, content_keys),
        "date": _first_text(notification, date_keys),
    }
