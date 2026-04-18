from __future__ import annotations


def render(app):
    """
    Mục đích:
        Dựng giao diện tab báo cáo tổng hợp cho màn Admin.
    Tham số:
        app: Ngữ cảnh ứng dụng admin, chứa container UI và datastore.
    Giá trị trả về:
        Không trả về giá trị.
    Tác dụng phụ:
        Xóa/khởi tạo lại widget trong container hiện tại và cập nhật status bar.
    Lưu ý nghiệp vụ:
        Tab này chỉ hiển thị tổng quan; báo cáo chi tiết mở qua cửa sổ riêng.
    """
    from GUI.Admin import Admin as admin

    admin.clear_container(app)

    tk = admin.tk
    THEME = admin.THEME

    # Dựng tiêu đề và mô tả tab.
    tk.Label(
        app['container'],
        text='Báo cáo tổng hợp',
        font=('Times New Roman', 22, 'bold'),
        bg=THEME['bg'],
        fg=THEME['text'],
    ).pack(anchor='w', pady=(0, 14))

    tk.Label(
        app['container'],
        text='Chọn loại báo cáo để mở cửa sổ chi tiết.',
        font=('Times New Roman', 12, 'italic'),
        bg=THEME['bg'],
        fg=THEME['muted'],
    ).pack(anchor='w', pady=(0, 16))

    # Dựng nhóm nút mở báo cáo chi tiết.
    actions = tk.Frame(app['container'], bg=THEME['bg'])
    actions.pack(fill='x')

    admin.style_button(
        actions,
        'Báo cáo doanh thu',
        '#0f766e',
        lambda: admin.open_revenue_report_window(app),
    ).pack(side='left', padx=(0, 8))

    admin.style_button(
        actions,
        'Tổng hợp theo tour',
        '#7c3aed',
        lambda: admin.open_booking_summary_window(app),
    ).pack(side='left', padx=(0, 8))

    # Lấy số liệu tổng quan để hiển thị nhanh ngay trong tab.
    report = admin.build_revenue_report(app['ql'])
    overview = report.get('overview', {})

    box = tk.Frame(app['container'], bg=THEME['surface'], bd=1, relief='solid', padx=16, pady=14)
    box.pack(fill='x', pady=(16, 0))

    rows = [
        f"Tổng booking: {overview.get('tongBooking', 0)}",
        f"Booking hiệu lực: {overview.get('bookingHieuLuc', 0)}",
        f"Doanh thu dự kiến: {admin.format_currency(overview.get('doanhThuDuKien', 0))}",
        f"Đã thu: {admin.format_currency(overview.get('daThu', 0))}",
        f"Còn nợ: {admin.format_currency(overview.get('conNo', 0))}",
        f"Chờ hoàn tiền: {overview.get('dangChoHoan', 0)}",
    ]

    for row in rows:
        tk.Label(
            box,
            text=row,
            bg=THEME['surface'],
            fg=THEME['text'],
            font=('Times New Roman', 12),
            anchor='w',
        ).pack(fill='x', pady=1)

    admin.set_status(app, 'Đang ở Báo cáo tổng hợp', THEME['primary'])
