#!/bin/bash
# Windows (WSL/MSYS2) 빌드 스크립트

set -e  # 오류 발생 시 중단

echo "================================"
echo "TraceRecoviz CMake Build Script"
echo "================================"
echo ""

# 빌드 디렉토리 생성
if [ ! -d "build" ]; then
    echo "Creating build directory..."
    mkdir build
fi

cd build

# CMake 구성
echo ""
echo "Configuring CMake..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "mingw"* ]]; then
    # MSYS2/MinGW 환경
    echo "Detected MSYS2/MinGW environment"
    cmake .. -G "MinGW Makefiles"
else
    # WSL 또는 Linux 환경
    echo "Detected Linux/WSL environment"
    cmake ..
fi

# 빌드
echo ""
echo "Building project..."
cmake --build . --target all_tests -j $(nproc 2>/dev/null || echo 4)

echo ""
echo "================================"
echo "Build completed successfully!"
echo "================================"
echo ""
echo "Executables:"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "mingw"* ]]; then
    echo "  - $(pwd)/all_tests_new.exe"
    echo "  - $(pwd)/all_tests_old.exe"
else
    echo "  - $(pwd)/all_tests_new"
    echo "  - $(pwd)/all_tests_old"
fi
echo ""
echo "To run tests:"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "mingw"* ]]; then
    echo "  ./all_tests_new.exe"
    echo "  ./all_tests_old.exe"
else
    echo "  ./all_tests_new"
    echo "  ./all_tests_old"
fi
