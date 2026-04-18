from __future__ import annotations

from datetime import datetime

from core.system_rules import CANCEL_BOOKING_STATUSES


def safe_int(value, default=0):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `safe_int` (safe int).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        default: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_ddmmyyyy(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `parse_ddmmyyyy` (parse ddmmyyyy).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    try:
        return datetime.strptime(str(value or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def normalize_tour_scope(value) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_tour_scope` (normalize tour scope).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    items = []
    for part in str(value or "").replace(";", ",").replace("\n", ",").split(","):
        normalized = part.strip().upper()
        if normalized and normalized not in items:
            items.append(normalized)
    return ", ".join(items)


def parse_tour_scope(value) -> list[str]:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `parse_tour_scope` (parse tour scope).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = normalize_tour_scope(value)
    return [part.strip() for part in normalized.split(",") if part.strip()]


def resolve_voucher_discount(voucher, gross_total):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `resolve_voucher_discount` (resolve voucher discount).
    Tham số:
        voucher: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        gross_total: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not voucher:
        return 0

    gross_total = max(0, safe_int(gross_total))
    loai_giam = str(voucher.get("loaiGiam", "")).strip()
    raw_discount = str(voucher.get("giamGiaVoucher", "")).strip()

    if loai_giam == "Phần trăm":
        try:
            percent = float(raw_discount.replace("%", "").strip())
        except ValueError:
            return 0
        return min(gross_total, max(0, int(round(gross_total * percent / 100))))

    return min(gross_total, max(0, safe_int(raw_discount)))


def _list_vouchers(datastore):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_list_vouchers` ( list vouchers).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    vouchers = getattr(datastore, "list_vouchers", None)
    if vouchers is not None:
        return vouchers
    return datastore.data.get("maVoucher", [])


def _find_voucher(datastore, code):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_find_voucher` ( find voucher).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized = str(code or "").strip().upper()
    if not normalized:
        return None

    finder = getattr(datastore, "find_voucher", None)
    if callable(finder):
        result = finder(normalized)
        if result:
            return result

    return next(
        (
            voucher
            for voucher in _list_vouchers(datastore)
            if str(voucher.get("maVoucher", "")).strip().upper() == normalized
        ),
        None,
    )


def _iter_active_voucher_bookings(datastore, code, exclude_booking=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_iter_active_voucher_bookings` ( iter active voucher bookings).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        exclude_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized_code = str(code or "").strip().upper()
    exclude_booking = str(exclude_booking or "").strip()

    for booking in getattr(datastore, "list_bookings", datastore.data.get("bookings", [])):
        if str(booking.get("maVoucher", "")).strip().upper() != normalized_code:
            continue

        booking_code = str(booking.get("maBooking", "")).strip()
        if exclude_booking and booking_code == exclude_booking:
            continue

        refund_status = str(booking.get("trangThaiHoanTien", "")).strip()
        if booking.get("trangThai") in CANCEL_BOOKING_STATUSES and refund_status != "Từ chối":
            continue

        yield booking


def get_voucher_usage(datastore, code, username="", ma_tour="", exclude_booking=None) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `get_voucher_usage` (get voucher usage).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        exclude_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    normalized_username = str(username or "").strip().lower()
    normalized_tour = str(ma_tour or "").strip().upper()

    total = 0
    user_uses = 0
    tour_uses = 0

    for booking in _iter_active_voucher_bookings(datastore, code, exclude_booking=exclude_booking):
        total += 1

        booking_username = str(booking.get("usernameDat", "")).strip().lower()
        booking_tour = str(booking.get("maTour", "")).strip().upper()

        if normalized_username and booking_username == normalized_username:
            user_uses += 1
        if normalized_tour and booking_tour == normalized_tour:
            tour_uses += 1

    return {
        "total": total,
        "user_uses": user_uses,
        "tour_uses": tour_uses,
    }


def build_voucher_scope_label(voucher) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `build_voucher_scope_label` (build voucher scope label).
    Tham số:
        voucher: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tours = parse_tour_scope(voucher.get("tourApDung", ""))
    if not tours:
        return "Áp dụng toàn bộ tour"
    return "Chỉ áp dụng: " + ", ".join(tours)


def validate_voucher_payload(datastore, data, old_code=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `validate_voucher_payload` (validate voucher payload).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        old_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    required = [
        "maVoucher",
        "tenVoucher",
        "loaiGiam",
        "giamGiaVoucher",
        "donToiThieu",
        "soLuong",
        "daSuDung",
        "ngayBatDau",
        "ngayKetThuc",
        "trangThai",
        "moTa",
    ]

    for key in required:
        if not str(data.get(key, "")).strip():
            return False, "Vui lòng nhập đầy đủ thông tin voucher."

    code = str(data.get("maVoucher", "")).strip().upper()
    if len(code) < 2:
        return False, "Mã voucher không hợp lệ."

    old_normalized = str(old_code or "").strip().upper()
    for voucher in _list_vouchers(datastore):
        if str(voucher.get("maVoucher", "")).strip().upper() == code and code != old_normalized:
            return False, "Mã voucher đã tồn tại."

    loai = str(data.get("loaiGiam", "")).strip()
    giam = str(data.get("giamGiaVoucher", "")).strip()
    if loai == "Phần trăm":
        if not giam.endswith("%"):
            return False, "Giảm giá phần trăm phải có dạng ví dụ: 10%."
        try:
            percent = float(giam.replace("%", "").strip())
        except ValueError:
            return False, "Giảm giá phần trăm không hợp lệ."
        if percent <= 0 or percent > 100:
            return False, "Phần trăm giảm phải từ 1% đến 100%."
    else:
        if not giam.isdigit() or int(giam) <= 0:
            return False, "Giảm giá tiền mặt phải là số dương."

    numeric_fields = {
        "donToiThieu": "Đơn tối thiểu",
        "soLuong": "Số lượng",
        "daSuDung": "Đã sử dụng",
        "gioiHanMoiUser": "Giới hạn mỗi user",
    }
    for field, label in numeric_fields.items():
        raw_value = str(data.get(field, "0") or "0").strip()
        if raw_value and (not raw_value.isdigit() or int(raw_value) < 0):
            return False, f"{label} phải là số >= 0."

    if safe_int(data.get("daSuDung", 0)) > safe_int(data.get("soLuong", 0)):
        return False, "Số đã sử dụng không được lớn hơn số lượng."

    start_date = parse_ddmmyyyy(data.get("ngayBatDau"))
    end_date = parse_ddmmyyyy(data.get("ngayKetThuc"))
    if not start_date or not end_date:
        return False, "Ngày bắt đầu / kết thúc không đúng định dạng dd/mm/yyyy."
    if end_date < start_date:
        return False, "Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu."

    normalized_scope = normalize_tour_scope(data.get("tourApDung", ""))
    if normalized_scope:
        known_tours = {
            str(tour.get("ma", "")).strip().upper()
            for tour in getattr(datastore, "list_tours", datastore.data.get("tours", []))
        }
        missing = [tour_code for tour_code in parse_tour_scope(normalized_scope) if tour_code not in known_tours]
        if missing:
            return False, f"Không tìm thấy tour áp dụng: {', '.join(missing)}."

    return True, ""


def build_voucher_quote(datastore, voucher_code, gross_total, username="", ma_tour="", exclude_booking=None):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `build_voucher_quote` (build voucher quote).
    Tham số:
        datastore: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        voucher_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        gross_total: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        username: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        ma_tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        exclude_booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    code = str(voucher_code or "").strip().upper()
    if not code:
        return {
            "ok": True,
            "voucher": None,
            "code": "",
            "discount": 0,
            "message": "Chưa áp dụng mã giảm giá.",
        }

    voucher = _find_voucher(datastore, code)
    if not voucher:
        return {
            "ok": False,
            "voucher": None,
            "code": code,
            "discount": 0,
            "message": "Mã giảm giá không tồn tại.",
        }

    status = str(voucher.get("trangThai", "")).strip().lower()
    start_date = parse_ddmmyyyy(voucher.get("ngayBatDau"))
    end_date = parse_ddmmyyyy(voucher.get("ngayKetThuc"))
    today_local = datetime.now().date()
    remaining = max(0, safe_int(voucher.get("soLuong", 0)) - safe_int(voucher.get("daSuDung", 0)))
    minimum_order = max(0, safe_int(voucher.get("donToiThieu", 0)))
    user_limit = max(0, safe_int(voucher.get("gioiHanMoiUser", 0)))
    allowed_tours = parse_tour_scope(voucher.get("tourApDung", ""))
    usage = get_voucher_usage(datastore, code, username=username, ma_tour=ma_tour, exclude_booking=exclude_booking)

    if "ngừng" in status:
        return {"ok": False, "voucher": voucher, "code": code, "discount": 0, "message": "Mã này đang tạm ngừng áp dụng."}
    if start_date and today_local < start_date:
        return {
            "ok": False,
            "voucher": voucher,
            "code": code,
            "discount": 0,
            "message": f"Mã này có hiệu lực từ {start_date.strftime('%d/%m/%Y')}.",
        }
    if end_date and today_local > end_date:
        return {"ok": False, "voucher": voucher, "code": code, "discount": 0, "message": "Mã này đã hết hạn."}
    if remaining <= 0:
        return {"ok": False, "voucher": voucher, "code": code, "discount": 0, "message": "Mã này đã dùng hết lượt."}
    if gross_total < minimum_order:
        return {
            "ok": False,
            "voucher": voucher,
            "code": code,
            "discount": 0,
            "message": f"Đơn tối thiểu để dùng mã là {minimum_order:,}đ.".replace(",", "."),
        }

    normalized_tour = str(ma_tour or "").strip().upper()
    if allowed_tours and normalized_tour and normalized_tour not in allowed_tours:
        return {
            "ok": False,
            "voucher": voucher,
            "code": code,
            "discount": 0,
            "message": f"Mã này chỉ áp dụng cho tour: {', '.join(allowed_tours)}.",
        }

    if allowed_tours and not normalized_tour:
        return {
            "ok": False,
            "voucher": voucher,
            "code": code,
            "discount": 0,
            "message": "Cần chọn tour trước khi áp dụng mã giảm giá này.",
        }

    if user_limit > 0:
        normalized_username = str(username or "").strip()
        if not normalized_username:
            return {
                "ok": False,
                "voucher": voucher,
                "code": code,
                "discount": 0,
                "message": "Mã này yêu cầu gắn với tài khoản khách hàng cụ thể.",
            }
        if usage["user_uses"] >= user_limit:
            return {
                "ok": False,
                "voucher": voucher,
                "code": code,
                "discount": 0,
                "message": f"Tài khoản này đã dùng mã tối đa {user_limit} lần.",
            }

    discount_amount = resolve_voucher_discount(voucher, gross_total)
    if discount_amount <= 0:
        return {"ok": False, "voucher": voucher, "code": code, "discount": 0, "message": "Mã giảm giá không hợp lệ."}

    success_parts = [f"Áp dụng {code} thành công, giảm {discount_amount:,}đ.".replace(",", ".")]
    if user_limit > 0:
        success_parts.append(f"Còn {max(user_limit - usage['user_uses'] - 1, 0)} lượt cho tài khoản này.")
    if allowed_tours:
        success_parts.append("Phạm vi: " + ", ".join(allowed_tours))

    return {
        "ok": True,
        "voucher": voucher,
        "code": code,
        "discount": discount_amount,
        "message": " ".join(success_parts),
        "remaining": remaining,
        "user_limit": user_limit,
        "allowed_tours": allowed_tours,
    }
