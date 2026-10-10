#include <cstdio>

void writeLog(const char* path, const char* text) {
    FILE* fp = fopen(path, "a");
    if (fp) {
        fprintf(fp, "%s\n", text);
        fclose(fp);
    }
}
