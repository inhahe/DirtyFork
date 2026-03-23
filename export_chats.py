#!/usr/bin/env python3
"""Export DirtyFork Claude Code chat history as date-prefixed HTML files.

Usage:  python export_chats.py <project_dir> <output_dir>
"""

import json, os, sys, glob, subprocess


def main():
    if len(sys.argv) < 3:
        print("Usage: python export_chats.py <project_dir> <output_dir>", file=sys.stderr)
        sys.exit(1)

    project_dir = sys.argv[1]
    output_dir = sys.argv[2]

    chat_dir = os.path.join(
        os.environ.get('USERPROFILE', os.path.expanduser('~')),
        '.claude', 'projects', 'D--visual-studio-projects-DirtyFork'
    )

    if not os.path.isdir(chat_dir):
        print(f"Chat directory not found: {chat_dir}", file=sys.stderr)
        return

    # Collect all conversation JSONL files with their start dates
    chats = []
    for fpath in glob.glob(os.path.join(chat_dir, '*.jsonl')):
        fname = os.path.basename(fpath)
        if fname.startswith('agent-'):
            continue
        try:
            ts = ''
            with open(fpath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    # Try top-level timestamp first, then nested
                    ts = obj.get('timestamp', '') or ''
                    if not ts and obj.get('snapshot', {}).get('timestamp'):
                        ts = obj['snapshot']['timestamp']
                    if ts:
                        ts = ts[:10]
                        break
            if not ts:
                ts = 'unknown'
        except Exception:
            ts = 'unknown'
        chats.append((ts, fpath))

    chats.sort()

    cc2html = os.path.join(project_dir, 'cc2html.py')
    os.makedirs(output_dir, exist_ok=True)

    for i, (ts, fpath) in enumerate(chats):
        out_name = f"{ts}_session{i + 1}.html"
        out_path = os.path.join(output_dir, out_name)
        print(f"  Converting to {out_name}...")
        subprocess.run([sys.executable, cc2html, fpath, out_path])


if __name__ == '__main__':
    main()
