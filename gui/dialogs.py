# gui/dialogs.py - Các dialog popup cho thêm/sửa dữ liệu
# Sử dụng ttkbootstrap Toplevel

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import tkinter as tk

from models import SinhVien, MonHoc, LopHocPhan, BangDiem
from utils import (
    validate_mssv, validate_ho_ten, validate_ngay_sinh,
    validate_email, validate_diem, validate_ma_mon, validate_so_tin_chi,
    generate_hust_email
)


class BaseDialog(ttk.Toplevel):
    """Lớp cơ sở cho các dialog popup."""

    def __init__(self, parent, title, size=(500, 450)):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{size[0]}x{size[1]}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Căn giữa dialog
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (size[0] // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (size[1] // 2)
        self.geometry(f"+{x}+{y}")

        self.result = None

        # Frame chính
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(fill=BOTH, expand=True)

    def _create_field(self, parent, label, row, default="", readonly=False, widget_type="entry"):
        """Tạo một trường nhập liệu."""
        ttk.Label(
            parent, text=label, font=("Segoe UI", 10)
        ).grid(row=row, column=0, sticky=W, pady=(0, 5), padx=(0, 10))

        if widget_type == "entry":
            var = ttk.StringVar(value=default)
            entry = ttk.Entry(
                parent, textvariable=var, font=("Segoe UI", 10),
                width=35, bootstyle="info" if not readonly else "secondary"
            )
            if readonly:
                entry.configure(state="readonly")
            entry.grid(row=row, column=1, sticky=EW, pady=(0, 5))
            return var
        elif widget_type == "combobox":
            var = ttk.StringVar(value=default)
            combo = ttk.Combobox(
                parent, textvariable=var, font=("Segoe UI", 10),
                width=33, bootstyle="info", state="readonly"
            )
            combo.grid(row=row, column=1, sticky=EW, pady=(0, 5))
            return var, combo

    def _create_buttons(self, parent, on_save):
        """Tạo nút Lưu và Hủy."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=(20, 0))

        ttk.Button(
            btn_frame, text="💾  Lưu", bootstyle="success",
            command=on_save, width=15, padding=(10, 8)
        ).pack(side=RIGHT, padx=(10, 0))

        ttk.Button(
            btn_frame, text="❌  Hủy", bootstyle="danger",
            command=self.destroy, width=15, padding=(10, 8)
        ).pack(side=RIGHT)


class SinhVienDialog(BaseDialog):
    """Dialog thêm/sửa sinh viên."""

    def __init__(self, parent, sv=None):
        title = "✏️ Cập nhật thông tin Sinh Viên" if sv else "➕ Thêm Sinh Viên"
        super().__init__(parent, title, (520, 570))

        self.sv = sv  # None = thêm mới, có giá trị = sửa

        # Tiêu đề
        ttk.Label(
            self.main_frame, text=title,
            font=("Segoe UI", 14, "bold"), bootstyle="primary"
        ).pack(anchor=W, pady=(0, 15))

        ttk.Separator(self.main_frame).pack(fill=X, pady=(0, 15))

        # Form fields
        form = ttk.Frame(self.main_frame)
        form.pack(fill=X)
        form.columnconfigure(1, weight=1)

        self.var_mssv = self._create_field(
            form, "Mã SV:", 0,
            default=sv.mssv if sv else "",
            readonly=(sv is not None)
        )
        self.var_ho_ten = self._create_field(
            form, "Họ tên:", 1,
            default=sv.ho_ten if sv else ""
        )
        self.var_ngay_sinh = self._create_field(
            form, "Ngày sinh:", 2,
            default=sv.ngay_sinh if sv else ""
        )

        # Giới tính (Combobox)
        self.var_gioi_tinh, self.cmb_gioi_tinh = self._create_field(
            form, "Giới tính:", 3,
            default=sv.gioi_tinh if sv else "Nam",
            widget_type="combobox"
        )
        self.cmb_gioi_tinh['values'] = ("Nam", "Nữ")

        self.var_lop = self._create_field(
            form, "Lớp:", 4,
            default=sv.lop if sv else ""
        )
        self.var_email = self._create_field(
            form, "Email:", 5,
            default=sv.email if sv else ""
        )

        # Nút tự động sinh email
        auto_btn_frame = ttk.Frame(self.main_frame)
        auto_btn_frame.pack(fill=X, pady=(5, 0))
        ttk.Button(
            auto_btn_frame, text="🔄 Tự động sinh Email",
            bootstyle="info-outline", padding=(8, 4),
            command=self._auto_generate_email
        ).pack(side=LEFT)

        # Ghi chú format
        ttk.Label(
            self.main_frame,
            text="📌 Ngày sinh định dạng: dd/mm/yyyy\n📌 Email: Tên.HọĐệm[MSSV bỏ 20]@sis.hust.edu.vn\n     VD: Nguyễn Văn An (20215678) → An.NV215678@sis.hust.edu.vn",
            font=("Segoe UI", 8), bootstyle="secondary"
        ).pack(anchor=W, pady=(10, 0))

        # Buttons
        self._create_buttons(self.main_frame, self._on_save)

        # Focus vào ô đầu tiên
        self.after(100, lambda: self.focus_set())

    def _auto_generate_email(self):
        """Tự động sinh email từ họ tên và MSSV."""
        ho_ten = self.var_ho_ten.get().strip()
        mssv = self.var_mssv.get().strip()
        if not ho_ten or not mssv:
            Messagebox.show_warning(
                "Vui lòng nhập Mã SV và Họ tên trước khi sinh email tự động!",
                "Thiếu thông tin", parent=self
            )
            return
        email = generate_hust_email(ho_ten, mssv)
        self.var_email.set(email)

    def _on_save(self):
        """Xử lý khi nhấn Lưu."""
        mssv = self.var_mssv.get().strip()
        ho_ten = self.var_ho_ten.get().strip()
        ngay_sinh = self.var_ngay_sinh.get().strip()
        gioi_tinh = self.var_gioi_tinh.get().strip()
        lop = self.var_lop.get().strip()
        email = self.var_email.get().strip()

        # Validation
        ok, msg = validate_mssv(mssv)
        if not ok:
            Messagebox.show_error(msg, "Lỗi nhập liệu", parent=self)
            return

        ok, msg = validate_ho_ten(ho_ten)
        if not ok:
            Messagebox.show_error(msg, "Lỗi nhập liệu", parent=self)
            return

        ok, msg = validate_ngay_sinh(ngay_sinh)
        if not ok:
            Messagebox.show_error(msg, "Lỗi nhập liệu", parent=self)
            return

        ok, msg = validate_email(email, ho_ten, mssv)
        if not ok:
            Messagebox.show_error(msg, "Lỗi nhập liệu", parent=self)
            return

        if not lop:
            Messagebox.show_error("Lớp không được để trống!", "Lỗi nhập liệu", parent=self)
            return

        # Tạo đối tượng sinh viên
        self.result = SinhVien(mssv, ho_ten, ngay_sinh, gioi_tinh, lop, email)
        self.destroy()


class MonHocDialog(BaseDialog):
    """Dialog thêm/sửa môn học."""

    def __init__(self, parent, mh=None):
        title = "✏️ Cập nhật thông tin Học Phần" if mh else "➕ Thêm Học Phần"
        super().__init__(parent, title, (500, 350))

        self.mh = mh

        ttk.Label(
            self.main_frame, text=title,
            font=("Segoe UI", 14, "bold"), bootstyle="info"
        ).pack(anchor=W, pady=(0, 15))

        ttk.Separator(self.main_frame).pack(fill=X, pady=(0, 15))

        form = ttk.Frame(self.main_frame)
        form.pack(fill=X)
        form.columnconfigure(1, weight=1)

        self.var_ma_mon = self._create_field(
            form, "Mã học phần:", 0,
            default=mh.ma_mon if mh else "",
            readonly=(mh is not None)
        )
        self.var_ten_mon = self._create_field(
            form, "Tên học phần:", 1,
            default=mh.ten_mon if mh else ""
        )
        self.var_so_tc = self._create_field(
            form, "Số tín chỉ:", 2,
            default=str(mh.so_tin_chi) if mh else ""
        )

        self._create_buttons(self.main_frame, self._on_save)

    def _on_save(self):
        ma_mon = self.var_ma_mon.get().strip()
        ten_mon = self.var_ten_mon.get().strip()
        so_tc_str = self.var_so_tc.get().strip()

        ok, msg = validate_ma_mon(ma_mon)
        if not ok:
            Messagebox.show_error(msg, "Lỗi nhập liệu", parent=self)
            return

        if not ten_mon:
            Messagebox.show_error("Tên học phần không được để trống!", "Lỗi nhập liệu", parent=self)
            return
        if len(ten_mon) < 2:
            Messagebox.show_error("Tên học phần phải có ít nhất 2 ký tự!", "Lỗi nhập liệu", parent=self)
            return
        import re
        if not re.match(r'^[a-zA-ZÀ-ỹ\s]+$', ten_mon):
            Messagebox.show_error("Tên học phần chỉ được chứa chữ cái và khoảng trắng!", "Lỗi nhập liệu", parent=self)
            return

        ok, so_tc, msg = validate_so_tin_chi(so_tc_str)
        if not ok:
            Messagebox.show_error(msg, "Lỗi nhập liệu", parent=self)
            return

        self.result = MonHoc(ma_mon, ten_mon, so_tc)
        self.destroy()


class LopHocPhanDialog(BaseDialog):
    """Dialog thêm/sửa lớp học phần."""

    def __init__(self, parent, ds_mon_hoc, lhp=None):
        title = "✏️ Cập nhật thông tin Lớp Học Phần" if lhp else "➕ Thêm Lớp Học Phần"
        super().__init__(parent, title, (520, 420))

        self.lhp = lhp
        self.ds_mon_hoc = ds_mon_hoc

        ttk.Label(
            self.main_frame, text=title,
            font=("Segoe UI", 14, "bold"), bootstyle="success"
        ).pack(anchor=W, pady=(0, 15))

        ttk.Separator(self.main_frame).pack(fill=X, pady=(0, 15))

        form = ttk.Frame(self.main_frame)
        form.pack(fill=X)
        form.columnconfigure(1, weight=1)

        self.var_ma_lhp = self._create_field(
            form, "Mã lớp HP:", 0,
            default=lhp.ma_lhp if lhp else "",
            readonly=(lhp is not None)
        )

        # Combobox chọn môn học
        self.var_ma_mon, self.cmb_mon = self._create_field(
            form, "Học phần:", 1,
            default=lhp.ma_mon if lhp else "",
            widget_type="combobox"
        )
        mon_list = [f"{mh.ma_mon} - {mh.ten_mon}" for mh in ds_mon_hoc]
        self.cmb_mon['values'] = mon_list
        if lhp and ds_mon_hoc:
            for i, mh in enumerate(ds_mon_hoc):
                if mh.ma_mon.upper() == lhp.ma_mon.upper():
                    self.cmb_mon.current(i)
                    break

        # Học kỳ
        self.var_hoc_ky, self.cmb_hk = self._create_field(
            form, "Học kỳ:", 2,
            default=lhp.hoc_ky if lhp else "2025.1",
            widget_type="combobox"
        )
        self.cmb_hk['values'] = ("2025.1", "2025.2", "2025.3")

        self.var_nam_hoc = self._create_field(
            form, "Năm học:", 3,
            default=lhp.nam_hoc if lhp else "2024-2025"
        )

        self._create_buttons(self.main_frame, self._on_save)

    def _on_save(self):
        ma_lhp = self.var_ma_lhp.get().strip()
        ma_mon_raw = self.var_ma_mon.get().strip()
        hoc_ky = self.var_hoc_ky.get().strip()
        nam_hoc = self.var_nam_hoc.get().strip()

        if not ma_lhp:
            Messagebox.show_error("Mã lớp HP không được để trống!", "Lỗi", parent=self)
            return

        # Lấy mã môn từ combobox (format: "MA_MON - Tên môn")
        ma_mon = ma_mon_raw.split(" - ")[0].strip() if " - " in ma_mon_raw else ma_mon_raw

        if not ma_mon:
            Messagebox.show_error("Vui lòng chọn học phần!", "Lỗi", parent=self)
            return

        if not nam_hoc:
            Messagebox.show_error("Năm học không được để trống!", "Lỗi", parent=self)
            return

        ds_mssv = self.lhp.ds_mssv if self.lhp else []
        self.result = LopHocPhan(ma_lhp, ma_mon, hoc_ky, nam_hoc, ds_mssv)
        self.destroy()


class DiemDialog(BaseDialog):
    """Dialog nhập/cập nhật điểm."""

    def __init__(self, parent, ds_sinh_vien, ds_mon_hoc, bd=None):
        title = "✏️ Cập Nhật Điểm" if bd else "➕ Nhập Điểm"
        super().__init__(parent, title, (520, 450))

        self.bd = bd
        self.ds_sinh_vien = ds_sinh_vien
        self.ds_mon_hoc = ds_mon_hoc

        ttk.Label(
            self.main_frame, text=title,
            font=("Segoe UI", 14, "bold"), bootstyle="warning"
        ).pack(anchor=W, pady=(0, 15))

        ttk.Separator(self.main_frame).pack(fill=X, pady=(0, 15))

        form = ttk.Frame(self.main_frame)
        form.pack(fill=X)
        form.columnconfigure(1, weight=1)

        # Sinh viên (Combobox)
        self.var_mssv, self.cmb_sv = self._create_field(
            form, "Sinh viên:", 0,
            default="",
            widget_type="combobox"
        )
        sv_list = [f"{sv.mssv} - {sv.ho_ten}" for sv in ds_sinh_vien]
        self.cmb_sv['values'] = sv_list
        if bd:
            for i, sv in enumerate(ds_sinh_vien):
                if sv.mssv.upper() == bd.mssv.upper():
                    self.cmb_sv.current(i)
                    break
            self.cmb_sv.configure(state="disabled")

        # Môn học (Combobox)
        self.var_ma_mon, self.cmb_mon = self._create_field(
            form, "Học phần:", 1,
            default="",
            widget_type="combobox"
        )
        mon_list = [f"{mh.ma_mon} - {mh.ten_mon}" for mh in ds_mon_hoc]
        self.cmb_mon['values'] = mon_list
        if bd:
            for i, mh in enumerate(ds_mon_hoc):
                if mh.ma_mon.upper() == bd.ma_mon.upper():
                    self.cmb_mon.current(i)
                    break
            self.cmb_mon.configure(state="disabled")

        # Điểm
        self.var_diem_qt = self._create_field(
            form, "Điểm quá trình:", 2,
            default=str(bd.diem_qua_trinh) if bd else ""
        )
        self.var_diem_thi = self._create_field(
            form, "Điểm thi:", 3,
            default=str(bd.diem_thi) if bd else ""
        )

        # Ghi chú
        note_frame = tk.LabelFrame(self.main_frame, text="📌 Ghi chú", padx=10, pady=10)
        note_frame.pack(fill=X, pady=(15, 0))
        ttk.Label(
            note_frame,
            text="• Điểm từ 0 đến 10\n• Điểm tổng kết = 50% × QT + 50% × Thi",
            font=("Segoe UI", 9), bootstyle="secondary"
        ).pack(anchor=W)

        self._create_buttons(self.main_frame, self._on_save)

    def _on_save(self):
        mssv_raw = self.var_mssv.get().strip()
        ma_mon_raw = self.var_ma_mon.get().strip()
        diem_qt_str = self.var_diem_qt.get().strip()
        diem_thi_str = self.var_diem_thi.get().strip()

        # Parse MSSV và mã môn
        mssv = mssv_raw.split(" - ")[0].strip() if " - " in mssv_raw else mssv_raw
        ma_mon = ma_mon_raw.split(" - ")[0].strip() if " - " in ma_mon_raw else ma_mon_raw

        if not mssv:
            Messagebox.show_error("Vui lòng chọn sinh viên!", "Lỗi", parent=self)
            return
        if not ma_mon:
            Messagebox.show_error("Vui lòng chọn học phần!", "Lỗi", parent=self)
            return

        ok, diem_qt, msg = validate_diem(diem_qt_str)
        if not ok:
            Messagebox.show_error(f"Điểm quá trình: {msg}", "Lỗi", parent=self)
            return

        ok, diem_thi, msg = validate_diem(diem_thi_str)
        if not ok:
            Messagebox.show_error(f"Điểm thi: {msg}", "Lỗi", parent=self)
            return

        self.result = BangDiem(mssv, ma_mon, diem_qt, diem_thi)
        self.destroy()


class BangDiemSVDialog(BaseDialog):
    """Dialog xem bảng điểm chi tiết của 1 sinh viên."""

    def __init__(self, parent, sv, ds_bang_diem, ds_mon_hoc, gpa4, gpa10, xep_loai):
        super().__init__(parent, f"📋 Bảng Điểm - {sv.ho_ten}", (700, 520))
        self.sv = sv
        self.ds_bang_diem = ds_bang_diem
        self.ds_mon_hoc = ds_mon_hoc
        self.gpa4 = gpa4
        self.gpa10 = gpa10
        self.xep_loai = xep_loai

        # Thông tin SV
        info_frame = tk.LabelFrame(self.main_frame, text="👤 Thông tin sinh viên", padx=10, pady=10)
        info_frame.pack(fill=X, pady=(0, 10))

        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=X)

        ttk.Label(info_grid, text=f"MSSV: {sv.mssv}", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=W, padx=(0, 30))
        ttk.Label(info_grid, text=f"Họ tên: {sv.ho_ten}", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky=W)
        ttk.Label(info_grid, text=f"Lớp: {sv.lop}", font=("Segoe UI", 10)).grid(row=1, column=0, sticky=W, padx=(0, 30))

        gpa4_str = f"{gpa4:.2f}" if gpa4 >= 0 else "N/A"
        gpa10_str = f"{gpa10:.2f}" if gpa10 >= 0 else "N/A"
        ttk.Label(info_grid, text=f"GPA (hệ 4): {gpa4_str} | GPA (hệ 10): {gpa10_str} | Xếp loại: {xep_loai}",
                  font=("Segoe UI", 10, "bold"), bootstyle="success").grid(row=1, column=1, sticky=W)

        # Bảng điểm
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill=BOTH, expand=True)

        columns = ("ma_mon", "ten_mon", "tin_chi", "diem_qt", "diem_thi", "tong_ket", "he4", "chu", "xep_loai")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12, bootstyle="info")

        headers = [("ma_mon", "Mã HP", 70), ("ten_mon", "Tên học phần", 140), ("tin_chi", "TC", 40),
                   ("diem_qt", "Đ.QT", 55), ("diem_thi", "Đ.Thi", 55), ("tong_ket", "T.Kết", 55),
                   ("he4", "Hệ 4", 50), ("chu", "Chữ", 45), ("xep_loai", "Xếp loại", 90)]

        for col, heading, width in headers:
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor=CENTER)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        tree.pack(fill=BOTH, expand=True)

        # Điền dữ liệu
        for bd in ds_bang_diem:
            ten_mon = ""
            tin_chi = ""
            for mh in ds_mon_hoc:
                if mh.ma_mon.upper() == bd.ma_mon.upper():
                    ten_mon = mh.ten_mon
                    tin_chi = mh.so_tin_chi
                    break
            tree.insert("", END, values=(
                bd.ma_mon, ten_mon, tin_chi,
                f"{bd.diem_qua_trinh:.1f}", f"{bd.diem_thi:.1f}",
                f"{bd.diem_tong_ket:.1f}", f"{bd.diem_he4:.1f}",
                bd.diem_chu, bd.xep_loai
            ))

        # Khung chứa các nút điều khiển dưới cùng
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=X, pady=(10, 0))

        ttk.Button(
            btn_frame, text="🖨️ Xuất File Bảng Điểm", bootstyle="warning",
            command=self._export_txt, width=22, padding=(10, 8)
        ).pack(side=LEFT)

        ttk.Button(
            btn_frame, text="Đóng", bootstyle="secondary",
            command=self.destroy, width=15, padding=(10, 8)
        ).pack(side=RIGHT)

    def _export_txt(self):
        """Xuất bảng điểm chi tiết thành tệp định dạng văn bản .txt."""
        from tkinter import filedialog
        
        filepath = filedialog.asksaveasfilename(
            title="Xuất bảng điểm",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"BangDiem_{self.sv.mssv}.txt",
            parent=self
        )
        if not filepath:
            return
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write(f" BẢNG ĐIỂM CHI TIẾT - SINH VIÊN: {self.sv.ho_ten.upper()} ({self.sv.mssv})\n")
                f.write(f" Lớp: {self.sv.lop} | Email: {self.sv.email}\n")
                f.write("="*70 + "\n")
                f.write(f"{'Mã HP':<8} | {'Tên học phần':<25} | {'TC':<3} | {'Đ.QT':<4} | {'Đ.Thi':<5} | {'TK10':<5} | {'Hệ 4':<4} | {'Chữ'}\n")
                f.write("-" * 70 + "\n")
                for bd in self.ds_bang_diem:
                    ten_mon = ""
                    tin_chi = 0
                    for mh in self.ds_mon_hoc:
                        if mh.ma_mon.upper() == bd.ma_mon.upper():
                            ten_mon = mh.ten_mon
                            tin_chi = mh.so_tin_chi
                            break
                    f.write(f"{bd.ma_mon:<8} | {ten_mon:<25} | {tin_chi:<3} | {bd.diem_qua_trinh:<4.1f} | {bd.diem_thi:<5.1f} | {bd.diem_tong_ket:<5.1f} | {bd.diem_he4:<4.1f} | {bd.diem_chu}\n")
                f.write("-" * 70 + "\n")
                gpa4_str = f"{self.gpa4:.2f}" if self.gpa4 >= 0 else "N/A"
                gpa10_str = f"{self.gpa10:.2f}" if self.gpa10 >= 0 else "N/A"
                f.write(f" GPA Tích lũy (Hệ 10): {gpa10_str}  |  GPA Tích lũy (Hệ 4): {gpa4_str}\n")
                f.write(f" Xếp loại học lực: {self.xep_loai}\n")
                f.write("="*70 + "\n")
            Messagebox.show_info(f"Đã xuất bảng điểm thành công tại:\n{filepath}", "Thành công", parent=self)
        except Exception as e:
            Messagebox.show_error(f"Lỗi xuất file: {e}", "Lỗi", parent=self)
