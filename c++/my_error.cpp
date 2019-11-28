#include "my_error.hpp"

my_error::my_error(std::string message): message(message)
{
}

my_error::~my_error()
{
}

const char* my_error::what() const throw()
{
    return message.c_str();
}