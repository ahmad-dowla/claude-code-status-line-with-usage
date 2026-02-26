# Claude Code Status Line With 5-hour and 7-day Usage Limits
Minimal status line that shows usage limits without having to constantly run the /usage command. I've used this with Claude's Team plan as of February 2026 which doesn't show separate limits for Sonnet vs Opus.

```shell
5h: 6% (4h 23m - 6pm)
7d: 78% (4.1d - 3/2)
```

To use, place in a directory of your choice, and ask Claude to setup statusline using the file. Note that timezone is currently hardcoded to CST.
