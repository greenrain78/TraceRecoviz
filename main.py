import shutil
import os
import pathlib
import shutil
import sys
import threading

from PySide6.QtCore import (
    QDir, Qt, QSortFilterProxyModel, QSettings, QRegularExpression, QSize, QModelIndex, QProcess
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QImageReader, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QTreeView, QTableView, QLineEdit, QLabel, QHeaderView, QFileSystemModel,
    QSplitter, QStyleFactory, QToolBar, QStyle, QSizePolicy,
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QStackedWidget,
    QGroupBox, QPushButton, QFormLayout, QMessageBox, QDialogButtonBox, QDialog
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

# from pathlib import Path

APP_ORG = "ExampleCo"
APP_NAME = "TraceRecoViz"  # 앱/설정 저장용 애플리케이션 이름



backend_app = FastAPI()

# CORS 설정 (Live Server와 연동 위해)
backend_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SEQUENCE_DIAGRAM_DIR = os.path.join(os.path.dirname(__file__), "build", "sequence_diagram")

INDEX_HTML_PATH = os.path.join(os.path.dirname(__file__), "index.html")
VIEWER_HTML_PATH = os.path.join(os.path.dirname(__file__), "viewer.html")

@backend_app.get("/api/sequence-diagrams")
def get_sequence_diagrams():
    try:
        all_files = [f for f in os.listdir(SEQUENCE_DIAGRAM_DIR) if os.path.isfile(os.path.join(SEQUENCE_DIAGRAM_DIR, f))]
        # .json 파일만 필터링
        json_files = [f for f in all_files if f.endswith('.json')]
        # _new.json, _old.json 제외
        base_files = set()
        for f in json_files:
            if f.endswith('_new.json') or f.endswith('_old.json'):
                continue
            base_name = f[:-5]  # .json 제거
            # 해당 base에 _new.json 또는 _old.json이 있으면 base만 추가
            has_new = f"{base_name}_new.json" in json_files
            has_old = f"{base_name}_old.json" in json_files
            if has_new or has_old:
                base_files.add(f)
        # base_files만 반환
        return JSONResponse(content={"files": sorted(list(base_files))})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# 루트에서 index.html 반환
@backend_app.get("/")
def serve_index():
    return FileResponse(INDEX_HTML_PATH, media_type="text/html")

# /viewer.html에서 viewer.html 반환
@backend_app.get("/viewer.html")
def serve_viewer():
    return FileResponse(VIEWER_HTML_PATH, media_type="text/html")

# /build/sequence_diagram/{filename}에서 JSON 파일 반환
from fastapi import Path

@backend_app.get("/build/sequence_diagram/{file_path:path}")
def serve_sequence_json(file_path: str = Path(...)):
    abs_path = os.path.join(SEQUENCE_DIAGRAM_DIR, file_path)
    print(f"Requested file path: {file_path}, Absolute path: {abs_path}")
    print(f"File exists: {os.path.isfile(abs_path)}")
    if not os.path.isfile(abs_path):
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    return FileResponse(abs_path, media_type="application/json")



import uvicorn

class UvicornRunner:
    """
    FastAPI/ASGI 앱을 uvicorn.Server로 백그라운드 스레드에서 실행/중지.
    - start(): 이미 실행 중이면 무시
    - stop(): 정상 종료 신호 후 join
    """
    def __init__(self, app, host="127.0.0.1", port=8000, log_level="info"):
        self.app = app
        self.host = host
        self.port = port
        self.log_level = log_level

        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    def _target(self):
        # workers=1, reload=False, 백그라운드 스레드에서 신호 핸들러 비설치
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level=self.log_level,
            workers=1,
        )
        self._server = uvicorn.Server(config)
        # run()은 블로킹. 스레드에서 실행됨.
        self._server.run()

    def start(self):
        if self.is_running():
            return
        self._thread = threading.Thread(target=self._target, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0):
        if not self.is_running():
            return
        assert self._server is not None
        self._server.should_exit = True
        self._server.force_exit = True
        if self._thread:
            self._thread.join(timeout)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()


# ------------------------------- 스타일/아이콘 -------------------------------
def make_icon(fallback_name: str, std_pixmap: QStyle.StandardPixmap) -> QIcon:
    """
    아이콘 생성 헬퍼:
    1) 시스템 테마 아이콘 시도 → 성공 시 반환
    2) 실패 시 Qt의 표준 픽스맵 아이콘으로 폴백
    """
    if not QIcon.fromTheme("folder").isNull():
        ic = QIcon.fromTheme(fallback_name)
        if not ic.isNull():
            return ic
    return QApplication.style().standardIcon(std_pixmap)


