#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strip comments from front-end files interactively.
Features: color output, backup, exclude patterns, config saving, log file.
"""

import os
import re
import sys
import locale
import shutil
import json
import fnmatch
import datetime
from pathlib import Path

# 彩色输出
class Colors:
    _enabled = True
    @classmethod
    def enable(cls, force=True):
        cls._enabled = force and cls._supports_color()
    @classmethod
    def _supports_color(cls):
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetStdHandle(-11)
                mode = ctypes.c_ulong()
                if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(handle, mode.value | 0x0004)
                    return True
            except:
                pass
            return False
        return sys.stdout.isatty()
    @classmethod
    def _c(cls, text, code):
        return f"\033[{code}m{text}\033[0m" if cls._enabled else text
    @classmethod
    def red(cls, t): return cls._c(t, '31')
    @classmethod
    def green(cls, t): return cls._c(t, '32')
    @classmethod
    def yellow(cls, t): return cls._c(t, '33')
    @classmethod
    def blue(cls, t): return cls._c(t, '34')
    @classmethod
    def magenta(cls, t): return cls._c(t, '35')
    @classmethod
    def cyan(cls, t): return cls._c(t, '36')
    @classmethod
    def bold(cls, t): return cls._c(t, '1')
    @classmethod
    def dim(cls, t): return cls._c(t, '2')
Colors.enable()

# 多语言文本
TEXTS = {
    'en': {
        'ask_lang': 'Choose language (1=English, 2=中文) [default: auto]',
        'ask_dir': 'Enter project directory [default: current]',
        'ask_exts': 'File extensions to process (comma-separated) [default: all]',
        'ask_skip_dirs': 'Additional directories to skip (comma-separated) [default: none]',
        'ask_exclude': 'Exclude file patterns (glob, comma-separated) [default: none]',
        'ask_backup': 'Create .bak backup? (y/n) [default: y]',
        'ask_dry': 'Dry run? (y/n) [default: n]',
        'ask_verbose': 'Verbose output? (y/n) [default: n]',
        'invalid': 'Invalid input, using default.',
        'processing': 'Processing',
        'progress': 'Progress: {current}/{total} files',
        'done': 'Done. Modified: {modified}, Skipped: {skipped}, Errors: {errors}',
        'done_stats': 'Total lines removed: {lines}, Total bytes saved: {bytes}',
        'error': 'ERROR',
        'skipped': 'Skipped',
        'stripped': 'Stripped',
        'backup_created': 'Backup created: {backup}',
        'no_files': 'No matching files found.',
        'dry_run': '[DRY RUN] Would strip:',
        'file_stats': '  Removed {lines} lines, saved {bytes} bytes',
        'log_header': '=== Strip Comments Log ===',
        'log_timestamp': 'Timestamp: {ts}',
        'config_loaded': 'Loaded config from {cfg}',
        'config_saved': 'Saved config to {cfg}',
    },
    'zh': {
        'ask_lang': '选择语言（1=English, 2=中文）[默认：自动识别]',
        'ask_dir': '请输入项目目录 [默认：当前目录]',
        'ask_exts': '要处理的文件扩展名（逗号分隔）[默认：全部]',
        'ask_skip_dirs': '额外跳过的目录（逗号分隔）[默认：无]',
        'ask_exclude': '排除的文件模式（glob，逗号分隔）[默认：无]',
        'ask_backup': '修改前创建 .bak 备份？(y/n) [默认：y]',
        'ask_dry': '试运行？(y/n) [默认：n]',
        'ask_verbose': '显示详细信息？(y/n) [默认：n]',
        'invalid': '输入无效，使用默认值。',
        'processing': '处理中',
        'progress': '进度：{current}/{total} 个文件',
        'done': '完成。修改：{modified}，跳过：{skipped}，错误：{errors}',
        'done_stats': '总计移除行数：{lines}，节省字节数：{bytes}',
        'error': '错误',
        'skipped': '跳过',
        'stripped': '已清理',
        'backup_created': '已创建备份：{backup}',
        'no_files': '未找到匹配的文件。',
        'dry_run': '[试运行] 将清理：',
        'file_stats': '  移除 {lines} 行，节省 {bytes} 字节',
        'log_header': '=== 注释移除日志 ===',
        'log_timestamp': '时间戳：{ts}',
        'config_loaded': '已加载配置：{cfg}',
        'config_saved': '已保存配置：{cfg}',
    }
}

def get_system_lang():
    # 尝试使用 getlocale() 获取语言代码
    try:
        lang_code, _ = locale.getlocale()
        if lang_code and lang_code.startswith('zh'):
            return 'zh'
    except:
        pass
    # 如果 getlocale() 返回 None，尝试从环境变量读取
    try:
        import os
        lang_env = os.environ.get('LANG', '') or os.environ.get('LC_ALL', '')
        if lang_env.startswith('zh'):
            return 'zh'
    except:
        pass
    # 默认英文
    return 'en'

def t(key, lang):
    return TEXTS[lang].get(key, key)

# 配置管理
CONFIG_FILE = Path.home() / '.strip_comments_config.json'

def load_config(lang):
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            print(Colors.dim(t('config_loaded', lang).format(cfg=CONFIG_FILE)))
            return cfg
        except:
            pass
    return {}

def save_config(cfg, lang):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
        print(Colors.dim(t('config_saved', lang).format(cfg=CONFIG_FILE)))
    except:
        pass

# 日志记录
LOG_FILE = Path('strip_comments.log')

def write_log(message, lang):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except:
        pass

# 注释移除核心（状态机）
def strip_js_comments(text):
    result = []
    i, n = 0, len(text)
    in_string = None
    in_regex = False
    escape = False
    while i < n:
        ch = text[i]
        if in_string is not None:
            result.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == in_string:
                in_string = None
            i += 1
            continue
        if in_regex:
            result.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '/':
                in_regex = False
            i += 1
            continue
        # 多行注释
        if ch == '/' and i + 1 < n and text[i+1] == '*':
            i += 2
            while i + 1 < n and not (text[i] == '*' and text[i+1] == '/'):
                if text[i] == '\n':
                    result.append('\n')
                i += 1
            if i + 1 < n:
                i += 2
            continue
        # 单行注释（保护 ://）
        if ch == '/' and i + 1 < n and text[i+1] == '/':
            if i > 0 and text[i-1] == ':':
                result.append(ch)
                i += 1
                continue
            i += 2
            while i < n and text[i] != '\n':
                i += 1
            if i < n and text[i] == '\n':
                result.append('\n')
                i += 1
            continue
        if ch in ('"', "'", '`'):
            in_string = ch
            result.append(ch)
            i += 1
            continue
        if ch == '/':
            if i == 0 or text[i-1] in '([{;,=!&|+-*/%':
                if i + 1 < n and text[i+1] not in '/*':
                    in_regex = True
                    result.append(ch)
                    i += 1
                    continue
        result.append(ch)
        i += 1
    return ''.join(result)

def strip_css_comments(text, allow_single_line=False):
    result = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == '/' and i+1 < n and text[i+1] == '*':
            i += 2
            while i+1 < n and not (text[i] == '*' and text[i+1] == '/'):
                i += 1
            if i+1 < n:
                i += 2
            continue
        result.append(text[i])
        i += 1
    text = ''.join(result)
    if allow_single_line:
        text = re.sub(r'(?<!:)\/\/[^\n]*', '', text)
    return text

def strip_html_comments(text, lang='en'):
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    def clean_script(m):
        return f'<script>{strip_js_comments(m.group(1))}</script>'
    text = re.sub(r'<script>([\s\S]*?)</script>', clean_script, text, flags=re.IGNORECASE)
    def clean_style(m):
        return f'<style>{strip_css_comments(m.group(1), allow_single_line=True)}</style>'
    text = re.sub(r'<style>([\s\S]*?)</style>', clean_style, text, flags=re.IGNORECASE)
    return text

def strip_vue_comments(text, lang='en'):
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    def clean_script(m):
        return f'<script{m.group(1)}>{strip_js_comments(m.group(2))}</script>'
    text = re.sub(r'<script([^>]*)>([\s\S]*?)</script>', clean_script, text, flags=re.IGNORECASE)
    def clean_style(m):
        return f'<style{m.group(1)}>{strip_css_comments(m.group(2), allow_single_line=True)}</style>'
    text = re.sub(r'<style([^>]*)>([\s\S]*?)</style>', clean_style, text, flags=re.IGNORECASE)
    return text

def get_stripper(ext):
    ext = ext.lower()
    if ext in ('.js', '.ts', '.jsx', '.tsx'):
        return strip_js_comments
    if ext == '.vue':
        return strip_vue_comments
    if ext == '.css':
        return lambda t: strip_css_comments(t, allow_single_line=False)
    if ext in ('.scss', '.less'):
        return lambda t: strip_css_comments(t, allow_single_line=True)
    if ext in ('.html', '.htm'):
        return strip_html_comments
    return None

def count_lines(text):
    return text.count('\n')

# 交互输入
def interactive_input(prompt_key, default, lang, choices=None):
    prompt = t(prompt_key, lang)
    if default is not None:
        prompt += f" [{default}]"
    prompt += ": "
    while True:
        val = input(prompt).strip()
        if val == '' and default is not None:
            return default
        if choices is None:
            return val
        if val in choices:
            return val
        print(Colors.yellow(t('invalid', lang)))

# 文件过滤和清理
def should_exclude(filename, patterns):
    if not patterns:
        return False
    for pat in patterns:
        if fnmatch.fnmatch(filename, pat):
            return True
    return False

def process_file(path, dry_run, verbose, lang, backup, exclude_patterns):
    basename = os.path.basename(path)
    if should_exclude(basename, exclude_patterns):
        if verbose:
            print(f"  {Colors.dim('Excluded by pattern')}: {path}")
        return 'skip', 0, 0

    ext = os.path.splitext(path)[1].lower()
    stripper = get_stripper(ext)
    if stripper is None:
        return 'skip', 0, 0

    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            original = f.read()
    except Exception as e:
        if verbose:
            print(f"  {Colors.red(t('error', lang))} {path}: {e}")
        write_log(f"ERROR reading {path}: {e}", lang)
        return 'error', 0, 0

    original_lines = count_lines(original)
    original_bytes = len(original.encode('utf-8'))

    cleaned = stripper(original)
    if cleaned == original:
        return 'skip', 0, 0

    cleaned_lines = count_lines(cleaned)
    cleaned_bytes = len(cleaned.encode('utf-8'))
    lines_removed = original_lines - cleaned_lines
    bytes_saved = original_bytes - cleaned_bytes

    if dry_run:
        if verbose:
            print(f"  {Colors.cyan(t('dry_run', lang))} {path}")
            print(f"    {t('file_stats', lang).format(lines=lines_removed, bytes=bytes_saved)}")
        return 'modified', lines_removed, bytes_saved

    if backup:
        try:
            backup_path = path + '.bak'
            shutil.copy2(path, backup_path)
            if verbose:
                print(f"  {Colors.dim(t('backup_created', lang).format(backup=backup_path))}")
        except Exception as e:
            if verbose:
                print(f"  {Colors.red(t('error', lang))} backup {path}: {e}")
            write_log(f"ERROR backup {path}: {e}", lang)
            return 'error', 0, 0

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        if verbose:
            print(f"  {Colors.green(t('stripped', lang))}: {path}")
            print(f"    {t('file_stats', lang).format(lines=lines_removed, bytes=bytes_saved)}")
        write_log(f"STRIPPED {path} (removed {lines_removed} lines, saved {bytes_saved} bytes)", lang)
        return 'modified', lines_removed, bytes_saved
    except Exception as e:
        if verbose:
            print(f"  {Colors.red(t('error', lang))} {path}: {e}")
        write_log(f"ERROR writing {path}: {e}", lang)
        return 'error', 0, 0

# 主程序
def main():
    sys_lang = get_system_lang()
    config = load_config(sys_lang)

    lang_choice = interactive_input('ask_lang', config.get('lang', 'auto'), sys_lang, choices=['1', '2', 'auto'])
    lang = 'en' if lang_choice == '1' else 'zh' if lang_choice == '2' else sys_lang

    dir_input = interactive_input('ask_dir', config.get('dir', '.'), lang)
    root_path = Path(dir_input).resolve()
    if not root_path.is_dir():
        print(Colors.red(f"{t('error', lang)}: {root_path} is not a directory."))
        sys.exit(1)

    default_exts = config.get('exts', '.js,.ts,.jsx,.tsx,.vue,.css,.scss,.less,.html,.htm')
    exts_input = interactive_input('ask_exts', default_exts, lang)
    exts = set(ext.strip().lower() for ext in exts_input.split(',') if ext.strip())

    skip_extra = interactive_input('ask_skip_dirs', config.get('skip_dirs', ''), lang)
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.idea', '.vscode'}
    if skip_extra:
        skip_dirs.update(d.strip() for d in skip_extra.split(',') if d.strip())

    exclude_input = interactive_input('ask_exclude', config.get('exclude', ''), lang)
    exclude_patterns = [p.strip() for p in exclude_input.split(',') if p.strip()]

    backup_choice = interactive_input('ask_backup', config.get('backup', 'y'), lang, choices=['y', 'n'])
    backup = (backup_choice.lower() == 'y')

    dry_choice = interactive_input('ask_dry', config.get('dry', 'n'), lang, choices=['y', 'n'])
    dry_run = (dry_choice.lower() == 'y')

    verbose_choice = interactive_input('ask_verbose', config.get('verbose', 'n'), lang, choices=['y', 'n'])
    verbose = (verbose_choice.lower() == 'y')

    new_config = {
        'lang': lang_choice,
        'dir': str(root_path),
        'exts': exts_input,
        'skip_dirs': skip_extra,
        'exclude': exclude_input,
        'backup': backup_choice,
        'dry': dry_choice,
        'verbose': verbose_choice,
    }
    save_config(new_config, lang)

    write_log(t('log_header', lang), lang)
    write_log(t('log_timestamp', lang).format(ts=datetime.datetime.now().isoformat()), lang)
    write_log(f"Directory: {root_path}", lang)
    write_log(f"Extensions: {exts}", lang)
    write_log(f"Skip dirs: {skip_dirs}", lang)
    write_log(f"Exclude patterns: {exclude_patterns}", lang)
    write_log(f"Backup: {backup}, Dry-run: {dry_run}, Verbose: {verbose}", lang)

    print(f"\n{Colors.bold(t('processing', lang))}: {root_path}")
    print(f"Extensions: {', '.join(exts)}")
    print(f"Skip dirs: {', '.join(skip_dirs)}")
    if exclude_patterns:
        print(f"Exclude patterns: {', '.join(exclude_patterns)}")
    if dry_run:
        print(Colors.yellow("*** DRY RUN - No files will be modified ***"))
    if backup:
        print(Colors.dim("*** Backup will be created (.bak) ***"))

    stats = {'modified': 0, 'skipped': 0, 'errors': 0}
    total_lines_removed = 0
    total_bytes_saved = 0
    file_list = []

    for root, dirs, files in os.walk(root_path):
        for d in list(dirs):
            if d in skip_dirs:
                dirs.remove(d)
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in exts:
                file_list.append(os.path.join(root, fname))

    total = len(file_list)
    if total == 0:
        print(Colors.yellow(t('no_files', lang)))
        write_log("No matching files found.", lang)
        return

    for idx, file_path in enumerate(file_list, 1):
        if verbose:
            print(f"\n[{idx}/{total}] {os.path.relpath(file_path, root_path)}")
        else:
            if idx % 10 == 0 or idx == total:
                print(Colors.dim(t('progress', lang).format(current=idx, total=total)))

        result, lines, bytes_saved = process_file(file_path, dry_run, verbose, lang, backup, exclude_patterns)
        if result == 'modified':
            stats['modified'] += 1
            total_lines_removed += lines
            total_bytes_saved += bytes_saved
        elif result == 'skip':
            stats['skipped'] += 1
        else:
            stats['errors'] += 1

    print(f"\n{Colors.bold(t('done', lang).format(**stats))}")
    if total_lines_removed > 0 or total_bytes_saved > 0:
        print(Colors.cyan(t('done_stats', lang).format(lines=total_lines_removed, bytes=total_bytes_saved)))
    write_log(f"Done. Modified: {stats['modified']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}", lang)
    write_log(f"Total lines removed: {total_lines_removed}, Total bytes saved: {total_bytes_saved}", lang)

if __name__ == '__main__':
    main()