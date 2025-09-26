import os
import sys
from pathlib import Path

from PySide6.QtCore import (
    QDir, Qt, QSortFilterProxyModel, QSettings, QRegularExpression, QSize, QModelIndex
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QImageReader
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QTreeView, QTableView, QLineEdit, QLabel, QHeaderView, QFileSystemModel,
    QSplitter, QStyleFactory, QToolBar, QStyle, QSizePolicy,
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QStackedWidget, QFrame
)

APP_ORG = "ExampleCo"
APP_NAME = "ModernFolderBrowser"


def themed_icons_available():
    return QIcon.fromTheme("folder").isNull() is False


def make_icon(fallback_name: str, std_pixmap: QStyle.StandardPixmap) -> QIcon:
    if themed_icons_available():
        ic = QIcon.fromTheme(fallback_name)
        if not ic.isNull():
            return ic
    return QApplication.style().standardIcon(std_pixmap)


DARK_QSS = """
* { font-family: 'Inter', 'Pretendard', 'Apple SD Gothic Neo', 'Segoe UI', sans-serif; }
QMainWindow, QWidget { background: #111318; color: #E6E9EF; }
QToolBar { background: #151821; border: 0px; padding: 6px; }
QToolButton { color: #E6E9EF; background: transparent; border-radius: 10px; padding: 6px 10px; }
QToolButton:hover { background: #1f2430; }
QToolButton:pressed { background: #2a3140; }
QLineEdit {
    background: #171b24; border: 1px solid #2a3140; border-radius: 10px; padding: 8px 10px;
    selection-background-color: #3e7cff;
}
QLineEdit:focus { border: 1px solid #3e7cff; }
QLabel#Breadcrumb { color: #b8c0cc; padding: 4px 2px; }
QTreeView, QTableView {
    background: #131722; alternate-background-color: #161b26;
    border: 1px solid #262b39; border-radius: 12px; padding: 6px;
}
QHeaderView::section { background: #151a24; color: #BFC7D5; border: 0px; padding: 8px; }
QTreeView::item, QTableView::item { padding: 6px; }
QTreeView::item:selected, QTableView::item:selected { background: #20304f; }

/* Preview panel */
#PreviewBox {
    border: 1px solid #262b39;
    border-radius: 12px;
    background: #131722;
}
#PreviewHeader {
    color: #BFC7D5;
}
"""

LIGHT_QSS = """
* { font-family: 'Inter', 'Pretendard', 'Apple SD Gothic Neo', 'Segoe UI', sans-serif; }
QMainWindow, QWidget { background: #FAFBFD; color: #1c1f24; }
QToolBar { background: #FFFFFF; border: 0px; padding: 6px; }
QToolButton { color: #1c1f24; background: transparent; border-radius: 10px; padding: 6px 10px; }
QToolButton:hover { background: #EFF3F9; }
QToolButton:pressed { background: #E3EAF5; }
QLineEdit {
    background: #FFFFFF; border: 1px solid #DDE3EE; border-radius: 10px; padding: 8px 10px;
    selection-background-color: #3e7cff;
}
QLineEdit:focus { border: 1px solid #3e7cff; }
QLabel#Breadcrumb { color: #6b7280; padding: 4px 2px; }
QTreeView, QTableView {
    background: #FFFFFF; alternate-background-color: #F7F9FC;
    border: 1px solid #E7ECF5; border-radius: 12px; padding: 6px;
}
QHeaderView::section { background: #F4F7FB; color: #464b53; border: 0px; padding: 8px; }
QTreeView::item, QTableView::item { padding: 6px; }
QTreeView::item:selected, QTableView::item:selected { background: #E7F0FF; }

/* Preview panel */
#PreviewBox {
    border: 1px solid #E7ECF5;
    border-radius: 12px;
    background: #FFFFFF;
}
#PreviewHeader {
    color: #464b53;
}
"""


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


