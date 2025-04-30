rm -r build/
mkdir build && cd build
cd build
cmake ..
make
./hello-tool
cd ..