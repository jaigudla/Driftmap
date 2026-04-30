cmake_minimum_required(VERSION 3.18)
project(driftmap_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(
  driftmap_core
  src/bindings.cpp
  src/stats.cpp
)

target_include_directories(
  driftmap_core
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
