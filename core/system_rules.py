# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime, timedelta

from core.booking_pricing import calculate_age_discount, normalize_passenger_breakdown


VALID_BOOKING_STATUSES = {"Mới tạo", "Đã cọc", "Đã thanh toán", "Đã hoàn thành", "Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}
CANCEL_BOOKING_STATUSES = {"Đã hủy", "Chờ hoàn tiền", "Hoàn tiền"}
TERMINAL_TOUR_STATUSES = {"Hoàn tất", "Đã hủy", "Tạm hoãn"}
AUTO_CANCEL_UNPAID_DAYS = 15


def _safe_int(value, default=0):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_safe_int` ( safe int).
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


def _non_negative_int(value, default=0):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_non_negative_int` ( non negative int).
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
    return max(0, _safe_int(value, default))


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


def _normalize_voucher_scope(raw_value) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_voucher_scope` ( normalize voucher scope).
    Tham số:
        raw_value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    parts = []
    for part in str(raw_value or "").replace(";", ",").replace("\n", ",").split(","):
        normalized = part.strip().upper()
        if normalized and normalized not in parts:
            parts.append(normalized)
    return ", ".join(parts)


def _normalize_booking(booking: dict, tours_by_code: dict[str, dict], today: date) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_booking` ( normalize booking).
    Tham số:
        booking: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        tours_by_code: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        today: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    tour_code = str(booking.get("maTour", "")).strip()
    tour = tours_by_code.get(tour_code)

    so_nguoi = max(1, _safe_int(booking.get("soNguoi", 1), 1))
    booking["soNguoi"] = str(so_nguoi)

    price_per_person = _non_negative_int(tour.get("gia", 0)) if tour else _non_negative_int(booking.get("gia", 0))
    tong_tien_goc = (
        price_per_person * so_nguoi
        if price_per_person > 0
        else _non_negative_int(booking.get("tongTienGoc", booking.get("tongTien", 0)))
    )
    normalized_breakdown = normalize_passenger_breakdown(booking.get("coCauDoTuoi", {}), so_nguoi)
    if normalized_breakdown is None:
        normalized_breakdown = normalize_passenger_breakdown({}, so_nguoi) or {
            "treEm": 0,
            "trungNien": so_nguoi,
            "nguoiCaoTuoi": 0,
        }

    if price_per_person > 0:
        giam_gia_doi_tuong = calculate_age_discount(price_per_person, normalized_breakdown)
    else:
        giam_gia_doi_tuong = _non_negative_int(booking.get("giamGiaDoiTuong", 0))
    giam_gia_doi_tuong = min(giam_gia_doi_tuong, tong_tien_goc)

    giam_gia_voucher = _non_negative_int(booking.get("giamGiaVoucher", 0))
    giam_gia_voucher = min(giam_gia_voucher, max(tong_tien_goc - giam_gia_doi_tuong, 0))
    tong_tien = max(tong_tien_goc - giam_gia_doi_tuong - giam_gia_voucher, 0)
    da_thanh_toan = _non_negative_int(booking.get("daThanhToan", booking.get("tienCoc", 0)))
    tien_coc = _non_negative_int(booking.get("tienCoc", 0))

    if tong_tien > 0 and da_thanh_toan > tong_tien:
        da_thanh_toan = tong_tien
    if tien_coc > da_thanh_toan:
        tien_coc = da_thanh_toan

    auto_cancel_unpaid = False
    if tour and da_thanh_toan <= 0 and tien_coc <= 0:
        ngay_khoi_hanh = _parse_ddmmyyyy(tour.get("ngay"))
        if ngay_khoi_hanh:
            payment_deadline = ngay_khoi_hanh - timedelta(days=AUTO_CANCEL_UNPAID_DAYS)
            auto_cancel_unpaid = today >= payment_deadline
            if auto_cancel_unpaid:
                auto_note = f"[AUTO] Hủy do chưa đặt cọc/thanh toán trước hạn {payment_deadline.strftime('%d/%m/%Y')}."
                existing_note = str(booking.get("ghiChu", "") or "").strip()
                if auto_note not in existing_note:
                    booking["ghiChu"] = f"{auto_note} {existing_note}".strip()

    refund_status = str(booking.get("trangThaiHoanTien", "") or "").strip()
    refund_amount = _non_negative_int(booking.get("soTienHoan", 0))
    status = str(booking.get("trangThai", "") or "").strip()

    if status == "Chờ hoàn tiền" and not refund_status:
        refund_status = "Chờ duyệt"

    if status in CANCEL_BOOKING_STATUSES:
        if status == "Đã hủy":
            if da_thanh_toan > 0 and refund_status != "Từ chối":
                status = "Chờ hoàn tiền"
                refund_status = "Chờ duyệt"
                refund_amount = max(refund_amount, da_thanh_toan)
            con_no = 0
        elif status == "Chờ hoàn tiền":
            refund_status = "Chờ duyệt"
            refund_amount = max(refund_amount, da_thanh_toan)
            con_no = 0
        else:
            refund_status = "Đã hoàn tiền"
            refund_amount = max(refund_amount, da_thanh_toan)
            da_thanh_toan = 0
            tien_coc = 0
            con_no = 0
    elif auto_cancel_unpaid and status not in VALID_BOOKING_STATUSES:
        status = "Đã hủy"
        con_no = 0
    else:
        if status == "Đã hoàn thành":
            con_no = max(tong_tien - da_thanh_toan, 0)
            refund_status = ""
            refund_amount = 0
            booking["ngayYeuCauHoanTien"] = ""
            booking["ngayXuLyHoanTien"] = ""
            booking["nguoiXuLyHoanTien"] = ""
            booking["ghiChuHoanTien"] = ""
            booking["trangThai"] = status
            booking["trangThaiHoanTien"] = refund_status
            booking["soTienHoan"] = refund_amount
            booking["tongTienGoc"] = tong_tien_goc
            booking["giamGiaDoiTuong"] = giam_gia_doi_tuong
            booking["coCauDoTuoi"] = normalized_breakdown
            booking["tongTien"] = tong_tien
            booking["tienCoc"] = tien_coc
            booking["daThanhToan"] = da_thanh_toan
            booking["conNo"] = con_no
            if not str(booking.get("hinhThucThanhToan", "") or "").strip():
                booking["hinhThucThanhToan"] = "Chưa thanh toán" if da_thanh_toan <= 0 else "Tiền mặt"
            return
        if status in {"Mới tạo", "Đã cọc", "Đã thanh toán"}:
            if status == "Mới tạo":
                da_thanh_toan = min(da_thanh_toan, 0)
                tien_coc = min(tien_coc, da_thanh_toan)
            elif status == "Đã cọc" and tong_tien > 0 and da_thanh_toan >= tong_tien:
                status = "Đã thanh toán"
            elif status == "Đã thanh toán" and tong_tien > 0 and da_thanh_toan < tong_tien:
                da_thanh_toan = tong_tien
                tien_coc = min(tien_coc, da_thanh_toan)
        elif da_thanh_toan <= 0:
            status = "Mới tạo"
        elif tong_tien > 0 and da_thanh_toan < tong_tien:
            status = "Đã cọc"
        else:
            status = "Đã thanh toán"
        con_no = max(tong_tien - da_thanh_toan, 0)
        refund_status = ""
        refund_amount = 0
        booking["ngayYeuCauHoanTien"] = ""
        booking["ngayXuLyHoanTien"] = ""
        booking["nguoiXuLyHoanTien"] = ""
        booking["ghiChuHoanTien"] = ""

    ngay_dat = _parse_ddmmyyyy(booking.get("ngayDat"))
    if ngay_dat is None:
        booking["ngayDat"] = today.strftime("%d/%m/%Y")

    booking.setdefault("hinhThucThanhToan", "Chưa thanh toán" if da_thanh_toan <= 0 else "Tiền mặt")
    booking.setdefault("nguonKhach", "Khách lẻ")
    booking.setdefault("ghiChu", "")
    booking.setdefault("usernameDat", "")
    booking.setdefault("danhSachKhach", [])
    if not isinstance(booking.get("danhSachKhach"), list):
        booking["danhSachKhach"] = []
    booking.setdefault("maVoucher", "")
    booking.setdefault("tenVoucher", "")
    booking.setdefault("giamGiaDoiTuong", 0)
    booking.setdefault("giamGiaVoucher", 0)
    booking.setdefault("coCauDoTuoi", {})
    booking.setdefault("trangThaiHoanTien", refund_status)
    booking.setdefault("soTienHoan", refund_amount)
    booking.setdefault("ngayYeuCauHoanTien", "")
    booking.setdefault("ngayXuLyHoanTien", "")
    booking.setdefault("nguoiXuLyHoanTien", "")
    booking.setdefault("ghiChuHoanTien", "")
    booking["tongTienGoc"] = tong_tien_goc
    booking["giamGiaDoiTuong"] = giam_gia_doi_tuong
    booking["coCauDoTuoi"] = normalized_breakdown
    booking["tongTien"] = tong_tien
    booking["tienCoc"] = tien_coc
    booking["daThanhToan"] = da_thanh_toan
    booking["conNo"] = con_no
    booking["trangThai"] = status
    booking["trangThaiHoanTien"] = refund_status
    booking["soTienHoan"] = refund_amount
    if not str(booking.get("hinhThucThanhToan", "") or "").strip():
        booking["hinhThucThanhToan"] = "Chưa thanh toán" if da_thanh_toan <= 0 else "Tiền mặt"


def _normalize_voucher(voucher: dict, used_count: int, today: date) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_voucher` ( normalize voucher).
    Tham số:
        voucher: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        used_count: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        today: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    voucher["maVoucher"] = str(voucher.get("maVoucher", "")).strip().upper()
    voucher.setdefault("tenVoucher", "")
    voucher.setdefault("loaiGiam", "Tiền mặt")
    voucher.setdefault("giamGiaVoucher", 0)
    voucher["donToiThieu"] = str(_non_negative_int(voucher.get("donToiThieu", 0)))

    so_luong = max(_non_negative_int(voucher.get("soLuong", 0)), used_count)
    voucher["soLuong"] = str(so_luong)
    voucher["daSuDung"] = str(max(0, used_count))
    voucher["gioiHanMoiUser"] = str(_non_negative_int(voucher.get("gioiHanMoiUser", 0)))
    voucher["tourApDung"] = _normalize_voucher_scope(voucher.get("tourApDung", ""))
    voucher.setdefault("ngayBatDau", "")
    voucher.setdefault("ngayKetThuc", "")
    voucher.setdefault("moTa", "")

    status = str(voucher.get("trangThai", "")).strip()
    status_lower = status.lower()
    start_date = _parse_ddmmyyyy(voucher.get("ngayBatDau"))
    end_date = _parse_ddmmyyyy(voucher.get("ngayKetThuc"))

    if "ngừng" in status_lower:
        normalized_status = "Ngừng áp dụng"
    elif end_date and today > end_date:
        normalized_status = "Hết hạn"
    elif so_luong > 0 and used_count >= so_luong:
        normalized_status = "Hết lượt"
    elif start_date and today < start_date:
        normalized_status = "Sắp áp dụng"
    else:
        normalized_status = "Đang áp dụng"

    voucher["trangThai"] = normalized_status


def _normalize_tour(tour: dict, occupied: int, today: date) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_tour` ( normalize tour).
    Tham số:
        tour: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        occupied: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        today: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    status = str(tour.get("trangThai", "")).strip()
    if status == "Đã chốt":
        status = "Đã chốt đoàn"
    if status == "Hoàn thành":
        status = "Hoàn tất"

    valid_statuses = {
        "Giữ chỗ",
        "Mở bán",
        "Đã chốt đoàn",
        "Chờ khởi hành",
        "Đang đi",
        "Hoàn tất",
        "Đã hủy",
        "Tạm hoãn",
    }

    suc_chua = max(1, _safe_int(tour.get("khach", 1), 1))
    gia = _non_negative_int(tour.get("gia", 0))
    chi_phi_du_kien = _non_negative_int(tour.get("chiPhiDuKien", 0))
    chi_phi_thuc_te = _non_negative_int(tour.get("chiPhiThucTe", 0))

    ngay_di = _parse_ddmmyyyy(tour.get("ngay"))
    ngay_ve = _parse_ddmmyyyy(tour.get("ngayKetThuc")) or ngay_di
    if ngay_di and ngay_ve and ngay_ve < ngay_di:
        ngay_ve = ngay_di

    if ngay_di and ngay_ve:
        so_ngay = (ngay_ve - ngay_di).days + 1
        so_dem = max(so_ngay - 1, 0)
        tour["soNgay"] = f"{so_ngay}N{so_dem}D"
        tour["ngayKetThuc"] = ngay_ve.strftime("%d/%m/%Y")

    if ngay_ve and today > ngay_ve:
        auto_status = "Hoàn tất"
    elif ngay_di and today >= ngay_di:
        auto_status = "Đang đi"
    elif occupied >= suc_chua:
        auto_status = "Đã chốt đoàn"
    elif occupied > 0:
        auto_status = "Giữ chỗ"
    else:
        auto_status = "Mở bán"

    if status not in valid_statuses:
        status = auto_status
    elif status not in {"Đã hủy", "Tạm hoãn", "Hoàn tất"}:
        if occupied >= suc_chua and status in {"Mở bán", "Giữ chỗ"}:
            status = "Đã chốt đoàn"
        elif ngay_ve and today > ngay_ve and status in {"Đang đi", "Chờ khởi hành", "Đã chốt đoàn"}:
            status = "Hoàn tất"
        elif status == "Đang đi" and ngay_di and today < ngay_di:
            status = "Chờ khởi hành"

    ghi_chu = str(tour.get("ghiChuDieuHanh", "") or "").strip()
    if occupied > suc_chua:
        overbook_note = f"[AUTO] Quá tải {occupied - suc_chua} chỗ."
        if overbook_note not in ghi_chu:
            ghi_chu = f"{overbook_note} {ghi_chu}".strip()

    tour["trangThai"] = status
    tour["khach"] = str(suc_chua)
    tour["gia"] = str(gia)
    tour["chiPhiDuKien"] = chi_phi_du_kien
    tour["chiPhiThucTe"] = chi_phi_thuc_te
    tour["ghiChuDieuHanh"] = ghi_chu
    tour.setdefault("hdvPhuTrach", "")


def _normalize_guide(guide: dict, assignments: dict[str, dict]) -> None:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_normalize_guide` ( normalize guide).
    Tham số:
        guide: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        assignments: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    ma_hdv = str(guide.get("maHDV", "")).strip()
    current_status = str(guide.get("trangThai", "")).strip()
    assignment = assignments.get(ma_hdv, {"assigned": False, "in_progress": False})

    if current_status == "Tạm nghỉ":
        guide["trangThai"] = "Tạm nghỉ"
    elif assignment["in_progress"]:
        guide["trangThai"] = "Đang dẫn tour"
    elif assignment["assigned"]:
        guide["trangThai"] = "Đã phân công"
    elif current_status in {"Sẵn sàng", "Đã phân công", "Đang dẫn tour"}:
        guide["trangThai"] = current_status
    else:
        guide["trangThai"] = "Sẵn sàng"

    guide.setdefault("password", "123")
    guide.setdefault("total_reviews", 0)
    guide.setdefault("avg_rating", 0)
    guide.setdefault("skill_score", 0)
    guide.setdefault("attitude_score", 0)
    guide.setdefault("problem_solving_score", 0)


def apply_system_rules(data: dict, today: date | None = None) -> dict:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `apply_system_rules` (apply system rules).
    Tham số:
        data: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        today: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not isinstance(data, dict):
        return data

    today = today or date.today()
    data.setdefault("hdv", [])
    data.setdefault("tours", [])
    data.setdefault("bookings", [])
    data.setdefault("users", [])
    data.setdefault("admin", {})
    data.setdefault("maVoucher", [])

    tours_by_code = {}
    for tour in data["tours"]:
        ma_tour = str(tour.get("ma", "")).strip()
        if ma_tour:
            tours_by_code[ma_tour] = tour

    occupied_by_tour = {}
    for booking in data["bookings"]:
        _normalize_booking(booking, tours_by_code, today)
        ma_tour = str(booking.get("maTour", "")).strip()
        if ma_tour and booking.get("trangThai") not in CANCEL_BOOKING_STATUSES:
            occupied_by_tour[ma_tour] = occupied_by_tour.get(ma_tour, 0) + _safe_int(booking.get("soNguoi", 0))

    for tour in data["tours"]:
        ma_tour = str(tour.get("ma", "")).strip()
        occupied = occupied_by_tour.get(ma_tour, 0)
        _normalize_tour(tour, occupied, today)

    assignments = {}
    for tour in data["tours"]:
        ma_hdv = str(tour.get("hdvPhuTrach", "")).strip()
        if not ma_hdv:
            continue
        status = str(tour.get("trangThai", "")).strip()
        if status in TERMINAL_TOUR_STATUSES:
            continue
        info = assignments.setdefault(ma_hdv, {"assigned": False, "in_progress": False})
        info["assigned"] = True
        if status == "Đang đi":
            info["in_progress"] = True

    for guide in data["hdv"]:
        _normalize_guide(guide, assignments)

    for user in data["users"]:
        user.setdefault("sdt", "")

    voucher_usage = {}
    for booking in data["bookings"]:
        if booking.get("trangThai") in CANCEL_BOOKING_STATUSES:
            continue
        voucher_code = str(booking.get("maVoucher", "")).strip().upper()
        if voucher_code:
            voucher_usage[voucher_code] = voucher_usage.get(voucher_code, 0) + 1

    for voucher in data["maVoucher"]:
        code = str(voucher.get("maVoucher", "")).strip().upper()
        _normalize_voucher(voucher, voucher_usage.get(code, 0), today)

    admin = data.get("admin", {})
    if isinstance(admin, dict):
        admin.setdefault("username", "admin")
        admin.setdefault("password", "123")

    return data
