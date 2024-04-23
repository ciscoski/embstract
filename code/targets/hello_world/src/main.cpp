#include <iostream>

#define TEST_THIS_ONE_P

using Ciao = int;

/// @brief Ciao mondo !
/// @param x
void Foo(int tTest)
{
    int buf[10];
    if (tTest == 1000)
        buf[tTest] = 0; // <- ERROR
}

#ifdef NDEBUG
/// @brief Cisco is the best
void Csisco()
{
    std::cout << "Cisco";
}
#endif

/// @brief Main entry point
/// @return always 0
auto main() -> int
{
    Foo(10);
    std::cout << "Hello World!";
    return 0;
}
