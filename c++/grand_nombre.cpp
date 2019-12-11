#include <vector>
#include <sstream>
#include <string>
#include <iterator>
#include <algorithm>
#include <iostream>
#include "grand_nombre.hpp"

grand_nombre::grand_nombre(std::vector<int> number, bool sign): number(number), sign(sign)
{
}

grand_nombre::grand_nombre(std::string nb, bool sign): sign(sign)
{
    set_number(nb);

}

grand_nombre::~grand_nombre()
{
}

std::ostream &operator<<(std::ostream &os, grand_nombre const &bn)
{
    if (bn.sign)
        os << "-";
    for (auto element : bn.number)
        os << element;
    return os;
}

grand_nombre grand_nombre::operator*(grand_nombre const& bn)
{
    std::vector<std::vector<int>> vec_of_vec;
    for (auto element1 = number.rbegin(); element1 != number.rend(); element1++)
    {
        std::vector<int> vec;
        auto number_of_zero = std::distance(element1.base() - 1, number.end()) - 1;
        for (int i = 0; i < number_of_zero; i++)
            vec.push_back(0);
        auto save = 0;
        for (auto element2 = bn.number.rbegin(); element2 != bn.number.rend(); element2++)
        {
            auto res = *element1 * *element2 + save;
            vec.insert(vec.begin(), res % 10);
            if (std::distance(element2.base() - 1, bn.number.begin()) == 0 && res >= 10)
            {
                vec.insert(vec.begin(), res / 10);
                break;
            }
            save = res / 10;
        }
        vec_of_vec.push_back(vec);
    }
    grand_nombre result(std::vector<int>{0});
    for (auto element : vec_of_vec)
        result += grand_nombre(element);
    return result;
}

grand_nombre grand_nombre::operator+(grand_nombre &bn)
{
    auto save = 0;
    std::vector<int> partial_res;
    auto res = 0;
    if (*this < bn)
    {
        auto it1_iterator = bn.number.end() - 1;
        auto it2_iterator_forward = number.end() - 1;
        while (it1_iterator != bn.number.begin() || it2_iterator_forward != number.begin() || *it1_iterator != 0 || *it2_iterator_forward != 0)
        {
            res = *it1_iterator + *it2_iterator_forward;
            partial_res.insert(partial_res.begin(), res % 10);
            save = res / 10;
            if (it2_iterator_forward == number.begin() && it1_iterator == bn.number.begin())
            {
                it2_iterator_forward = number.insert(it2_iterator_forward, save);
                it1_iterator = bn.number.insert(it1_iterator, 0);
            }
            else if(it2_iterator_forward == number.begin())
            {
                it2_iterator_forward = number.insert(it2_iterator_forward, save);
                it1_iterator--;
            }
            else
            {
                it2_iterator_forward--;
                *it2_iterator_forward += save;
                it1_iterator--;
            }
        }
        auto it = std::find_if_not(partial_res.begin(), partial_res.end(), [](int x) { return x == 0; });
        partial_res.erase(partial_res.begin(), it);
    }
    else if (*this >= bn)
    {
        auto it1_iterator = number.end() - 1;
        auto it2_iterator_forward = bn.number.end() - 1;
        while (it1_iterator != number.begin() || it2_iterator_forward != bn.number.begin() || *it1_iterator != 0 || *it2_iterator_forward != 0)
        {
            res = *it1_iterator + *it2_iterator_forward;
            partial_res.insert(partial_res.begin(), res % 10);
            save = res / 10;
            if (it2_iterator_forward == bn.number.begin() && it1_iterator == number.begin())
            {
                it2_iterator_forward = bn.number.insert(it2_iterator_forward, save);
                it1_iterator = number.insert(it1_iterator, 0);
            }
            else if(it2_iterator_forward == bn.number.begin())
            {
                it2_iterator_forward = bn.number.insert(it2_iterator_forward, save);
                it1_iterator--;
            }
            else
            {
                it2_iterator_forward--;
                *it2_iterator_forward += save;
                it1_iterator--;
            }
        }
        auto it = std::find_if_not(partial_res.begin(), partial_res.end(), [](int x) { return x == 0; } );
        partial_res.erase(partial_res.begin(), it);
    }
    else
        partial_res.push_back(0);
    grand_nombre result(partial_res);
    return result;
}

