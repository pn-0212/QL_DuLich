from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def auto_fit_treeview_columns(tree, columns, min_widths=None, max_widths=None, padding=24):
    """
    Mục đích:
        Tự tính chiều rộng cột Treeview dựa trên tiêu đề và dữ liệu hiện có.
    Tham số:
        tree: Widget `ttk.Treeview` cần điều chỉnh cột.
        columns: Danh sách mã cột cần auto-fit.
        min_widths: Dict giới hạn chiều rộng tối thiểu cho từng cột.
        max_widths: Dict giới hạn chiều rộng tối đa cho từng cột.
        padding: Phần bù pixel cho khoảng thở nội dung.
    Giá trị trả về:
        Không trả về giá trị.
    Tác dụng phụ:
        Cập nhật trực tiếp cấu hình cột trên `tree`.
    Lưu ý nghiệp vụ:
        Dùng cho bảng dữ liệu HDV để tránh cột quá hẹp hoặc quá rộng.
    """

    def estimate_width(text):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `estimate_width` (estimate width).
        Tham số:
            text: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        text = "" if text is None else str(text)
        return max(40, len(text) * 8 + padding)

    for col in columns:
        header_text = tree.heading(col)["text"]
        width = estimate_width(header_text)

        for item in tree.get_children():
            cell_value = tree.set(item, col)
            width = max(width, estimate_width(cell_value))

        if min_widths and col in min_widths:
            width = max(width, min_widths[col])
        if max_widths and col in max_widths:
            width = min(width, max_widths[col])

        tree.column(col, width=width)


def apply_zebra(tree, theme):
    """
    Mục đích:
        Áp dụng màu xen kẽ cho các dòng trong Treeview để dễ đọc.
    Tham số:
        tree: Widget `ttk.Treeview` cần tô màu.
        theme: Dict màu giao diện có `zebra_odd` và `zebra_even`.
    Giá trị trả về:
        Không trả về giá trị.
    Tác dụng phụ:
        Thay đổi tag hiển thị của từng dòng trong bảng.
    Lưu ý nghiệp vụ:
        Nên gọi lại sau mỗi lần reload dữ liệu bảng.
    """
    tree.tag_configure("odd", background=theme["zebra_odd"])
    tree.tag_configure("even", background=theme["zebra_even"])
    for idx, item in enumerate(tree.get_children()):
        tree.item(item, tags=(("even" if idx % 2 == 0 else "odd"),))


def style_button(parent, text, bg, command, fg="white"):
    """
    Mục đích:
        Tạo button theo phong cách thống nhất cho màn hình HDV.
    Tham số:
        parent: Widget cha chứa button.
        text: Nhãn hiển thị trên button.
        bg: Màu nền button.
        command: Hàm callback khi bấm.
        fg: Màu chữ.
    Giá trị trả về:
        Đối tượng `tk.Button` đã cấu hình style.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Hàm này chỉ dựng style, chưa tự pack/grid widget.
    """
    return tk.Button(
        parent,
        text=text,
        bg=bg,
        fg=fg,
        activebackground=bg,
        activeforeground=fg,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=("Times New Roman", 11, "bold"),
        padx=14,
        pady=9,
        highlightthickness=1,
        highlightbackground=bg,
        highlightcolor=bg,
        command=command,
    )


def configure_ui_fonts(root):
    """
    Mục đích:
        Thiết lập font mặc định cho toàn bộ widget Tk/Ttk trong cửa sổ.
    Tham số:
        root: Cửa sổ gốc Tkinter.
    Giá trị trả về:
        Không trả về giá trị.
    Tác dụng phụ:
        Cập nhật cấu hình font global của ứng dụng.
    Lưu ý nghiệp vụ:
        Giúp giao diện HDV nhất quán kiểu chữ với các phân hệ khác.
    """
    default_font = ("Times New Roman", 12)
    heading_font = ("Times New Roman", 12, "bold")
    root.option_add("*Font", default_font)
    root.option_add("*Label.Font", default_font)
    root.option_add("*Button.Font", default_font)
    root.option_add("*Entry.Font", default_font)
    root.option_add("*Text.Font", default_font)
    root.option_add("*Spinbox.Font", default_font)
    root.option_add("*TCombobox*Listbox*Font", default_font)

    style = ttk.Style(root)
    style.configure("TLabel", font=default_font)
    style.configure("TButton", font=heading_font)
    style.configure("TEntry", font=default_font)
    style.configure("TCombobox", font=default_font)


def create_scrollable_frame(parent, bg):
    """
    Mục đích:
        Tạo frame có thanh cuộn dọc cho các màn dữ liệu dài.
    Tham số:
        parent: Widget cha để chứa vùng cuộn.
        bg: Màu nền vùng hiển thị.
    Giá trị trả về:
        Bộ đôi `(outer, content)` gồm khung ngoài và khung nội dung.
    Tác dụng phụ:
        Gắn các binding sự kiện resize để đồng bộ kích thước vùng cuộn.
    Lưu ý nghiệp vụ:
        `content` là nơi cần thêm widget nghiệp vụ.
    """
    # Dựng widget nền gồm canvas + scrollbar để tạo vùng cuộn.
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    content = tk.Frame(canvas, bg=bg)

    # Bind sự kiện thay đổi kích thước nội dung để cập nhật scrollregion.
    content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    def resize_content(event):
        """Đồng bộ chiều rộng frame nội dung theo chiều rộng canvas."""
        canvas.itemconfig(canvas_window, width=event.width)

    # Bind sự kiện resize canvas để khung nội dung co giãn linh hoạt.
    canvas.bind("<Configure>", resize_content)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return outer, content


def responsive_wraplength(widget, offset=80, min_width=260, fallback=760):
    """
    Mục đích:
        Tính `wraplength` động theo chiều rộng widget hiện tại.
    Tham số:
        widget: Widget dùng để đo chiều rộng.
        offset: Khoảng trừ để chừa lề.
        min_width: Giới hạn wrap nhỏ nhất.
        fallback: Giá trị dự phòng khi widget chưa layout xong.
    Giá trị trả về:
        Chiều rộng wrap phù hợp cho text dài.
    Tác dụng phụ:
        Không có.
    Lưu ý nghiệp vụ:
        Tránh hiện tượng text quá dài làm bể bố cục popup.
    """
    width = widget.winfo_width()
    if width <= 1:
        return fallback
    return max(min_width, width - offset)
