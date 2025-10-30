@echo off
REM Windows 네이티브 빌드 스크립트 (CMD)

echo ================================
echo TraceRecoviz CMake Build Script
echo ================================
echo.

REM 빌드 디렉토리 생성
if not exist "build" (
    echo Creating build directory...
    mkdir build
)

cd build

REM CMake 구성
echo.
echo Configuring CMake...

REM MSYS2 UCRT64 경로 자동 감지 및 CMake 변수 설정
set "MSYS_PREFIX=C:\msys64\ucrt64"
set "MINGW_PREFIX=C:\msys64\mingw64"

set "LLVM_DIR_HINT="
set "Clang_DIR_HINT="
set "GTest_DIR_HINT="

if exist "%MSYS_PREFIX%\lib\cmake\llvm\LLVMConfig.cmake" set "LLVM_DIR_HINT=%MSYS_PREFIX%\lib\cmake\llvm"
if exist "%MINGW_PREFIX%\lib\cmake\llvm\LLVMConfig.cmake" if "%LLVM_DIR_HINT%"=="" set "LLVM_DIR_HINT=%MINGW_PREFIX%\lib\cmake\llvm"

if exist "%MSYS_PREFIX%\lib\cmake\clang\ClangConfig.cmake" set "Clang_DIR_HINT=%MSYS_PREFIX%\lib\cmake\clang"
if exist "%MINGW_PREFIX%\lib\cmake\clang\ClangConfig.cmake" if "%Clang_DIR_HINT%"=="" set "Clang_DIR_HINT=%MINGW_PREFIX%\lib\cmake\clang"

if exist "%MSYS_PREFIX%\lib\cmake\GTest\GTestConfig.cmake" set "GTest_DIR_HINT=%MSYS_PREFIX%\lib\cmake\GTest"
if exist "%MINGW_PREFIX%\lib\cmake\GTest\GTestConfig.cmake" if "%GTest_DIR_HINT%"=="" set "GTest_DIR_HINT=%MINGW_PREFIX%\lib\cmake\GTest"

set "CMAKE_ARGS="
if not "%LLVM_DIR_HINT%"=="" set "CMAKE_ARGS=%CMAKE_ARGS% -DLLVM_DIR=%LLVM_DIR_HINT%"
if not "%Clang_DIR_HINT%"=="" set "CMAKE_ARGS=%CMAKE_ARGS% -DClang_DIR=%Clang_DIR_HINT%"
if not "%GTest_DIR_HINT%"=="" set "CMAKE_ARGS=%CMAKE_ARGS% -DGTest_DIR=%GTest_DIR_HINT%"

REM 컴파일러 자동 지정 (MSYS2 MinGW 툴체인 우선)
if exist "%MSYS_PREFIX%\bin\gcc.exe" set "CMAKE_ARGS=%CMAKE_ARGS% -DCMAKE_C_COMPILER=%MSYS_PREFIX%\bin\gcc.exe"
if exist "%MSYS_PREFIX%\bin\g++.exe" set "CMAKE_ARGS=%CMAKE_ARGS% -DCMAKE_CXX_COMPILER=%MSYS_PREFIX%\bin\g++.exe"

REM 생성기 선택: VS -> Ninja -> MinGW Makefiles -> Default
where cl.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Detected Visual Studio environment
    cmake .. -G "Visual Studio 17 2022" %CMAKE_ARGS%
) else (
    where ninja.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Detected Ninja
        cmake .. -G "Ninja" %CMAKE_ARGS%
    ) else (
        where mingw32-make.exe >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo Detected MinGW environment
            cmake .. -G "MinGW Makefiles" %CMAKE_ARGS%
        ) else (
            echo Warning: No known compiler detected, using default generator
            cmake .. %CMAKE_ARGS%
        )
    )
)

if %ERRORLEVEL% NEQ 0 (
    echo CMake configuration failed!
    cd ..
    exit /b 1
)

REM 빌드
echo.
echo Building project...
cmake --build . --target all_tests -j 8

if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    cd ..
    exit /b 1
)

echo.
echo ================================
echo Build completed successfully!
echo ================================
echo.
echo Executables:
echo   - %CD%\all_tests_new.exe
echo   - %CD%\all_tests_old.exe
echo.
echo To run tests:
echo   all_tests_new.exe
echo   all_tests_old.exe

cd ..
