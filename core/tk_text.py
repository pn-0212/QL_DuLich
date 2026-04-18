from __future__ import annotations

import re
import tkinter as tk
from tkinter import messagebox, ttk


_PATCHED = False
_MARKERS = (
    "\u00c3",
    "\u00c4",
    "\u00c2",
    "\u00ca",
    "\u00d4",
    "\u00c6",
    "\u00e1",
    "\u00e0",
    "\u00e2",
    "\u00f0",
    "\u2122",
    "\u0153",
    "\u0178",
    "\u00ba",
    "\u00bb",
    "\u2014",
    "\u2019",
    "\u201d",
    "\u0192",
    "\u201e",
    "\u02dc",
    "\u20ac",
)
_TOKEN_SPLIT_RE = re.compile(r"(\s+)")
_SECOND_ORDER_REPLACEMENTS = (
    ("\u0102\u0192", "\u00c3"),
    ("\u0102\u201e", "\u00c4"),
    ("\u0102\u00c2", "\u00c2"),
    ("\u0102\u00ca", "\u00ca"),
    ("\u0102\u00d4", "\u00d4"),
    ("\u0102\u00c6", "\u00c6"),
    ("\u201e", "\u00c4"),
    ("\u0192", "\u00c6"),
)
_MANUAL_REPLACEMENTS = {
    "\u00c2\u00a0": " ",
    "\u00e2\u20ac\u201c": "-",
    "\u00e2\u20ac\u201d": "\u2014",
    "\u00e2\u20ac\u2122": "'",
    "\u00e2\u20ac\u0153": '"',
}


def _fix_token(token: str) -> str:
    """
    Mục đích:
        Thực hiện xử lý cho hàm `_fix_token` ( fix token).
    Tham số:
        token: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Giá trị theo khai báo kiểu trả về của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if not token or not any(marker in token for marker in _MARKERS):
        return token

    normalized = token
    for broken, repaired in _SECOND_ORDER_REPLACEMENTS:
        normalized = normalized.replace(broken, repaired)
    if normalized != token:
        token = normalized

    for source_encoding in ("cp1252", "latin-1"):
        try:
            fixed = token.encode(source_encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if fixed != token:
            return fixed
    return token


def fix_mojibake(value):
    """
    Mục đích:
        Thực hiện xử lý cho hàm `fix_mojibake` (fix mojibake).
    Tham số:
        value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    if isinstance(value, str):
        # Bảo vệ chữ Việt hợp lệ: chỉ cố sửa khi có dấu hiệu mojibake rõ ràng.
        suspicious_markers = ("\u00c3", "\u00c4", "\u00c2", "\u00ca", "\u00d4", "\u00c6", "\ufffd")
        if not any(marker in value for marker in suspicious_markers):
            return value

        text = value.strip()
        if not text or not any(marker in text for marker in _MARKERS):
            return value
        fixed = "".join(_fix_token(part) for part in _TOKEN_SPLIT_RE.split(value))
        for broken, repaired in _MANUAL_REPLACEMENTS.items():
            fixed = fixed.replace(broken, repaired)
        return fixed
    if isinstance(value, (list, tuple)):
        fixed = [fix_mojibake(item) for item in value]
        return type(value)(fixed)
    if isinstance(value, dict):
        return {key: fix_mojibake(item) for key, item in value.items()}
    return value


