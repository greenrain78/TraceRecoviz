# TraceRecoviz


# run

``` bash

make SRCS="src/sample1.cc src/sample1_unittest.cc" TARGET=test1
make SRCS="src/sample2.cc src/sample2_unittest.cc" TARGET=test2
make SRCS="src/sample3_unittest.cc" TARGET=test3

```
https://greenrain78.github.io/GTestGraph/html/sd6.html?data=data/unittest6/sd1.json

# install
    
``` bash
sudo apt update
sudo apt install llvm-17 clang-17 libclang-17-dev

python3 -m venv venv
source venv/bin/activate
pip install libclang

```

## builder

``` bash
sudo apt install aspectc++
```


# 설명
## analyer 
1단계: 정적 분석기 (C++ 파서)
- 소스코드에서 정의된 클래스명, 함수명, 인자명과 타입, 반환타입 을 추출하여 JSON으로 변환
## builder
2단계: AspectC++ 코드 생성기
- 삽입할 계측코드를 생성
## compiler
3단계: ag++ 컴파일 및 trace.log 생성
- AspectC++로 생성된 코드를 포함하여 컴파일
## decoder
4단계: trace.log 파서 → 시각화 데이터 변환기
- trace.log를 파싱하여 JSON으로 변환
