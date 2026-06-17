import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk


class ThongKeFrame(ttk.Frame):

    def __init__(self, parent, diem_manager, sv_manager, mh_manager, lhp_manager=None):
        super().__init__(parent)
        self.diem_manager = diem_manager
        self.sv_manager = sv_manager
        self.mh_manager = mh_manager
        self.lhp_manager = lhp_manager
        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=X, padx=20, pady=(20, 10))

        ttk.Label(
            header, text="📈  Thống Kê & Báo Cáo",
            font=("Segoe UI", 18, "bold"), bootstyle="danger"
        ).pack(side=LEFT)

        ttk.Button(
            header, text="🔄 Làm mới", bootstyle="secondary-outline",
            command=self.refresh, padding=(10, 6)
        ).pack(side=RIGHT)

        self.notebook = ttk.Notebook(self, bootstyle="danger")
        self.notebook.pack(fill=BOTH, expand=True, padx=20, pady=(0, 15))

        self.tab_xep_loai = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_xep_loai, text="📊 Phân bố xếp loại")

        self.tab_top_sv = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_top_sv, text="🏆 Top sinh viên")

        self.tab_tong_quan = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_tong_quan, text="📋 Tổng quan")

    def refresh(self):
        self._build_tab_xep_loai()
        self._build_tab_top_sv()
        self._build_tab_tong_quan()

    def _build_tab_xep_loai(self):
        for w in self.tab_xep_loai.winfo_children():
            w.destroy()

        thong_ke = self.diem_manager.thong_ke_xep_loai(
            self.sv_manager.ds_sinh_vien,
            self.mh_manager.ds_mon_hoc
        )

        total_sv = sum(thong_ke.values())
        if total_sv == 0:
            ttk.Label(
                self.tab_xep_loai,
                text="📭 Chưa có dữ liệu thống kê.\nVui lòng thêm sinh viên và nhập điểm trước.",
                font=("Segoe UI", 13), bootstyle="secondary", justify=CENTER
            ).pack(expand=True)
            return

        ttk.Label(
            self.tab_xep_loai,
            text=f"Phân bố xếp loại học lực ({total_sv} sinh viên)",
            font=("Segoe UI", 13, "bold"), bootstyle="light"
        ).pack(anchor=W, pady=(0, 15))

        canvas_frame = ttk.Frame(self.tab_xep_loai)
        canvas_frame.pack(fill=BOTH, expand=True)

        canvas = tk.Canvas(canvas_frame, bg="#2b2b2b", highlightthickness=0)
        canvas.pack(fill=BOTH, expand=True)

        colors = {
            "Xuất sắc": "#00e676",
            "Giỏi": "#69f0ae",
            "Khá": "#40c4ff",
            "TB Khá": "#ffab40",
            "Trung bình": "#ffd740",
            "Yếu": "#ff6e40",
            "Kém": "#ff5252",
            "Chưa có điểm": "#757575"
        }

        max_val = max(thong_ke.values()) if thong_ke.values() else 1
        bar_height = 32
        y_start = 20
        x_label = 130
        x_bar_start = 140
        max_bar_width = 400

        for i, (label, count) in enumerate(thong_ke.items()):
            y = y_start + i * (bar_height + 12)
            color = colors.get(label, "#888888")

            canvas.create_text(
                x_label - 5, y + bar_height // 2,
                text=label, anchor=E,
                fill="white", font=("Segoe UI", 11, "bold")
            )

            bar_width = (count / max_val * max_bar_width) if max_val > 0 else 0
            if bar_width < 5 and count > 0:
                bar_width = 5

            canvas.create_rectangle(
                x_bar_start, y, x_bar_start + bar_width, y + bar_height,
                fill=color, outline=""
            )

            pct = (count / total_sv * 100) if total_sv > 0 else 0
            canvas.create_text(
                x_bar_start + bar_width + 10, y + bar_height // 2,
                text=f"{count} SV ({pct:.1f}%)",
                anchor=W, fill="white", font=("Segoe UI", 10)
            )

        summary_frame = tk.LabelFrame(self.tab_xep_loai, text="📊 Chi tiết", padx=10, pady=10, fg="white", bg="#2b2b2b")
        summary_frame.pack(fill=X, pady=(10, 0))

        tree = ttk.Treeview(
            summary_frame,
            columns=("xep_loai", "so_luong", "ty_le"),
            show="headings", height=8, bootstyle="info"
        )
        tree.heading("xep_loai", text="Xếp loại")
        tree.heading("so_luong", text="Số lượng")
        tree.heading("ty_le", text="Tỷ lệ (%)")
        tree.column("xep_loai", width=150, anchor=CENTER)
        tree.column("so_luong", width=100, anchor=CENTER)
        tree.column("ty_le", width=100, anchor=CENTER)
        tree.pack(fill=X)

        for label, count in thong_ke.items():
            pct = (count / total_sv * 100) if total_sv > 0 else 0
            tree.insert("", END, values=(label, count, f"{pct:.1f}%"))

    def _build_tab_top_sv(self):
        for w in self.tab_top_sv.winfo_children():
            w.destroy()

        top_list = self.diem_manager.top_sinh_vien(
            self.sv_manager.ds_sinh_vien,
            self.mh_manager.ds_mon_hoc, n=20
        )

        if not top_list:
            ttk.Label(
                self.tab_top_sv,
                text="📭 Chưa có dữ liệu.\nVui lòng nhập điểm cho sinh viên trước.",
                font=("Segoe UI", 13), bootstyle="secondary", justify=CENTER
            ).pack(expand=True)
            return

        ttk.Label(
            self.tab_top_sv,
            text="🏆 Top Sinh Viên Có GPA Cao Nhất",
            font=("Segoe UI", 13, "bold"), bootstyle="light"
        ).pack(anchor=W, pady=(0, 10))

        columns = ("stt", "mssv", "ho_ten", "lop", "gpa4", "gpa10", "xep_loai")
        tree = ttk.Treeview(
            self.tab_top_sv, columns=columns,
            show="headings", height=15, bootstyle="warning"
        )

        headers = [("STT", 45), ("MSSV", 90), ("Họ tên", 200), ("Lớp", 100),
                   ("GPA (hệ 4)", 90), ("GPA (hệ 10)", 90), ("Xếp loại", 110)]

        for col, (heading, width) in zip(columns, headers):
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor=CENTER)

        vsb = ttk.Scrollbar(self.tab_top_sv, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

        for i, (sv, gpa4, gpa10, xl) in enumerate(top_list, 1):
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "

            tree.insert("", END, values=(
                f"{medal}{i}", sv.mssv, sv.ho_ten, sv.lop,
                f"{gpa4:.2f}", f"{gpa10:.2f}", xl
            ))

    def _build_tab_tong_quan(self):
        for w in self.tab_tong_quan.winfo_children():
            w.destroy()

        ttk.Label(
            self.tab_tong_quan,
            text="📋 Tổng Quan Hệ Thống",
            font=("Segoe UI", 13, "bold"), bootstyle="light"
        ).pack(anchor=W, pady=(0, 15))

        cards_frame = ttk.Frame(self.tab_tong_quan)
        cards_frame.pack(fill=X, pady=(0, 15))

        stats = [
            ("👤 Sinh viên", self.sv_manager.so_luong(), "primary"),
            ("📚 Học phần", self.mh_manager.so_luong(), "info"),
            ("🏫 Lớp HP", self.lhp_manager.so_luong() if self.lhp_manager else 0, "success"),
            ("📊 Bản ghi điểm", self.diem_manager.so_luong(), "warning"),
        ]

        for i, (label, value, style) in enumerate(stats):
            card = tk.LabelFrame(cards_frame, text=label, padx=15, pady=15)
            card.grid(row=0, column=i, padx=8, sticky=NSEW)
            cards_frame.columnconfigure(i, weight=1)

            ttk.Label(
                card, text=str(value),
                font=("Segoe UI", 28, "bold"), bootstyle=style
            ).pack()

        if self.sv_manager.ds_sinh_vien and self.diem_manager.ds_diem:
            gpa_frame = tk.LabelFrame(
                self.tab_tong_quan, text="📈 GPA Tổng Hợp Tất Cả Sinh Viên",
                padx=10, pady=10
            )
            gpa_frame.pack(fill=BOTH, expand=True, pady=(0, 0))

            columns = ("mssv", "ho_ten", "lop", "so_mon", "gpa4", "gpa10", "xep_loai")
            tree = ttk.Treeview(
                gpa_frame, columns=columns,
                show="headings", height=10, bootstyle="info"
            )

            headers = [("MSSV", 80), ("Họ tên", 170), ("Lớp", 90), ("Số môn", 60),
                       ("GPA (4)", 70), ("GPA (10)", 70), ("Xếp loại", 100)]

            for col, (heading, width) in zip(columns, headers):
                tree.heading(col, text=heading)
                tree.column(col, width=width, anchor=CENTER)

            vsb = ttk.Scrollbar(gpa_frame, orient=VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            tree.pack(side=LEFT, fill=BOTH, expand=True)
            vsb.pack(side=RIGHT, fill=Y)

            for sv in self.sv_manager.ds_sinh_vien:
                ds_bd = self.diem_manager.lay_diem_sv(sv.mssv)
                so_mon = len(ds_bd)
                gpa4 = self.diem_manager.tinh_gpa_he4(sv.mssv, self.mh_manager.ds_mon_hoc)
                gpa10 = self.diem_manager.tinh_gpa_he10(sv.mssv, self.mh_manager.ds_mon_hoc)
                xl = self.diem_manager.xep_loai_sv(sv.mssv, self.mh_manager.ds_mon_hoc)

                gpa4_str = f"{gpa4:.2f}" if gpa4 >= 0 else "N/A"
                gpa10_str = f"{gpa10:.2f}" if gpa10 >= 0 else "N/A"

                tree.insert("", END, values=(
                    sv.mssv, sv.ho_ten, sv.lop, so_mon,
                    gpa4_str, gpa10_str, xl
                ))
        else:
            ttk.Label(
                self.tab_tong_quan,
                text="📭 Thêm sinh viên và nhập điểm để xem thống kê chi tiết.",
                font=("Segoe UI", 11), bootstyle="secondary"
            ).pack(pady=20)
