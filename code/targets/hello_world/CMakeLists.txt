add_executable(hello_world src/main.cpp)
#set_target_properties(hello_world PROPERTIES CXX_STANDARD 17)
target_compile_features(hello_world PUBLIC cxx_std_11)

set_target_properties(hello_world PROPERTIES "PCLINT_TEST" "bal bla bla")

set(PCLINT_COMPILER_OPTIONS "test Test" CACHE STRING "Test 123")