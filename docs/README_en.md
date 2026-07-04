# strip-comments-tool - Frontend Comment Stripping Tool

An interactive command-line tool for batch-removing comments from front-end projects. Supports multiple file types, backup, dry-run, colored output, configuration persistence, and more.

[中文](https://github.com/VZService/strip-comments-tool/blob/main/README.md) | English

---

## Features

- **Interactive Configuration**: Answer a few questions to choose language, directory, file types, etc. No need to memorize command-line arguments.
- **Multi-language Support**: Built-in Chinese and English interfaces. Auto-detects system language; switch manually anytime.
- **Precise Comment Removal**: Uses a state machine to scan character by character, accurately identifying and removing `//` and `/* */` comments in JS/TS while protecting strings, template literals, regular expressions, and `://` protocols.
- **Broad File Type Support**: Works with `.js`, `.ts`, `.jsx`, `.tsx`, `.vue`, `.css`, `.scss`, `.less`, `.html`, `.htm`.
- **Intelligent Inline Handling**: Automatically cleans JS comments inside `<script>` tags and CSS comments inside `<style>` tags in HTML; Vue single-file components handle `<template>`, `<script>`, and `<style>` sections separately.
- **Backup Mechanism**: Creates a `.bak` backup for every file before modification, making recovery easy.
- **Dry‑Run Mode**: Preview which files will be changed and see statistics without writing anything.
- **Exclusion Patterns**: Supports glob‑style patterns (e.g., `*.min.js`) to skip specific files.
- **Detailed Statistics**: Shows lines removed and bytes saved per file, with a total summary.
- **Logging**: All operations are written to `strip_comments.log` with timestamps and detailed records.
- **Configuration Persistence**: Automatically saves your last interactive choices to `~/.strip_comments_config.json` and loads them as defaults next time.
- **Colored Output**: Uses ANSI colors to distinguish status (success/error/warning/info); enabled on Windows automatically (via virtual terminal).

---

## Quick Start

### Requirements
- Python 3.6 or higher (no extra dependencies required)

### Download
Save `strip_comments.py` from this repository to your local machine.

### Run
Execute in your terminal:
```bash
python strip_comments.py
