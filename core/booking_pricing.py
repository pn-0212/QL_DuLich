from __future__ import annotations


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


def normalize_passenger_breakdown(raw_breakdown, total_people):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `normalize_passenger_breakdown` (normalize passenger breakdown).
    Tham số:
        raw_breakdown: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        total_people: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    total = max(1, safe_int(total_people, 1))
    data = raw_breakdown if isinstance(raw_breakdown, dict) else {}

    child = max(0, safe_int(data.get("treEm", 0)))
    senior = max(0, safe_int(data.get("nguoiCaoTuoi", 0)))
    middle = max(0, safe_int(data.get("trungNien", 0)))

    if child + senior + middle != total:
        if child + senior > total:
            return None
        middle = total - child - senior

    return {
        "treEm": child,
        "trungNien": middle,
        "nguoiCaoTuoi": senior,
    }


def calculate_age_discount(price_per_person, breakdown):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `calculate_age_discount` (calculate age discount).
    Tham số:
        price_per_person: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        breakdown: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not isinstance(breakdown, dict):
        return 0

    price = max(0, safe_int(price_per_person))
    child = max(0, safe_int(breakdown.get("treEm", 0)))
    senior = max(0, safe_int(breakdown.get("nguoiCaoTuoi", 0)))

    return max(
        0,
        round(price * child * 0.20) + round(price * senior * 0.35),
    )
