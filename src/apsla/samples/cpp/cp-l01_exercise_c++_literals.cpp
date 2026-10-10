#include <string_view>
using namespace std::literals;
int main() { auto raw = R"x(first line\nsecond line)x"; auto count=1'000'000; auto hex=0x1.8p+2; auto suffix="sample"sv; char8_t a=u8'a'; char16_t b=u'b'; char32_t c=U'c'; wchar_t d=L'd'; return int(count + int(hex) + int(raw.size()+suffix.size()+a+b+c+d)); }
