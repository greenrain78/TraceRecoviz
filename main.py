import os
import sys
from pathlib import Path

from PySide6.QtCore import (
    QDir, Qt, QSortFilterProxyModel, QSettings, QRegularExpression, QSize, QModelIndex
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QImageReader, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QTreeView, QTableView, QLineEdit, QLabel, QHeaderView, QFileSystemModel,
    QSplitter, QStyleFactory, QToolBar, QStyle, QSizePolicy,
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QStackedWidget,
    QGroupBox, QPushButton, QCheckBox, QComboBox, QFormLayout, QMessageBox
)

APP_ORG = "ExampleCo"
APP_NAME = "TraceRecoViz"  # 프로젝트 목적에 맞춘 이름


# ------------------------------- 스타일/아이콘 -------------------------------
def themed_icons_available():
    return QIcon.fromTheme("folder").isNull() is False


def make_icon(fallback_name: str, std_pixmap: QStyle.StandardPixmap) -> QIcon:
    if themed_icons_available():
        ic = QIcon.fromTheme(fallback_name)
        if not ic.isNull():
            return ic
    return QApplication.style().standardIcon(std_pixmap)


DARK_QSS = """
* { font-family: 'Inter','Pretendard','Apple SD Gothic Neo','Segoe UI',sans-serif; }
QMainWindow, QWidget { background: #0f1115; color: #E6E9EF; }
QToolBar { background: #141822; border: 0; padding: 8px; }
QToolButton { color: #E6E9EF; background: transparent; border-radius: 10px; padding: 6px 10px; }
QToolButton:hover { background: #202636; }
QToolButton:pressed { background: #2a3142; }
QLineEdit, QComboBox {
    background: #151a24; border: 1px solid #283044; border-radius: 10px; padding: 8px 10px;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #3e7cff; }
QGroupBox {
    border: 1px solid #283044; border-radius: 12px; margin-top: 16px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #c9d1e1; background: #0f1115;
}
QTreeView, QTableView {
    background: #121724; alternate-background-color: #171c2b;
    border: 1px solid #283044; border-radius: 12px; padding: 6px;
}
QHeaderView::section { background: #141a28; color: #C6D0E0; border: 0; padding: 8px; }
QTreeView::item, QTableView::item { padding: 6px; }
QTreeView::item:selected, QTableView::item:selected { background: #22314f; }
QPlainTextEdit {
    background: #121724; border: 1px solid #283044; border-radius: 12px; padding: 8px;
}
QPushButton {
    background: #2f5ae3; color: white; border: 0; border-radius: 10px; padding: 8px 12px;
}
QPushButton:disabled {
    background: #3b4255; color: #9aa2b1;
}
QPushButton:hover:!disabled { background: #3965ff; }
#Breadcrumb { color: #a9b4c7; }
#PreviewBox { border: 1px solid #283044; border-radius: 12px; background: #121724; }
#PreviewHeader { color: #C6D0E0; }
"""

LIGHT_QSS = """
* { font-family: 'Inter','Pretendard','Apple SD Gothic Neo','Segoe UI',sans-serif; }
QMainWindow, QWidget { background: #FAFBFD; color: #1c1f24; }
QToolBar { background: #ffffff; border: 0; padding: 8px; }
QToolButton { color: #1c1f24; background: transparent; border-radius: 10px; padding: 6px 10px; }
QToolButton:hover { background: #EFF3F9; }
QToolButton:pressed { background: #E3EAF5; }
QLineEdit, QComboBox {
    background: #ffffff; border: 1px solid #DDE3EE; border-radius: 10px; padding: 8px 10px;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #3e7cff; }
QGroupBox {
    border: 1px solid #E7ECF5; border-radius: 12px; margin-top: 16px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #465069; background: #FAFBFD;
}
QTreeView, QTableView {
    background: #ffffff; alternate-background-color: #F7F9FC;
    border: 1px solid #E7ECF5; border-radius: 12px; padding: 6px;
}
QHeaderView::section { background: #F4F7FB; color: #464b53; border: 0; padding: 8px; }
QTreeView::item, QTableView::item { padding: 6px; }
QTreeView::item:selected, QTableView::item:selected { background: #E7F0FF; }
QPlainTextEdit {
    background: #ffffff; border: 1px solid #E7ECF5; border-radius: 12px; padding: 8px;
}
QPushButton {
    background: #2f5ae3; color: white; border: 0; border-radius: 10px; padding: 8px 12px;
}
QPushButton:disabled {
    background: #C6D0E1; color: #8e97a6;
}
QPushButton:hover:!disabled { background: #3965ff; }
#Breadcrumb { color: #6b7280; }
#PreviewBox { border: 1px solid #E7ECF5; border-radius: 12px; background: #ffffff; }
#PreviewHeader { color: #464b53; }
"""
# -----------------------------------------------------------------------------


