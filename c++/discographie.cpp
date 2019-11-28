#include "discographie.hpp"
#include "my_error.hpp"

discographie::discographie()
{
}

discographie::~discographie()
{
}

/*void discographie::enregistrer(std::vector<std::string> const& input, discographie const& discographie)
{
    std::ofstream os{input[1], std::ios::app};
}

void discographie::charger(std::vector<std::string> const& input, discographie & discographie)
{
    std::ifstream ifs{input[1]};
}*/
void discographie::ajouter(discographie &discographie, std::vector<std::string> input)
{
    if (input.size() == 0)
    {
        std::map<std::string, std::string> entry;
        entry["morceau"] = "Morceau inconnu";
        entry["album"] = "Album inconnu";
        entry["artiste"] = "Artiste inconnu";
        discographie.storage.push_back(entry);
        std::sort(discographie.storage.begin(), discographie.storage.end());
        std::unique(discographie.storage.begin(), discographie.storage.end());
    }
    else if (input.size() == 1)
    {
        std::map<std::string, std::string> entry;
        entry["morceau"] = input[0];
        entry["album"] = "Album inconnu";
        entry["artiste"] = "Artiste inconnu";
        discographie.storage.push_back(entry);
        std::sort(discographie.storage.begin(), discographie.storage.end());
        std::unique(discographie.storage.begin(), discographie.storage.end());
    }
    else if (input.size() == 2)
    {
        std::map<std::string, std::string> entry;
        entry["morceau"] = input[0];
        entry["album"] = input[1];
        entry["artiste"] = "Artiste inconnu";
        discographie.storage.push_back(entry);
        std::sort(discographie.storage.begin(), discographie.storage.end());
        std::unique(discographie.storage.begin(), discographie.storage.end());
    }
    else if (input.size() == 3)
    {
        std::map<std::string, std::string> entry;
        entry["morceau"] = input[0];
        if (input[1] == " ")
            entry["album"] = "Album inconnu";
        else
            entry["album"] = input[1];
        entry["artiste"] = input[2];
        discographie.storage.push_back(entry);
        std::sort(discographie.storage.begin(), discographie.storage.end());
        std::unique(discographie.storage.begin(), discographie.storage.end());
    }
    else
        throw my_error("Erreur: Commande invalide.\n");
}

void discographie::afficher(discographie &discographie, std::vector<std::string> input)
{
    if (input.size() > 2)
        throw my_error("Erreur: Commande invalide.\n");
    else if (input[0] == "morceau")
    {
        std::sort(discographie.storage.begin(), discographie.storage.end(), [](auto x, auto y) { return (x.at("morceau")) < (y.at("morceau")); });
        for (auto element : discographie.storage)
        {
            std::cout << element["morceau"] << " | " << element["album"] << " | " << element["artiste"] <<std::endl;
        }
    }
    else if (input[0] == "album")
    {
        std::sort(discographie.storage.begin(), discographie.storage.end(), [](auto x, auto y) { return (x.at("album")) < (y.at("album")); });

        auto start = discographie.storage.begin();
        while (start != discographie.storage.end())
        {
            auto it = std::adjacent_find(start, discographie.storage.end(), [](auto x, auto y) { return x.at("album") != y.at("album") || x.at("artiste") != y.at("artiste"); });
            if (it != discographie.storage.end())
                it++;
            std::sort(start, it, [](auto x, auto y) { return (x.at("morceau")) < (y.at("morceau")); });

            std::cout << "--> " << (*start).at("album") << "| " << (*start).at("artiste") <<std::endl;

            while (start != it)
            {
                std::cout << "\t/--> " << (*start).at("morceau") << std::endl;
                start++;
            }
        }
    }
    else if (input[0] == "artistes")
    {
        std::sort(discographie.storage.begin(), discographie.storage.end(), [](auto x, auto y) { return (x.at("artiste")) < (y.at("artiste")); });

        auto start = discographie.storage.begin();
        while (start != discographie.storage.end())
        {
            auto it = std::find_if_not(start, discographie.storage.end(), [start](auto x) { return (*start).at("artiste") == x.at("artiste"); });

            std::sort(start, it, [](auto x, auto y) { return (x.at("album")) < (y.at("album")); });

            auto it2 = std::find_if_not(start, it, [start](auto x) { return (*start).at("album") == x.at("album"); });

            std::sort(start, it2, [](auto x, auto y) { return (x.at("morceau")) < (y.at("morceau")); });

            std::cout << "--> " << (*start).at("artiste") << std::endl;
            while (start != it)
            {
                std::cout << "\t/--> " << (*start).at("album") << std::endl;
                while (start != it2)
                {
                    std::cout << "\t\t/--> " << (*start).at("morceau") << std::endl;
                    start++;
                }
                it2 = std::find_if_not(start, discographie.storage.end(), [start](auto x) { return (*start).at("album") == x.at("album"); });
            }
        }
    }
    else
        throw my_error("Erreur: Commande invalide.\n");
}
