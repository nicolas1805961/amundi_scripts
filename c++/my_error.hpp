#pragma once
#include <exception>
#include <string>

class my_error: public std::exception
{
private:
    std::string message;

public:
    my_error(std::string message);
    virtual ~my_error();
    virtual const char *what() const throw();
};
