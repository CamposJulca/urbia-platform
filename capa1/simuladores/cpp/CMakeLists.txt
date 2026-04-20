cmake_minimum_required(VERSION 3.16)
project(urbia_sensor_cpp VERSION 1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

find_package(nlohmann_json REQUIRED)

add_executable(urbia_sensor
    src/main.cpp
    src/sensor_base.cpp
    src/sensor_trifasico.cpp
    src/mqtt_publisher.cpp
)

target_include_directories(urbia_sensor PRIVATE include)
target_link_libraries(urbia_sensor
    nlohmann_json::nlohmann_json
    paho-mqtt3as
    paho-mqttpp3
)
