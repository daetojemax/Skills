# Source

Apple's `device-interaction` skill, exported unchanged from Xcode 27.0 (`xcrun agent skills export`) on 2026-10-12.

Apple ships it without a license file; it is kept in this private repository for personal use. `SKILL.md` is Apple's text, not edited.

To update after an Xcode release, export again and copy the folder over this one:

```bash
xcrun agent skills export --output-dir /tmp/xcode-skills
rsync -a --delete --exclude SOURCES.md /tmp/xcode-skills/device-interaction/ device-interaction/
```

Project rule (see `templates/AGENTS.md`): use this skill only when the app runs through Xcode MCP – outside the Claude desktop app, where the built-in simulator is used instead.
