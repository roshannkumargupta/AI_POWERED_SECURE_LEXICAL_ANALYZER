#include <string>
struct MetricRecord {
    std::string serviceName;
    int statusCode;
    double latencyMs;
};
MetricRecord createRecord(int code, double lat) {
    return {"AuthService", code, lat};
}
