LLVM/Clang18 설치
sudo apt-get install llvm-18 clang-18 clang-tools-18 libclang-18-dev

기존에있던 구버전 llvm 삭제하고 
sudo apt remove --purge llvm-* clang-* libclang-dev libllvm-dev
sudo apt autoremove

다시설치
# 레포 키 등록
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh

# LLVM 18 설치
sudo ./llvm.sh 18

# 설치되었는지 확인
llvm-config-18 --version
clang-18 --version

# 모든 라이브러리 경로확인
llvm-config-18 --libdir

# 불필요한 에러코드 숨기기
sudo apt install bear
bear -- make

기본 clang//llvm 으로 연결
sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-18 100
sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-18 100
sudo update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-18 100



GoogleTest 설치
sudo apt-get install libgtest-dev
cd /usr/src/gtest
sudo cmake .
sudo make
sudo cp *.a /usr/lib // libgtest.a, libgtest_main.a 이동

python3 설치
sudo apt-get install python3