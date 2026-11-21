#pragma once
#include "coexistence.h"

namespace pgsavant {
inline bool same_path(const char *a, const char *b) {
    while (*a && *a == *b) { ++a; ++b; }
    return *a == *b;
}

// No OS/runtime dependency: execute this same policy matrix on Android or Wasm.
inline int coexistence_matrix() {
    const PathState states[] = {PathState::missing, PathState::file, PathState::directory, PathState::unknown};
    int cases = 0;
    for (auto parent : states) for (auto original : states) for (auto off : states) {
        const bool allowed = original_allows_injection([&](const char *path) {
            if (same_path(path, "/data/adb/modules")) return parent;
            if (same_path(path, "/data/adb/modules/pgrazor")) return original;
            return off;
        });
        const bool expected = parent == PathState::directory &&
            (original == PathState::missing || (original == PathState::directory && off == PathState::file));
        ++cases;
        if (allowed != expected) return -cases;
    }
    return cases;
}
}