grand_nombre& grand_nombre::operator+=(grand_nombre const& bn)
{
    auto save = 0;
    std::vector<int> partial_res;
    auto res = 0;
    if (*this < bn)
    {
        std::vector<int> copy = this->number;
        auto it1_iterator = bn.number.rbegin();
        auto it2_iterator_forward = copy.end() - 1;
        while (it1_iterator != bn.number.rend())
        {
            res = *it1_iterator + *it2_iterator_forward;
            partial_res.insert(partial_res.begin(), res % 10);
            save = res / 10;
            it1_iterator++;
            if (it2_iterator_forward == copy.begin())
                it2_iterator_forward = copy.insert(it2_iterator_forward, save);
            else
            {
                it2_iterator_forward--;
                *it2_iterator_forward += save;
            }
        }
        auto it = std::find_if_not(partial_res.begin(), partial_res.end(), [](int x) { return x == 0; } );
        partial_res.erase(partial_res.begin(), it);
    }
    else if (*this >= bn)
    {
        std::vector<int> copy = bn.number;
        auto it1_iterator = number.rbegin();
        auto it2_iterator_forward = copy.end() - 1;
        while (it1_iterator != number.rend())
        {
            res = *it1_iterator + *it2_iterator_forward;
            partial_res.insert(partial_res.begin(), res % 10);
            save = res / 10;
            it1_iterator++;
            if (it2_iterator_forward == copy.begin())
                it2_iterator_forward = copy.insert(it2_iterator_forward, save);
            else
            {
                it2_iterator_forward--;
                *it2_iterator_forward += save;
            }
        }
        auto it = std::find_if_not(partial_res.begin(), partial_res.end(), [](int x) { return x == 0; } );
        partial_res.erase(partial_res.begin(), it);
    }
    else
        partial_res.push_back(0);
    number = partial_res;
    return *this;
}

grand_nombre& grand_nombre::operator-=(grand_nombre &bn)
{
    auto save = 0;
    std::vector<int> partial_res;
    auto res = 0;
    if (*this < bn)
    {
        auto it1_iterator = bn.number.rbegin();
        auto it2_iterator = number.rbegin();
        while (it1_iterator != bn.number.rend())
        {
            if (*it1_iterator < *it2_iterator)
            {
                res = (*it1_iterator + 10) - *it2_iterator;
                save = 1;
            }
            else
            {
                res = *it1_iterator - *it2_iterator;
                save = 0;
            }
            partial_res.insert(partial_res.begin(), res);
            it1_iterator++;
            if (it2_iterator + 1 == number.rend())
            {
                number.insert(it2_iterator.base() - 1, save);
                it2_iterator = number.rend() - 1;
            }
            else
            {
                number.insert(it2_iterator.base() - 1, *(it2_iterator + 1) + save);
                it2_iterator++;
            }
        }
        auto it = std::find_if_not(partial_res.begin(), partial_res.end(), [](int x) { return x == 0; } );
        partial_res.erase(partial_res.begin(), it);
        this->sign = true;
    }
    else if (*this > bn)
    {
        auto it1_iterator = number.rbegin();
        auto it2_iterator = bn.number.rbegin();
        while (it1_iterator != number.rend())
        {
            if (*it1_iterator < *it2_iterator)
            {
                res = (*it1_iterator + 10) - *it2_iterator;
                save = 1;
            }
            else
            {
                res = *it1_iterator - *it2_iterator;
                save = 0;
            }
            partial_res.insert(partial_res.begin(), res);
            it1_iterator++;
            if (it2_iterator + 1 == bn.number.rend())
            {
                bn.number.insert(it2_iterator.base() - 1, save);
                it2_iterator = bn.number.rend() - 1;
            }
            else
            {
                bn.number.insert(it2_iterator.base() - 1, *(it2_iterator + 1) + save);
                it2_iterator++;
            }
        }
        auto it = std::find_if_not(partial_res.begin(), partial_res.end(), [](int x) { return x == 0; } );
        partial_res.erase(partial_res.begin(), it);
    }
    else
        partial_res.push_back(0);

    number = partial_res;
    return *this;
}

