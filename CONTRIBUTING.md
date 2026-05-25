# Contributing to roomq

Thanks for your interest! roomq is young, so bug reports, ideas, and pull requests are all genuinely welcome.

## Ways to help

- **Report a bug or request a feature** → open an [issue](https://github.com/swastikmaiti/roomq/issues).
- **Ask a question or share a use-case** → start a [discussion](https://github.com/swastikmaiti/roomq/discussions).
- **Improve docs or code** → open a pull request (see below).
- **Just trying it out and hit a rough edge?** That's valuable feedback — file an issue.

## Development setup

Requires **Python 3.13** and **Node 20.19+**.

```sh
git clone https://github.com/swastikmaiti/roomq.git
cd roomq
make install   # backend venv + frontend deps (one time)
make dev       # backend :8000 + frontend :3000 (Ctrl+C stops both)
make test      # backend test suite
```

Run `make help` for all targets. You can also run the whole stack in a container with `make docker-build && make docker-run`.

## Pull requests

1. Fork the repo and branch off `main`.
2. Keep the change focused — one logical change per PR.
3. **Add or update tests**, and make sure `make test` passes.
4. For UI changes, run `npx tsc --noEmit` and `npm run build` in `packages/ui`.
5. Write a clear PR description: what changed and why.

## Style & conventions

- **Backend (Python):** match the surrounding style and type hints; reuse existing helpers (e.g. the retry helper in `packages/server/app/services/retry.py` for IO-bound calls).
- **Frontend (TypeScript/Next.js):** keep components small and follow existing patterns.
- Keep commits small with clear, single-line messages.

## License of contributions

By contributing, you agree that your contributions are licensed under the project's [Apache License 2.0](LICENSE). No separate CLA is required.