# 다크/라이트 테마용 QSS(전역 스타일시트).
# 폰트 패밀리에 한글 지원 글꼴(예: Pretendard, Apple SD Gothic Neo)을 포함.
# WSL/리눅스에서 한글이 깨질 경우, 시스템에 CJK 폰트(Noto Sans CJK 등)를 설치하세요.
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
    """
    파일/폴더 이름 필터링 프록시 모델.
    - setRecursiveFilteringEnabled(True) 사용: 하위 트리까지 필터 재귀 적용.
    - 폴더의 경우: 자기 자신이 매칭되지 않아도, 자식 중 하나라도 매칭되면 표시(탐색성 개선).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)  # 대소문자 무시
        self.setRecursiveFilteringEnabled(True)            # 재귀 필터 활성화

    def filterAcceptsRow(self, source_row, source_parent):
        """
        행(파일/폴더) 하나가 필터에 의해 표시될지 판단.
        - 폴더: 이름 매칭 OR 자손 중 하나라도 매칭되면 True
        - 파일: 기본(부모 구현) 로직 사용
        """
        index0 = self.sourceModel().index(source_row, 0, source_parent)
        if not index0.isValid():
            return False
        is_dir = self.sourceModel().isDir(index0)
        if is_dir:
            name = self.sourceModel().fileName(index0)
            pattern = self.filterRegularExpression()
            # 1) 폴더명 매칭
            if pattern.match(name).hasMatch():
                return True
            # 2) 자식 중 매칭이 있는지 재귀 확인
            for r in range(self.sourceModel().rowCount(index0)):
                if self.filterAcceptsRow(r, index0):
                    return True
            return False
        # 파일은 부모 구현에 위임(열 이름 등의 기본 매칭)
        return super().filterAcceptsRow(source_row, source_parent)
# -----------------------------------------------------------------------------


# ------------------------------- 미리보기 패널 --------------------------------
class PreviewPanel(QWidget):
    """
    선택된 경로의 미리보기.
    - 디렉터리: 간단한 정보(이름/경로/총 크기)
    - 이미지: 썸네일 뷰
    - 텍스트: 최대 200KB 미리보기, 인코딩은 UTF-8→CP949→latin-1 순으로 시도
    - 기타: 간단 정보
    - 확장자 없는 빌드 스크립트(Makefile, CMakeLists.txt 등)도 텍스트로 취급
    """
    # 대표 텍스트 확장자
    TEXT_EXTS = {
        ".txt", ".md", ".py", ".cpp", ".c", ".h", ".hpp", ".json", ".xml",
        ".csv", ".log", ".ini", ".yaml", ".yml", ".toml", ".html", ".htm",
        ".css", ".js", ".ts", ".rs", ".go", ".java", ".kt", ".sh", ".bat",
        ".gradle", ".cmake"
    }
    # 확장자 없이 자주 쓰이는 텍스트/빌드 스크립트 파일 이름(소문자 매칭)
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
    # 이미지 확장자
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff", ".tif", ".ico"}

    # 미리보기·판정 시 읽는 바이트 한계
    MAX_TEXT_BYTES = 200 * 1024  # 텍스트 미리보기 상한(200KB)
    SNIFF_BYTES = 64 * 1024      # 텍스트/바이너리 판정용(앞쪽 64KB)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 전체 레이아웃 및 상단 헤더(아이콘 + 경로 라벨)
        outer = QVBoxLayout(self); outer.setContentsMargins(10,8,10,10); outer.setSpacing(8)

        header = QHBoxLayout()
        self.icon_label = QLabel(); self.icon_label.setFixedSize(18,18)  # 작은 파일 아이콘
        self.path_label = QLabel("미리보기 없음"); self.path_label.setObjectName("PreviewHeader")
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 경로 복사 가능
        header.addWidget(self.icon_label); header.addWidget(self.path_label, 1); header.addStretch()

        # 중앙 본문은 스택 위젯: 0=이미지, 1=텍스트, 2=정보
        self.stack = QStackedWidget(); self.stack.setObjectName("PreviewBox")

        # (0) 이미지 미리보기
        img_wrap = QWidget(); img_layout = QVBoxLayout(img_wrap); img_layout.setContentsMargins(10,10,10,10)
        self.image_label = QLabel(alignment=Qt.AlignCenter); self.image_label.setMinimumHeight(160)
        img_layout.addWidget(self.image_label); self.stack.addWidget(img_wrap)

        # (1) 텍스트 미리보기
        self.text_edit = QPlainTextEdit(); self.text_edit.setReadOnly(True)
        self.stack.addWidget(self.text_edit)

        # (2) 정보(이름/종류/경로/크기)
        self.info_label = QLabel(alignment=Qt.AlignLeft | Qt.AlignTop); self.info_label.setWordWrap(True)
        info_wrap = QWidget(); info_layout = QVBoxLayout(info_wrap); info_layout.setContentsMargins(12,12,12,12)
        info_layout.addWidget(self.info_label); self.stack.addWidget(info_wrap)

        outer.addLayout(header); outer.addWidget(self.stack, 1)
        self.clear()

    def clear(self):
        """미리보기 초기화."""
        self.path_label.setText("미리보기 없음")
        self.icon_label.setPixmap(QPixmap())
        self.image_label.clear()
        self.text_edit.clear()
        self.info_label.setText("파일을 선택하면 여기에서 미리보기가 표시됩니다.")

    def _set_header(self, path: str):
        """상단 헤더(경로 텍스트, 파일형 아이콘) 갱신."""
        self.path_label.setText(path)
        fi_icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
        self.icon_label.setPixmap(fi_icon.pixmap(18, 18))

    def update_preview(self, path: str):
        """
        외부에서 선택된 경로를 받아 미리보기 뷰를 전환.
        - 디렉터리 → 정보 뷰
        - 이미지 → 이미지 뷰
        - 텍스트 → 텍스트 뷰
        - 그 외 → 정보 뷰
        """
        if not path or not os.path.exists(path):
            self.clear(); return
        self._set_header(path)
        if os.path.isdir(path):
            self.info_label.setText(self._format_info(path, True))
            self.stack.setCurrentIndex(2); return

        p = pathlib.Path(path)
        suffix = p.suffix.lower()
        name = p.name.lower()

        # (A) 이미지 파일 처리
        if suffix in self.IMAGE_EXTS:
            pm = self._load_pixmap(path)
            if pm:
                self.image_label.setPixmap(self._fit(pm))
                self.stack.setCurrentIndex(0)
                return
            # 이미지 읽기 실패 시 정보 뷰 + 경고 출력
            self.info_label.setText(self._format_info(path, False) + "\n\n⚠️ 이미지를 불러올 수 없습니다.")
            self.stack.setCurrentIndex(2)
            return

        # (B) 텍스트 파일 처리(확장자/이름/내용 스니핑 기준 중 하나라도 통과)
        if (suffix in self.TEXT_EXTS) or (name in self.NAME_TEXT_FILES) or self._looks_like_text(path):
            self.text_edit.setPlainText(self._read_text_head(path))
            self.stack.setCurrentIndex(1)
            return

        # (C) 기타: 정보 뷰
        self.info_label.setText(self._format_info(path, False))
        self.stack.setCurrentIndex(2)

    # --- 내부 헬퍼들 ---
    def _load_pixmap(self, path:str)->QPixmap|None:
        """QImageReader로 이미지 읽어 QPixmap 반환(실패 시 None)."""
        reader = QImageReader(path)
        if not reader.canRead(): return None
        img = reader.read()
        if img.isNull(): return None
        return QPixmap.fromImage(img)

    def resizeEvent(self, e):
        """
        위젯 리사이즈 시 이미지가 놓여 있다면 현재 라벨 크기에 맞춰 재스케일.
        (비율 유지 + 보간 품질 향상)
        """
        if self.image_label.pixmap():
            self.image_label.setPixmap(self._fit(self.image_label.pixmap()))
        return super().resizeEvent(e)

    def _fit(self, pm:QPixmap)->QPixmap:
        """현재 image_label 크기 내부에 비율 유지로 맞춰 스케일."""
        if self.image_label.width()<=0 or self.image_label.height()<=0: return pm
        return pm.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _looks_like_text(self, path:str)->bool:
        """
        확장자가 없더라도 텍스트처럼 보이는지 간이 판정:
        - NUL(0x00) 바이트가 없어야 함(바이너리 가능성 낮춤)
        - 앞 64KB를 UTF-8 또는 CP949로 '엄격' 디코딩 가능해야 텍스트로 간주
        """
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
        """
        텍스트 미리보기 본문 읽기:
        - 파일 크기의 최대 200KB까지만 로드(대용량 파일 대비)
        - 디코딩 순서: UTF-8 → CP949 → latin-1
          (모두 실패 시 UTF-8 replace로 안전 표시)
        """
        try:
            size = os.path.getsize(path)
            n = min(size, self.MAX_TEXT_BYTES)
            data = pathlib.Path(path).read_bytes()[:n]
            for enc in ("utf-8","cp949","latin-1"):
                try:
                    return data.decode(enc, errors="replace")
                except Exception:
                    continue
            return data.decode("utf-8", errors="replace")
        except Exception as e:
            return f"⚠️ 텍스트 읽기 실패: {e}"

    def _format_info(self, path:str, is_dir:bool)->str:
        """
        정보 뷰 내용 구성:
        - 이름 / 종류 / 경로 / 크기
        - 디렉터리는 rglob로 합산(큰 트리에서는 시간이 걸릴 수 있으므로 주의)
        """
        p = pathlib.Path(path)
        try:
            size = sum(f.stat().st_size for f in p.rglob("*")) if is_dir else p.stat().st_size
        except Exception:
            size = 0
        size_kb = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/1024/1024:.2f} MB"
        kind = "폴더" if is_dir else f"파일 ({p.suffix.lower() or '확장자 없음'})"
        return f"이름: {p.name}\n종류: {kind}\n경로: {str(p)}\n크기: {size_kb}"
# -----------------------------------------------------------------------------
class MakefileEditorDialog(QDialog):
    """
    간단한 Makefile 편집기:
    - 경로 표시, 본문 편집, 저장/다른이름저장/닫기
    - 인코딩: utf-8 → cp949 → latin-1 순으로 읽기, 저장은 원 인코딩 유지(없으면 utf-8)
    """
    def __init__(self, path: pathlib.Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Makefile 편집")
        self.setMinimumSize(900, 600)

        self.path = path
        self.encoding = "utf-8"  # 기본 저장 인코딩

        v = QVBoxLayout(self)
        self.lbl_path = QLabel(str(self.path))
        self.lbl_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v.addWidget(self.lbl_path)

        self.edit = QPlainTextEdit(self)
        self.edit.setPlaceholderText("여기에 Makefile 내용을 입력하세요…")
        v.addWidget(self.edit, 1)

        self.buttons = QDialogButtonBox(self)
        self.btn_save = self.buttons.addButton("저장", QDialogButtonBox.AcceptRole)
        self.btn_save_as = self.buttons.addButton("다른 이름으로 저장", QDialogButtonBox.ActionRole)
        self.btn_close = self.buttons.addButton("닫기", QDialogButtonBox.RejectRole)
        v.addWidget(self.buttons)

        self.btn_save.clicked.connect(self._save)
        self.btn_save_as.clicked.connect(self._save_as)
        self.buttons.rejected.connect(self.reject)

        # 파일 읽기(없으면 빈 문서로 시작)
        self._load_if_exists()

    # --- helpers ---
    def _detect_text(self, data: bytes) -> str:
        for enc in ("utf-8", "cp949", "latin-1"):
            try:
                txt = data.decode(enc)  # strict
                self.encoding = enc
                return txt
            except UnicodeDecodeError:
                continue
        # 마지막 폴백
        self.encoding = "utf-8"
        return data.decode("utf-8", errors="replace")

    def _load_if_exists(self):
        if self.path.exists():
            try:
                data = self.path.read_bytes()
                text = self._detect_text(data)
                self.edit.setPlainText(text)
            except Exception as e:
                QMessageBox.warning(self, "열기 실패", f"파일을 불러오지 못했습니다:\n{e}")
        else:
            # 새 파일로 시작
            self.encoding = "utf-8"

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            text = self.edit.toPlainText()
            self.path.write_text(text, encoding=self.encoding)
            QMessageBox.information(self, "저장 완료", f"저장되었습니다:\n{self.path}\n(인코딩: {self.encoding})")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"파일 저장 중 오류:\n{e}")

    def _save_as(self):
        new_path_str, _ = QFileDialog.getSaveFileName(self, "다른 이름으로 저장", str(self.path), "All Files (*);;Makefile (Makefile)")
        if not new_path_str:
            return
        new_path = pathlib.Path(new_path_str)
        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            text = self.edit.toPlainText()
            new_path.write_text(text, encoding=self.encoding)
            self.path = new_path
            self.lbl_path.setText(str(self.path))
            QMessageBox.information(self, "저장 완료", f"다른 이름으로 저장되었습니다:\n{self.path}\n(인코딩: {self.encoding})")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"파일 저장 중 오류:\n{e}")

# ─────────────────────────────────────────────────────────────────────────────
# 로그 팝업: 최소 구현 (중지/닫기 + 실시간 append)
# ─────────────────────────────────────────────────────────────────────────────
class BuildLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("빌드 로그")
        self.setMinimumSize(800, 480)

        v = QVBoxLayout(self)
        self.log = QPlainTextEdit(self)
        self.log.setReadOnly(True)
        v.addWidget(self.log)

        self.buttons = QDialogButtonBox(self)
        self.btn_stop = self.buttons.addButton("중지", QDialogButtonBox.DestructiveRole)
        self.btn_close = self.buttons.addButton("닫기", QDialogButtonBox.RejectRole)
        self.btn_close.setEnabled(False)  # 실행 중에는 닫기 비활성화
        v.addWidget(self.buttons)

    def append(self, text: str):
        if text:
            self.log.appendPlainText(text)

    def set_running(self, running: bool):
        self.btn_close.setEnabled(running)
        self.btn_close.setEnabled(not running)

# ------------------------------ 좌측 컨트롤 패널 ------------------------------
class ControlPanel(QWidget):
    """
    좌측 컨트롤 패널: 프로젝트 경로 입력/선택 + 계측/빌드 옵션 + 액션 버튼.
    - 현재 버튼 동작은 '스텁'(메시지 박스만 뜸)
    - 실제 빌드/계측 로직 연동은 추후 on_click 슬롯에서 구현하면 됨.
    """
    def __init__(self, settings: QSettings, on_pick_folder):
        super().__init__()
        self.settings = settings
        self.on_pick_folder = on_pick_folder

        self._uvicorn = UvicornRunner(backend_app, host="127.0.0.1", port=8000, log_level="info")


        # 컨테이너 레이아웃(세로)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(10)

        # ----- 프로젝트 경로 입력/선택 (그룹 1) -----
        gb_proj1 = QGroupBox("프로젝트 패널")
        fl = QFormLayout(gb_proj1); fl.setLabelAlignment(Qt.AlignLeft)

        # old 프로젝트 경로
        self.edit_proj_old = QLineEdit(self)
        self.edit_proj_old.setReadOnly(True)
        btn_browse = QPushButton("폴더 선택", self)
        btn_browse.clicked.connect(lambda: self._browse("old", self.edit_proj_old))

        proj_row_old = QHBoxLayout()
        proj_row_old.addWidget(self.edit_proj_old, 1)
        proj_row_old.addWidget(btn_browse)
        fl.addRow("수정 전 프로젝트 경로", proj_row_old)

        # new 프로젝트 경로
        self.edit_proj_new = QLineEdit(self)
        self.edit_proj_new.setReadOnly(True)
        btn_browse = QPushButton("폴더 선택", self)
        btn_browse.clicked.connect(lambda: self._browse("new", self.edit_proj_new))

        proj_row_new = QHBoxLayout()
        proj_row_new.addWidget(self.edit_proj_new, 1)
        proj_row_new.addWidget(btn_browse)
        fl.addRow("수정 후 프로젝트 경로", proj_row_new)

        # ----- 액션 버튼 -----
        gb_actions = QGroupBox("작업")
        a = QHBoxLayout(gb_actions)
        self.btn_build = QPushButton("계측 코드 삽입 및 시퀀스 다이어그램 생성")
        # self.btn_run = QPushButton("웹 서버 실행")
        # 현재는 메시지 박스만 띄우는 스텁 동작
        self.btn_build.clicked.connect(self._on_build_clicked)
        # self.btn_run.clicked.connect(lambda: self._stub("빌드 시작"))

        self.btn_web = QPushButton("웹서버 OFF")
        self.btn_web.setCheckable(True)
        self.btn_web.toggled.connect(self._on_web_toggled)
        tip = QLabel("http://127.0.0.1:8000")
        tip.setToolTip("서버 ON일 때 접속 URL")

        a.addWidget(self.btn_build)
        a.addWidget(self.btn_web)

        gb_actions2 = QGroupBox("작업")
        ha = QHBoxLayout(gb_actions2)
        self.btn_edit_mk = QPushButton("Makefile 편집")
        self.btn_edit_mk.clicked.connect(self._on_edit_makefile_clicked)
        ha.addWidget(self.btn_edit_mk)


        # ----- 루트 레이아웃에 섹션 배치 -----
        root.addWidget(gb_proj1)
        root.addWidget(gb_actions)
        root.addWidget(gb_actions2)
        root.addStretch(1)

        # 마지막 프로젝트 경로 복원(QSettings)
        last_project_old = self.settings.value("project_dir_old", "")
        if last_project_old: self.edit_proj_old.setText(last_project_old)

        last_project_new = self.settings.value("project_dir_new", "")
        if last_project_new: self.edit_proj_new.setText(last_project_new)

    def _on_edit_makefile_clicked(self):
        """
        우선순위로 Makefile 경로를 정한다:
        1) Path.cwd()/Makefile 존재 시 → 사용
        3) 둘 다 없으면 Path.cwd()/Makefile 로 새 파일로 편집 시작(저장 시 생성)
        """
        # 1) CWD
        cwd = self._dest_dir()
        mk_path = cwd / "Makefile"
        dlg = MakefileEditorDialog(mk_path, self)
        dlg.exec()

    def _on_web_toggled(self, checked: bool):
        if checked:
            # 시작
            try:
                self._uvicorn.start()
            except Exception as e:
                self.btn_web.blockSignals(True)
                self.btn_web.setChecked(False)
                self.btn_web.blockSignals(False)
                QMessageBox.critical(self, "웹서버 시작 실패", f"{e}")
                return
            self.btn_web.setText("웹서버 ON")

            # ✅ 커스텀 다이얼로그로 클릭 가능한 링크 표시
            dlg = QDialog(self)
            dlg.setWindowTitle("웹서버 시작")
            dlg.setMinimumWidth(400)

            layout = QVBoxLayout(dlg)
            lbl_info = QLabel("FastAPI 서버를 시작했습니다.<br>아래 링크를 클릭해 접속할 수 있습니다.")
            lbl_info.setWordWrap(True)
            lbl_info.setTextFormat(Qt.RichText)

            lbl_link = QLabel('<a href="http://127.0.0.1:8000">http://127.0.0.1:8000</a>')
            lbl_link.setOpenExternalLinks(True)  # 클릭 시 기본 브라우저로 열림
            lbl_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
            lbl_link.setAlignment(Qt.AlignCenter)

            btn_ok = QPushButton("확인")
            btn_ok.clicked.connect(dlg.accept)

            layout.addWidget(lbl_info)
            layout.addWidget(lbl_link)
            layout.addWidget(btn_ok, alignment=Qt.AlignCenter)

            dlg.exec()

        else:
            # 종료
            try:
                self._uvicorn.stop()
            except Exception as e:
                QMessageBox.warning(self, "웹서버 종료 오류", f"{e}")
            self.btn_web.setText("웹서버 OFF")


    def _on_build_clicked(self):
        # 현재 작업 디렉터리 고정
        work_dir = self._dest_dir()

        # 실행할 커맨드 시퀀스 구성
        self._cmds = []
        self._cmds.append(("make", ["clean"]))
        self._cmds.append(("make", []))
        self._cmds.append(("./all_tests_new", []))
        self._cmds.append(("./all_tests_old", []))
        self._cmds.append(("python", ["src/diff/main.py"]))
        self._cmds.append(("python", ["src/parser/main.py"]))
        self._cmd_index = 0

        # 팝업 준비
        self._dlg = BuildLogDialog(self)
        self._dlg.append(f"작업 디렉터리: {work_dir}")
        self._dlg.append("실행할 명령:")
        for prog, args in self._cmds:
            self._dlg.append("  - " + " ".join([prog] + args))
        self._dlg.set_running(True)

        # 프로세스 준비
        self._proc = QProcess(self)
        self._proc.setWorkingDirectory(str(work_dir))
        self._proc.setProcessChannelMode(QProcess.MergedChannels)
        self._proc.readyReadStandardOutput.connect(self._on_proc_output)
        self._proc.readyReadStandardError.connect(self._on_proc_output)
        self._proc.finished.connect(self._on_proc_finished)
        self._proc.errorOccurred.connect(self._on_proc_error)

        # 팝업 버튼
        self._dlg.btn_stop.clicked.connect(self._on_stop_clicked)
        self._dlg.buttons.rejected.connect(self._on_close_clicked)

        # 실행
        self._start_next()
        self._dlg.exec()

    def _start_next(self):
        if self._proc is None or self._dlg is None:
            return
        if self._cmd_index >= len(self._cmds):
            self._dlg.append("✅ 전체 빌드 완료")
            self._dlg.set_running(False)
            return
        prog, args = self._cmds[self._cmd_index]
        self._dlg.append("\n▶ 실행: " + " ".join([prog] + args))
        self._proc.start(prog, args)
        if not self._proc.waitForStarted(5000):
            self._dlg.append("❌ 프로세스 시작 실패")
            self._dlg.set_running(False)

    def _on_proc_output(self):
        if not (self._proc and self._dlg):
            return
        data = self._proc.readAll().data().decode(errors="replace")
        self._dlg.append(data.rstrip("\n"))

    def _on_proc_finished(self, exitCode, exitStatus):
        if not self._dlg:
            return
        if exitStatus == QProcess.NormalExit and exitCode == 0:
            self._dlg.append("✅ 단계 완료")
            self._cmd_index += 1
            self._start_next()
        else:
            self._dlg.append(f"❌ 실패 (exit={exitCode}, status={int(exitStatus)})")
            self._dlg.set_running(False)

    def _on_proc_error(self, err):
        if self._dlg:
            self._dlg.append(f"⚠️ 프로세스 오류: {err}")
            self._dlg.set_running(False)

    def _on_stop_clicked(self):
        if self._proc and self._proc.state() != QProcess.NotRunning:
            self._dlg.append("⛔ 중지 요청…")
            self._proc.kill()

    def _on_close_clicked(self):
        # 실행 중이면 닫기 불가, 종료 후만 닫기 허용
        if self._proc and self._proc.state() != QProcess.NotRunning:
            return
        self._dlg.reject()
    def _browse(self, type, edit: QLineEdit):
        """
        '폴더 선택' 버튼 콜백:
        - 파일 대화상자로 디렉터리 선택
        - 선택 시 QSettings('project_dir') 저장 및 상위 콜백(on_pick_folder) 호출
        """
        cur = edit.text().strip() or str(pathlib.Path.home())
        src_str = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택", cur, QFileDialog.ShowDirsOnly)
        if not src_str:
            return  # 취소

        src = pathlib.Path(src_str)
        if not src.exists() or not src.is_dir():
            QMessageBox.warning(self, "잘못된 폴더", "선택한 경로가 유효한 폴더가 아닙니다.")
            return

        # 1) 대상 경로 계산: 프로그램 내부의 target_new
        dst = self._dest_dir() / f"target_{type}"

        # 2) 대상 비우기(있으면 전부 삭제) 후 빈 폴더 준비
        try:
            self._ensure_empty_dir(dst)
        except Exception as e:
            QMessageBox.critical(self, "대상 준비 실패", str(e))
            return

        # 3) 전체 복사 수행
        try:
            self._copy_entire_folder_to(src, dst)
        except Exception as e:
            # 복사 실패 시 깨끗하게 유지하도록 dst를 비워 둡니다.
            try:
                self._ensure_empty_dir(dst)
            except Exception:
                pass
            QMessageBox.critical(self, "복사 실패", str(e))
            return

        # 4) UI/설정 갱신
        edit.setText(str(src))
        self.settings.setValue(f"project_dir_{type}", str(src))
        # 5) 메인으로 콜백: 우측 탐색기를 target_new로 바로 열어 보여줌
        if self.on_pick_folder:
            self.on_pick_folder(dst)
            # 6) 사용자 안내
            QMessageBox.information(
                self,
                "복사 완료",
                f"선택한 폴더 전체를 다음 위치로 복사했습니다.\n\n원본: {src}\n대상:  {dst}"
            )

    def _stub(self, name:str):
        """
        현재 단계에서는 기능 스텁: 안내 메시지 박스만 표시.
        - 실제 구현 시, 서브프로세스 실행/로그 스트리밍 등을 연결.
        """
        QMessageBox.information(self, name, f"현재는 UI 스켈레톤입니다.\n‘{name}’ 기능은 추후 구현 예정입니다.")

    def _dest_dir(self) -> pathlib.Path:
        """
        프로그램(실행 파일) 기준의 target_new 절대 경로를 반환.
        - PyInstaller로 배포 시 applicationDirPath()는 실행파일이 위치한 폴더입니다. (권한 문제로 쓰기 불가한 환경이라면 AppData 등으로 바꾸세요.)
        """
        return pathlib.Path(getattr(sys, '_MEIPASS', pathlib.Path(__file__).resolve().parent))

    def _ensure_empty_dir(self, path: pathlib.Path) -> None:
        """
        path가 존재하면 통째로 삭제 후 깨끗한 디렉터리로 재생성.
        """
        try:
            if path.exists():
                shutil.rmtree(path)
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"대상 폴더 초기화 실패: {path}\n{e}")

    def _copy_entire_folder_to(self, src: pathlib.Path, dst: pathlib.Path) -> None:
        """
        src 폴더 전체를 dst(target_new)에 복사.
        - dst는 미리 비워진(또는 새로 만든) 폴더라고 가정.
        - shutil.copytree(..., dirs_exist_ok=True)를 사용해 src의 모든 내용을 dst로 복사.
        """
        try:
            # dst가 이미 존재해도 허용하고, src의 내용을 dst 내부로 복사
            shutil.copytree(src, dst, dirs_exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"폴더 복사 실패: {src} → {dst}\n{e}")


# -----------------------------------------------------------------------------


# -------------------------------- 메인 윈도우 --------------------------------
class MainWindow(QMainWindow):
    """
    전체 앱의 메인 윈도우.
    - 상단 툴바(프로젝트 열기/다크 토글/검색/로그 액션)
    - 좌측 컨트롤 패널(ControlPanel)
    - 우측: (상) 디렉터리 트리 + 파일 테이블, (하) 미리보기 + 로그 콘솔
    - 사용자 설정(QSettings)으로 마지막 경로/테마 복원
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TraceRecoViz")
        self.setMinimumSize(1200, 760)
        self.settings = QSettings(APP_ORG, APP_NAME)

        # ----- Toolbar 구성 -----
        tb = QToolBar("Main"); tb.setIconSize(QSize(20, 20)); self.addToolBar(tb)
        # self.action_open = QAction(make_icon("folder-open", QStyle.SP_DirOpenIcon), "프로젝트 열기", self)
        self.action_dark = QAction(make_icon("weather-clear-night", QStyle.SP_DialogYesButton), "다크 모드", self)
        self.action_dark.setCheckable(True)
        # 툴바에 액션 배치(구분선 포함)
        tb.addAction(self.action_dark); tb.addSeparator()

        # 검색 입력 상자(파일/폴더 이름 필터)
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("검색(파일/폴더 이름)…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(320)
        # 툴바에 액션 배치(구분선 포함)
        tb.addWidget(self.search); tb.addSeparator()

        # 브레드크럼: 현재 보고 있는 경로 요약
        self.breadcrumb = QLabel("/", self)
        self.breadcrumb.setObjectName("Breadcrumb")  # QSS로 색상 등 스타일 지정
        self.breadcrumb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(self.breadcrumb)

        # 툴바 우측 정렬 스페이서
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        #
        # # 로그 액션(지우기/복사/저장)
        # self.action_log_clear = QAction(make_icon("edit-clear", QStyle.SP_DialogResetButton), "로그 지우기", self)
        # self.action_log_copy  = QAction(make_icon("edit-copy", QStyle.SP_FileDialogDetailedView), "로그 복사", self)
        # self.action_log_save  = QAction(make_icon("document-save", QStyle.SP_DialogSaveButton), "로그 저장", self)
        # tb.addAction(self.action_log_clear); tb.addAction(self.action_log_copy); tb.addAction(self.action_log_save)

        # ----- 메인 스플리터: 좌(컨트롤) | 우(탐색/미리보기) -----
        root_split = QSplitter(Qt.Horizontal, self)  # 수평 분할: 좌/우
        root_split.setHandleWidth(10)                # 핸들(경계) 잡기 쉬움

        # 좌측: 컨트롤 패널(프로젝트 경로/옵션/작업 버튼)
        self.ctrl_panel = ControlPanel(self.settings, on_pick_folder=self.set_root)
        root_split.addWidget(self.ctrl_panel)

        # 우측: 상단(탐색기) + 하단(미리보기/로그)
        right_split = QSplitter(Qt.Vertical, self)
        right_split.setHandleWidth(10)

        # ----- 파일 탐색기 (상단 좌: 트리, 상단 우: 테이블) -----
        # 디렉터리 트리 모델: 디렉터리 전용 필터(드라이브/루트 포함)
        self.dir_model = QFileSystemModel(self); self.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Drives); self.dir_model.setRootPath(QDir.rootPath())
        self.dir_view = QTreeView(self); self.dir_view.setModel(self.dir_model); self.dir_view.setHeaderHidden(True); self.dir_view.setAnimated(True)
        self.dir_view.setAlternatingRowColors(True); self.dir_view.setExpandsOnDoubleClick(True); self.dir_view.setIndentation(18)
        for c in range(1, self.dir_model.columnCount()): self.dir_view.hideColumn(c)  # 트리에서는 이름만 표시

        # 파일 테이블 모델: 파일/폴더 전부 표시
        self.file_model = QFileSystemModel(self); self.file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot); self.file_model.setRootPath(QDir.rootPath())
        # 프록시로 필터/정렬 제공
        self.proxy = FilesProxy(self); self.proxy.setSourceModel(self.file_model)

        self.table = QTableView(self); self.table.setModel(self.proxy); self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True); self.table.setSelectionBehavior(QTableView.SelectRows); self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader(); header.setSectionResizeMode(0, QHeaderView.Stretch)  # 이름 컬럼은 남은 공간 채움
        for col in [1,2,3]: header.setSectionResizeMode(col, QHeaderView.ResizeToContents)          # 크기/종류/수정일 컬럼은 내용에 맞게

        # 상단 좌우 스플리터(트리 | 테이블)
        top_split = QSplitter(Qt.Horizontal, self); top_split.setHandleWidth(10)
        top_split.addWidget(self.dir_view); top_split.addWidget(self.table)
        top_split.setStretchFactor(0,1); top_split.setStretchFactor(1,2)

        # ----- 하단: 미리보기 + 로그 콘솔 -----
        bottom = QSplitter(Qt.Horizontal, self); bottom.setHandleWidth(10)
        self.preview = PreviewPanel(self)

        self.log_edit = QPlainTextEdit(self)
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("빌드/계측 로그 콘솔")
        bottom.addWidget(self.preview); bottom.addWidget(self.log_edit)
        bottom.setStretchFactor(0, 2); bottom.setStretchFactor(1, 1)

        # 우측 상/하 배치
        right_split.addWidget(top_split)
        right_split.addWidget(bottom)
        right_split.setStretchFactor(0, 3)
        right_split.setStretchFactor(1, 2)

        # 좌/우 배치
        root_split.addWidget(right_split)
        root_split.setStretchFactor(0, 0)  # 좌(컨트롤) 폭은 고정적
        root_split.setStretchFactor(1, 1)  # 우(탐색 등) 확장

        self.setCentralWidget(root_split)

        # ----- 시그널 연결 -----
        # self.action_open.triggered.connect(self._toolbar_open_project)  # 툴바 '프로젝트 열기'
        self.action_dark.toggled.connect(self.toggle_theme)             # 다크 모드 토글
        self.search.textChanged.connect(self.apply_filter)              # 검색 텍스트 변경 → 필터 반영
        self.dir_view.selectionModel().currentChanged.connect(self.on_dir_changed)            # 트리 선택 변경
        self.table.selectionModel().currentChanged.connect(self.on_table_current_changed)     # 테이블 선택 변경
        #
        # self.action_log_clear.triggered.connect(self.log_edit.clear)    # 로그 지우기
        # self.action_log_copy.triggered.connect(self._copy_log)          # 로그 복사
        # self.action_log_save.triggered.connect(self._save_log)          # 로그 저장

        # ----- 설정 복원 -----
        start_dir = self.settings.value("last_dir", str(pathlib.Path.home()))
        theme = self.settings.value("theme", "dark")
        self.action_dark.setChecked(theme == "dark")
        self.apply_theme(theme)
        self.set_root(pathlib.Path(start_dir))

        # 초기 안내 메시지(로그 창)
        self._append_log("ℹ️ UI 스켈레톤 준비 완료. 미리보기는 Makefile 계열까지 텍스트로 표시됩니다.")

    # ---------------------- Theme ----------------------
    def apply_theme(self, mode: str):
        """
        Fusion 스타일 + 전역 QSS 적용.
        - mode == "dark" → DARK_QSS
        - 그 외 → LIGHT_QSS
        """
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        if mode == "dark":
            QApplication.instance().setStyleSheet(DARK_QSS)
        else:
            QApplication.instance().setStyleSheet(LIGHT_QSS)

    def toggle_theme(self, checked: bool):
        """다크 모드 체크 상태에 따라 테마 전환 및 설정 저장."""
        mode = "dark" if checked else "light"
        self.apply_theme(mode)
        self.settings.setValue("theme", mode)

    # ---------------------- Folder handling ----------------------
    # def _toolbar_open_project(self):
    #     """
    #     툴바의 '프로젝트 열기' 액션:
    #     - 파일 대화상자에서 폴더 선택
    #     - ControlPanel의 경로 입력에 반영 + 설정 저장 + set_root() 호출
    #     """
    #     cur = self.ctrl_panel.edit_proj.text().strip() or self.current_root()
    #     path = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택", cur, QFileDialog.ShowDirsOnly)
    #     if path:
    #         self.ctrl_panel.edit_proj.setText(path)
    #         self.settings.setValue("project_dir", path)
    #         self.set_root(Path(path))

    def set_root(self, path: pathlib.Path):
        """
        탐색기의 루트 디렉터리를 변경:
        - 트리/테이블의 모델 루트 인덱스 갱신
        - 브레드크럼 업데이트
        - 미리보기 초기화
        - 설정(last_dir) 저장
        """
        path_str = str(path)
        dir_index = self.dir_model.index(path_str)
        if not dir_index.isValid():
            # 경로가 유효하지 않으면 홈 디렉터리로 폴백
            path_str = str(pathlib.Path.home())
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
        """현재 트리의 루트 인덱스 경로 반환(없으면 홈 경로)."""
        idx = self.dir_view.rootIndex()
        if idx.isValid(): return self.dir_model.filePath(idx)
        return str(pathlib.Path.home())

    def on_dir_changed(self, current, _previous):
        """
        트리 선택 변경 시 콜백:
        - 해당 폴더를 테이블의 루트로 매핑(우측 파일 목록 갱신)
        - 브레드크럼 및 미리보기 갱신
        """
        path = self.dir_model.filePath(current)
        src_index = self.file_model.index(path)
        self.table.setRootIndex(self.proxy.mapFromSource(src_index))
        self.update_breadcrumb(path)
        self.preview.update_preview(path)

    def on_table_current_changed(self, current: QModelIndex, _prev: QModelIndex):
        """
        테이블(파일/폴더 목록)에서 현재 선택 항목 변경 시:
        - 선택된 경로를 미리보기에 반영
        """
        if not current.isValid():
            self.preview.clear(); return
        src_index = self.proxy.mapToSource(current)
        path = self.file_model.filePath(src_index)
        self.preview.update_preview(path)

    # ---------------------- UI helpers ----------------------
    def apply_filter(self, text: str):
        """
        검색 문자열을 공백 기준으로 토큰화 → 토큰 사이에 '.*'를 넣어 순서 매칭 정규식 생성.
        예: "cmake list" → "cmake.*list"
        """
        tokens = [QRegularExpression.escape(t) for t in text.strip().split() if t.strip()]
        pattern = ".*".join(tokens) if tokens else ""
        self.proxy.setFilterRegularExpression(QRegularExpression(pattern))

    def update_breadcrumb(self, path: str):
        """단순 경로 파츠를 ' / '로 이어서 브레드크럼 라벨에 표시."""
        root = pathlib.Path(path)
        parts = root.parts
        pretty = " / ".join(parts) if parts else "/"
        self.breadcrumb.setText(pretty)

    def _append_log(self, line: str):
        """로그 콘솔(QPlainTextEdit)에 한 줄 추가."""
        self.log_edit.appendPlainText(line)

    def _copy_log(self):
        """로그 전체를 클립보드에 복사하고 확인 메시지 추가."""
        QGuiApplication.clipboard().setText(self.log_edit.toPlainText())
        self._append_log("✅ 로그를 클립보드로 복사했습니다.")

    def _save_log(self):
        """
        로그를 파일로 저장:
        - 기본 경로: 홈 디렉터리의 trace_log.txt
        - 인코딩: UTF-8
        """
        path, _ = QFileDialog.getSaveFileName(self, "로그 저장", str(pathlib.Path.home() / "trace_log.txt"), "Text Files (*.txt);;All Files (*.*)")
        if not path:
            return
        try:
            pathlib.Path(path).write_text(self.log_edit.toPlainText(), encoding="utf-8")
            self._append_log(f"💾 로그 저장 완료: {path}")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"로그 저장 중 오류: {e}")

# -----------------------------------------------------------------------------


def main():
    """
    애플리케이션 엔트리 포인트.
    - QApplication 생성
    - 앱/조직 이름 설정(QSettings의 스코프에도 영향)
    - 메인 윈도우 생성/표시 후 이벤트 루프 진입
    """
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    # Qt6: HiDPI는 기본적으로 지원. 추가 스케일 팩터 설정이 필요하면 여기서 조정 가능.
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    BUILD_DIRS = [
        os.path.join(os.path.dirname(__file__), "build", "sequence_diagram"),
        os.path.join(os.path.dirname(__file__), "build", "log"),
        os.path.join(os.path.dirname(__file__), "build", "new"),
        os.path.join(os.path.dirname(__file__), "build", "old"),
        os.path.join(os.path.dirname(__file__), "build", "result"),
    ]
    for path in BUILD_DIRS:
        os.makedirs(path, exist_ok=True)
    main()

