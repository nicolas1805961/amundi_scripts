#include <vector>
#include <string>
#include <iostream>
#include <algorithm>
#include <sstream>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <unordered_map>
#include <map>
#include <variant>
#include <iterator>
#include "discographie.hpp"
#include "my_error.hpp"
#include <exception>

void analyse(std::string word, discographie &discographie, std::istringstream &is)
{
    std::vector<std::string> input;
    std::string temp_word;
    while (std::getline(is, temp_word, '|'))
    {
        if (temp_word != " ")
        {
            auto it = std::find_if_not(temp_word.begin(), temp_word.end(), [](char x) { return isspace(x); });
            temp_word.erase(temp_word.begin(), it);
            auto it2 = std::find_if_not(temp_word.rbegin(), temp_word.rend(), [](char x) { return isspace(x); });
            temp_word.erase(temp_word.rbegin().base(), it2.base());
        }
        input.push_back(temp_word);
    }
    if (word == "quitter")
        exit(0);
    /*else if (input[0] == "enregistrer" && input.size() == 2)
    discographie.enregistrer(input, discographie);
else if (input[0] == "charger" && input.size() == 2)
    discographie.charger(input, discographie);*/
    else if (word == "ajouter")
        discographie.ajouter(discographie, input);
    else if (word == "afficher")
        discographie.afficher(discographie, input);
    else
        throw my_error("Erreur: Commande invalide.\n");
}

void prompt(discographie &discographie)
{
    std::vector<std::string> input{};
    std::string line;
    std::string word;
    while (true)
    {
        std::cout << "> ";
        std::getline(std::cin, line);
        if (line == "")
            continue;
        std::istringstream is{line};
        is >> word;
        try
        {
            analyse(word, discographie, is);
        }
        catch (const std::exception& e)
        {
            std::cerr << e.what() << '\n';
        }
        input.clear();
    }
}

int main(void)
{
    discographie discographie;
    prompt(discographie);
    return 0;
}