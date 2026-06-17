import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import tkinter as tk
from tkinter import filedialog

from models import SinhVien, MonHoc, LopHocPhan, BangDiem
from gui.dialogs import SinhVienDialog, MonHocDialog, LopHocPhanDialog, DiemDialog, BangDiemSVDialog
from excel_handler import (
    import_sinh_vien, import_mon_hoc, import_diem,
    export_template_sinh_vien, export_template_mon_hoc, export_template_diem
)


class BaseFrame(ttk.Frame):

    def __init__(self, parent, title, icon, style="primary"):
        super().__init__(parent)
        self.parent = parent
        self.title_text = title
        self.icon = icon
        self.style = style

    def _build_header(self, parent_frame):
        header = ttk.Frame(parent_frame)
        header.pack(fill=X, padx=20, pady=(20, 10))

        ttk.Label(
            header, text=f"{self.icon}  {self.title_text}",
            font=("Segoe UI", 18, "bold"), bootstyle=self.style
        ).pack(side=LEFT)

        return header

    def _build_search_bar(self, parent_frame, search_callback, options=None):
        search_frame = tk.LabelFrame(parent_frame, text="🔍 Tìm kiếm", padx=10, pady=10)
        search_frame.pack(fill=X, padx=20, pady=(0, 10))

        inner = ttk.Frame(search_frame)
        inner.pack(fill=X)

        if options:
            self.var_search_type = ttk.StringVar(value=options[0])
            cmb = ttk.Combobox(
                inner, textvariable=self.var_search_type,
                values=options, state="readonly", width=12,
                bootstyle="info", font=("Segoe UI", 10)
            )
            cmb.pack(side=LEFT, padx=(0, 10))

        self.var_search = ttk.StringVar()
        entry = ttk.Entry(
            inner, textvariable=self.var_search,
            font=("Segoe UI", 10), bootstyle="info"
        )
        entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        ttk.Button(
            inner, text="🔍 Tìm", bootstyle="info",
            command=search_callback, width=8, padding=(8, 5)
        ).pack(side=LEFT, padx=(0, 5))

        ttk.Button(
            inner, text="🔄", bootstyle="secondary-outline",
            command=lambda: (self.var_search.set(""), search_callback()),
            width=3, padding=(8, 5)
        ).pack(side=LEFT)

        # Bind Enter key
        entry.bind("<Return>", lambda e: search_callback())

        return search_frame

    def _build_treeview(self, parent_frame, columns, headings_widths, height=15):
        tree_container = ttk.Frame(parent_frame)
        tree_container.pack(fill=BOTH, expand=True, padx=20, pady=(0, 5))

        tree = ttk.Treeview(
            tree_container, columns=columns,
            show="headings", height=height, bootstyle="info"
        )

        for col, (heading, width) in zip(columns, headings_widths):
            tree.heading(col, text=heading, command=lambda c=col: self._sort_treeview(tree, c))
            tree.column(col, width=width, anchor=CENTER)

        vsb = ttk.Scrollbar(tree_container, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_container, orient=HORIZONTAL, command=tree.xview)
        tree.configure(xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky=NSEW)
        vsb.grid(row=0, column=1, sticky=NS)
        hsb.grid(row=1, column=0, sticky=EW)
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        return tree

    def _sort_treeview(self, tree, col):
        items = [(tree.set(k, col), k) for k in tree.get_children('')]
        try:
            items.sort(key=lambda t: float(t[0]))
        except ValueError:
            items.sort(key=lambda t: t[0].lower())

        if hasattr(self, f'_sort_reverse_{col}'):
            reverse = getattr(self, f'_sort_reverse_{col}')
            setattr(self, f'_sort_reverse_{col}', not reverse)
            if reverse:
                items.reverse()
        else:
            setattr(self, f'_sort_reverse_{col}', True)

        for index, (val, k) in enumerate(items):
            tree.move(k, '', index)

    def _build_action_buttons(self, parent_frame, on_add, on_edit, on_delete, extra_buttons=None):
        btn_frame = ttk.Frame(parent_frame)
        btn_frame.pack(fill=X, padx=20, pady=(5, 15))

        ttk.Button(
            btn_frame, text="➕ Thêm mới", bootstyle="success",
            command=on_add, padding=(12, 8)
        ).pack(side=LEFT, padx=(0, 8))

        ttk.Button(
            btn_frame, text="✏️ Cập nhật thông tin", bootstyle="warning",
            command=on_edit, padding=(12, 8)
        ).pack(side=LEFT, padx=(0, 8))

        ttk.Button(
            btn_frame, text="🗑️ Xóa", bootstyle="danger",
            command=on_delete, padding=(12, 8)
        ).pack(side=LEFT, padx=(0, 8))

        if extra_buttons:
            for text, style, cmd in extra_buttons:
                ttk.Button(
                    btn_frame, text=text, bootstyle=style,
                    command=cmd, padding=(12, 8)
                ).pack(side=LEFT, padx=(0, 8))

        self.lbl_count = ttk.Label(
            btn_frame, text="", font=("Segoe UI", 9), bootstyle="secondary"
        )
        self.lbl_count.pack(side=RIGHT)

        return btn_frame

