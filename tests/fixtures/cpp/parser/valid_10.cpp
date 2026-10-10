int computeHash(const char* data, int len) {
    int hash = 5381;
    for (int i = 0; i < len; ++i) {
        hash = ((hash << 5) + hash) + data[i];
    }
    return hash;
}
