# CMake 빌드 가이드

## 개요
이 프로젝트는 이제 CMake를 사용하여 크로스 플랫폼 빌드를 지원합니다.
- ✅ Linux
- ✅ Windows (MinGW, MSYS2, Visual Studio)
- ✅ macOS

## 필수 요구사항

### 공통
- CMake 3.15 이상
- C++17 지원 컴파일러
- LLVM/Clang 18
- GoogleTest

### Windows

#### 옵션 1: MSYS2 (권장)
```bash
# MSYS2 설치 후 MSYS2 터미널에서:
pacman -S mingw-w64-x86_64-cmake
pacman -S mingw-w64-x86_64-clang
pacman -S mingw-w64-x86_64-llvm
pacman -S mingw-w64-x86_64-gtest
```

#### 옵션 2: Visual Studio + vcpkg
```powershell
# vcpkg로 의존성 설치
vcpkg install llvm:x64-windows
vcpkg install gtest:x64-windows
vcpkg integrate install
```

#### 옵션 3: WSL (현재 사용 중)
```bash
# Ubuntu/Debian 기반
sudo apt-get install cmake
sudo apt-get install llvm-18 clang-18 libclang-18-dev
sudo apt-get install libgtest-dev
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install cmake
sudo apt-get install llvm-18 clang-18 libclang-18-dev
sudo apt-get install libgtest-dev

# GoogleTest 빌드 (필요시)
cd /usr/src/gtest
sudo cmake .
sudo make
sudo cp *.a /usr/lib
```

### macOS
```bash
brew install cmake
brew install llvm@18
brew install googletest
```

## 빌드 방법

### 1. 빌드 디렉토리 생성 및 구성
```bash
# 프로젝트 루트에서
mkdir build
cd build

# CMake 구성
cmake ..

# 또는 특정 컴파일러 지정 (Windows)
cmake .. -G "MinGW Makefiles"
cmake .. -G "Visual Studio 17 2022"
cmake .. -G "Unix Makefiles"
```

### 2. 빌드
```bash
# 모든 타겟 빌드
cmake --build .

# 특정 타겟만 빌드
cmake --build . --target inject_trace_tool
cmake --build . --target all_tests_new
cmake --build . --target all_tests_old
cmake --build . --target all_tests

# 병렬 빌드 (더 빠름)
cmake --build . -j 8
```

### 3. 실행
```bash
# Windows
.\all_tests_new.exe
.\all_tests_old.exe

# Linux/macOS
./all_tests_new
./all_tests_old
```

### 4. 정리
```bash
# 빌드 디렉토리만 정리
cmake --build . --target clean

# 모든 생성 파일 정리
cmake --build . --target clean-all

# 또는 빌드 디렉토리 전체 삭제
cd ..
rm -rf build  # Linux/macOS
rmdir /s /q build  # Windows CMD
```

## 빠른 시작

### Linux/WSL
```bash
mkdir build && cd build
cmake ..
cmake --build . --target all_tests -j
./all_tests_new
./all_tests_old
```

### Windows (MSYS2 MinGW64)
```bash
mkdir build && cd build
cmake .. -G "MinGW Makefiles"
cmake --build . --target all_tests -j
./all_tests_new.exe
./all_tests_old.exe
```

### Windows (Visual Studio)
```powershell
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release --target all_tests
.\Release\all_tests_new.exe
.\Release\all_tests_old.exe
```

## 트러블슈팅

### LLVM/Clang을 찾을 수 없음
```bash
# LLVM 경로 수동 지정
cmake .. -DLLVM_DIR=/path/to/llvm/lib/cmake/llvm

# Windows 예시
cmake .. -DLLVM_DIR="C:/Program Files/LLVM/lib/cmake/llvm"

# MSYS2 예시
cmake .. -DLLVM_DIR=/mingw64/lib/cmake/llvm
```

### GoogleTest를 찾을 수 없음
```bash
# GTest 경로 수동 지정
cmake .. -DGTest_DIR=/path/to/gtest/lib/cmake/GTest

# 또는 pkg-config 사용
export PKG_CONFIG_PATH=/path/to/gtest/lib/pkgconfig:$PKG_CONFIG_PATH
```

### Windows에서 링크 오류
```bash
# 올바른 생성기 사용 확인
cmake .. -G "MinGW Makefiles"  # MinGW 사용 시
cmake .. -G "Visual Studio 17 2022"  # Visual Studio 사용 시

# 경로에 공백이 있는 경우 따옴표 사용
cmake .. "-DCMAKE_PREFIX_PATH=C:/Program Files/LLVM"
```

## 프로젝트 구조
```
build/                          # CMake 빌드 디렉토리
├── instrumented/              # 계측된 코드
│   ├── target_new/           # 새 버전 계측 코드
│   └── target_old/           # 이전 버전 계측 코드
├── inject_trace_tool(.exe)   # 계측 도구
├── all_tests_new(.exe)       # 새 버전 테스트
└── all_tests_old(.exe)       # 이전 버전 테스트
```

## 기존 Makefile과의 비교

| 기능 | Makefile | CMake |
|------|----------|-------|
| 크로스 플랫폼 | ❌ Linux 전용 | ✅ Windows/Linux/macOS |
| IDE 지원 | ❌ 제한적 | ✅ VS Code, Visual Studio, CLion |
| 병렬 빌드 | ✅ make -j | ✅ cmake --build . -j |
| 의존성 관리 | ⚠️ 수동 | ✅ 자동 |
| 증분 빌드 | ✅ | ✅ 더 정확함 |

## 추가 정보

- Makefile은 여전히 사용 가능합니다 (Linux 환경에서)
- CMake는 더 나은 IDE 통합과 크로스 플랫폼 지원을 제공합니다
- Visual Studio Code의 CMake Tools 확장을 사용하면 GUI로 빌드 가능합니다
