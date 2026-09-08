# Bamboo Forest gameplay and audio quality pass

The release adds swept player, projectile, wind and ground-enemy collisions;
safe moving-platform carries; reliable double jumps, springs and updrafts;
safe timed-platform reappearance; portal exit locks; and bounded rising lava
with refuge platforms. Enemies use terrain-aware pursuit, visible attack
warnings and appropriate active damage phases. Collected bamboo and defeated
enemies stay claimed through checkpoint retries, preventing score farming.
Every chapter supplies staff, dash and glide pickups.

## Sound

Eight original looping arrangements cover grove, shadow, ember, wind, crystal,
tide, gravity and boss encounters. Twenty-eight cues cover movement, combat,
pickups, world mechanisms and results. Tracks crossfade, pause lowers music,
and repeated effects are rate limited. Music and effects can be switched
independently with the browser buttons or M / N. Preferences persist locally.

The music and effects use original synthesized instruments, without sampled
recordings. Rebuild with `python scripts/compose-bamboo-audio.py` (NumPy and
ffmpeg required), then `python scripts/package-bamboo-journey.py`.
`audio/manifest.json` records the track durations and signal levels.

## Top three

Completed normal runs can enter three initials when their score qualifies.
The title and pause screens display the three highest scores, initials and
chapter reached. Practice runs do not qualify. Scores persist across reloads
in browser localStorage, or the desktop save file. This is explicitly a
**per-device board**, not a shared website leaderboard. Clearing browser data
clears that board; unavailable storage produces a save-failure message.

## Verification

Run `python scripts/test-bamboo-journey.py` and
`python scripts/test-bamboo-quality.py` after packaging. Both test the shipped
archive, and both run before deployment. They cover all 18 chapters, platform
landing collisions, pickup access geometry, enemy updates, major biome
mechanics, exits, score persistence, audio decoding and ability regressions.
Browser checks exercise the actual WASM game, desktop keyboard and mobile
touch controls, responsive layout, audio settings and emitted audio signal.

The route graph checks geometry, including candidate moving and timed
surfaces. It is not a timing-aware playthrough of every route. Automated
checks cannot establish that every level has optimal difficulty or that no
unseen bug remains; repeated human playtesting is still needed for that.
