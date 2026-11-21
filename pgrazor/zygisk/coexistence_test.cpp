#include "coexistence.h"
#include <cassert>
#include <cstring>
#include <cstdio>

int main() {
    using namespace pgsavant;
    const PathState states[] = {PathState::missing, PathState::file, PathState::directory, PathState::unknown};
    int cases = 0;
    for (auto original : states) for (auto off : states) {
        bool allowed = original_allows_injection([&](const char *path) {
            return std::strcmp(path, "/data/adb/modules/pgrazor") == 0 ? original : off;
        });
        assert(allowed == (original == PathState::missing ||
            (original == PathState::directory && off == PathState::file)));
        ++cases;
    }
    std::printf("PASS PGSavant original-runtime guard: %d state combinations\n", cases);
}
