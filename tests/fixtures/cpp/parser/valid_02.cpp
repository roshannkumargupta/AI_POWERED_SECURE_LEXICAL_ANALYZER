#include <string>

class SessionManager {
public:
    SessionManager(const std::string& id);
    ~SessionManager();
    void close();
private:
    std::string sessionId;
};
