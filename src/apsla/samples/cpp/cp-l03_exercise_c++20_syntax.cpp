#include <compare>
#include <concepts>
namespace demo { template<class T> concept Number = std::integral<T>; struct Box { int value; auto operator<=>(const Box&) const = default; }; int Box::* member = &Box::value; template<Number T> auto twice(T x) { auto fn = [x] { return x + x; }; return fn(); } }
int main() { demo::Box b{2}; return (b.*demo::member) + int(demo::twice(1)); }