def enable_tk_text_autofix():
    """
    Mục đích:
        Thực hiện xử lý cho hàm `enable_tk_text_autofix` (enable tk text autofix).
    Tham số:
        Không có.
    Giá trị trả về:
        Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
    Tác dụng phụ:
        Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
    Lưu ý nghiệp vụ:
        Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
    """
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    def patch_widget_init(widget_class):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `patch_widget_init` (patch widget init).
        Tham số:
            widget_class: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        original_init = widget_class.__init__

        def wrapped_init(self, *args, **kwargs):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `wrapped_init` (wrapped init).
            Tham số:
                self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                *args: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                **kwargs: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            if "text" in kwargs:
                kwargs["text"] = fix_mojibake(kwargs["text"])
            return original_init(self, *args, **kwargs)

        widget_class.__init__ = wrapped_init

    for widget_class in (
        tk.Label,
        tk.Button,
        tk.LabelFrame,
        tk.Checkbutton,
        tk.Radiobutton,
        tk.Message,
        ttk.Label,
        ttk.Button,
        ttk.Checkbutton,
        ttk.Radiobutton,
        ttk.LabelFrame,
    ):
        patch_widget_init(widget_class)

    original_tk_title = tk.Wm.title

    def wrapped_title(self, string=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_title` (wrapped title).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            string: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if string is not None:
            string = fix_mojibake(string)
        return original_tk_title(self, string)

    tk.Wm.title = wrapped_title

    original_tree_heading = ttk.Treeview.heading

    def wrapped_heading(self, column, option=None, **kwargs):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_heading` (wrapped heading).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            column: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            option: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            **kwargs: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if "text" in kwargs:
            kwargs["text"] = fix_mojibake(kwargs["text"])
        return original_tree_heading(self, column, option, **kwargs)

    ttk.Treeview.heading = wrapped_heading

    original_tree_insert = ttk.Treeview.insert

    def wrapped_insert(self, parent, index, iid=None, **kwargs):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_insert` (wrapped insert).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            parent: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            index: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            iid: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            **kwargs: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        if "values" in kwargs:
            kwargs["values"] = fix_mojibake(kwargs["values"])
        if "text" in kwargs:
            kwargs["text"] = fix_mojibake(kwargs["text"])
        return original_tree_insert(self, parent, index, iid=iid, **kwargs)

    ttk.Treeview.insert = wrapped_insert

    original_stringvar_init = tk.StringVar.__init__

    def wrapped_stringvar_init(self, master=None, value=None, name=None):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_stringvar_init` (wrapped stringvar init).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            master: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            name: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return original_stringvar_init(self, master=master, value=fix_mojibake(value), name=name)

    tk.StringVar.__init__ = wrapped_stringvar_init

    original_variable_set = tk.Variable.set

    def wrapped_variable_set(self, value):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrapped_variable_set` (wrapped variable set).
        Tham số:
            self: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            value: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        return original_variable_set(self, fix_mojibake(value))

    tk.Variable.set = wrapped_variable_set

    original_showinfo = messagebox.showinfo
    original_showwarning = messagebox.showwarning
    original_showerror = messagebox.showerror
    original_askyesno = messagebox.askyesno

    def wrap_messagebox(func):
        """
        Mục đích:
            Thực hiện xử lý cho hàm `wrap_messagebox` (wrap messagebox).
        Tham số:
            func: Tham số đầu vào phục vụ nghiệp vụ của hàm.
        Giá trị trả về:
            Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
        Tác dụng phụ:
            Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
        Lưu ý nghiệp vụ:
            Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
        """
        def wrapped(title=None, message=None, *args, **kwargs):
            """
            Mục đích:
                Thực hiện xử lý cho hàm `wrapped` (wrapped).
            Tham số:
                title: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                message: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                *args: Tham số đầu vào phục vụ nghiệp vụ của hàm.
                **kwargs: Tham số đầu vào phục vụ nghiệp vụ của hàm.
            Giá trị trả về:
                Dữ liệu kết quả theo luồng xử lý hiện tại của hàm.
            Tác dụng phụ:
                Có thể đọc/ghi trạng thái tùy theo ngữ cảnh gọi hàm.
            Lưu ý nghiệp vụ:
                Giữ nguyên hành vi cũ, chỉ chuẩn hóa trình bày và tài liệu hóa.
            """
            return func(fix_mojibake(title), fix_mojibake(message), *args, **kwargs)

        return wrapped

    messagebox.showinfo = wrap_messagebox(original_showinfo)
    messagebox.showwarning = wrap_messagebox(original_showwarning)
    messagebox.showerror = wrap_messagebox(original_showerror)
    messagebox.askyesno = wrap_messagebox(original_askyesno)
