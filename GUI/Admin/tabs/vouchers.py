from __future__ import annotations


def render(app):
    """
    Mục đích:
        Dựng tab quản lý voucher/khuyến mãi.
    Tham số:
        app: Ngữ cảnh ứng dụng admin hiện tại.
    Giá trị trả về:
        Kết quả trả về từ `admin.admin_voucher_tab`.
    Tác dụng phụ:
        Cập nhật giao diện danh sách và form voucher.
    Lưu ý nghiệp vụ:
        Rule áp dụng voucher nằm ở tầng core, tab chỉ gọi hiển thị.
    """
    from GUI.Admin import Admin as admin

    return admin.admin_voucher_tab(app)
