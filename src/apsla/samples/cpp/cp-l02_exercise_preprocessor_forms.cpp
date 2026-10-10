#ifndef SAMPLE_HEADER
#define SAMPLE_HEADER
#define SAMPLE_VALUE(x) \
    ((x) + 1)
#if defined(__cplusplus)
#include <iostream>
#elif defined(SAMPLE_C)
#include "sample.h"
#else
#pragma once
#endif
int main() { return SAMPLE_VALUE(1); }
