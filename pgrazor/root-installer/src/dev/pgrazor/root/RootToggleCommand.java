package dev.pgrazor.root;

/** Fixed-path launch-time switch commands, shared by the installer and the JVM/shell fixtures. */
final class RootToggleCommand {
    private RootToggleCommand() {}
    static final String OK_PREFIX = "PGSAVANT_TOGGLE_OK";
    private static final String PATHS = "L=/data/adb/modules/pgsavant\nU=/data/adb/modules_update/pgsavant\nF=pgrazor/injection-off\n"
        + "fail(){ echo PGSAVANT_TOGGLE_FAIL=$1; exit 1; }\n";
    static final String LIVE_INJECTION_PROBE =
        "if [ -f /data/adb/modules/pgsavant/pgrazor/injection-off ]; then echo MODOFF=1; else echo MODOFF=0; fi";

    static String command(boolean on) {
        String action = on ? "rm -f" : "touch";
        String verify = on ? "[ ! -e" : "[ -f";
        return PATHS
            + "command -v pidof >/dev/null 2>&1 || fail process_check_unavailable\n"
            + "GAME_PID=$(pidof com.nianticlabs.pokemongo 2>/dev/null); GAME_RC=$?\n"
            + "[ \"$GAME_RC\" -eq 1 ] && [ -z \"$GAME_PID\" ] || fail close_game_first\n"
            + "[ -f \"$L/module.prop\" ] || fail not_installed\n"
            + "[ -f \"$L/pgrazor/toggle-v1\" ] || fail no_toggle_marker\n"
            + "[ ! -e \"$L/disable\" ] || fail disabled\n"
            + "[ ! -e \"$L/remove\" ] || fail removal_pending\n"
            + "if [ -d \"$U\" ]; then [ -d \"$U/pgrazor\" ] || fail staged_payload_missing; fi\n"
            + (on ? originalOffGuard() : "")
            + action + " \"$L/$F\" || fail write_live\n"
            + "if [ -d \"$U/pgrazor\" ]; then " + action + " \"$U/$F\" || fail write_staged; fi\n"
            + verify + " \"$L/$F\" ] || fail verify_live\n"
            + "if [ -d \"$U/pgrazor\" ]; then " + verify + " \"$U/$F\" ] || fail verify_staged; fi\n"
            + "echo " + OK_PREFIX + (on ? "=on\n" : "=off\n");
    }
    private static String originalOffGuard() {
        return "O=/data/adb/modules/pgrazor\n"
            + "[ -r /data/adb/modules ] && [ -x /data/adb/modules ] || fail original_state_unknown\n"
            + "if [ -e \"$O\" ] || [ -L \"$O\" ]; then\n"
            + "  [ -d \"$O\" ] && [ ! -L \"$O\" ] || fail original_state_unknown\n"
            + "  [ -f \"$O/pgrazor/injection-off\" ] && [ ! -L \"$O/pgrazor/injection-off\" ] && [ -r \"$O/pgrazor/injection-off\" ] || fail turn_original_pgrazor_off_first\n"
            + "fi\n";
    }
    static String preserveOffCommand() {
        return PATHS
            + "[ -d \"$U/pgrazor\" ] || fail no_staged_payload\n"
            + "touch \"$U/$F\" || fail write_staged\n"
            + "[ -f \"$U/$F\" ] || fail verify_staged\n"
            + "echo " + OK_PREFIX + "=preserved_off\n";
    }
    static boolean hasLine(String output, String line) {
        if (output != null) for (String value : output.split("\\r?\\n")) if (line.equals(value.trim())) return true;
        return false;
    }
    static boolean injectionOffFromProbe(String output) { return hasLine(output, "MODOFF=1"); }
    static boolean confirmed(boolean on, String output) { return hasLine(output, OK_PREFIX + (on ? "=on" : "=off")); }
}
