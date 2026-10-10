#include <syslog.h>
void safe_report_incident(const char* alert_msg) {
    syslog(LOG_ERR, "%s", alert_msg);
}
