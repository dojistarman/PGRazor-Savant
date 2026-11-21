#include "coexistence_matrix.h"
#include <cassert>
#include <cstdio>

int main() {
    const int cases = pgsavant::coexistence_matrix();
    assert(cases == 64);
    std::printf("PASS PGSavant original-runtime guard: %d state combinations\n", cases);
}
