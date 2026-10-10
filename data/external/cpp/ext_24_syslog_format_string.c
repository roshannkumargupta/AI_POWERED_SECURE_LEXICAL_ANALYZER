#include <syslog.h>
void report_incident(const char* alert_msg) {
    syslog(LOG_ERR, alert_msg);
}
