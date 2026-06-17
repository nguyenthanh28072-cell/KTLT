import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

from gui.frames import SinhVienFrame, MonHocFrame, LopHocPhanFrame, DiemFrame
from gui.stats_frame import ThongKeFrame


class MainWindow:
    """Cửa sổ chính của ứng dụng quản lý sinh viên."""

    def __init__(self, sv_manager, mh_manager, lhp_manager, diem_manager):
        # Lưu các manager
        self.sv_manager = sv_manager
        self.mh_manager = mh_manager
        self.lhp_manager = lhp_manager
        self.diem_manager = diem_manager

        # Tạo cửa sổ chính với ttkbootstrap theme sáng
        self.root = ttk.Window(
            title="🎓 HUST Student Management System",
            themename="cosmo",
            size=(1200, 750),
            minsize=(1000, 600)
        )

        # Định nghĩa tone màu HUST (Đỏ sẫm chủ đạo)
        self.style = ttk.Style()
        self.style.colors.primary = "#9E1F22"       # Màu đỏ HUST đặc trưng
        self.style.colors.secondary = "#E0E0E0"     # Màu xám sáng cho các nút phụ
        self.style.colors.info = "#7F8C8D"          # Màu xám đậm hơn cho các nút import/excel
        self.style.colors.success = "#2C3E50"       # Xanh navy/xám tối cho các thành phần lớp
        self.style.colors.warning = "#D35400"       # Màu cam đất
        self.style.colors.danger = "#C0392B"         # Đỏ tươi cảnh báo


        # Căn giữa màn hình
        self._center_window()

        # Biến theo dõi trang hiện tại
        self.current_frame = None
        self.current_btn = None
        self.frames = {}

        # Xây dựng giao diện
        self._build_ui()

        # Hiển thị trang đầu tiên
        self._show_frame("sinh_vien")

    def _center_window(self):
        """Căn giữa cửa sổ trên màn hình."""
        self.root.update_idletasks()
        w = 1200
        h = 750
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')

    def _build_ui(self):
        """Xây dựng giao diện chính."""
        # ============ HEADER ============
        header_frame = ttk.Frame(self.root, bootstyle="primary")
        header_frame.pack(fill=X, side=TOP)

        # Logo và tiêu đề
        title_frame = ttk.Frame(header_frame, bootstyle="primary")
        title_frame.pack(fill=X, padx=20, pady=12)

        ttk.Label(
            title_frame,
            text="🎓",
            font=("Segoe UI Emoji", 24),
            bootstyle="inverse-primary"
        ).pack(side=LEFT, padx=(0, 10))

        title_container = ttk.Frame(title_frame, bootstyle="primary")
        title_container.pack(side=LEFT)

        ttk.Label(
            title_container,
            text="HỆ THỐNG QUẢN LÝ SINH VIÊN",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-primary"
        ).pack(anchor=W)

        ttk.Label(
            title_container,
            text="Chương trình quản lý sinh viên và điểm số - Bài tập lớn KTLT",
            font=("Segoe UI", 9),
            bootstyle="inverse-primary"
        ).pack(anchor=W)

        # Thông tin bên phải header
        info_frame = ttk.Frame(title_frame, bootstyle="primary")
        info_frame.pack(side=RIGHT)

        self.lbl_thong_tin = ttk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 9),
            bootstyle="inverse-primary"
        )
        self.lbl_thong_tin.pack(anchor=E)
        self._update_header_info()

        # ============ BODY (SIDEBAR + CONTENT) ============
        body_frame = ttk.Frame(self.root)
        body_frame.pack(fill=BOTH, expand=True)

        # ---- SIDEBAR ----
        sidebar = ttk.Frame(body_frame, width=220, bootstyle="light")
        sidebar.pack(side=LEFT, fill=Y)
        sidebar.pack_propagate(False)

        # Spacer trên
        ttk.Frame(sidebar, height=15, bootstyle="light").pack(fill=X)

        # Các nút sidebar
        self.sidebar_buttons = {}
        menu_items = [
            ("sinh_vien", "👤  Sinh Viên", "primary"),
            ("mon_hoc", "📚  Học Phần", "info"),
            ("lop_hp", "🏫  Lớp Học Phần", "success"),
            ("diem", "📊  Điểm Số", "warning"),
            ("thong_ke", "📈  Thống Kê", "danger"),
        ]

        for key, text, style in menu_items:
            btn = ttk.Button(
                sidebar,
                text=text,
                bootstyle=f"{style}-outline",
                command=lambda k=key: self._show_frame(k),
                width=22,
                padding=(15, 12)
            )
            btn.pack(padx=10, pady=4, fill=X)
            self.sidebar_buttons[key] = (btn, style)

        # Spacer giữa
        ttk.Separator(sidebar).pack(fill=X, padx=15, pady=20)

        # Thống kê nhanh trên sidebar
        stats_frame = tk.LabelFrame(sidebar, text="📋 Tổng quan", padx=10, pady=10)
        stats_frame.pack(padx=10, fill=X)

        self.lbl_tong_sv = ttk.Label(stats_frame, text="Sinh viên: 0", font=("Segoe UI", 9))
        self.lbl_tong_sv.pack(anchor=W, pady=2)

        self.lbl_tong_mh = ttk.Label(stats_frame, text="Học phần: 0", font=("Segoe UI", 9))
        self.lbl_tong_mh.pack(anchor=W, pady=2)

        self.lbl_tong_lhp = ttk.Label(stats_frame, text="Lớp HP: 0", font=("Segoe UI", 9))
        self.lbl_tong_lhp.pack(anchor=W, pady=2)

        self.lbl_tong_diem = ttk.Label(stats_frame, text="Bản ghi điểm: 0", font=("Segoe UI", 9))
        self.lbl_tong_diem.pack(anchor=W, pady=2)

        self._update_sidebar_stats()

        # ---- CONTENT AREA ----
        self.content_frame = ttk.Frame(body_frame)
        self.content_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=0, pady=0)

        # Tạo các frame nội dung
        self.frames["sinh_vien"] = SinhVienFrame(
            self.content_frame, self.sv_manager, self._on_data_changed
        )
        self.frames["mon_hoc"] = MonHocFrame(
            self.content_frame, self.mh_manager, self._on_data_changed
        )
        self.frames["lop_hp"] = LopHocPhanFrame(
            self.content_frame, self.lhp_manager,
            self.sv_manager, self.mh_manager, self._on_data_changed
        )
        self.frames["diem"] = DiemFrame(
            self.content_frame, self.diem_manager,
            self.sv_manager, self.mh_manager, self._on_data_changed
        )
        self.frames["thong_ke"] = ThongKeFrame(
            self.content_frame, self.diem_manager,
            self.sv_manager, self.mh_manager, self.lhp_manager
        )

        # ============ FOOTER ============
        footer = ttk.Frame(self.root, bootstyle="secondary")
        footer.pack(fill=X, side=BOTTOM)

        ttk.Label(
            footer,
            text="© 2025 - Bài tập lớn Kỹ Thuật Lập Trình | Python + Tkinter + ttkbootstrap",
            font=("Segoe UI", 8),
            bootstyle="inverse-secondary"
        ).pack(pady=5)

    def _show_frame(self, frame_key):
        """Chuyển đổi giữa các frame nội dung."""
        # Ẩn frame hiện tại
        if self.current_frame:
            self.current_frame.pack_forget()

        # Đặt lại style sidebar
        if self.current_btn:
            old_key = self.current_btn
            btn, style = self.sidebar_buttons[old_key]
            btn.configure(bootstyle=f"{style}-outline")

        # Hiển thị frame mới
        frame = self.frames[frame_key]
        frame.pack(fill=BOTH, expand=True)
        self.current_frame = frame
        self.current_btn = frame_key

        # Đổi style nút active
        btn, style = self.sidebar_buttons[frame_key]
        btn.configure(bootstyle=style)

        # Refresh dữ liệu frame
        if hasattr(frame, 'refresh'):
            frame.refresh()

    def _update_header_info(self):
        """Cập nhật thông tin trên header."""
        total = self.sv_manager.so_luong()
        self.lbl_thong_tin.configure(
            text=f"Tổng sinh viên: {total}"
        )

    def _update_sidebar_stats(self):
        """Cập nhật thống kê trên sidebar."""
        self.lbl_tong_sv.configure(text=f"👤 Sinh viên: {self.sv_manager.so_luong()}")
        self.lbl_tong_mh.configure(text=f"📚 Học phần: {self.mh_manager.so_luong()}")
        self.lbl_tong_lhp.configure(text=f"🏫 Lớp HP: {self.lhp_manager.so_luong()}")
        self.lbl_tong_diem.configure(text=f"📊 Bản ghi điểm: {self.diem_manager.so_luong()}")

    def _on_data_changed(self):
        """Callback khi dữ liệu thay đổi — cập nhật giao diện."""
        self._update_header_info()
        self._update_sidebar_stats()

    def run(self):
        """Chạy ứng dụng."""
        self.root.mainloop()
