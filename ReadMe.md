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


cd /mnt/c/Users/user/Documents/GitHub/FINALPROJECT_Version2

# 1) 이미지 빌드 (현재 디렉터리에 Dockerfile이 있다고 가정)
docker build -t clang18-env .

# 2) 프로젝트 디렉터리를 컨테이너에 마운트해 진입
docker run --rm -it -v "$PWD":/work clang18-env

# 3) 컨테이너 내부에서 Makefile 실행
make          # 또는 make runAll
# 컴파일 DB가 필요하면
bear -- make


pip install PySide6 pyinstaller

pyinstaller --onefile --windowed --name TraceRecoviz_linux --add-data ".:." main.py

source venv/bin/activate

한글 폰트 설치
sudo apt install -y fonts-noto-cjk fonts-nanum fonts-noto-color-emoji


sds - 

#todo 객체 생성 소멸 추가 - 
객체의 lifeline이 색칠되는지 확인
파라미터가 바꼈다는 것을 잘 드러나게

gui
비기능요구사항 호환성


pyinstaller TraceRecoviz_linux.spec


pacman -S --needed mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-ninja mingw-w64-ucrt-x86_64-llvm mingw-w64-ucrt-x86_64-clang mingw-w64-ucrt-x86_64-clang-tools-extra mingw-w64-ucrt-x86_64-gtest

delta