# ----------------- Preview Panel -----------------
class PreviewPanel(QWidget):
    """
    파일 미리보기:
      - 이미지: QLabel에 썸네일
      - 텍스트: QPlainTextEdit에 앞부분 표시(최대 200KB)
      - 기타: 간단 정보
    """
    TEXT_EXTS = {
        ".txt", ".md", ".py", ".cpp", ".c", ".h", ".hpp", ".json", ".xml",
        ".csv", ".log", ".ini", ".yaml", ".yml", ".toml", ".html", ".htm",
        ".css", ".js", ".ts", ".rs", ".go", ".java", ".kt", ".sh", ".bat"
    }
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff", ".tif", ".ico", ".svg"}  # svg는 rasterize X → 로고 표시만
    MAX_TEXT_BYTES = 200 * 1024  # 200KB

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 10)
        outer.setSpacing(8)

        # 상단 헤더
        header = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        self.path_label = QLabel("미리보기 없음")
        self.path_label.setObjectName("PreviewHeader")
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header.addWidget(self.icon_label)
        header.addWidget(self.path_label, 1)
        header.addStretch()

        # 내용 영역(스택)
        self.stack = QStackedWidget()
        self.stack.setObjectName("PreviewBox")

        # 이미지 뷰어
        img_wrap = QWidget()
        img_layout = QVBoxLayout(img_wrap)
        img_layout.setContentsMargins(10, 10, 10, 10)
        self.image_label = QLabel(alignment=Qt.AlignCenter)
        self.image_label.setMinimumHeight(160)
        self.image_label.setScaledContents(False)
        img_layout.addWidget(self.image_label)
        self.stack.addWidget(img_wrap)

        # 텍스트 뷰어
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setWordWrapMode(self.text_edit.wordWrapMode())  # 기본 유지
        self.stack.addWidget(self.text_edit)

        # 정보(기타) 뷰
        self.info_label = QLabel(alignment=Qt.AlignLeft | Qt.AlignTop)
        self.info_label.setWordWrap(True)
        info_wrap = QWidget()
        info_layout = QVBoxLayout(info_wrap)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.addWidget(self.info_label)
        self.stack.addWidget(info_wrap)

        outer.addLayout(header)
        outer.addWidget(self.stack, 1)

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

    def _read_text(self, path: str) -> str:
        size = os.path.getsize(path)
        n = min(size, self.MAX_TEXT_BYTES)
        with open(path, "rb") as f:
            data = f.read(n)
        # 우선 UTF-8, 실패하면 cp949(윈도우 한글), 그래도 안되면 latin-1
        for enc in ("utf-8", "cp949", "latin-1"):
            try:
                return data.decode(enc, errors="replace")
            except Exception:
                continue
        return data.decode("utf-8", errors="replace")

    def _load_image(self, path: str) -> QPixmap | None:
        reader = QImageReader(path)
        if not reader.canRead():
            return None
        img = reader.read()
        if img.isNull():
            return None
        return QPixmap.fromImage(img)

    def update_preview(self, path: str):
        if not path or not os.path.exists(path):
            self.clear()
            return

        self._set_header(path)
        suffix = Path(path).suffix.lower()

        # 폴더는 정보 패널로
        if os.path.isdir(path):
            info = self._format_info(path, is_dir=True)
            self.info_label.setText(info)
            self.stack.setCurrentIndex(2)
            return

        # 이미지
        if suffix in self.IMAGE_EXTS and os.path.isfile(path):
            pm = self._load_image(path)
            if pm:
                self.image_label.setPixmap(self._fit_pixmap(pm))
                self.stack.setCurrentIndex(0)
                return
            # 이미지 로드 실패 → 정보 패널로 폴백
            info = self._format_info(path)
            self.info_label.setText(info + "\n\n⚠️ 이미지를 불러올 수 없습니다.")
            self.stack.setCurrentIndex(2)
            return

        # 텍스트
        if suffix in self.TEXT_EXTS:
            try:
                text = self._read_text(path)
                # 큰 파일일 경우 안내
                size = os.path.getsize(path)
                if size > self.MAX_TEXT_BYTES:
                    head = f"⚠️ 파일이 큼({size/1024:.0f}KB). 처음 {self.MAX_TEXT_BYTES/1024:.0f}KB만 표시.\n\n"
                else:
                    head = ""
                self.text_edit.setPlainText(head + text)
                self.stack.setCurrentIndex(1)
                return
            except Exception as e:
                info = self._format_info(path)
                self.info_label.setText(info + f"\n\n⚠️ 텍스트 읽기 실패: {e}")
                self.stack.setCurrentIndex(2)
                return

        # PDF/기타
        info = self._format_info(path)
        if suffix == ".pdf":
            info += "\n\n📄 PDF 문서입니다. 간단 정보만 표시합니다."
        self.info_label.setText(info)
        self.stack.setCurrentIndex(2)

    def _fit_pixmap(self, pm: QPixmap) -> QPixmap:
        # 라벨 크기에 맞춰 AspectRatio 유지 축소
        if self.image_label.width() <= 0 or self.image_label.height() <= 0:
            return pm
        return pm.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def resizeEvent(self, event):
        # 리사이즈 시 이미지 다시 맞춤
        if not self.image_label.pixmap():
            return super().resizeEvent(event)
        pm = self.image_label.pixmap()
        self.image_label.setPixmap(self._fit_pixmap(pm))
        return super().resizeEvent(event)

    def _format_info(self, path: str, is_dir: bool = False) -> str:
        p = Path(path)
        try:
            size = sum(f.stat().st_size for f in p.rglob("*")) if is_dir else p.stat().st_size
        except Exception:
            size = 0
        size_kb = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/1024/1024:.2f} MB"
        kind = "폴더" if is_dir else f"파일 ({p.suffix.lower() or '확장자 없음'})"
        return f"이름: {p.name}\n종류: {kind}\n경로: {str(p)}\n크기: {size_kb}"