class SinhVienFrame(BaseFrame):

    def __init__(self, parent, sv_manager, on_data_changed):
        super().__init__(parent, "Quản Lý Sinh Viên", "👤", "primary")
        self.sv_manager = sv_manager
        self.on_data_changed = on_data_changed
        self._build_ui()

    def _build_ui(self):
        self._build_header(self)

        self._build_search_bar(
            self, self._search,
            options=["MSSV", "Họ tên", "Lớp"]
        )

        columns = ("mssv", "ho_ten", "ngay_sinh", "gioi_tinh", "lop", "email")
        headings = [("MSSV", 90), ("Họ tên", 180), ("Ngày sinh", 100),
                    ("Giới tính", 80), ("Lớp", 100), ("Email", 180)]
        self.tree = self._build_treeview(self, columns, headings)
        self.tree.bind("<Double-1>", lambda e: self._on_edit())

        extra = [
            ("📥 Import Excel", "info", self._on_import_excel),
            ("🖨️ In ra", "warning", self._on_export_template),
        ]
        self._build_action_buttons(self, self._on_add, self._on_edit, self._on_delete, extra)

        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
 
        self.sv_manager.sap_xep_mac_dinh()
        
        for sv in self.sv_manager.ds_sinh_vien:
            self.tree.insert("", END, values=(
                sv.mssv, sv.ho_ten, sv.ngay_sinh,
                sv.gioi_tinh, sv.lop, sv.email
            ))
        self.lbl_count.configure(text=f"Tổng: {self.sv_manager.so_luong()} sinh viên")

    def _search(self):
        keyword = self.var_search.get()
        tieu_chi_map = {"MSSV": "mssv", "Họ tên": "ho_ten", "Lớp": "lop"}
        tieu_chi = tieu_chi_map.get(self.var_search_type.get(), "mssv")
        results = self.sv_manager.tim_kiem(keyword, tieu_chi)

        from utils import vietnamese_sort_key
        results.sort(key=lambda sv: vietnamese_sort_key(sv.ho_ten))

        for item in self.tree.get_children():
            self.tree.delete(item)
        for sv in results:
            self.tree.insert("", END, values=(
                sv.mssv, sv.ho_ten, sv.ngay_sinh,
                sv.gioi_tinh, sv.lop, sv.email
            ))
        self.lbl_count.configure(text=f"Tìm thấy: {len(results)} sinh viên")

    def _on_add(self):
        dialog = SinhVienDialog(self.winfo_toplevel())
        self.wait_window(dialog)
        if dialog.result:
            ok, msg = self.sv_manager.them(dialog.result)
            if ok:
                Messagebox.show_info(msg, "Thành công")
                self.refresh()
                self.on_data_changed()
            else:
                Messagebox.show_error(msg, "Lỗi")

    def _on_edit(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Vui lòng chọn sinh viên cần sửa!", "Chưa chọn")
            return

        values = self.tree.item(selected[0])['values']
        mssv = str(values[0])
        sv = self.sv_manager.tim_theo_mssv(mssv)
        if not sv:
            return

        dialog = SinhVienDialog(self.winfo_toplevel(), sv)
        self.wait_window(dialog)
        if dialog.result:
            ok, msg = self.sv_manager.sua(mssv, dialog.result)
            if ok:
                Messagebox.show_info(msg, "Thành công")
                self.refresh()
                self.on_data_changed()
            else:
                Messagebox.show_error(msg, "Lỗi")

    def _on_delete(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Vui lòng chọn sinh viên cần xóa!", "Chưa chọn")
            return

        count = len(selected)
        if count == 1:
            values = self.tree.item(selected[0])['values']
            mssv = str(values[0])
            ho_ten = str(values[1])
            confirm = Messagebox.yesno(
                f"Bạn có chắc muốn xóa sinh viên:\n{ho_ten} ({mssv})?",
                "Xác nhận xóa"
            )
        else:
            confirm = Messagebox.yesno(
                f"Bạn có chắc muốn xóa {count} sinh viên đã chọn?",
                "Xác nhận xóa hàng loạt"
            )

        if confirm == "Yes":
            success_count = 0
            fail_errors = []
            for item in selected:
                values = self.tree.item(item)['values']
                mssv = str(values[0])
                ok, msg = self.sv_manager.xoa(mssv)
                if ok:
                    success_count += 1
                else:
                    fail_errors.append(f"{mssv}: {msg}")
            
            if success_count > 0:
                Messagebox.show_info(f"Đã xóa thành công {success_count}/{count} sinh viên.", "Thành công")
            if fail_errors:
                Messagebox.show_error("Một số lỗi xảy ra:\n" + "\n".join(fail_errors[:5]), "Lỗi")
            
            self.refresh()
            self.on_data_changed()

    def _on_import_excel(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file Excel danh sách sinh viên",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
            parent=self.winfo_toplevel()
        )
        if not filepath:
            return

        ds_sv, errors = import_sinh_vien(filepath)

        if not ds_sv and errors:
            Messagebox.show_error("\n".join(errors), "Lỗi import")
            return

        count_ok = 0
        count_skip = 0
        for sv in ds_sv:
            ok, _ = self.sv_manager.them(sv)
            if ok:
                count_ok += 1
            else:
                count_skip += 1

        msg = f"✅ Đã import {count_ok} sinh viên thành công!"
        if count_skip > 0:
            msg += f"\n⚠️ Bỏ qua {count_skip} (trùng MSSV)"
        if errors:
            msg += f"\n❌ Lỗi: {len(errors)} hàng"

        Messagebox.show_info(msg, "Kết quả Import")
        self.refresh()
        self.on_data_changed()

    def _on_export_template(self):
        filepath = filedialog.asksaveasfilename(
            title="Lưu file mẫu danh sách sinh viên",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="Mau_DanhSachSinhVien.xlsx",
            parent=self.winfo_toplevel()
        )
        if not filepath:
            return
        try:
            export_template_sinh_vien(filepath)
            Messagebox.show_info(f"Đã tạo file mẫu tại:\n{filepath}", "Thành công")
        except Exception as e:
            Messagebox.show_error(f"Lỗi tạo file: {e}", "Lỗi")

class MonHocFrame(BaseFrame):

    def __init__(self, parent, mh_manager, on_data_changed):
        super().__init__(parent, "Quản Lý Học Phần", "📚", "info")
        self.mh_manager = mh_manager
        self.on_data_changed = on_data_changed
        self._build_ui()

    def _build_ui(self):
        self._build_header(self)

        self._build_search_bar(self, self._search)

        columns = ("ma_mon", "ten_mon", "so_tin_chi")
        headings = [("Mã học phần", 120), ("Tên học phần", 350), ("Số tín chỉ", 100)]
        self.tree = self._build_treeview(self, columns, headings)
        self.tree.bind("<Double-1>", lambda e: self._on_edit())

        extra = [
            ("📥 Import Excel", "info", self._on_import_excel),
        ]
        self._build_action_buttons(self, self._on_add, self._on_edit, self._on_delete, extra)
        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for mh in self.mh_manager.ds_mon_hoc:
            self.tree.insert("", END, values=(
                mh.ma_mon, mh.ten_mon, mh.so_tin_chi
            ))
        self.lbl_count.configure(text=f"Tổng: {self.mh_manager.so_luong()} học phần")

    def _search(self):
        keyword = self.var_search.get()
        results = self.mh_manager.tim_kiem(keyword)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for mh in results:
            self.tree.insert("", END, values=(
                mh.ma_mon, mh.ten_mon, mh.so_tin_chi
            ))
        self.lbl_count.configure(text=f"Tìm thấy: {len(results)} học phần")

    def _on_add(self):
        dialog = MonHocDialog(self.winfo_toplevel())
        self.wait_window(dialog)
        if dialog.result:
            ok, msg = self.mh_manager.them(dialog.result)
            if ok:
                Messagebox.show_info(msg, "Thành công")
                self.refresh()
                self.on_data_changed()
            else:
                Messagebox.show_error(msg, "Lỗi")

    def _on_edit(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Vui lòng chọn học phần cần sửa!", "Chưa chọn")
            return
        values = self.tree.item(selected[0])['values']
        ma_mon = str(values[0])
        mh = self.mh_manager.tim_theo_ma(ma_mon)
        if not mh:
            return

        dialog = MonHocDialog(self.winfo_toplevel(), mh)
        self.wait_window(dialog)
        if dialog.result:
            ok, msg = self.mh_manager.sua(ma_mon, dialog.result)
            if ok:
                Messagebox.show_info(msg, "Thành công")
                self.refresh()
                self.on_data_changed()
            else:
                Messagebox.show_error(msg, "Lỗi")

    def _on_delete(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Vui lòng chọn học phần cần xóa!", "Chưa chọn")
            return

        count = len(selected)
        if count == 1:
            values = self.tree.item(selected[0])['values']
            ma_mon = str(values[0])
            ten_mon = str(values[1])
            confirm = Messagebox.yesno(
                f"Bạn có chắc muốn xóa học phần:\n{ten_mon} ({ma_mon})?",
                "Xác nhận xóa"
            )
        else:
            confirm = Messagebox.yesno(
                f"Bạn có chắc muốn xóa {count} học phần đã chọn?",
                "Xác nhận xóa hàng loạt"
            )

        if confirm == "Yes":
            success_count = 0
            fail_errors = []
            for item in selected:
                values = self.tree.item(item)['values']
                ma_mon = str(values[0])
                ok, msg = self.mh_manager.xoa(ma_mon)
                if ok:
                    success_count += 1
                else:
                    fail_errors.append(f"{ma_mon}: {msg}")
            
            if success_count > 0:
                Messagebox.show_info(f"Đã xóa thành công {success_count}/{count} học phần.", "Thành công")
            if fail_errors:
                Messagebox.show_error("Một số lỗi xảy ra:\n" + "\n".join(fail_errors[:5]), "Lỗi")
            
            self.refresh()
            self.on_data_changed()

    def _on_import_excel(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file Excel danh sách học phần",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
            parent=self.winfo_toplevel()
        )
        if not filepath:
            return

        ds_mh, errors = import_mon_hoc(filepath)

        if not ds_mh and errors:
            Messagebox.show_error("\n".join(errors), "Lỗi import")
            return

        count_ok = 0
        count_skip = 0
        for mh in ds_mh:
            ok, _ = self.mh_manager.them(mh)
            if ok:
                count_ok += 1
            else:
                count_skip += 1

        msg = f"✅ Đã import {count_ok} học phần thành công!"
        if count_skip > 0:
            msg += f"\n⚠️ Bỏ qua {count_skip} (trùng mã học phần)"
        if errors:
            msg += f"\n❌ Lỗi: {len(errors)} hàng"

        Messagebox.show_info(msg, "Kết quả Import")
        self.refresh()
        self.on_data_changed()

    def _on_export_template(self):
        filepath = filedialog.asksaveasfilename(
            title="Lưu file mẫu danh sách học phần",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="Mau_DanhSachHocPhan.xlsx",
            parent=self.winfo_toplevel()
        )
        if not filepath:
            return
        try:
            export_template_mon_hoc(filepath)
            Messagebox.show_info(f"Đã tạo file mẫu tại:\n{filepath}", "Thành công")
        except Exception as e:
            Messagebox.show_error(f"Lỗi tạo file: {e}", "Lỗi")

class LopHocPhanFrame(BaseFrame):

    def __init__(self, parent, lhp_manager, sv_manager, mh_manager, on_data_changed):
        super().__init__(parent, "Quản Lý Lớp Học Phần", "🏫", "success")
        self.lhp_manager = lhp_manager
        self.sv_manager = sv_manager
        self.mh_manager = mh_manager
        self.on_data_changed = on_data_changed
        self._build_ui()

    def _build_ui(self):
        self._build_header(self)
        self._build_search_bar(self, self._search)

        paned = ttk.Panedwindow(self, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True, padx=20, pady=(0, 5))

        left_frame = tk.LabelFrame(paned, text="📋 Danh sách Lớp Học Phần", padx=5, pady=5)

        columns = ("ma_lhp", "ma_mon", "ten_mon", "hoc_ky", "nam_hoc", "so_sv")
        headings = [("Mã LHP", 80), ("Mã học phần", 80), ("Tên học phần", 140),
                    ("Học kỳ", 60), ("Năm học", 90), ("Số SV", 50)]

        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=12, bootstyle="info")
        for col, (heading, width) in zip(columns, headings):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=CENTER)

        vsb = ttk.Scrollbar(left_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb.pack(side=RIGHT, fill=Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select_lhp)

        paned.add(left_frame, weight=3)

        right_frame = tk.LabelFrame(paned, text="👥 Sinh viên trong lớp", padx=5, pady=5)

        self.tree_sv = ttk.Treeview(
            right_frame, columns=("mssv", "ho_ten", "lop"),
            show="headings", height=12, bootstyle="info"
        )
        self.tree_sv.heading("mssv", text="MSSV")
        self.tree_sv.heading("ho_ten", text="Họ tên")
        self.tree_sv.heading("lop", text="Lớp")
        self.tree_sv.column("mssv", width=80, anchor=CENTER)
        self.tree_sv.column("ho_ten", width=150, anchor=W)
        self.tree_sv.column("lop", width=70, anchor=CENTER)

        self.tree_sv.pack(fill=BOTH, expand=True)

        sv_btn_frame = ttk.Frame(right_frame)
        sv_btn_frame.pack(fill=X, pady=(5, 0))

        ttk.Button(
            sv_btn_frame, text="➕ Thêm SV", bootstyle="success-outline",
            command=self._on_add_sv_to_class, padding=(8, 5)
        ).pack(side=LEFT, padx=(0, 5))

        ttk.Button(
            sv_btn_frame, text="➖ Xóa SV", bootstyle="danger-outline",
            command=self._on_remove_sv_from_class, padding=(8, 5)
        ).pack(side=LEFT)

        paned.add(right_frame, weight=2)

        self._build_action_buttons(self, self._on_add, self._on_edit, self._on_delete)
        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for lhp in self.lhp_manager.ds_lop_hp:
            ten_mon = ""
            for mh in self.mh_manager.ds_mon_hoc:
                if mh.ma_mon.upper() == lhp.ma_mon.upper():
                    ten_mon = mh.ten_mon
                    break
            self.tree.insert("", END, values=(
                lhp.ma_lhp, lhp.ma_mon, ten_mon,
                lhp.hoc_ky, lhp.nam_hoc, lhp.so_luong_sv()
            ))
        self.lbl_count.configure(text=f"Tổng: {self.lhp_manager.so_luong()} lớp HP")
        for item in self.tree_sv.get_children():
            self.tree_sv.delete(item)

    def _search(self):
        keyword = self.var_search.get()
        results = self.lhp_manager.tim_kiem(keyword)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for lhp in results:
            ten_mon = ""
            for mh in self.mh_manager.ds_mon_hoc:
                if mh.ma_mon.upper() == lhp.ma_mon.upper():
                    ten_mon = mh.ten_mon
                    break
            self.tree.insert("", END, values=(
                lhp.ma_lhp, lhp.ma_mon, ten_mon,
                lhp.hoc_ky, lhp.nam_hoc, lhp.so_luong_sv()
            ))
        self.lbl_count.configure(text=f"Tìm thấy: {len(results)} lớp HP")

    def _on_select_lhp(self, event):
        for item in self.tree_sv.get_children():
            self.tree_sv.delete(item)

        selected = self.tree.selection()
        if not selected:
            return

        ma_lhp = str(self.tree.item(selected[0])['values'][0])
        lhp = self.lhp_manager.tim_theo_ma(ma_lhp)
        if not lhp:
            return

        for mssv in lhp.ds_mssv:
            sv = self.sv_manager.tim_theo_mssv(mssv)
            if sv:
                self.tree_sv.insert("", END, values=(sv.mssv, sv.ho_ten, sv.lop))
            else:
                self.tree_sv.insert("", END, values=(mssv, "(Không tìm thấy)", ""))

    def _on_add(self):
        if not self.mh_manager.ds_mon_hoc:
            Messagebox.show_warning("Chưa có học phần nào! Vui lòng thêm học phần trước.", "Chưa có dữ liệu")
            return
        dialog = LopHocPhanDialog(self.winfo_toplevel(), self.mh_manager.ds_mon_hoc)
        self.wait_window(dialog)
        if dialog.result:
            ok, msg = self.lhp_manager.them(dialog.result)
            if ok:
                Messagebox.show_info(msg, "Thành công")
                self.refresh()
                self.on_data_changed()
            else:
                Messagebox.show_error(msg, "Lỗi")

    def _on_edit(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Vui lòng chọn lớp HP cần sửa!", "Chưa chọn")
            return
        ma_lhp = str(self.tree.item(selected[0])['values'][0])
        lhp = self.lhp_manager.tim_theo_ma(ma_lhp)
        if not lhp:
            return

        dialog = LopHocPhanDialog(self.winfo_toplevel(), self.mh_manager.ds_mon_hoc, lhp)
        self.wait_window(dialog)
        if dialog.result:
            ok, msg = self.lhp_manager.sua(ma_lhp, dialog.result)
            if ok:
                Messagebox.show_info(msg, "Thành công")
                self.refresh()
                self.on_data_changed()
            else:
                Messagebox.show_error(msg, "Lỗi")

    def _on_delete(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Vui lòng chọn lớp HP cần xóa!", "Chưa chọn")
            return
        ma_lhp = str(self.tree.item(selected[0])['values'][0])
        confirm = Messagebox.yesno(f"Bạn có chắc muốn xóa lớp HP: {ma_lhp}?", "Xác nhận xóa")
        if confirm == "Yes":
            ok, msg = self.lhp_manager.xoa(ma_lhp)
            if ok:
                Messagebox.show_info(msg, "Thành công")
                self.refresh()
                self.on_data_changed()
            else:
                Messagebox.show_error(msg, "Lỗi")

    def _on_add_sv_to_class(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Vui lòng chọn lớp HP trước!", "Chưa chọn lớp")
            return

        ma_lhp = str(self.tree.item(selected[0])['values'][0])

        if not self.sv_manager.ds_sinh_vien:
            Messagebox.show_warning("Chưa có sinh viên nào!", "Chưa có dữ liệu")
            return

        popup = ttk.Toplevel(self.winfo_toplevel())
        popup.title("Chọn sinh viên")
        popup.geometry("400x400")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        ttk.Label(popup, text="Chọn sinh viên để thêm vào lớp:", font=("Segoe UI", 11, "bold")).pack(padx=15, pady=10)

        listbox_frame = ttk.Frame(popup)
        listbox_frame.pack(fill=BOTH, expand=True, padx=15, pady=(0, 10))

        listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, font=("Segoe UI", 10))
        scrollbar = ttk.Scrollbar(listbox_frame, orient=VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        lhp = self.lhp_manager.tim_theo_ma(ma_lhp)
        sv_list = []
        for sv in self.sv_manager.ds_sinh_vien:
            if sv.mssv not in (lhp.ds_mssv if lhp else []):
                listbox.insert(tk.END, f"{sv.mssv} - {sv.ho_ten} ({sv.lop})")
                sv_list.append(sv.mssv)

        def _add_selected():
            indices = listbox.curselection()
            count = 0
            for idx in indices:
                mssv = sv_list[idx]
                ok, _ = self.lhp_manager.them_sv_vao_lop(ma_lhp, mssv)
                if ok:
                    count += 1
            popup.destroy()
            if count > 0:
                Messagebox.show_info(f"Đã thêm {count} sinh viên vào lớp {ma_lhp}!", "Thành công")
                self.refresh()
                self._on_select_lhp(None)
                # Re-select the same item
                for item in self.tree.get_children():
                    if str(self.tree.item(item)['values'][0]) == ma_lhp:
                        self.tree.selection_set(item)
                        self._on_select_lhp(None)
                        break
                self.on_data_changed()

        ttk.Button(popup, text="✅ Thêm", bootstyle="success", command=_add_selected, padding=(15, 8)).pack(pady=(0, 15))

    def _on_remove_sv_from_class(self):
        selected_lhp = self.tree.selection()
        selected_sv = self.tree_sv.selection()

        if not selected_lhp:
            Messagebox.show_warning("Vui lòng chọn lớp HP!", "Chưa chọn")
            return
        if not selected_sv:
            Messagebox.show_warning("Vui lòng chọn sinh viên cần xóa!", "Chưa chọn")
            return

        ma_lhp = str(self.tree.item(selected_lhp[0])['values'][0])
        mssv = str(self.tree_sv.item(selected_sv[0])['values'][0])

        confirm = Messagebox.yesno(
            f"Xóa SV {mssv} khỏi lớp {ma_lhp}?", "Xác nhận"
        )
        if confirm == "Yes":
            ok, msg = self.lhp_manager.xoa_sv_khoi_lop(ma_lhp, mssv)
            if ok:
                self.refresh()
                for item in self.tree.get_children():
                    if str(self.tree.item(item)['values'][0]) == ma_lhp:
                        self.tree.selection_set(item)
                        self._on_select_lhp(None)
                        break
                self.on_data_changed()

class DiemFrame(BaseFrame):

    def __init__(self, parent, diem_manager, sv_manager, mh_manager, on_data_changed):
        super().__init__(parent, "Quản Lý Điểm Số", "📊", "warning")
        self.diem_manager = diem_manager
        self.sv_manager = sv_manager
        self.mh_manager = mh_manager
        self.on_data_changed = on_data_changed
        self._build_ui()

    def _build_ui(self):
        self._build_header(self)
        self._build_search_bar(self, self._search)

        columns = ("mssv", "ho_ten", "ma_mon", "ten_mon", "diem_qt", "diem_thi",
                    "tong_ket", "he4", "chu", "xep_loai")
        headings = [("MSSV", 75), ("Họ tên", 140), ("Mã HP", 65), ("Tên học phần", 120),
                    ("Đ.QT", 50), ("Đ.Thi", 50), ("T.Kết", 55), ("Hệ 4", 45),
                    ("Chữ", 40), ("Xếp loại", 85)]
        self.tree = self._build_treeview(self, columns, headings)
        self.tree.bind("<Double-1>", lambda e: self._on_edit())

        extra = [
            ("📋 Bảng điểm SV", "success", self._on_view_bangdiem),
            ("📥 Import Excel", "info", self._on_import_excel),
            ("🖨️ In ra", "warning", self._on_export_template),
        ]
        self._build_action_buttons(self, self._on_add, self._on_edit, self._on_delete, extra)
        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for bd in self.diem_manager.ds_diem:
            ho_ten = ""
            ten_mon = ""
            sv = self.sv_manager.tim_theo_mssv(bd.mssv)
            if sv:
                ho_ten = sv.ho_ten
            mh = self.mh_manager.tim_theo_ma(bd.ma_mon)
            if mh:
                ten_mon = mh.ten_mon

            self.tree.insert("", END, values=(
                bd.mssv, ho_ten, bd.ma_mon, ten_mon,
                f"{bd.diem_qua_trinh:.1f}", f"{bd.diem_thi:.1f}",
                f"{bd.diem_tong_ket:.1f}", f"{bd.diem_he4:.1f}",
                bd.diem_chu, bd.xep_loai
            ))
        self.lbl_count.configure(text=f"Tổng: {self.diem_manager.so_luong()} bản ghi điểm")

    def _search(self):
        keyword = self.var_search.get()
        results = self.diem_manager.tim_kiem(keyword)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for bd in results:
            ho_ten = ""
            ten_mon = ""
            sv = self.sv_manager.tim_theo_mssv(bd.mssv)
            if sv:
                ho_ten = sv.ho_ten
            mh = self.mh_manager.tim_theo_ma(bd.ma_mon)
            if mh:
                ten_mon = mh.ten_mon

            self.tree.insert("", END, values=(
                bd.mssv, ho_ten, bd.ma_mon, ten_mon,
                f"{bd.diem_qua_trinh:.1f}", f"{bd.diem_thi:.1f}",
                f"{bd.diem_tong_ket:.1f}", f"{bd.diem_he4:.1f}",
                bd.diem_chu, bd.xep_loai
            ))
        self.lbl_count.configure(text=f"Tìm thấy: {len(results)} bản ghi")

    def _on_add(self):
        if not self.sv_manager.ds_sinh_vien:
            Messagebox.show_warning("Chưa có sinh viên! Vui lòng thêm sinh viên trước.", "Chưa có dữ liệu")
            return
        if not self.mh_manager.ds_mon_hoc:
            Messagebox.show_warning("Chưa có môn học! Vui lòng thêm môn học trước.", "Chưa có dữ liệu")
            return

        dialog = DiemDialog(
            self.winfo_toplevel(),
            self.sv_manager.ds_sinh_vien,
            self.mh_manager.ds_mon_hoc
        )
        self.wait_window(dialog)
        if dialog.result:
            ok, msg = self.diem_manager.nhap_diem(dialog.result)
            if ok:
                Messagebox.show_info(msg, "Thành công")
                self.refresh()
                self.on_data_changed()

    def _on_edit(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Vui lòng chọn bản ghi cần sửa!", "Chưa chọn")
            return

        values = self.tree.item(selected[0])['values']
        mssv = str(values[0])
        ma_mon = str(values[2])
        bd = self.diem_manager.lay_diem(mssv, ma_mon)
        if not bd:
            return

        dialog = DiemDialog(
            self.winfo_toplevel(),
            self.sv_manager.ds_sinh_vien,
            self.mh_manager.ds_mon_hoc,
            bd
        )
        self.wait_window(dialog)
        if dialog.result:
            ok, msg = self.diem_manager.nhap_diem(dialog.result)
            if ok:
                Messagebox.show_info(msg, "Thành công")
                self.refresh()
                self.on_data_changed()

    def _on_delete(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("Vui lòng chọn bản ghi cần xóa!", "Chưa chọn")
            return

        count = len(selected)
        if count == 1:
            values = self.tree.item(selected[0])['values']
            mssv = str(values[0])
            ma_mon = str(values[2])
            confirm = Messagebox.yesno(
                f"Xóa điểm môn {ma_mon} của SV {mssv}?", "Xác nhận xóa"
            )
        else:
            confirm = Messagebox.yesno(
                f"Bạn có chắc muốn xóa {count} bản ghi điểm đã chọn?",
                "Xác nhận xóa hàng loạt"
            )

        if confirm == "Yes":
            success_count = 0
            fail_errors = []
            for item in selected:
                values = self.tree.item(item)['values']
                mssv = str(values[0])
                ma_mon = str(values[2])
                ok, msg = self.diem_manager.xoa_diem(mssv, ma_mon)
                if ok:
                    success_count += 1
                else:
                    fail_errors.append(f"{mssv} - {ma_mon}: {msg}")
            
            if success_count > 0:
                Messagebox.show_info(f"Đã xóa thành công {success_count}/{count} bản ghi điểm.", "Thành công")
            if fail_errors:
                Messagebox.show_error("Một số lỗi xảy ra:\n" + "\n".join(fail_errors[:5]), "Lỗi")
            
            self.refresh()
            self.on_data_changed()

    def _on_view_bangdiem(self):
        selected = self.tree.selection()
        mssv = ""

        if selected:
            values = self.tree.item(selected[0])['values']
            mssv = str(values[0])
        else:
            # Popup nhập MSSV
            popup = ttk.Toplevel(self.winfo_toplevel())
            popup.title("Nhập MSSV")
            popup.geometry("350x150")
            popup.transient(self.winfo_toplevel())
            popup.grab_set()

            ttk.Label(popup, text="Nhập MSSV để xem bảng điểm:", font=("Segoe UI", 11)).pack(padx=20, pady=(20, 10))
            var = ttk.StringVar()
            entry = ttk.Entry(popup, textvariable=var, font=("Segoe UI", 11), bootstyle="info")
            entry.pack(padx=20, fill=X)
            entry.focus_set()

            result = [None]

            def _on_ok(event=None):
                result[0] = var.get().strip()
                popup.destroy()

            entry.bind("<Return>", _on_ok)
            ttk.Button(popup, text="OK", bootstyle="primary", command=_on_ok, padding=(15, 8)).pack(pady=15)
            popup.wait_window()
            mssv = result[0] if result[0] else ""

        if not mssv:
            return

        sv = self.sv_manager.tim_theo_mssv(mssv)
        if not sv:
            Messagebox.show_error(f"Không tìm thấy SV có MSSV: {mssv}", "Lỗi")
            return

        ds_bd = self.diem_manager.lay_diem_sv(mssv)
        if not ds_bd:
            Messagebox.show_warning(f"SV {sv.ho_ten} chưa có điểm nào!", "Chưa có điểm")
            return

        gpa4 = self.diem_manager.tinh_gpa_he4(mssv, self.mh_manager.ds_mon_hoc)
        gpa10 = self.diem_manager.tinh_gpa_he10(mssv, self.mh_manager.ds_mon_hoc)
        xl = self.diem_manager.xep_loai_sv(mssv, self.mh_manager.ds_mon_hoc)

        BangDiemSVDialog(
            self.winfo_toplevel(), sv, ds_bd,
            self.mh_manager.ds_mon_hoc, gpa4, gpa10, xl
        )

    def _on_import_excel(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file Excel danh sách điểm",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
            parent=self.winfo_toplevel()
        )
        if not filepath:
            return

        ds_diem, errors = import_diem(filepath)

        if not ds_diem and errors:
            Messagebox.show_error("\n".join(errors), "Lỗi import")
            return

        count_ok = 0
        count_fail = 0
        for bd in ds_diem:
            # Kiểm tra xem SV và Môn học có tồn tại không trước khi lưu
            sv = self.sv_manager.tim_theo_mssv(bd.mssv)
            mh = self.mh_manager.tim_theo_ma(bd.ma_mon)
            if not sv or not mh:
                errors.append(f"Hàng bỏ qua: MSSV {bd.mssv} hoặc Mã môn {bd.ma_mon} không tồn tại trong hệ thống")
                count_fail += 1
                continue
            
            ok, _ = self.diem_manager.nhap_diem(bd)
            if ok:
                count_ok += 1
            else:
                count_fail += 1

        msg = f"✅ Đã import {count_ok} bản ghi điểm thành công!"
        if count_fail > 0:
            msg += f"\n⚠️ Thất bại/Bỏ qua: {count_fail}"
        if errors:
            # Hiện tối đa 5 lỗi để tránh tràn màn hình
            limit_errs = errors[:5]
            msg += f"\n❌ Chi tiết một số lỗi:\n" + "\n".join(limit_errs)
            if len(errors) > 5:
                msg += f"\n... và {len(errors) - 5} lỗi khác."

        Messagebox.show_info(msg, "Kết quả Import")
        self.refresh()
        self.on_data_changed()

    def _on_export_template(self):
        filepath = filedialog.asksaveasfilename(
            title="Lưu file mẫu nhập điểm",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="Mau_NhapDiem.xlsx",
            parent=self.winfo_toplevel()
        )
        if not filepath:
            return
        try:
            export_template_diem(filepath)
            Messagebox.show_info(f"Đã tạo file mẫu tại:\n{filepath}", "Thành công")
        except Exception as e:
            Messagebox.show_error(f"Lỗi tạo file: {e}", "Lỗi")

