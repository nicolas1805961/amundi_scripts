#include "grand_nombre.hpp"
#include <iostream>
#include <cctype>

void collapse_high_precedence(std::vector<std::string> &input);
void collapse_low_precedence(std::vector<std::string> &input);

std::string collapse(std::vector<std::string> &input)
{
    collapse_high_precedence(input);
    collapse_low_precedence(input);
    return input[0];
}

void collapse_parenthesis(std::vector<std::string> &input)
{
    auto left_parenthesis = find_if(input.begin(), input.end(), [](std::string s) { return s == "("; });

    while (left_parenthesis != input.end())
    {
        auto right_parenthesis = find_if(left_parenthesis, input.end(), [](std::string s) { return s == ")"; });
        std::vector<std::string> copy(left_parenthesis + 1, right_parenthesis);
        auto res = collapse(copy);
        *left_parenthesis = res;
        left_parenthesis = input.erase(left_parenthesis + 1, right_parenthesis + 1);
        left_parenthesis = find_if(left_parenthesis, input.end(), [](std::string s) { return s == "("; });
    }
}

void collapse_high_precedence(std::vector<std::string> &input)
{
    auto operator_high_precedence = input.begin() + 1;
    operator_high_precedence = std::find_if(operator_high_precedence, input.end(), [](std::string s) { return s == "*" || s == "/"; });
    while (operator_high_precedence != input.end())
    {
        grand_nombre left(*(operator_high_precedence - 1));
        grand_nombre right(*(operator_high_precedence + 1));
        grand_nombre result(std::vector<int>{});
        if (*operator_high_precedence == "*")
        {
            grand_nombre temp(left * right);
            result = temp;
        }
        else if (*operator_high_precedence == "/")
        {
            grand_nombre temp(left / right);
            result = temp;
        }
        *(operator_high_precedence - 1) = std::to_string(result.get_number());
        operator_high_precedence = input.erase(operator_high_precedence, operator_high_precedence + 2);
        operator_high_precedence = std::find_if(operator_high_precedence, input.end(), [](std::string s) { return s == "*" || s == "/"; });
    }
}

void collapse_low_precedence(std::vector<std::string> &input)
{
    auto operator_high_precedence = input.begin() + 1;
    operator_high_precedence = std::find_if(operator_high_precedence, input.end(), [](std::string s) { return s == "+" || s == "-"; });
    while (operator_high_precedence != input.end())
    {
        grand_nombre left(*(operator_high_precedence - 1));
        grand_nombre right(*(operator_high_precedence + 1));
        grand_nombre result(std::vector<int>{});
        if (*operator_high_precedence == "+")
        {
            grand_nombre temp(left + right);
            result = temp;
        }
        else if (*operator_high_precedence == "-")
        {
            grand_nombre temp(left - right);
            result = temp;
        }
        *(operator_high_precedence - 1) = std::to_string(result.get_number());
        operator_high_precedence = input.erase(operator_high_precedence, operator_high_precedence + 2);
        operator_high_precedence = std::find_if(operator_high_precedence, input.end(), [](std::string s) { return s == "+" || s == "-"; });
    }
}

int main(void)
{
    std::vector<std::string> input;
    std::string line;
    while (true)
    {
        std::cout << "> ";
        std::getline(std::cin, line);
        auto it = std::find_if_not(line.begin(), line.end(), [](char c) {return isdigit(c); });
        while (it != line.end())
        {
            if (*it == '(')
                it = line.insert(it + 1, ' ') + 1;
            else if (*it == ')')
                it = line.insert(it, ' ') + 2;
            else
            {
                it = line.insert(it, ' ') + 2;
                it = line.insert(it, ' ') + 1;
            }
            it = std::find_if_not(it, line.end(), [](char c) { return isdigit(c); });
        }
        std::stringstream ss{line};
        std::string word;
        while (std::getline(ss, word, ' '))
            input.push_back(word);
        collapse_parenthesis(input);
        std::cout << collapse(input) << std::endl;
        input.clear();
    }
    return 0;
}