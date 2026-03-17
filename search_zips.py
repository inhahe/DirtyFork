"""Search for a pattern inside all zip files under a directory, recursively."""

import zipfile, os, sys, fnmatch

if len(sys.argv) < 3:
    print("Usage: python search_zips.py <directory> <pattern>")
    print("Example: python search_zips.py D:\\bbs tedit*")
    sys.exit(1)

search_dir = sys.argv[1]
pattern = sys.argv[2].lower()

zip_count = 0
match_count = 0

for root, dirs, files in os.walk(search_dir):
    for f in files:
        if f.lower().endswith('.zip'):
            zip_count += 1
            path = os.path.join(root, f)
            try:
                with zipfile.ZipFile(path, 'r') as z:
                    for name in z.namelist():
                        basename = os.path.basename(name).lower()
                        if fnmatch.fnmatch(basename, pattern):
                            print(f"{path}: {name}")
                            match_count += 1
            except Exception:
                pass

print(f"\nSearched {zip_count} zip files, found {match_count} matches.")
