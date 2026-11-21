# PGSavant Root installer (`com.arevj.pgsavant`)

This Root-only derivative installer carries its own `pgsavant` Zygisk module. Java implementation classes remain under `dev.pgrazor.root`, independently of Android's installed application ID. Explicit restart routing targets the new installer package. Original PGRazor's package and module are untouched.

## Injection selection

A new module ships **Off**. Installing the installer APK does not install or enable its module. Installing or updating the module may require one phone reboot to activate the Zygisk loader. Updates retain the derivative's previous On/Off choice.

1. Close Pokémon GO.
2. To enable PGSavant, turn original PGRazor **Off** in its own installer first.
3. In PGSavant, choose On, then reopen the game when ready.

The derivative refuses a switch while the game is running, and refuses On while original PGRazor may inject or its state cannot be established. It does not force-stop the game, toggle original PGRazor, or reboot automatically. Its native loader independently checks original PGRazor's per-launch Off marker before reading its payload. A root-manager disable/removal flag alone is insufficient because an existing zygote can still hold that module until reboot.

To return to the original, close the game, turn PGSavant Off, then turn original PGRazor On in its installer. This explicit closed-game procedure is required; the upstream loader does not cooperate with a new shared lock.

The later immediate **PvP inputs** switch is separate from injection selection and is not implemented by this installer change.

## Isolation and checks

- Module controls only `/data/adb/modules/pgsavant` and its staged update. Original paths are read only for coexistence checks.
- Runtime settings/preferences, account/vault names, logs, backups and code-cache prefixes use PGSavant namespaces inside the game UID. Original state is not migrated or cleared.
- The installer reports root manager, Zygisk, module state and exact game version/signature. It uses bounded root actions after user interaction; background detection is read-only.
- Retain the same derivative signing key for future updates. Never replace the original installer to bypass a certificate mismatch.
- Host JVM/shell tests exercise state parsing, write/refusal behavior and bounded command execution. The standalone native guard fixture covers missing, present, malformed and unknown path states without operating the game.
