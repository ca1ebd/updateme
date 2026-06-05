# Contributing

Thanks for your interest in updateme!

## Branching

- Branch off `main`
- Name your branch `feature/short-description` or `fix/short-description`
- Open a PR back to `main` when ready

## Making changes

1. Fork or clone the repo
2. Edit `config.sh` for personal settings (it is gitignored-friendly — do not commit your personal config)
3. Test by running `./updateme.sh` or `updateme` if installed
4. Open a PR with a short description of what changed and why

## Code style

- All scripts use `#!/usr/bin/env bash` and target bash 4+
- Modules live in `modules/` and are sourced by `updateme.sh`
- Keep external dependencies to zero: `curl`, `python3`, and `bash` only
- Graceful degradation: if a section fails, warn and continue rather than exit

## Adding a new section

1. Create `modules/mysection.sh` with a `show_mysection()` function
2. Source it in `updateme.sh` alongside the other modules
3. Add a `--mysection` flag to the arg parser
