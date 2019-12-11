#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <typeinfo>

class grand_nombre
{
private:
    std::vector<int> number;
    bool sign;

public:

    grand_nombre(std::vector<int> number, bool sign = false);

    grand_nombre(std::string nb, bool sign = false);

    ~grand_nombre();

    grand_nombre operator*(grand_nombre const& bn);

    grand_nombre operator+(grand_nombre &bn);

    grand_nombre& operator+=(grand_nombre const &bn);

    grand_nombre& operator-=(grand_nombre &bn);

    grand_nombre operator-(grand_nombre &bn);

    grand_nombre operator/(grand_nombre const &bn);

    grand_nombre& operator=(grand_nombre const &bn);

    bool operator<(grand_nombre const &bn);
    bool operator<=(grand_nombre const &bn);
    bool operator>=(grand_nombre const &bn);
    bool operator>(grand_nombre const &bn);

    friend std::ostream &operator<<(std::ostream &os, grand_nombre const &bn);

    int get_number() const;

    void set_number(std::string nb);
};