# ----------------- /Preview Panel -----------------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Folder Browser")
        self.setMinimumSize(1100, 700)
        self.settings = QSettings(APP_ORG, APP_NAME)

        # ----- Toolbar -----
        tb = QToolBar("Main")
        tb.setIconSize(QSize(20, 20))
        self.addToolBar(tb)

        self.action_open = QAction(make_icon("folder-open", QStyle.SP_DirOpenIcon), "폴더 선택", self)
        self.action_dark = QAction(make_icon("weather-clear-night", QStyle.SP_DialogYesButton), "다크 모드", self)
        self.action_dark.setCheckable(True)

        tb.addAction(self.action_open)
        tb.addSeparator()
        tb.addAction(self.action_dark)
        tb.addSeparator()

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("검색(파일/폴더 이름 필터)…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(320)
        tb.addWidget(self.search)

        tb.addSeparator()
        self.breadcrumb = QLabel("/", self)
        self.breadcrumb.setObjectName("Breadcrumb")
        self.breadcrumb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(self.breadcrumb)

        # ----- Splitters -----
        main_split = QSplitter(Qt.Horizontal, self)   # 좌/우
        main_split.setHandleWidth(10)

        # Left: Dir tree
        self.dir_model = QFileSystemModel(self)
        self.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Drives)
        self.dir_model.setRootPath(QDir.rootPath())

        self.dir_view = QTreeView(self)
        self.dir_view.setModel(self.dir_model)
        self.dir_view.setHeaderHidden(True)
        self.dir_view.setAnimated(True)
        self.dir_view.setAlternatingRowColors(True)
        self.dir_view.setExpandsOnDoubleClick(True)
        self.dir_view.setIndentation(18)
        for c in range(1, self.dir_model.columnCount()):
            self.dir_view.hideColumn(c)

        # Right: (Top) Table + (Bottom) Preview
        right_split = QSplitter(Qt.Vertical, self)
        right_split.setHandleWidth(10)

        self.file_model = QFileSystemModel(self)
        self.file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
        self.file_model.setRootPath(QDir.rootPath())

        self.proxy = FilesProxy(self)
        self.proxy.setSourceModel(self.file_model)

        self.table = QTableView(self)
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in [1, 2, 3]:
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.preview = PreviewPanel(self)

        right_split.addWidget(self.table)
        right_split.addWidget(self.preview)
        right_split.setStretchFactor(0, 3)  # 테이블
        right_split.setStretchFactor(1, 2)  # 미리보기

        main_split.addWidget(self.dir_view)
        main_split.addWidget(right_split)
        main_split.setStretchFactor(0, 1)  # 좌
        main_split.setStretchFactor(1, 2)  # 우
        self.setCentralWidget(main_split)

        # ----- Signals -----
        self.action_open.triggered.connect(self.choose_folder)
        self.action_dark.toggled.connect(self.toggle_theme)
        self.dir_view.selectionModel().currentChanged.connect(self.on_dir_changed)
        self.search.textChanged.connect(self.apply_filter)

        # 테이블 선택 변경 → 미리보기 갱신
        self.table.selectionModel().currentChanged.connect(self.on_table_current_changed)

        # ----- Restore settings -----
        start_dir = self.settings.value("last_dir", str(Path.home()))
        theme = self.settings.value("theme", "dark")
        self.action_dark.setChecked(theme == "dark")
        self.apply_theme(theme)
        self.set_root(Path(start_dir))

    # ---------- Theme ----------
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

    # ---------- Folder handling ----------
    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, "폴더 선택", self.current_root(), QFileDialog.ShowDirsOnly)
        if path:
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

        self.dir_view.expand(dir_index)
        self.dir_view.scrollTo(dir_index)

        self.update_breadcrumb(path_str)
        self.settings.setValue("last_dir", path_str)

        # 루트 바꾸면 미리보기 초기화
        self.preview.clear()

    def current_root(self) -> str:
        idx = self.dir_view.rootIndex()
        if idx.isValid():
            return self.dir_model.filePath(idx)
        return str(Path.home())

    def on_dir_changed(self, current, _previous):
        path = self.dir_model.filePath(current)
        src_index = self.file_model.index(path)
        self.table.setRootIndex(self.proxy.mapFromSource(src_index))
        self.update_breadcrumb(path)
        # 폴더 선택 시, 폴더 자체 정보 보여주기
        self.preview.update_preview(path)

    # ---------- Table selection → Preview ----------
    def on_table_current_changed(self, current: QModelIndex, _prev: QModelIndex):
        if not current.isValid():
            self.preview.clear()
            return
        src_index = self.proxy.mapToSource(current)
        path = self.file_model.filePath(src_index)
        self.preview.update_preview(path)

    # ---------- UI helpers ----------
    def apply_filter(self, text: str):
        tokens = [QRegularExpression.escape(t) for t in text.strip().split() if t.strip()]
        pattern = ".*".join(tokens) if tokens else ""
        self.proxy.setFilterRegularExpression(QRegularExpression(pattern))

    def update_breadcrumb(self, path: str):
        root = Path(path)
        parts = root.parts
        pretty = " / ".join(parts) if parts else "/"
        self.breadcrumb.setText(pretty)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)

    # Qt6: HiDPI 자동 지원(Deprecated 속성 사용 안 함)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
