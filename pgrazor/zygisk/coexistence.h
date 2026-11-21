#pragma once

namespace pgsavant {
enum class PathState { missing, file, directory, unknown };

// Before app specialization, require original PGRazor's per-launch Off marker.
// A root-manager disable/removal flag alone is insufficient: an already-running
// zygote can still hold the original module until a phone reboot.
template<class Probe> bool original_allows_injection(Probe probe) {
    const auto original = probe("/data/adb/modules/pgrazor");
    if (original == PathState::missing) return true;
    if (original != PathState::directory) return false;
    return probe("/data/adb/modules/pgrazor/pgrazor/injection-off") == PathState::file;
}
}
