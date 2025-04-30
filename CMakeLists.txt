cmake_minimum_required(VERSION 3.4.3)

project(HelloClangTool)

find_package(LLVM REQUIRED CONFIG)
list(APPEND CMAKE_MODULE_PATH "${LLVM_CMAKE_DIR}")
include(AddLLVM)

find_package(Clang REQUIRED CONFIG)
include_directories(${CLANG_INCLUDE_DIRS})
add_definitions(${CLANG_DEFINITIONS})

add_executable(hello-tool tool.cpp)

target_link_libraries(hello-tool
  PRIVATE
  clangTooling
  clangBasic
  clangASTMatchers
)
