#pragma once
#include <vector>
#include <map>
#include <vector>
#include <string>
#include <iostream>
#include <fstream>
#include <algorithm>
#include <sstream>

class discographie
{
private:
    std::vector<std::map<std::string, std::string>> storage;


public:
    discographie();
    ~discographie();
    //void enregistrer(std::vector<std::string> const& input, discographie const& discographie);
    //void charger(std::vector<std::string> const& input, discographie & discographie);
    void ajouter(discographie &discographie, std::vector<std::string> input);
    void afficher(discographie &discographie, std::vector<std::string> input);
};