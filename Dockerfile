# -------- Base 이미지 --------
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /work

# -------- 필수 패키지 --------
RUN apt-get update && apt-get install -y \
    wget gnupg lsb-release software-properties-common \
    build-essential cmake git ninja-build \
    python3 python3-pip bear \
    # GoogleTest 소스
    libgtest-dev \
    # 이 아래는 gtest 빌드에 필요
    && rm -rf /var/lib/apt/lists/*

# -------- LLVM/Clang 18 설치 --------
RUN wget https://apt.llvm.org/llvm.sh && \
    chmod +x llvm.sh && \
    ./llvm.sh 18 all && \
    rm llvm.sh

# -------- GoogleTest 정적 라이브러리 빌드 --------
RUN cd /usr/src/gtest && \
    cmake -S . -B build -DCMAKE_C_COMPILER=clang-18 -DCMAKE_CXX_COMPILER=clang++-18 && \
    cmake --build build && \
    cp build/lib/*.a /usr/lib

# -------- 기본 컴파일러를 clang-18로 고정 --------
RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-18 100 && \
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-18 100 && \
    update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-18 100

# -------- 환경 변수 --------
ENV CC=/usr/bin/clang
ENV CXX=/usr/bin/clang++

# -------- 기본 실행 쉘 --------
CMD ["/bin/bash"]
    