# ------------------------------ 파일 모델/프록시 ------------------------------
class FilesProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setRecursiveFilteringEnabled(True)

    def filterAcceptsRow(self, source_row, source_parent):
        index0 = self.sourceModel().index(source_row, 0, source_parent)
        if not index0.isValid():
            return False
        is_dir = self.sourceModel().isDir(index0)
        if is_dir:
            name = self.sourceModel().fileName(index0)
            pattern = self.filterRegularExpression()
            if pattern.match(name).hasMatch():
                return True
            for r in range(self.sourceModel().rowCount(index0)):
                if self.filterAcceptsRow(r, index0):
                    return True
            return False
        return super().filterAcceptsRow(source_row, source_parent)
# -----------------------------------------------------------------------------


# ------------------------------- 미리보기 패널 --------------------------------
class PreviewPanel(QWidget):
    """
    - 이미지: 썸네일
    - 텍스트: 최대 200KB, UTF-8→CP949→latin-1 순서로 디코딩
    - 기타: 간단 정보
    - 추가: Makefile/CMakeLists.txt/Dockerfile 등 '확장자 없는/특수 이름'도 텍스트 처리
    """
    TEXT_EXTS = {
        ".txt", ".md", ".py", ".cpp", ".c", ".h", ".hpp", ".json", ".xml",
        ".csv", ".log", ".ini", ".yaml", ".yml", ".toml", ".html", ".htm",
        ".css", ".js", ".ts", ".rs", ".go", ".java", ".kt", ".sh", ".bat",
        ".gradle", ".cmake"
    }
    # 확장자 없이 자주 쓰는 텍스트/빌드 스크립트 이름들
    NAME_TEXT_FILES = {
        "makefile", "gnumakefile", "dockerfile", "cmakelists.txt", "meson.build",
        "sconstruct", "sconscript", "rakefile", "gemfile", "workspace", "build",
        "requirements.txt", "pipfile", "pyproject.toml", "poetry.lock",
        "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "go.mod", "go.sum", "cargo.toml", "cargo.lock", "gemfile.lock",
        "settings.gradle", "build.gradle", "gradle.properties",
        ".gitignore", ".gitattributes", ".editorconfig", ".env",
        ".clang-format", ".clang-tidy", ".prettierrc", ".eslintrc", ".flake8",
        "vcpkg.json", "conanfile.txt", "conanfile.py", "bazel.build", "bazel.rc"
    }
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff", ".tif", ".ico"}

    MAX_TEXT_BYTES = 200 * 1024  # 200KB
    SNIFF_BYTES = 64 * 1024      # 텍스트/바이너리 판정용

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self); outer.setContentsMargins(10,8,10,10); outer.setSpacing(8)

        header = QHBoxLayout()
        self.icon_label = QLabel(); self.icon_label.setFixedSize(18,18)
        self.path_label = QLabel("미리보기 없음"); self.path_label.setObjectName("PreviewHeader")
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header.addWidget(self.icon_label); header.addWidget(self.path_label, 1); header.addStretch()

        self.stack = QStackedWidget(); self.stack.setObjectName("PreviewBox")

        # 이미지 뷰
        img_wrap = QWidget(); img_layout = QVBoxLayout(img_wrap); img_layout.setContentsMargins(10,10,10,10)
        self.image_label = QLabel(alignment=Qt.AlignCenter); self.image_label.setMinimumHeight(160)
        img_layout.addWidget(self.image_label); self.stack.addWidget(img_wrap)

        # 텍스트 뷰
        self.text_edit = QPlainTextEdit(); self.text_edit.setReadOnly(True)
        self.stack.addWidget(self.text_edit)

        # 정보 뷰
        self.info_label = QLabel(alignment=Qt.AlignLeft | Qt.AlignTop); self.info_label.setWordWrap(True)
        info_wrap = QWidget(); info_layout = QVBoxLayout(info_wrap); info_layout.setContentsMargins(12,12,12,12)
        info_layout.addWidget(self.info_label); self.stack.addWidget(info_wrap)

        outer.addLayout(header); outer.addWidget(self.stack, 1)
        self.clear()

    def clear(self):
        self.path_label.setText("미리보기 없음")
        self.icon_label.setPixmap(QPixmap())
        self.image_label.clear()
        self.text_edit.clear()
        self.info_label.setText("파일을 선택하면 여기에서 미리보기가 표시됩니다.")

    def _set_header(self, path: str):
        self.path_label.setText(path)
        fi_icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
        self.icon_label.setPixmap(fi_icon.pixmap(18, 18))

    def update_preview(self, path: str):
        if not path or not os.path.exists(path):
            self.clear(); return
        self._set_header(path)
        if os.path.isdir(path):
            self.info_label.setText(self._format_info(path, True))
            self.stack.setCurrentIndex(2); return

        p = Path(path)
        suffix = p.suffix.lower()
        name = p.name.lower()

        # 이미지
        if suffix in self.IMAGE_EXTS:
            pm = self._load_pixmap(path)
            if pm:
                self.image_label.setPixmap(self._fit(pm))
                self.stack.setCurrentIndex(0)
                return
            self.info_label.setText(self._format_info(path, False) + "\n\n⚠️ 이미지를 불러올 수 없습니다.")
            self.stack.setCurrentIndex(2)
            return

        # 텍스트 조건: (1) 확장자 매칭 or (2) 이름 매칭 or (3) 내용이 텍스트로 보임
        if (suffix in self.TEXT_EXTS) or (name in self.NAME_TEXT_FILES) or self._looks_like_text(path):
            self.text_edit.setPlainText(self._read_text_head(path))
            self.stack.setCurrentIndex(1)
            return

        # 기타
        self.info_label.setText(self._format_info(path, False))
        self.stack.setCurrentIndex(2)

    # --- helpers ---
    def _load_pixmap(self, path:str)->QPixmap|None:
        reader = QImageReader(path)
        if not reader.canRead(): return None
        img = reader.read()
        if img.isNull(): return None
        return QPixmap.fromImage(img)

    def resizeEvent(self, e):
        if self.image_label.pixmap():
            self.image_label.setPixmap(self._fit(self.image_label.pixmap()))
        return super().resizeEvent(e)

    def _fit(self, pm:QPixmap)->QPixmap:
        if self.image_label.width()<=0 or self.image_label.height()<=0: return pm
        return pm.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _looks_like_text(self, path:str)->bool:
        """확장자 없어도 텍스트로 보이면 True: NUL 미포함 + UTF-8/CP949 중 하나로 '엄격' 디코딩 가능"""
        try:
            with open(path, "rb") as f:
                data = f.read(self.SNIFF_BYTES)
            if b"\x00" in data:
                return False
            try:
                data.decode("utf-8")  # strict
                return True
            except UnicodeDecodeError:
                try:
                    data.decode("cp949")  # strict
                    return True
                except UnicodeDecodeError:
                    return False
        except Exception:
            return False

    def _read_text_head(self, path:str)->str:
        try:
            size = os.path.getsize(path)
            n = min(size, self.MAX_TEXT_BYTES)
            data = Path(path).read_bytes()[:n]
            for enc in ("utf-8","cp949","latin-1"):
                try:
                    return data.decode(enc, errors="replace")
                except Exception:
                    continue
            return data.decode("utf-8", errors="replace")
        except Exception as e:
            return f"⚠️ 텍스트 읽기 실패: {e}"

    def _format_info(self, path:str, is_dir:bool)->str:
        p = Path(path)
        try:
            size = sum(f.stat().st_size for f in p.rglob("*")) if is_dir else p.stat().st_size
        except Exception:
            size = 0
        size_kb = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/1024/1024:.2f} MB"
        kind = "폴더" if is_dir else f"파일 ({p.suffix.lower() or '확장자 없음'})"
        return f"이름: {p.name}\n종류: {kind}\n경로: {str(p)}\n크기: {size_kb}"
