#pragma once

namespace pgsavant {
enum class PathState { missing, file, directory, unknown };

// Before app specialization, require original PGRazor's per-launch Off marker.
// A root-manager disable/removal flag alone is insufficient: an already-running
// zygote can still hold the original module until a phone reboot.
template<class Probe> bool original_allows_injection(Probe probe) {
    // ENOENT for the child is only evidence of absence when the parent itself
    // is visible. A hidden/unknown module root must not mean "no original".
    if (probe("/data/adb/modules") != PathState::directory) return false;
    const auto original = probe("/data/adb/modules/pgrazor");
    if (original == PathState::missing) return true;
    if (original != PathState::directory) return false;
    return probe("/data/adb/modules/pgrazor/pgrazor/injection-off") == PathState::file;
}
}
