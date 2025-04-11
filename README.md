# TraceRecoviz


# run

``` bash

make SRCS="src/sample1.cc src/sample1_unittest.cc" TARGET=my_test

```

# install
    
``` bash
sudo apt-get install libboost-all-dev
```
# 설명
## analyer 
1단계: 정적 분석기 (C++ 파서)
## builder
2단계: AspectC++ 코드 생성기
## compiler
3단계: ag++ 컴파일 및 trace.log 실행기
## decoder
4단계: trace.log 파서 → 시각화 데이터 변환기