grand_nombre grand_nombre::operator-(grand_nombre &bn)
{
    auto save = 0;
    std::vector<int> partial_res;
    auto res = 0;
    if (*this < bn)
    {
        auto it1_iterator = bn.number.end() - 1;
        auto it2_iterator = number.end() - 1;
        while (it1_iterator != bn.number.begin() - 1)
        {
            if (*it1_iterator < *it2_iterator)
            {
                res = (*it1_iterator + 10) - *it2_iterator;
                save = 1;
            }
            else
            {
                res = *it1_iterator - *it2_iterator;
                save = 0;
            }
            partial_res.insert(partial_res.begin(), res);
            it1_iterator--;
            if (it2_iterator == number.begin())
                it2_iterator = number.insert(it2_iterator, save);
            else
            {
                it2_iterator--;
                *it2_iterator += save;
            }
        }
        auto it = std::find_if_not(partial_res.begin(), partial_res.end(), [](int x) { return x == 0; } );
        partial_res.erase(partial_res.begin(), it);
        grand_nombre result(partial_res);
        result.sign = true;
        return result;
    }
    else if (*this > bn)
    {
        auto it1_iterator = number.end() - 1;
        auto it2_iterator = bn.number.end() - 1;
        while (it1_iterator != number.begin() - 1)
        {
            if (*it1_iterator < *it2_iterator)
            {
                res = (*it1_iterator + 10) - *it2_iterator;
                save = 1;
            }
            else
            {
                res = *it1_iterator - *it2_iterator;
                save = 0;
            }
            partial_res.insert(partial_res.begin(), res);
            it1_iterator--;
            if (it2_iterator == bn.number.begin())
                it2_iterator = bn.number.insert(it2_iterator, save);
            else
            {
                it2_iterator--;
                *it2_iterator += save;
            }
        }
        auto it = std::find_if_not(partial_res.begin(), partial_res.end(), [](int x) { return x == 0; } );
        partial_res.erase(partial_res.begin(), it);
        grand_nombre result(partial_res);
        return result;
    }
    else
    {
        partial_res.push_back(0);
        grand_nombre result(partial_res);
        return result;
    }
}

grand_nombre grand_nombre::operator/(grand_nombre const &bn)
{
    std::vector<int> partial_res;
    auto res = 0;
    auto it_numerateur = number.begin();
    auto numerateur = *it_numerateur;
    grand_nombre temp(std::vector<int>{numerateur});
    auto denominateur = bn.get_number();
    auto reste = *it_numerateur;
    auto next = it_numerateur + 1;
    while (it_numerateur != number.end())
    {
        while (numerateur < denominateur)
        {
            temp.number.push_back(*next);
            numerateur = temp.get_number();
            next++;
        }
        temp.number.clear();
        res = numerateur / denominateur;
        partial_res.push_back(res);
        reste = numerateur % denominateur;
        if (reste != 0)
        {
            temp.set_number(std::to_string(reste));
            numerateur = temp.get_number();
        }
        else if (next != number.end())
        {
            temp.set_number(std::to_string(*next));
            numerateur = temp.get_number();
        }
        it_numerateur = next;
    }
    return grand_nombre(partial_res);
}

void grand_nombre::set_number(std::string nb)
{
    auto it = nb.begin();
    if (*it == '-')
    {
        sign = true;
        it++;
    }
    while (it != nb.end())
    {
        number.push_back(*it - '0');
        it++;
    }
}

int grand_nombre::get_number() const
{
    std::stringstream ss;
    if (sign)
        ss << "-";
    for (auto element : number)
        ss << std::to_string(element);
    auto string_number = ss.str();
    return std::stoull(string_number);
}

grand_nombre& grand_nombre::operator=(grand_nombre const &bn)
{
    number.clear();
    sign = bn.sign;
    auto it_arg = bn.number.begin();
    while (it_arg != bn.number.end())
    {
        number.push_back(*it_arg);
        it_arg++;
    }
    return *this;
}

bool grand_nombre::operator<(grand_nombre const &bn)
{
    if (number.size() < bn.number.size())
        return true;
    else if (number.size() > bn.number.size())
        return false;
    else
    {
        auto pair = std::mismatch(number.begin(), number.end(), bn.number.begin());
        if (pair.first == number.end())
            return false;
        else if (*(pair.first) > *(pair.second))
            return false;
        else
            return true;
    }
}

bool grand_nombre::operator>(grand_nombre const &bn)
{
    if (number.size() > bn.number.size())
        return true;
    else if (number.size() < bn.number.size())
        return false;
    else
    {
        auto pair = std::mismatch(number.begin(), number.end(), bn.number.begin());
        if (pair.first == number.end())
            return false;
        else if (*(pair.first) > *(pair.second))
            return true;
        else
            return false;
    }
}

bool grand_nombre::operator<=(grand_nombre const &bn)
{
    if (number.size() < bn.number.size())
        return true;
    else if (number.size() > bn.number.size())
        return false;
    else
    {
        auto pair = std::mismatch(number.begin(), number.end(), bn.number.begin());
        if (pair.first == number.end())
            return true;
        else if (*(pair.first) > *(pair.second))
            return false;
        else
            return true;
    }
}

bool grand_nombre::operator>=(grand_nombre const &bn)
{
    if (number.size() < bn.number.size())
        return false;
    else if (number.size() > bn.number.size())
        return true;
    else
    {
        auto pair = std::mismatch(number.begin(), number.end(), bn.number.begin());
        if (pair.first == number.end())
            return true;
        else if (*(pair.first) > *(pair.second))
            return true;
        else
            return false;
    }
}