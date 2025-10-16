import os
import shutil
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
APP_NAME = "TraceRecoViz"  # 앱/설정 저장용 애플리케이션 이름


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

        p = Path(path)
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
        """
        정보 뷰 내용 구성:
        - 이름 / 종류 / 경로 / 크기
        - 디렉터리는 rglob로 합산(큰 트리에서는 시간이 걸릴 수 있으므로 주의)
        """
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
    좌측 컨트롤 패널: 프로젝트 경로 입력/선택 + 계측/빌드 옵션 + 액션 버튼.
    - 현재 버튼 동작은 '스텁'(메시지 박스만 뜸)
    - 실제 빌드/계측 로직 연동은 추후 on_click 슬롯에서 구현하면 됨.
    """
    def __init__(self, settings: QSettings, on_pick_folder):
        super().__init__()
        self.settings = settings
        self.on_pick_folder = on_pick_folder

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
        self.btn_run = QPushButton("웹 서버 실행")
        # 현재는 메시지 박스만 띄우는 스텁 동작
        self.btn_build.clicked.connect(lambda: self._stub("빌드 시작"))
        self.btn_run.clicked.connect(lambda: self._stub("빌드 시작"))
        a.addWidget(self.btn_build)
        a.addWidget(self.btn_run)

        # ----- 루트 레이아웃에 섹션 배치 -----
        root.addWidget(gb_proj1)
        root.addWidget(gb_actions)
        root.addStretch(1)

        # 마지막 프로젝트 경로 복원(QSettings)
        last_project_old = self.settings.value("project_dir_old", "")
        if last_project_old: self.edit_proj_old.setText(last_project_old)

        last_project_new = self.settings.value("project_dir_new", "")
        if last_project_new: self.edit_proj_new.setText(last_project_new)

    def _init_gb_project(self):
        pass

    def _browse(self, type, edit: QLineEdit):
        """
        '폴더 선택' 버튼 콜백:
        - 파일 대화상자로 디렉터리 선택
        - 선택 시 QSettings('project_dir') 저장 및 상위 콜백(on_pick_folder) 호출
        """
        cur = edit.text().strip() or str(Path.home())
        src_str = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택", cur, QFileDialog.ShowDirsOnly)
        if not src_str:
            return  # 취소

        src = Path(src_str)
        if not src.exists() or not src.is_dir():
            QMessageBox.warning(self, "잘못된 폴더", "선택한 경로가 유효한 폴더가 아닙니다.")
            return

        # 1) 대상 경로 계산: 프로그램 내부의 target_new
        dst =self._dest_dir() / f"target_{type}"

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
        print(f"프로젝트 폴더 복사 완료: project_dir_{type}")
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

    def _dest_dir(self) -> Path:
        """
        프로그램(실행 파일) 기준의 target_new 절대 경로를 반환.
        - PyInstaller로 배포 시 applicationDirPath()는 실행파일이 위치한 폴더입니다. (권한 문제로 쓰기 불가한 환경이라면 AppData 등으로 바꾸세요.)
        """
        return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))

    def _ensure_empty_dir(self, path: Path) -> None:
        """
        path가 존재하면 통째로 삭제 후 깨끗한 디렉터리로 재생성.
        """
        try:
            if path.exists():
                shutil.rmtree(path)
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"대상 폴더 초기화 실패: {path}\n{e}")

    def _copy_entire_folder_to(self, src: Path, dst: Path) -> None:
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
        start_dir = self.settings.value("last_dir", str(Path.home()))
        theme = self.settings.value("theme", "dark")
        self.action_dark.setChecked(theme == "dark")
        self.apply_theme(theme)
        self.set_root(Path(start_dir))

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

    def set_root(self, path: Path):
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
        """현재 트리의 루트 인덱스 경로 반환(없으면 홈 경로)."""
        idx = self.dir_view.rootIndex()
        if idx.isValid(): return self.dir_model.filePath(idx)
        return str(Path.home())

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
        root = Path(path)
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
    main()