# -----------------------------------------------------------------------------


# ------------------------------ 좌측 컨트롤 패널 ------------------------------
class ControlPanel(QWidget):
    """
    프로젝트 폴더 입력/선택 + 계측/빌드 옵션 + 액션 버튼 모듈
    현재는 모든 액션이 '스텁' 동작(메시지 박스)만 수행
    """
    def __init__(self, settings: QSettings, on_pick_folder):
        super().__init__()
        self.settings = settings
        self.on_pick_folder = on_pick_folder
        root = QVBoxLayout(self); root.setContentsMargins(10,8,10,10); root.setSpacing(10)

        # Project
        gb_proj1 = QGroupBox("프로젝트")
        fl = QFormLayout(gb_proj1); fl.setLabelAlignment(Qt.AlignLeft)
        self.edit_proj = QLineEdit(self)
        self.btn_browse = QPushButton("폴더 선택", self); self.btn_browse.clicked.connect(self._browse)
        proj_row = QHBoxLayout(); proj_row.addWidget(self.edit_proj, 1); proj_row.addWidget(self.btn_browse)
        fl.addRow("프로젝트 경로", proj_row)

        # Project
        gb_proj2 = QGroupBox("프로젝트")
        fl = QFormLayout(gb_proj2); fl.setLabelAlignment(Qt.AlignLeft)
        self.edit_proj = QLineEdit(self)
        self.btn_browse = QPushButton("폴더 선택", self); self.btn_browse.clicked.connect(self._browse)
        proj_row = QHBoxLayout(); proj_row.addWidget(self.edit_proj, 1); proj_row.addWidget(self.btn_browse)
        fl.addRow("프로젝트 경로", proj_row)

        self.combo_buildsys = QComboBox(); self.combo_buildsys.addItems(["자동 감지", "CMake", "Make", "MSBuild", "Bazel", "Ninja"])
        fl.addRow("빌드 시스템", self.combo_buildsys)

        # Instrumentation
        gb_inst = QGroupBox("계측 옵션")
        inst = QVBoxLayout(gb_inst); inst.setSpacing(6)
        self.cb_func_enter = QCheckBox("111111")
        self.cb_call_graph = QCheckBox("22222")
        self.cb_thread_id = QCheckBox("3333")
        self.cb_time_stamp = QCheckBox("44444")
        self.cb_only_targets = QCheckBox("ㅁㄴㅇㄻㄴㅇㄹ")
        for w in (self.cb_func_enter, self.cb_call_graph, self.cb_thread_id, self.cb_time_stamp, self.cb_only_targets):
            inst.addWidget(w)

        # Build
        gb_build = QGroupBox("빌드 옵션")
        b = QFormLayout(gb_build)
        self.combo_build_type = QComboBox(); self.combo_build_type.addItems(["Debug", "RelWithDebInfo", "Release"])
        self.cb_clean_build = QCheckBox("클린 빌드(빌드 디렉토리 초기화)")
        b.addRow("빌드 타입", self.combo_build_type)
        b.addRow("", self.cb_clean_build)

        # Actions
        gb_actions = QGroupBox("작업")
        a = QHBoxLayout(gb_actions)
        self.btn_analyze = QPushButton("구성 분석")
        self.btn_instrument = QPushButton("계측 삽입")
        self.btn_build = QPushButton("빌드 시작")
        self.btn_analyze.clicked.connect(lambda: self._stub("구성 분석"))
        self.btn_instrument.clicked.connect(lambda: self._stub("계측 삽입"))
        self.btn_build.clicked.connect(lambda: self._stub("빌드 시작"))
        a.addWidget(self.btn_analyze)
        a.addWidget(self.btn_instrument)
        a.addWidget(self.btn_build)

        # Fill
        root.addWidget(gb_proj1)
        root.addWidget(gb_proj2)
        root.addWidget(gb_inst)
        root.addWidget(gb_build)
        root.addWidget(gb_actions)
        root.addStretch(1)

        # Restore last project path
        last = self.settings.value("project_dir", "")
        if last: self.edit_proj.setText(last)

    def _browse(self):
        cur = self.edit_proj.text().strip() or str(Path.home())
        path = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택", cur, QFileDialog.ShowDirsOnly)
        if path:
            self.edit_proj.setText(path)
            self.settings.setValue("project_dir", path)
            if self.on_pick_folder:
                self.on_pick_folder(Path(path))

    def _stub(self, name:str):
        QMessageBox.information(self, name, f"현재는 UI 스켈레톤입니다.\n‘{name}’ 기능은 추후 구현 예정입니다.")
