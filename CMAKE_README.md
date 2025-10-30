# TraceRecoviz - CMake 크로스 플랫폼 빌드 시스템

## 🎉 새로운 기능: CMake 지원

이제 TraceRecoviz는 **Windows, Linux, macOS**에서 모두 빌드할 수 있습니다!

## 📋 생성된 파일들

### 핵심 파일
- **CMakeLists.txt** - 크로스 플랫폼 빌드 구성
- **CMAKE_BUILD_GUIDE.md** - 상세한 빌드 가이드
- **build_cmake.sh** - Linux/WSL/MSYS2용 빌드 스크립트
- **build_cmake.bat** - Windows CMD용 빌드 스크립트

## 🚀 빠른 시작

### Windows (WSL - 현재 환경)
```bash
# WSL 터미널에서
chmod +x build_cmake.sh
./build_cmake.sh
cd build
./all_tests_new
./all_tests_old
```

### Windows (MSYS2)
```bash
# MSYS2 터미널에서
./build_cmake.sh
cd build
./all_tests_new.exe
./all_tests_old.exe
```

### Windows (CMD/PowerShell)
```cmd
build_cmake.bat
cd build
all_tests_new.exe
all_tests_old.exe
```

### VS Code에서 빌드
1. **Ctrl+Shift+P** → "CMake: Configure" 실행
2. **Ctrl+Shift+B** → 빌드 실행
3. **F5** → 디버그 실행

## 📚 상세 가이드

전체 가이드는 **CMAKE_BUILD_GUIDE.md** 파일을 참조하세요:
- 각 플랫폼별 의존성 설치 방법
- 다양한 빌드 옵션
- 트러블슈팅 가이드
- IDE 통합 방법

## 🔄 기존 Makefile과의 차이점

| 기능 | Makefile | CMake |
|------|----------|-------|
| 플랫폼 지원 | Linux만 | Windows/Linux/macOS |
| IDE 통합 | 제한적 | 완벽 지원 |
| 병렬 빌드 | ✓ | ✓ (더 효율적) |
| 의존성 추적 | 수동 | 자동 |
| 크로스 컴파일 | 어려움 | 쉬움 |

## 💡 추천 사항

**기존 사용자 (Linux)**: Makefile 계속 사용 가능
```bash
make all_tests
```

**Windows 사용자**: CMake 사용 권장
```bash
./build_cmake.sh  # WSL/MSYS2
# 또는
build_cmake.bat   # CMD
```

**모든 사용자**: VS Code + CMake Tools 확장 설치 권장

## 🛠️ 필요한 도구

### 최소 요구사항
- CMake 3.15+
- C++17 컴파일러
- LLVM/Clang 18
- GoogleTest

### Windows 설치 옵션
1. **WSL** (권장) - Linux 환경 그대로 사용
2. **MSYS2** - Unix 도구 + MinGW
3. **Visual Studio** + vcpkg - 네이티브 Windows 빌드

상세한 설치 방법은 **CMAKE_BUILD_GUIDE.md**를 참조하세요.

## 🐛 문제 해결

### LLVM을 찾을 수 없음
```bash
cmake .. -DLLVM_DIR=/path/to/llvm/lib/cmake/llvm
```

### GoogleTest를 찾을 수 없음
```bash
cmake .. -DGTest_DIR=/path/to/gtest/lib/cmake/GTest
```

### 더 많은 해결책은 CMAKE_BUILD_GUIDE.md 참조

## 📞 지원

문제가 발생하면:
1. CMAKE_BUILD_GUIDE.md의 트러블슈팅 섹션 확인
2. `cmake --version`과 `clang --version`으로 버전 확인
3. `build` 디렉토리 삭제 후 재시도

---

**기존 Makefile은 여전히 사용 가능합니다!**