# -----------------------------------------------------------------------------


# -------------------------------- 메인 윈도우 --------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TraceRecoViz — Instrumentation Builder")
        self.setMinimumSize(1200, 760)
        self.settings = QSettings(APP_ORG, APP_NAME)

        # ----- Toolbar -----
        tb = QToolBar("Main"); tb.setIconSize(QSize(20, 20)); self.addToolBar(tb)
        self.action_open = QAction(make_icon("folder-open", QStyle.SP_DirOpenIcon), "프로젝트 열기", self)
        self.action_dark = QAction(make_icon("weather-clear-night", QStyle.SP_DialogYesButton), "다크 모드", self); self.action_dark.setCheckable(True)
        tb.addAction(self.action_open); tb.addSeparator(); tb.addAction(self.action_dark); tb.addSeparator()

        self.search = QLineEdit(self); self.search.setPlaceholderText("검색(파일/폴더 이름)…"); self.search.setClearButtonEnabled(True); self.search.setFixedWidth(320)
        tb.addWidget(self.search); tb.addSeparator()
        self.breadcrumb = QLabel("/", self); self.breadcrumb.setObjectName("Breadcrumb"); self.breadcrumb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(self.breadcrumb)

        # ---- 로그 콘솔 버튼(우측 정렬) ----
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)
        self.action_log_clear = QAction(make_icon("edit-clear", QStyle.SP_DialogResetButton), "로그 지우기", self)
        self.action_log_copy  = QAction(make_icon("edit-copy", QStyle.SP_FileDialogDetailedView), "로그 복사", self)
        self.action_log_save  = QAction(make_icon("document-save", QStyle.SP_DialogSaveButton), "로그 저장", self)
        tb.addAction(self.action_log_clear); tb.addAction(self.action_log_copy); tb.addAction(self.action_log_save)

        # ----- Splitters: 좌(컨트롤) | 우(탐색기+미리보기/로그) -----
        root_split = QSplitter(Qt.Horizontal, self); root_split.setHandleWidth(10)

        # Left: control panel
        self.ctrl_panel = ControlPanel(self.settings, on_pick_folder=self.set_root)
        root_split.addWidget(self.ctrl_panel)

        # Right: top(browser) + bottom(preview/log)
        right_split = QSplitter(Qt.Vertical, self); right_split.setHandleWidth(10)

        # File browser (tree + table)
        self.dir_model = QFileSystemModel(self); self.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Drives); self.dir_model.setRootPath(QDir.rootPath())
        self.dir_view = QTreeView(self); self.dir_view.setModel(self.dir_model); self.dir_view.setHeaderHidden(True); self.dir_view.setAnimated(True)
        self.dir_view.setAlternatingRowColors(True); self.dir_view.setExpandsOnDoubleClick(True); self.dir_view.setIndentation(18)
        for c in range(1, self.dir_model.columnCount()): self.dir_view.hideColumn(c)

        self.file_model = QFileSystemModel(self); self.file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot); self.file_model.setRootPath(QDir.rootPath())
        self.proxy = FilesProxy(self); self.proxy.setSourceModel(self.file_model)

        self.table = QTableView(self); self.table.setModel(self.proxy); self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True); self.table.setSelectionBehavior(QTableView.SelectRows); self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader(); header.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in [1,2,3]: header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        top_split = QSplitter(Qt.Horizontal, self); top_split.setHandleWidth(10)
        top_split.addWidget(self.dir_view); top_split.addWidget(self.table)
        top_split.setStretchFactor(0,1); top_split.setStretchFactor(1,2)

        # bottom: preview + build log (로그 콘솔)
        bottom = QSplitter(Qt.Horizontal, self); bottom.setHandleWidth(10)
        self.preview = PreviewPanel(self)

        self.log_edit = QPlainTextEdit(self)
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("빌드/계측 로그 콘솔")
        bottom.addWidget(self.preview); bottom.addWidget(self.log_edit)
        bottom.setStretchFactor(0, 2); bottom.setStretchFactor(1, 1)

        right_split.addWidget(top_split)
        right_split.addWidget(bottom)
        right_split.setStretchFactor(0, 3)
        right_split.setStretchFactor(1, 2)

        root_split.addWidget(right_split)
        root_split.setStretchFactor(0, 0)  # 좌(컨트롤)
        root_split.setStretchFactor(1, 1)  # 우(탐색+미리보기/로그)
        self.setCentralWidget(root_split)

        # ----- Signals -----
        self.action_open.triggered.connect(self._toolbar_open_project)
        self.action_dark.toggled.connect(self.toggle_theme)
        self.search.textChanged.connect(self.apply_filter)
        self.dir_view.selectionModel().currentChanged.connect(self.on_dir_changed)
        self.table.selectionModel().currentChanged.connect(self.on_table_current_changed)

        self.action_log_clear.triggered.connect(self.log_edit.clear)
        self.action_log_copy.triggered.connect(self._copy_log)
        self.action_log_save.triggered.connect(self._save_log)

        # ----- Restore settings -----
        start_dir = self.settings.value("last_dir", str(Path.home()))
        theme = self.settings.value("theme", "dark")
        self.action_dark.setChecked(theme == "dark")
        self.apply_theme(theme)
        self.set_root(Path(start_dir))

        # 초기 안내 메시지(로그 창)
        self._append_log("ℹ️ UI 스켈레톤 준비 완료. 미리보기는 Makefile 계열까지 텍스트로 표시됩니다.")

    # ---------------------- Theme ----------------------
    def apply_theme(self, mode: str):
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        if mode == "dark":
            QApplication.instance().setStyleSheet(DARK_QSS)
        else:
            QApplication.instance().setStyleSheet(LIGHT_QSS)

    def toggle_theme(self, checked: bool):
        mode = "dark" if checked else "light"
        self.apply_theme(mode)
        self.settings.setValue("theme", mode)

    # ---------------------- Folder handling ----------------------
    def _toolbar_open_project(self):
        cur = self.ctrl_panel.edit_proj.text().strip() or self.current_root()
        path = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택", cur, QFileDialog.ShowDirsOnly)
        if path:
            self.ctrl_panel.edit_proj.setText(path)
            self.settings.setValue("project_dir", path)
            self.set_root(Path(path))

    def set_root(self, path: Path):
        path_str = str(path)
        dir_index = self.dir_model.index(path_str)
        if not dir_index.isValid():
            path_str = str(Path.home())
            dir_index = self.dir_model.index(path_str)
        self.dir_view.setRootIndex(dir_index)

        file_index = self.file_model.index(path_str)
        self.table.setRootIndex(self.proxy.mapFromSource(file_index))

        self.dir_view.expand(dir_index); self.dir_view.scrollTo(dir_index)
        self.update_breadcrumb(path_str)
        self.settings.setValue("last_dir", path_str)

        self.preview.clear()
        self._append_log(f"📁 프로젝트 루트 설정: {path_str}")

    def current_root(self) -> str:
        idx = self.dir_view.rootIndex()
        if idx.isValid(): return self.dir_model.filePath(idx)
        return str(Path.home())

    def on_dir_changed(self, current, _previous):
        path = self.dir_model.filePath(current)
        src_index = self.file_model.index(path)
        self.table.setRootIndex(self.proxy.mapFromSource(src_index))
        self.update_breadcrumb(path)
        self.preview.update_preview(path)

    def on_table_current_changed(self, current: QModelIndex, _prev: QModelIndex):
        if not current.isValid():
            self.preview.clear(); return
        src_index = self.proxy.mapToSource(current)
        path = self.file_model.filePath(src_index)
        self.preview.update_preview(path)

    # ---------------------- UI helpers ----------------------
    def apply_filter(self, text: str):
        tokens = [QRegularExpression.escape(t) for t in text.strip().split() if t.strip()]
        pattern = ".*".join(tokens) if tokens else ""
        self.proxy.setFilterRegularExpression(QRegularExpression(pattern))

    def update_breadcrumb(self, path: str):
        root = Path(path)
        parts = root.parts
        pretty = " / ".join(parts) if parts else "/"
        self.breadcrumb.setText(pretty)

    def _append_log(self, line: str):
        self.log_edit.appendPlainText(line)

    def _copy_log(self):
        QGuiApplication.clipboard().setText(self.log_edit.toPlainText())
        self._append_log("✅ 로그를 클립보드로 복사했습니다.")

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "로그 저장", str(Path.home() / "trace_log.txt"), "Text Files (*.txt);;All Files (*.*)")
        if not path:
            return
        try:
            Path(path).write_text(self.log_edit.toPlainText(), encoding="utf-8")
            self._append_log(f"💾 로그 저장 완료: {path}")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"로그 저장 중 오류: {e}")

# -----------------------------------------------------------------------------


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    # Qt6: HiDPI 자동 지원(Deprecated 속성 사용 안 함)
    w = MainWindow(); w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
