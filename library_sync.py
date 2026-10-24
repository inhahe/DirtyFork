"""
library_sync.py: fill and refresh the file library's catalogue from the
sources in file_library.sources (DirtyFork.yaml).

    python library_sync.py [CONFIG] [--data-dir DIR] [--all] [--dry-run] [-v] [SOURCE ...]

Without SOURCE names it runs every source not marked "scheduled: false"
(what the scheduled task runs, register-library-sync.ps1), each only when
due: as often as its last check's cost allows (next_check). --all runs
every source, due or not; SOURCE names run those. Each run first makes
the catalogue agree with the library's own folders
(library.reconcile_uploads). --dry-run says what would change and
changes nothing (but the schema of a catalogue an older DirtyFork made,
which changes no entry). Its log is library_sync.log in the data directory.

Source types (library.SOURCE_TYPES), and what each lists:

  websites  each folder in dir is a website, zipped whole (but HTTrack's
            cache, log, cookies and project files), described by its start
            page's title (through HTTrack's index pages to the site's own);
            containers: folders whose subfolders are the websites; skip:
            folders to leave out. Loose .htm(l) files are webpages.
            Tags web, website (webpages: web, webpage).
  webpages  every .htm(l) (and .mht etc.) in dir and its subfolders, zipped
            with its "<name>_files" folder, described by its title; a
            subfolder that is itself a site (an HTTrack mirror, or one with
            an index or default page) is zipped whole as a website instead.
  github    every public repository of an account (include_forks: false),
            described by its GitHub description, tagged github. Each is kept
            cloned in repos_dir; a change is fetched, and only the files git
            says changed are replaced in its zip.
  gallery   pictures (tag pic) and videos (tag video) in dir, also tagged
            with each folder they are in, a picture described by thumbsup2's
            AI caption (captions: its thumbsup.db). Listed where they are.
  videos    videos in dir, described by their yt-dlp title. Listed in place.
  samples   samples (tag sample) and instruments (tags instrument and the
            extension), by extension (sample_types, instrument_types); with
            hierarchy_tags, also tagged with their folders. Other files are
            left out. Listed in place.
  mods      tracker modules, one per zip ("name.xm.zip", tags mod and the
            format, described by the song title inside), or bundles of them
            (tags mod, collection, described by what they hold). In place.

Every source also takes tags (more tags for all its files) and scheduled.

How a source is synced (sync_source): its handler yields an Item for each
file it would list; an item whose fingerprint (what the file is made from:
size and time, or a tree of them, or a commit) is unchanged keeps its entry,
with only its tags and description brought up to date; a new or changed one
is built (zipped) if it is a zip, then catalogued. A description and tags a
sysop set are kept either way (library.set_details; the catalogue's writes
see to it). Entries the handler no longer yields are forgotten, but only
once the handler has finished: a source that fails partway (a drive not
mounted, the network down) forgets nothing. Then the zips no entry lists
are deleted. A zip is written under a temporary name and then put in place,
so a caller never downloads half of one.
"""

import argparse
import contextlib
import hashlib
import html
import json
import logging
import logging.handlers
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
import zlib
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field

import library
from definitions import null

DEFAULT_CONFIG = "DirtyFork.yaml"
BATCH = 1000            # items compared with the catalogue at a time
COMMIT_EVERY = 0.5      # seconds the sync holds the catalogue's write lock at most (but for one write)
PACE = 30               # (file_library.sync_pace) a scheduled run checks a source again only once
                        # this many times as long as its last check took has passed...
MAX_GAP = 24 * 3600     # ...or a day
EARLY = 300             # seconds before it is due that a source is checked (the next run is
                        # minutes away, and runs start late by more or less)
TEMP_SUFFIX = ".~sync.zip"
HTML_TYPES = (".htm", ".html", ".xhtml", ".shtml", ".mht", ".mhtml")
SITE_EXCLUDE = ("hts-cache", "hts-log.txt", "hts-in_progress.lock", "hts-nohup.out", "cookies.txt", "*.whtt")
INDEX_PAGES = ("index.html", "index.htm", "default.html", "default.htm")
PICTURE_TYPES = frozenset("jpg jpeg jpe jfif png gif webp bmp avif svg tif tiff heic psd".split())
VIDEO_TYPES = frozenset("mp4 webm mkv avi mov wmv flv m4v mpg mpeg 3gp ogv".split())
SAMPLE_TYPES = ("flac", "xi", "wav", "mp3", "ogg", "aif", "aiff", "au", "8svx", "iff", "its")
INSTRUMENT_TYPES = ("ins", "s3i", "sbi", "iti", "pat", "sf2", "sfz", "ibk", "op2")
MODULE_TYPES = frozenset(
  "mod xm it s3m ahx mptm mtm med sfx dbm 669 mo3 mdl ult dtm gdm stm okt mt2 amf far symmod c67 "
  "dmf hvl j2b psm imf ptm ams plm fmt digi stp dsm stx umx oct".split())
# What each fingerprint was made by: changing how a kind of zip is made
# changes its prefix, so every zip of that kind is made again.
PAGE_RECIPE, SITE_RECIPE, REPO_RECIPE = "page1", "site1", "git1"
# git and 7-Zip are console programs: started from pythonw (the scheduled
# task), each would open a console window of its own.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

log = logging.getLogger("library_sync")


class SourceError(Exception):
  """A source that can't be read this time; it is skipped, and nothing it
  lists is forgotten."""


@dataclass(slots=True)
class Item:
  """A file a source would list.

  key: what it is within the source (stable from run to run; for a file
  listed in place, its path). root, path: where it is in the catalogue
  (library.resolve). What says the file must be made (or looked at) again:
  for a zip, fingerprint, what it is made from; for a file listed in place,
  stamp, its (size, mtime in ns) as the catalogue records them.
  description: known now, or None to call describe() (costly: only for a
  new or changed file). build: for a zip, build(old_entry) makes it at
  root/path (old_entry, or None, is what was catalogued before, for an
  update in place)."""
  key: str
  root: str
  path: str
  tags: list
  fingerprint: str = None
  stamp: tuple = None
  description: str = None
  describe: object = None
  build: object = None


@dataclass
class Context:
  """What every handler needs: the library, the catalogue connection, the
  tools, and how the run goes."""
  lib: object
  con: object
  seven_zip: str = None
  git: str = None
  dry_run: bool = False
  verbose: bool = False
  # Writes a handler wants made once the source is synced: a handler runs
  # interleaved with slow work (fetching), so it doesn't write itself, which
  # would hold the catalogue's write lock meanwhile.
  after: list = field(default_factory=list)

  def zip_path(self, rel):
    return os.path.join(self.lib.zips_dir, *rel.split("/"))


@dataclass
class Stats:
  listed: int = 0
  new: int = 0
  changed: int = 0
  updated: int = 0   # tags or description only
  removed: int = 0
  failed: int = 0
  skipped: Counter = field(default_factory=Counter)  # extension -> count, of files left out
  incomplete: bool = False  # some of it couldn't be read: forget nothing this time
  work: float = 0.0  # seconds spent on what changed (_work): not what checking the source costs

  def summary(self):
    text = (f"{self.listed} listed, {self.new} new, {self.changed} changed, {self.updated} retagged or "
            f"redescribed, {self.removed} removed, {self.failed} failed")
    if self.skipped:
      text += "; left out: " + ", ".join(f"{n} {ext or '(no extension)'}" for ext, n in self.skipped.most_common(8))
    return text


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _ext(name):
  return os.path.splitext(name)[1][1:].lower()


@contextlib.contextmanager
def _work(stats):
  """Time spent in here is work a change asked for (fetching, zipping,
  describing and cataloguing what is new or changed): Stats.work, which
  pacing leaves out of what checking a source costs (next_check)."""
  began = time.monotonic()
  try:
    yield
  finally:
    stats.work += time.monotonic() - began


def _rel(path, base):
  return os.path.relpath(path, base).replace(os.sep, "/")


def _conf_list(value, default=()):
  if not value:
    return list(default)
  if isinstance(value, str):
    return [value]
  return [str(v) for v in value]


_HIDDEN = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0) | getattr(stat, "FILE_ATTRIBUTE_SYSTEM", 0)


def _hidden(entry):
  """A hidden or system file or folder (Windows: $RECYCLE.BIN, System Volume
  Information, Thumbs.db, desktop.ini): never listed or zipped."""
  if not _HIDDEN:
    return False
  try:
    return bool(entry.stat(follow_symlinks=False).st_file_attributes & _HIDDEN)
  except (OSError, AttributeError):
    return False


def _excluded(name, patterns):
  import fnmatch
  return any(fnmatch.fnmatch(name.lower(), p.lower()) for p in patterns)


def tree_fingerprint(top, exclude=()):
  """A hash of every file under *top* (path, size, time), *exclude* (name
  patterns, at any depth) left out: it changes when any file does."""
  h = hashlib.sha1()
  entries = []
  stack = [top]
  while stack:
    d = stack.pop()
    with os.scandir(d) as it:
      for e in it:
        if _hidden(e) or (exclude and _excluded(e.name, exclude)):
          continue
        if e.is_dir(follow_symlinks=False):
          stack.append(e.path)
        elif e.is_file(follow_symlinks=False):
          st = e.stat()
          entries.append((_rel(e.path, top), st.st_size, st.st_mtime_ns))
  for rel, size, mtime in sorted(entries):
    h.update(f"{rel}\0{size}\0{mtime}\n".encode("utf-8", "surrogatepass"))
  return h.hexdigest()


# ---------------------------------------------------------------------------
# Titles
# ---------------------------------------------------------------------------

_TITLE = re.compile(rb"<title[^>]*>(.*?)</title\s*>", re.I | re.S)
_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?\s*([A-Za-z0-9_:-]+)""", re.I)
_HREF = re.compile(rb"""<a\s[^>]*?href\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.I)


def _read_head(path, size=512 * 1024):
  with open(path, "rb") as f:
    data = f.read(size)
  if data.startswith((b"\xff\xfe", b"\xfe\xff")):
    data = data.decode("utf-16", errors="replace").encode("utf-8")
  return data


def _decode(raw, data):
  m = _CHARSET.search(data)
  for enc in ((m.group(1).decode("ascii", "replace"),) if m else ()) + ("utf-8",):
    try:
      return raw.decode(enc)
    except (LookupError, UnicodeDecodeError):
      pass
  return raw.decode("cp1252", errors="replace")


def html_title(path):
  """The <title> of a saved page, unescaped, on one line ("" if none)."""
  try:
    data = _read_head(path)
  except OSError:
    return ""
  m = _TITLE.search(data)
  if not m:
    return ""
  return " ".join(html.unescape(_decode(m.group(1), data)).split())


_REFRESH = re.compile(rb"""<meta[^>]+http-equiv\s*=\s*["']?refresh["']?[^>]*?content\s*=\s*["']?\s*\d*\s*;?\s*"""
                      rb"""url\s*=\s*['"]?([^"'>\s]+)""", re.I)


def _is_httrack(title):
  """A title of HTTrack's own (its lists of projects and mirrors, and the
  page it leaves for a redirect), not the mirrored site's."""
  return "httrack" in title.lower() or title.lower() == "page has moved"


def _refresh_target(path):
  """The page a <meta http-equiv="refresh"> on page *path* goes to, if it is on disk."""
  try:
    m = _REFRESH.search(_read_head(path, 64 * 1024))
  except OSError:
    return None
  if not m:
    return None
  href = urllib.parse.unquote(m.group(1).decode("utf-8", "replace").split("#", 1)[0])
  if "://" in href or href.startswith("/"):
    return None
  target = os.path.normpath(os.path.join(os.path.dirname(path), href))
  return target if os.path.isfile(target) else None


def _local_links(path):
  """The pages a page links to on disk, in order (relative links only)."""
  try:
    data = _read_head(path)
  except OSError:
    return []
  base = os.path.dirname(path)
  out = []
  for m in _HREF.finditer(data):
    href = (m.group(1) or m.group(2) or m.group(3) or b"").decode("utf-8", "replace")
    href = urllib.parse.unquote(html.unescape(href.split("#", 1)[0].split("?", 1)[0]))
    if not href or "://" in href or href.startswith(("/", "mailto:", "javascript:")):
      continue
    target = os.path.normpath(os.path.join(base, href))
    if os.path.isdir(target):
      target = next((os.path.join(target, n) for n in INDEX_PAGES if os.path.isfile(os.path.join(target, n))), "")
    if target and target.lower().endswith(HTML_TYPES) and os.path.isfile(target):
      out.append(target)
  return out


def _index_page(folder):
  try:
    names = {n.lower(): n for n in os.listdir(folder)}
  except OSError:
    return None
  for want in INDEX_PAGES:
    if want in names and os.path.isfile(os.path.join(folder, names[want])):
      return os.path.join(folder, names[want])
  return None


def _start_page(folder):
  """A website's start page: its index page; in a folder without one, its
  first page; in a folder without pages, the start page of the one folder
  it holds, or else the first index page of the folders it holds."""
  for _ in range(4):
    page = _index_page(folder)
    if page:
      return page
    try:
      entries = sorted(os.listdir(folder))
    except OSError:
      return None
    pages = [n for n in entries if n.lower().endswith(HTML_TYPES) and os.path.isfile(os.path.join(folder, n))]
    if pages:
      return os.path.join(folder, pages[0])
    dirs = [n for n in entries if os.path.isdir(os.path.join(folder, n)) and "_files" not in n]
    if len(dirs) != 1:
      return next((p for p in (_index_page(os.path.join(folder, d)) for d in dirs) if p), None)
    folder = os.path.join(folder, dirs[0])
  return None


def site_title(folder):
  """A website's description: the title of its start page, past HTTrack's
  own pages (lists of projects and mirrors, redirect stubs) to the mirrored
  site's, by their redirects and links. Without a title worth having, the
  names of the mirrored hosts' folders in it ("wiki.example.org"), or ""."""
  page, seen = _start_page(folder), set()
  for _ in range(8):
    if page is None:
      break
    seen.add(os.path.normcase(page))
    title = html_title(page)
    if title and not _is_httrack(title):
      return title
    candidates = [_refresh_target(page)] + _local_links(page)
    page = next((p for p in candidates if p and os.path.normcase(p) not in seen), None)
  try:
    hosts = [n for n in sorted(os.listdir(folder)) if "." in n and " " not in n and "_files" not in n
             and os.path.isdir(os.path.join(folder, n))]
  except OSError:
    hosts = []
  return ", ".join(hosts)


_YT_ID = re.compile(r"\s*\[[A-Za-z0-9_-]{11}\]$")
_FULLWIDTH = str.maketrans({"\uff1a": ":", "\uff1f": "?", "\u29f8": "/", "\uff5c": "|", "\uff02": '"',
                            "\uff0a": "*", "\uff1c": "<", "\uff1e": ">", "\u29f9": "\\"})


def video_title(name):
  """A yt-dlp download's title: its name less the extension and " [id]",
  with the characters yt-dlp swaps for ones Windows refuses put back."""
  stem = os.path.splitext(name)[0]
  return _YT_ID.sub("", stem).translate(_FULLWIDTH).strip()


# ---------------------------------------------------------------------------
# Module titles
# ---------------------------------------------------------------------------

def _clean_text(raw):
  text = raw.split(b"\0", 1)[0].decode("cp437", errors="replace")
  return " ".join("".join(c if c.isprintable() else " " for c in text).split())


def module_title(head, kind):
  """The song title in the first bytes of a module of type *kind*, or ""."""
  if kind in ("it", "mptm") and head[:4] == b"IMPM":
    return _clean_text(head[4:30])
  if kind == "xm" and head[:17] == b"Extended Module: ":
    return _clean_text(head[17:37])
  if kind == "s3m" and head[44:48] == b"SCRM":
    return _clean_text(head[:28])
  if kind == "mtm" and head[:3] == b"MTM":
    return _clean_text(head[4:24])
  if kind == "ult" and head[:12] == b"MAS_UTrack_V":
    return _clean_text(head[15:47])
  if kind == "669" and head[:2] in (b"if", b"JN"):
    return _clean_text(head[2:38])
  if kind == "mod" and len(head) >= 1084:
    return _clean_text(head[:20])
  return ""


def mod_description(path, kind):
  """A module zip's description: the song title inside, or ""."""
  try:
    with zipfile.ZipFile(path) as z:
      members = [i for i in z.infolist() if not i.is_dir()]
      member = next((i for i in members if _ext(i.filename) == kind), members[0] if len(members) == 1 else None)
      if member is None:
        return ""
      with z.open(member) as f:
        return module_title(f.read(1100), kind)
  except (OSError, zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError, EOFError, ValueError):
    return ""


def bundle_description(path, limit=2000):
  """A bundle of modules: how many, and their names (as many as fit)."""
  try:
    with zipfile.ZipFile(path) as z:
      names = [os.path.basename(i.filename) for i in z.infolist() if not i.is_dir()]
  except (OSError, zipfile.BadZipFile, RuntimeError, ValueError):
    return ""
  names = [n[:-4] if n.lower().endswith(".zip") else n for n in names]
  text = f"{len(names)} modules: " + ", ".join(names)
  return text if len(text) <= limit else text[:limit - 1] + "~"


# ---------------------------------------------------------------------------
# Zips (7-Zip)
# ---------------------------------------------------------------------------

def find_seven_zip(configured=None):
  for candidate in ([configured] if configured else []) + [shutil.which("7z"), shutil.which("7za"),
                                                         r"C:\Program Files\7-Zip\7z.exe",
                                                         r"C:\Program Files (x86)\7-Zip\7z.exe"]:
    if candidate and os.path.isfile(candidate):
      return candidate
  return None


def run_7z(ctx, args, cwd, names):
  """7-Zip with *args*, the files *names* (relative to *cwd*) given in a
  list file (so no name is taken for a switch), UTF-8 names in the zip.
  Exit code 1 (a warning: a file that could not be read) is logged."""
  fd, listing = tempfile.mkstemp(prefix="library-sync-", suffix=".txt")
  try:
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
      for n in names:
        f.write(n + "\n")
    cmd = [ctx.seven_zip] + args[:1] + ["-tzip", "-mcu=on", "-scsUTF-8", "-ssw", "-y", "-bso0", "-bsp0"] \
      + args[1:] + ["@" + listing]
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=_NO_WINDOW)
  finally:
    with contextlib.suppress(OSError):
      os.remove(listing)
  if p.returncode == 1:
    log.warning("7-Zip warned in %s: %s", cwd, (p.stderr or p.stdout).strip()[:500])
  elif p.returncode != 0:
    raise RuntimeError(f"7-Zip failed ({p.returncode}) in {cwd}: {(p.stderr or p.stdout).strip()[:500]}")


def _temp_zip(final):
  return final[:-4] + TEMP_SUFFIX if final.lower().endswith(".zip") else final + TEMP_SUFFIX


def put_in_place(temp, final):
  """Replace *final* by *temp*. A zip being downloaded can't be replaced
  (Windows): then the temporary one is dropped and the error raised, so the
  item is tried again next time."""
  try:
    os.replace(temp, final)
  except OSError:
    with contextlib.suppress(OSError):
      os.remove(temp)
    raise


def zip_mirror(ctx, final, cwd, folder, exclude=()):
  """Make the zip at *final* hold *folder* (relative to *cwd*) as it is
  now: updated in place if it exists (files that didn't change are copied
  across, not compressed again), else made."""
  if not os.path.isfile(final):
    _zip_to(ctx, final, cwd, [folder], exclude, ["a", "-mx=5"])
    return
  _zip_to(ctx, final, cwd, [folder], exclude, ["u", "-mx=5", "-up0q0r2x2y2z1w2"], copy=True)


def _zip_to(ctx, final, cwd, names, exclude, args, copy=False):
  os.makedirs(os.path.dirname(final), exist_ok=True)
  temp = _temp_zip(final)
  with contextlib.suppress(FileNotFoundError):
    os.remove(temp)
  try:
    if copy:
      shutil.copyfile(final, temp)
    run_7z(ctx, args[:1] + [temp] + args[1:] + [f"-xr!{p}" for p in exclude], cwd, names)
  except BaseException:
    with contextlib.suppress(OSError):
      os.remove(temp)
    raise
  put_in_place(temp, final)


def zip_files(ctx, final, cwd, names):
  """A new zip at *final* of *names* (relative to *cwd*)."""
  _zip_to(ctx, final, cwd, names, (), ["a", "-mx=5"])


def zip_update(ctx, final, cwd, changed, deleted):
  """Replace *changed* (added or modified; relative to *cwd*) in the zip at
  *final* and remove *deleted* (paths in the zip) from it."""
  os.makedirs(os.path.dirname(final), exist_ok=True)
  temp = _temp_zip(final)
  with contextlib.suppress(FileNotFoundError):
    os.remove(temp)
  try:
    shutil.copyfile(final, temp)
    if deleted:
      run_7z(ctx, ["d", temp], cwd, deleted)
    if changed:
      run_7z(ctx, ["u", temp, "-mx=5"], cwd, changed)
  except BaseException:
    with contextlib.suppress(OSError):
      os.remove(temp)
    raise
  put_in_place(temp, final)


# ---------------------------------------------------------------------------
# Websites and webpages
# ---------------------------------------------------------------------------

def _page_companion(folder, name):
  """The "<stem>_files" folder a browser saved with page *name*, or None."""
  stem = os.path.splitext(name)[0]
  d = os.path.join(folder, stem + "_files")
  return d if os.path.isdir(d) else None


def _page_item(ctx, conf, folder, name, zip_rel, base_tags):
  """An Item for the page *name* in *folder*, zipped to zips/<zip_rel>."""
  page = os.path.join(folder, name)
  companion = _page_companion(folder, name)
  st = os.stat(page)
  h = hashlib.sha1(f"{name}\0{st.st_size}\0{st.st_mtime_ns}".encode("utf-8", "surrogatepass"))
  if companion:
    h.update(tree_fingerprint(companion).encode())
  names = [name] + ([os.path.basename(companion)] if companion else [])

  def build(old):
    zip_files(ctx, ctx.zip_path(zip_rel), folder, names)
  return Item(key=_rel(page, library.source_dir(conf)), root="zips", path=zip_rel,
              tags=base_tags + ["web", "webpage"] + _conf_list(conf.tags),
              fingerprint=f"{PAGE_RECIPE}:{h.hexdigest()}", describe=lambda: html_title(page), build=build)


def _site_item(ctx, conf, folder, zip_rel, base_tags):
  """An Item for the website in *folder*, zipped whole to zips/<zip_rel>."""
  parent, base = os.path.split(os.path.normpath(folder))

  def build(old):
    zip_mirror(ctx, ctx.zip_path(zip_rel), parent, base, SITE_EXCLUDE)
  return Item(key=_rel(folder, library.source_dir(conf)), root="zips", path=zip_rel,
              tags=base_tags + ["web", "website"] + _conf_list(conf.tags),
              fingerprint=f"{SITE_RECIPE}:{tree_fingerprint(folder, SITE_EXCLUDE)}",
              describe=lambda: site_title(folder), build=build)


def _zip_names(things):
  """{key: zip name} for things zipped into one folder, from {key: (stem,
  fallback)}: the stem, or the fallback where stems clash (two pages
  "x.htm" and "x.html" are "x.htm.zip" and "x.html.zip"; a page and a site
  both "x": "x.zip" and "x (website).zip")."""
  counts = Counter(stem.lower() for stem, _ in things.values())
  return {key: (stem if counts[stem.lower()] == 1 else fallback) + ".zip"
          for key, (stem, fallback) in things.items()}


def _unique(used, zip_rel):
  """*zip_rel*, or "... (2).zip" and so on if the source has a zip of that
  name already (any case: a folder named "x.htm" beside a page "x.htm", or
  a site "A - B" beside container A's site B). *used* is the source's."""
  candidate, n = zip_rel, 2
  while candidate.lower() in used:
    candidate = f"{zip_rel[:-4]} ({n}).zip"
    n += 1
  used.add(candidate.lower())
  return candidate


def _entries(folder, stats):
  """The (pages, folders) in *folder*, by name, hidden and system ones
  left out; ([], []) if it can't be read (logged; the source incomplete)."""
  try:
    with os.scandir(folder) as it:
      entries = sorted((e for e in it if not _hidden(e)), key=lambda e: e.name)
    pages = [e.name for e in entries if e.name.lower().endswith(HTML_TYPES) and e.is_file()]
    dirs = [e.name for e in entries if e.is_dir()]
  except OSError as exc:
    log.warning("Can't read %s, left out this time: %s", folder, exc)
    stats.incomplete = True
    return [], []
  return pages, dirs


def _made(make, stats, what):
  """make(): an Item; None (logged; the source incomplete) if what it reads
  can't be read."""
  try:
    return make()
  except OSError as exc:
    log.warning("Can't read %s, left out this time: %s", what, exc)
    stats.incomplete = True
    return None


def _has_files(folder):
  try:
    for _root, _dirs, files in os.walk(folder):
      if files:
        return True
  except OSError:
    pass
  return False


def _is_httrack_page(path):
  return os.path.basename(path).lower() in INDEX_PAGES and _is_httrack(html_title(path))


def handle_websites(ctx, source, conf, stats):
  top = library.source_dir(conf)
  if not os.path.isdir(top):
    raise SourceError(f"{top} is not a folder")
  containers = {c.lower() for c in _conf_list(conf.containers)}
  skip = {s.lower() for s in _conf_list(conf.skip)}
  used = set()

  def visit(folder, prefix):
    pages, dirs = _entries(folder, stats)
    pages = [n for n in pages if not _is_httrack_page(os.path.join(folder, n))]  # (HTTrack's list of projects)
    dirs = [n for n in dirs if "_files" not in n and n.lower() not in skip
            and _rel(os.path.join(folder, n), top).lower() not in skip]
    names = _zip_names({n: (" - ".join(prefix + [os.path.splitext(n)[0]]), " - ".join(prefix + [n]))
                        for n in pages}
                       | {n + "/": (" - ".join(prefix + [n]), " - ".join(prefix + [n]) + " (website)")
                          for n in dirs})
    for n in pages:
      item = _made(lambda: _page_item(ctx, conf, folder, n, _unique(used, f"{source}/{names[n]}"), []),
                   stats, os.path.join(folder, n))
      if item:
        yield item
    for n in dirs:
      rel = _rel(os.path.join(folder, n), top)
      if rel.lower() in containers or (folder == top and n.lower() in containers):
        yield from visit(os.path.join(folder, n), prefix + [n])
      elif _has_files(os.path.join(folder, n)):
        item = _made(lambda: _site_item(ctx, conf, os.path.join(folder, n),
                                        _unique(used, f"{source}/{names[n + '/']}"), []),
                     stats, os.path.join(folder, n))
        if item:
          yield item
  yield from visit(top, [])


def _is_site(folder):
  """A folder in a folder of saved pages that is a website of its own, to
  be zipped whole: an HTTrack mirror; one with an index or default page; or
  one with pages only in its subfolders, none saved by a browser (with a
  "_files" folder), whose pages then use the files in the folders beside
  theirs. A folder of pages saved one by one is not a site: its pages are
  zipped one by one."""
  try:
    names = os.listdir(folder)
  except OSError:
    return False
  lower = {n.lower() for n in names}
  if "hts-cache" in lower or any(n.endswith(".whtt") for n in lower) or any(p in lower for p in INDEX_PAGES):
    return True
  if any(n.endswith(HTML_TYPES) for n in lower):
    return False
  has_pages = False
  for _root, dirs, files in os.walk(folder):
    if any("_files" in d for d in dirs):
      return False
    has_pages = has_pages or any(f.lower().endswith(HTML_TYPES) for f in files)
  return has_pages


def handle_webpages(ctx, source, conf, stats):
  top = library.source_dir(conf)
  if not os.path.isdir(top):
    raise SourceError(f"{top} is not a folder")
  hierarchy = bool(conf.hierarchy_tags)
  used = set()

  def visit(folder):
    rel_folder = _rel(folder, top)
    out_dir = source if rel_folder == "." else f"{source}/{rel_folder}"
    tags = [] if not hierarchy or rel_folder == "." else rel_folder.split("/")
    pages, dirs = _entries(folder, stats)
    dirs = [n for n in dirs if "_files" not in n]
    sites = [n for n in dirs if _is_site(os.path.join(folder, n))]
    names = _zip_names({n: (os.path.splitext(n)[0], n) for n in pages}
                       | {n + "/": (n, n + " (website)") for n in sites})
    for n in pages:
      item = _made(lambda: _page_item(ctx, conf, folder, n, _unique(used, f"{out_dir}/{names[n]}"), tags),
                   stats, os.path.join(folder, n))
      if item:
        yield item
    for n in dirs:
      if n in sites:
        item = _made(lambda: _site_item(ctx, conf, os.path.join(folder, n),
                                        _unique(used, f"{out_dir}/{names[n + '/']}"), tags),
                     stats, os.path.join(folder, n))
        if item:
          yield item
      else:
        yield from visit(os.path.join(folder, n))
  yield from visit(top)





# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

def github_repos(user):
  """The account's public repositories, from GitHub's API (GITHUB_TOKEN, if
  set, raises the rate limit)."""
  repos, page = [], 1
  headers = {"Accept": "application/vnd.github+json", "User-Agent": "DirtyFork-library-sync"}
  if os.environ.get("GITHUB_TOKEN"):
    headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
  while True:
    url = (f"https://api.github.com/users/{urllib.parse.quote(user)}/repos"
           f"?per_page=100&type=owner&sort=full_name&page={page}")
    try:
      with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
        data = json.load(r)
    except (OSError, ValueError) as exc:
      raise SourceError(f"GitHub's list of {user}'s repositories: {exc}") from exc
    if not isinstance(data, list):
      raise SourceError(f"GitHub's list of {user}'s repositories: unexpected answer {str(data)[:200]}")
    repos += data
    if len(data) < 100:
      return repos
    page += 1


def git(ctx, *args, cwd=None):
  """Run git (text output, UTF-8 paths); RuntimeError if it fails."""
  p = subprocess.run([ctx.git, "-c", "core.quotepath=off", "-c", "core.autocrlf=false", *args], cwd=cwd,
                     capture_output=True, text=True, encoding="utf-8", errors="surrogateescape",
                     creationflags=_NO_WINDOW)
  if p.returncode != 0:
    raise RuntimeError(f"git {' '.join(args[:2])} failed: {(p.stderr or p.stdout).strip()[:500]}")
  return p.stdout


def _git_z(output):
  return [p for p in output.split("\0") if p]


def remove_tree(path):
  """Delete a folder, a git clone's read-only files too (Windows won't
  delete a read-only file). Logs what it couldn't delete."""
  def again(func, p, exc):
    try:
      os.chmod(p, stat.S_IWRITE)
      func(p)
    except OSError as exc2:
      log.warning("Could not delete %s: %s", p, exc2)
  if not os.path.lexists(path):
    return
  if sys.version_info >= (3, 12):
    shutil.rmtree(path, onexc=again)
  else:  # (onexc is new in 3.12)
    shutil.rmtree(path, onerror=lambda func, p, info: again(func, p, info[1]))


def handle_github(ctx, source, conf, stats):
  user = str(conf.user or "")
  if not user:
    raise SourceError("a github source needs a user")
  if ctx.git is None:
    raise SourceError("git is not installed")
  include_forks = bool(conf.include_forks)
  clones = os.path.join(ctx.lib.repos_dir, source)
  repos = [r for r in github_repos(user) if not r.get("private") and (include_forks or not r.get("fork"))
           and r.get("default_branch")]
  existing = library.source_entries(ctx.con, source)
  for repo in repos:
    name, branch = repo["name"], repo["default_branch"]
    clone = os.path.join(clones, name)
    zip_rel = f"{source}/{name}.zip"
    pushed = f"{repo.get('pushed_at')}|{branch}"
    old = existing.get(name)
    tags = ["github"] + _conf_list(conf.tags)
    description = repo.get("description") or ""
    if library.get_state(ctx.con, source, "empty:" + name) == pushed:
      continue  # (empty when last looked at, and not pushed to since)
    current = old is not None and (old.fingerprint or "").startswith(REPO_RECIPE + ":")
    if (current and library.get_state(ctx.con, source, "pushed:" + name) == pushed
            and os.path.isdir(clone) and os.path.isfile(ctx.zip_path(zip_rel))):
      yield Item(key=name, root="zips", path=zip_rel, tags=tags, fingerprint=old.fingerprint,
                 description=description)
      continue
    if ctx.dry_run:
      yield Item(key=name, root="zips", path=zip_rel, tags=tags, fingerprint="(would fetch)",
                 description=description)
      continue
    try:
      with _work(stats):  # (fetching what was pushed)
        if os.path.isdir(os.path.join(clone, ".git")):
          git(ctx, "fetch", "--depth", "1", "--no-tags", "origin", branch, cwd=clone)
          head = git(ctx, "rev-parse", "FETCH_HEAD", cwd=clone).strip()
        else:
          remove_tree(clone)
          os.makedirs(clones, exist_ok=True)
          git(ctx, "clone", "--depth", "1", "--single-branch", "--branch", branch, "--no-tags",
              repo["clone_url"], name, cwd=clones)
          git(ctx, "config", "core.autocrlf", "false", cwd=clone)
          head = git(ctx, "rev-parse", "HEAD", cwd=clone).strip()
    except (RuntimeError, OSError) as exc:
      if "not found in upstream" in str(exc) and old is None:
        # An empty repository (no commit, so no branch): nothing to list
        # until it is pushed to.
        log.info("%s: %s is empty; left out until it is pushed to", source, name)
        remove_tree(clone)
        ctx.after.append(lambda name=name, pushed=pushed: library.set_state(ctx.con, source, "empty:" + name,
                                                                            pushed))
        continue
      log.error("%s: %s: %s", source, name, exc)
      if old is not None:  # (keep what is listed)
        yield Item(key=name, root="zips", path=zip_rel, tags=tags, fingerprint=old.fingerprint,
                   description=description)
      continue

    # (built after the handler has moved on to other repositories: everything
    # it uses is bound now)
    def build(old_entry, name=name, clone=clone, head=head, zip_rel=zip_rel, pushed=pushed):
      final = ctx.zip_path(zip_rel)
      # (a zip made by another recipe is made again, whole)
      prefix, _, before = (old_entry.fingerprint or "").partition(":") if old_entry else ("", "", "")
      before = before if prefix == REPO_RECIPE else None
      changed = deleted = None
      if before and os.path.isfile(final):
        try:
          diff = _git_z(git(ctx, "diff", "--name-status", "--no-renames", "-z", before, head, cwd=clone))
          changed, deleted = [], []
          for status, path in zip(diff[::2], diff[1::2]):
            (deleted if status == "D" else changed).append(f"{name}/{path}")
        except RuntimeError as exc:  # (the old commit isn't in the clone: make the zip anew)
          log.info("%s: %s: no diff from %s (%s); zipping it whole", source, name, before[:12], exc)
          changed = None
      git(ctx, "reset", "--hard", "--quiet", head, cwd=clone)
      if changed is None:
        files = [f"{name}/{p}" for p in _git_z(git(ctx, "ls-files", "-z", cwd=clone))]
        zip_files(ctx, final, clones, files)
        log.info("%s: %s zipped whole at %s (%d files)", source, name, head[:12], len(files))
      else:
        zip_update(ctx, final, clones, changed, deleted)
        log.info("%s: %s updated to %s: %d changed, %d deleted", source, name, head[:12],
                 len(changed), len(deleted))
      library.set_state(ctx.con, source, "pushed:" + name, pushed)
    yield Item(key=name, root="zips", path=zip_rel, tags=tags, fingerprint=f"{REPO_RECIPE}:{head}",
               description=description, build=build)
  # clones of repositories no longer listed
  keep = {r["name"].lower() for r in repos}
  if os.path.isdir(clones) and not ctx.dry_run:
    for n in os.listdir(clones):
      if n.lower() not in keep:
        log.info("%s: removing the clone of %s (no longer listed)", source, n)
        remove_tree(os.path.join(clones, n))
        ctx.after.append(lambda n=n: library.set_state(ctx.con, source, "pushed:" + n, None))


# ---------------------------------------------------------------------------
# Files listed in place
# ---------------------------------------------------------------------------

def _stamp(entry):
  st = entry.stat()
  return st.st_size, st.st_mtime_ns


def walk_files(top, stats):
  """(relative path with /, DirEntry) for every file under *top* but hidden
  or system ones (_hidden). A folder's entries are streamed, not gathered
  (one of the sample folders holds more than a million and a half). A
  subfolder that can't be read is logged and left out, and the source
  marked incomplete (stats.incomplete: nothing it lists is forgotten)."""
  stack = [""]
  while stack:
    rel = stack.pop()
    folder = os.path.join(top, *rel.split("/")) if rel else top
    try:
      with os.scandir(folder) as it:
        for e in it:
          if _hidden(e):
            continue
          if e.is_dir(follow_symlinks=False):
            stack.append(f"{rel}/{e.name}" if rel else e.name)
          elif e.is_file(follow_symlinks=False):
            yield (f"{rel}/{e.name}" if rel else e.name), e
    except OSError as exc:
      if not rel:
        raise SourceError(f"{top}: {exc}") from exc
      log.warning("Can't read %s, left out this time: %s", folder, exc)
      stats.incomplete = True


def _linked_top(conf):
  top = library.source_dir(conf)
  if not os.path.isdir(top):
    raise SourceError(f"{top} is not a folder (a drive not mounted?)")
  return top


def thumbsup_key(name, size, mtime_ns):
  """thumbsup2's key for an image's AI caption: sha1 of its name, size and
  mtime in ms as JavaScript prints it (src/components/ai/ai.js, hashFile).
  Node's mtimeMs is sec * 1e3 + nsec / 1e6 in doubles; JavaScript and
  Python both print a double as its shortest round trip, but JavaScript
  leaves off a ".0"."""
  ms = (mtime_ns // 10 ** 9) * 1e3 + (mtime_ns % 10 ** 9) / 1e6
  text = repr(ms)
  if text.endswith(".0"):
    text = text[:-2]
  h = hashlib.sha1(name.encode("utf-8", "surrogatepass"))
  h.update(str(size).encode())
  h.update(text.encode())
  return h.hexdigest()


def load_captions(path):
  """thumbsup2's AI captions, by its hash; None if its database can't be
  read (so the pictures keep the captions they have)."""
  if not path:
    return {}
  try:
    con = sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(path).replace(os.sep, '/'))}?mode=ro",
                          uri=True, timeout=30)
    try:
      return {h: c for h, c in con.execute("SELECT hash, caption FROM ai_descriptions") if c}
    finally:
      con.close()
  except sqlite3.Error as exc:
    log.warning("Can't read the captions in %s, keeping those catalogued: %s", path, exc)
    return None


def handle_gallery(ctx, source, conf, stats):
  top = _linked_top(conf)
  captions = load_captions(str(conf.captions) if conf.captions else None)
  extra = _conf_list(conf.tags)
  for rel, e in walk_files(top, stats):
    kind = _ext(e.name)
    if kind in PICTURE_TYPES:
      tag = "pic"
    elif kind in VIDEO_TYPES:
      tag = "video"
    else:
      stats.skipped[kind] += 1
      continue
    st = e.stat()
    if tag != "pic":
      description = ""
    elif captions is None:
      description = None  # (unknown: kept as catalogued, or none for a new picture)
    else:
      description = captions.get(thumbsup_key(e.name, st.st_size, st.st_mtime_ns), "")
    yield Item(key=rel, root=source, path=rel, tags=[tag] + rel.split("/")[:-1] + extra,
               stamp=(st.st_size, st.st_mtime_ns), description=description)


def handle_videos(ctx, source, conf, stats):
  top = _linked_top(conf)
  extra = _conf_list(conf.tags)
  hierarchy = bool(conf.hierarchy_tags)
  for rel, e in walk_files(top, stats):
    if _ext(e.name) not in VIDEO_TYPES:
      stats.skipped[_ext(e.name)] += 1
      continue
    folders = rel.split("/")[:-1] if hierarchy else []
    yield Item(key=rel, root=source, path=rel, tags=["video"] + folders + extra,
               stamp=_stamp(e), description=video_title(e.name))


def handle_samples(ctx, source, conf, stats):
  top = _linked_top(conf)
  samples = {t.lower().lstrip(".") for t in _conf_list(conf.sample_types, SAMPLE_TYPES)}
  instruments = {t.lower().lstrip(".") for t in _conf_list(conf.instrument_types, INSTRUMENT_TYPES)}
  extra = _conf_list(conf.tags)
  hierarchy = bool(conf.hierarchy_tags)
  for rel, e in walk_files(top, stats):
    kind = _ext(e.name)
    if kind in samples:
      tags = ["sample"]
    elif kind in instruments:
      tags = ["instrument", kind]
    else:
      stats.skipped[kind] += 1
      continue
    if hierarchy:
      tags += rel.split("/")[:-1]
    yield Item(key=rel, root=source, path=rel, tags=tags + extra,
               stamp=_stamp(e), description="")


_COLLECTION_SUFFIX = re.compile(r" \([^()]*\)$")


def handle_mods(ctx, source, conf, stats):
  top = _linked_top(conf)
  extra = _conf_list(conf.tags)
  for rel, e in walk_files(top, stats):
    if _ext(e.name) != "zip":
      stats.skipped[_ext(e.name)] += 1
      continue
    base = _COLLECTION_SUFFIX.sub("", e.name[:-4])  # ("foo.xm (modarchive_2019_additions).zip")
    kind = _ext(base)
    path = e.path
    if kind in MODULE_TYPES:
      tags, describe = ["mod", kind], (lambda path=path, kind=kind: mod_description(path, kind))
    else:
      tags, describe = ["mod", "collection"], (lambda path=path: bundle_description(path))
    yield Item(key=rel, root=source, path=rel, tags=tags + extra,
               stamp=_stamp(e), describe=describe)


# handler(ctx, source, conf, stats) yields the Items a source would list
HANDLERS = {"websites": handle_websites, "webpages": handle_webpages, "github": handle_github,
            "gallery": handle_gallery, "videos": handle_videos, "samples": handle_samples,
            "mods": handle_mods}


# ---------------------------------------------------------------------------
# Syncing a source
# ---------------------------------------------------------------------------

def _batches(items, n):
  batch = []
  for item in items:
    batch.append(item)
    if len(batch) >= n:
      yield batch
      batch = []
  if batch:
    yield batch


def _existing(con, source, linked, keys):
  """{key: Entry} for *keys* of *source*: for a source listing files in
  place (*linked*), by their paths in the source's root (its key is its
  path, not stored again); for a source of zips, by the keys stored."""
  out = {}
  where = "root = ? AND path" if linked else "source = ? AND source_key IS NOT NULL AND source_key"
  for start in range(0, len(keys), 500):
    chunk = keys[start:start + 500]
    marks = ", ".join("?" * len(chunk))
    ids = [r[0] for r in con.execute(f"SELECT id FROM files WHERE {where} IN ({marks})", [source] + chunk)]
    for e in library.fetch(con, ids):
      out[e.source_key] = e
  return out


def _delete_zip(ctx, rel):
  """Delete one of the zips library_sync made (never anything outside zips_dir)."""
  path = os.path.realpath(ctx.zip_path(rel))
  if not library._within(os.path.realpath(ctx.lib.zips_dir), path):
    log.error("Not deleting %s: outside %s", path, ctx.lib.zips_dir)
    return
  try:
    os.remove(path)
  except FileNotFoundError:
    pass
  except OSError as exc:
    log.warning("Could not delete %s (%s); it will go next time", path, exc)


def open_catalogue(lib, dry_run=False):
  """The sync's connection to the catalogue. Its write transactions take the
  write lock as they begin (waiting for the BBS's, if need be): one begun
  deferred reads first, and a BBS write in between would make its first
  write fail at once (a stale snapshot, which no busy timeout retries). A dry
  run writes only its temporary table, and takes no lock."""
  con = library.connect(lib)
  con.isolation_level = None if dry_run else "IMMEDIATE"
  return con


def sync_source(ctx, source, conf):
  """Bring one source's entries up to date (see the module's docstring).
  Returns its Stats; SourceError when the source can't be read."""
  kind = str(conf.type)
  stats = Stats()
  ctx.after = []
  handler = HANDLERS[kind]
  items = handler(ctx, source, conf, stats)
  con, uploader = ctx.con, ctx.lib.sysop_handle
  linked = kind in library.LINKED_TYPES
  con.execute("CREATE TEMP TABLE IF NOT EXISTS seen (key TEXT PRIMARY KEY)")
  con.execute("DELETE FROM temp.seen")
  if not ctx.dry_run:
    # A source changed between a linked type and a zipped one has entries
    # of the other shape, which nothing below would find: forgotten first.
    before = library.get_state(con, source, "type")
    if before and (before in library.LINKED_TYPES) != linked:
      log.info("%s: was a %s source, now %s: forgot its %d file(s)", source, before, kind,
               _forget_source(ctx, source, before))
    # (what forget_unconfigured goes by, should the source leave the config)
    library.set_state(con, source, "type", kind)
  if con.in_transaction:
    con.commit()  # (an IMMEDIATE transaction holds the write lock: not while the handler starts its slow work)
  last_commit = time.monotonic()

  def settle(now=False):
    """Commit what is written so far: before anything slow (a zip, reading a
    file), and every COMMIT_EVERY seconds. The BBS writes to the catalogue
    too (uploads), and waits at most 30 s for the write lock."""
    nonlocal last_commit
    if not ctx.dry_run and con.in_transaction and (now or time.monotonic() - last_commit > COMMIT_EVERY):
      con.commit()
      last_commit = time.monotonic()

  for batch in _batches(items, BATCH):
    stats.listed += len(batch)
    con.executemany("INSERT OR IGNORE INTO temp.seen (key) VALUES (?)", [(i.key,) for i in batch])
    old_entries = _existing(con, source, linked, [i.key for i in batch])
    for item in batch:
      settle()
      # (how _existing finds it again: by its root and path, or by its stored key)
      if linked:
        assert (item.root, item.path, item.build) == (source, item.key, None), item
      else:
        assert item.root == library.ZIPS and item.key != item.path and item.stamp is None, item
      old = old_entries.get(item.key)
      if (old is not None and (old.root, old.path) == (item.root, item.path)
              and (old.fingerprint == item.fingerprint if item.stamp is None
                   else (old.size, old.mtime) == item.stamp)):
        if old.edited == library.EDITED:
          continue  # (a sysop's details: kept)
        description = item.description
        if description is None:
          # (only describe() can say, at a cost: asked only when the details
          # were given back. Without it, as for a picture whose captions can't
          # be read, the description is kept: the caption comes once it can be.)
          given_back = old.edited == library.RESET and item.describe
          description = item.describe() if given_back else old.description
        tags = library.clean_tags(item.tags)
        if old.edited == library.RESET or tags != list(old.tags) or description != old.description:
          stats.updated += 1
          if ctx.verbose:
            log.info("%s: %s: tags or description changed", source, item.key)
          if not ctx.dry_run:
            # (old is as it was when the batch began; set_details doesn't
            # write over a sysop's details set since)
            library.set_details(con, old.id, description,
                                tags if old.edited == library.RESET or tags != list(old.tags) else None)
        continue
      if old is None:
        stats.new += 1
      else:
        stats.changed += 1
      if ctx.verbose or (ctx.dry_run and stats.new + stats.changed <= 20):
        log.info("%s: %s %s", source, "new" if old is None else "changed", item.key)
      if ctx.dry_run:
        continue
      try:
        with _work(stats):
          if item.build is not None:
            settle(now=True)  # (making a zip can take minutes)
            item.build(old)
          if item.stamp is not None:
            size, mtime = item.stamp
          else:
            size, mtime = library.file_stamp(os.path.join(ctx.lib.roots[item.root], *item.path.split("/")))
          description = item.description if item.description is not None else (
            item.describe() if item.describe else "")
          if old is not None and (old.root, old.path) != (item.root, item.path):
            # (the same entry, so a sysop's details stay; its old zip goes in _sweep_zips)
            library.move(con, old.id, item.root, item.path)
          # (put keeps a sysop's details, even ones set since old was read)
          library.put(con, root=item.root, path=item.path, size=size, mtime=mtime, description=description,
                      uploader=uploader, tags=item.tags, source=source, source_key=item.key,
                      fingerprint=item.fingerprint)
      except sqlite3.Error:
        raise  # (the catalogue itself: the source fails, and is rolled back)
      except Exception as exc:
        # One file that can't be made or read: the rest go on, and it is
        # tried again next time. (A trace for anything but the expected.)
        stats.failed += 1
        log.error("%s: %s: %s", source, item.key, exc,
                  exc_info=not isinstance(exc, (OSError, RuntimeError, zipfile.BadZipFile)))
    if not ctx.dry_run:
      con.commit()
  # what the source no longer has
  if stats.incomplete:
    log.warning("%s: not all of it could be read: nothing it lists is forgotten this time", source)
    gone = []
  elif linked:
    gone = con.execute("SELECT id, path AS source_key FROM files WHERE root = ? AND path NOT IN "
                       "(SELECT key FROM temp.seen)", (source,)).fetchall()
  else:
    gone = con.execute("SELECT id, source_key FROM files WHERE source = ? AND source_key IS NOT NULL "
                       "AND source_key NOT IN (SELECT key FROM temp.seen)", (source,)).fetchall()
  for row in gone:
    stats.removed += 1
    if ctx.verbose or (ctx.dry_run and stats.removed <= 20):
      log.info("%s: removed %s", source, row["source_key"])
    if ctx.dry_run:
      continue
    settle()
    library.remove(con, row["id"])  # (its zip, if it has one, goes in _sweep_zips)
  if not ctx.dry_run:
    for write_state in ctx.after:
      write_state()
    con.commit()
    if not linked:
      _sweep_zips(ctx, source)
  return stats


def _same_file(a, b):
  try:
    return os.path.samefile(a, b)
  except OSError:
    return False


def _sweep_zips(ctx, source):
  """Delete the zips in the source's folder of zips that no entry lists:
  the zips of entries forgotten or moved (renamed), and any an interrupted
  run left. (Every zip goes here, once the source is synced, rather than
  as its entry goes: where file names ignore case, as on Windows, a page
  renamed from x.htm to X.htm has a new zip, X.zip, that is the forgotten
  x.zip. A zip listed by another case is kept if it is the same file.)"""
  folder = os.path.join(ctx.lib.zips_dir, source)
  if not os.path.isdir(folder):
    return
  listed = {r[0] for r in ctx.con.execute("SELECT path FROM files WHERE root = 'zips' AND source = ?", (source,))}
  by_case = {}
  for path in listed:
    by_case.setdefault(path.casefold(), []).append(path)
  for dirpath, dirnames, filenames in os.walk(folder, topdown=False):
    for n in filenames:
      rel = _rel(os.path.join(dirpath, n), ctx.lib.zips_dir)
      if rel in listed or any(_same_file(ctx.zip_path(rel), ctx.zip_path(p)) for p in by_case.get(rel.casefold(), ())):
        continue
      log.info("%s: deleting %s, which nothing lists", source, rel)
      _delete_zip(ctx, rel)
    if dirpath != folder:
      with contextlib.suppress(OSError):
        os.rmdir(dirpath)  # (only if empty)


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def _forget_source(ctx, source, kind):
  """Forget everything *source* lists as a source of type *kind*: its
  entries, then the zips it made and the clones it kept (a chunk at a time,
  committing between: the BBS waits for the lock only so long). Returns how
  many entries. The files of a linked source are never touched."""
  con = ctx.con
  # (a linked source's files are under the root named for it; a zip source's are its zips)
  where = "root = ?" if kind in library.LINKED_TYPES else "source = ? AND source_key IS NOT NULL"
  n = 0
  while True:
    rows = con.execute(f"SELECT id FROM files WHERE {where} LIMIT 5000", (source,)).fetchall()
    if not rows:
      break
    for row in rows:
      library.remove(con, row["id"])
    con.commit()
    n += len(rows)
  if kind not in library.LINKED_TYPES:
    for folder in (os.path.join(ctx.lib.zips_dir, source), os.path.join(ctx.lib.repos_dir, source)):
      remove_tree(folder)
  return n


def forget_unconfigured(ctx):
  """Forget what the sources no longer in the config listed (removed or
  renamed there), by the type sync_source records for each. A dry run only
  says so."""
  con = ctx.con
  for source, kind in con.execute("SELECT source, value FROM sync_state WHERE key = 'type'").fetchall():
    if source in ctx.lib.sources:
      continue
    if ctx.dry_run:
      where = "root = ?" if kind in library.LINKED_TYPES else "source = ? AND source_key IS NOT NULL"
      n = con.execute(f"SELECT COUNT(*) FROM files WHERE {where}", (source,)).fetchone()[0]
      log.info("%s is no longer in the config: would forget its %d file(s)", source, n)
      continue
    n = _forget_source(ctx, source, kind)
    con.execute("DELETE FROM sync_state WHERE source = ?", (source,))
    con.commit()
    log.info("%s is no longer in the config: forgot its %d file(s)", source, n)


def next_check(con, source, conf, pace, now):
  """When a scheduled run is to check *source* (its settings *conf*) next,
  in Unix time: 0, at once, if it never has been, its settings have
  changed since, or the clock has gone back. Its last check's cost
  decides: a check that cost t seconds is done again *pace* times t after
  the run that made it began, and at least daily. The cost leaves out the
  work changes asked for (Stats.work): what is paced is looking for
  changes, which reads all of a source's folders, and on a disk busy with
  something else takes a hundred times as long as on one idle."""
  try:
    began, cost, settings = library.get_state(con, source, library.CHECKED, "").split()
    began, cost = float(began), float(cost)
  except ValueError:
    return 0.0
  if settings != _settings_key(conf) or began > now:
    return 0.0
  return began + min(MAX_GAP, pace * cost)


def _record_check(ctx, source, conf, began, cost):
  """Record that the run that began at *began* checked *source*, at a cost
  of *cost* seconds (next_check): whatever came of it, a check that failed
  or couldn't read everything too, so a source that always does is paced
  like any other."""
  try:
    library.set_state(ctx.con, source, library.CHECKED, f"{began:.0f} {max(0.0, cost):.3f} {_settings_key(conf)}")
    ctx.con.commit()
  except sqlite3.Error as exc:  # (the catalogue locked too long: checked again next run)
    ctx.con.rollback()
    log.warning("%s: could not record its check: %s", source, exc)


def _settings_key(conf):
  """A short fingerprint of a source's settings: a check under others is
  no guide to the next (a new dir, more tags), so it is due at once."""
  def plain(v):
    if isinstance(v, Mapping):
      return {str(k): plain(v[k]) for k in v.keys()}
    if isinstance(v, (list, tuple)):
      return [plain(x) for x in v]
    return v if isinstance(v, (str, int, float, bool)) else str(v)
  return hashlib.sha1(json.dumps(plain(conf), sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _when(t):
  """Unix time *t* for the log: its time of day, and its day if not today."""
  local = time.localtime(t)
  return time.strftime("%H:%M" if local[:3] == time.localtime()[:3] else "%a %H:%M", local)


class AlreadyRunning(RuntimeError):
  """Another library_sync holds the lock."""


@contextlib.contextmanager
def single_instance(path):
  """Hold *path* locked for the run; AlreadyRunning if another run holds it."""
  os.makedirs(os.path.dirname(path), exist_ok=True)
  f = open(path, "a+b")
  try:
    try:
      if os.name == "nt":
        import msvcrt
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
      else:
        import fcntl
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
      raise AlreadyRunning(f"another library_sync is running ({path} is locked)")
    yield
  finally:
    f.close()


def _setup_logging(data_dir, verbose):
  if log.handlers:  # (main run twice in one process: the tests)
    return
  log.setLevel(logging.INFO)
  log.propagate = False
  fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
  fh = logging.handlers.RotatingFileHandler(os.path.join(data_dir, "library_sync.log"),
                                            maxBytes=2_000_000, backupCount=3, encoding="utf-8")
  fh.setFormatter(fmt)
  log.addHandler(fh)
  if sys.stderr is not None:  # (none under pythonw, as the scheduled task runs it)
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    log.addHandler(sh)


def main(argv=None):
  parser = argparse.ArgumentParser(description="Fill and refresh the file library's catalogue.")
  parser.add_argument("config", nargs="?", help=f"the BBS's config (default: {DEFAULT_CONFIG} in the data dir)")
  parser.add_argument("--data-dir", help="the BBS's data directory (as for DirtyFork.py)")
  parser.add_argument("--all", action="store_true", help="every source, scheduled: false ones too, due or not")
  parser.add_argument("--dry-run", action="store_true", help="say what would change; change nothing")
  parser.add_argument("-v", "--verbose", action="store_true", help="log every file that changes")
  parser.add_argument("sources", nargs="*", metavar="SOURCE", help="sources to sync, due or not (default: the scheduled ones that are due)")
  args = parser.parse_args(argv)
  # A config path given first and a source name are both positional: a name
  # ending in .yaml is the config.
  if args.config and not args.config.lower().endswith((".yaml", ".yml")):
    args.sources.insert(0, args.config)
    args.config = None

  import paths
  paths.data_dir = os.path.abspath(args.data_dir or ".")
  _setup_logging(paths.data_dir, args.verbose)  # (first: under pythonw, the log is all there is)
  try:
    return _run(args, paths)
  except Exception:
    log.exception("library_sync failed")
    return 1


def _run(args, paths):
  run_began = time.time()  # (what each check is recorded as begun at: next_check)
  config_path = os.path.abspath(args.config or paths.resolve_data(DEFAULT_CONFIG))
  os.chdir(paths.project_dir)  # (the config's !include paths are relative to it, as for the BBS)
  from config import get_config
  cfg = get_config(path=config_path, main=True)
  from file_transfer import TEMP_PREFIX
  try:
    lib = library.from_config(cfg)
  except ValueError as exc:
    log.error("%s", exc)
    return 2

  unknown = [s for s in args.sources if s not in lib.sources]
  if unknown:
    log.error("No such source: %s (the sources are: %s)", ", ".join(unknown), ", ".join(lib.sources) or "none")
    return 2
  if args.sources:
    chosen = args.sources
  else:
    chosen = [name for name, sc in lib.sources.items()
              if args.all or not (sc.scheduled is False or str(sc.scheduled).lower() == "false")]
  # (a scheduled run checks each source only as often as its last check's
  # cost allows: next_check; a run naming sources, or --all, checks them now)
  paced = not (args.sources or args.all or args.dry_run)
  pace = PACE
  if cfg.file_library.sync_pace is not null:
    try:
      pace = float(cfg.file_library.sync_pace)  # (0: every source at every run)
      if not 0 <= pace < float("inf"):
        raise ValueError
    except (TypeError, ValueError):
      log.warning("file_library.sync_pace %r is not a number of 0 or more; using %s", cfg.file_library.sync_pace,
                  PACE)
      pace = PACE

  if args.dry_run and not os.path.isfile(lib.catalog):
    con = library.empty_catalogue()  # (a dry run makes nothing, not even the catalogue)
  else:
    if args.dry_run:
      library.update_schema(lib)  # (an older DirtyFork's catalogue can't be read as it is)
    else:
      library.ensure_schema(lib)
    con = open_catalogue(lib, args.dry_run)
  seven_zip = find_seven_zip(str(cfg.file_library.seven_zip) if cfg.file_library.seven_zip else None)
  ctx = Context(lib=lib, con=con, seven_zip=seven_zip, git=shutil.which("git"), dry_run=args.dry_run,
                verbose=args.verbose)
  started = time.monotonic()
  failures = 0
  try:
    with contextlib.nullcontext() if args.dry_run else single_instance(lib.sync_lock):
      later = {}  # source -> when it is next checked, for those not due yet
      if paced:
        later = {name: due for name in chosen
                 if (due := next_check(con, name, lib.sources[name], pace, run_began)) > run_began + EARLY}
        chosen = [name for name in chosen if name not in later]
      log.info("library_sync: %s%s%s", ", ".join(chosen) or "(no sources)", " (dry run)" if args.dry_run else "",
               "; not due: " + ", ".join(f"{n} (at {_when(d)})" for n, d in later.items()) if later else "")
      if not args.dry_run:
        added, forgotten = library.reconcile_uploads(lib, ctx.con, TEMP_PREFIX)
        if added or forgotten:
          log.info("library folders: %d catalogued, %d forgotten", added, forgotten)
      forget_unconfigured(ctx)
      for name in chosen:
        conf = lib.sources[name]
        kind = str(conf.type)
        if kind in ("websites", "webpages", "github") and ctx.seven_zip is None and not args.dry_run:
          log.error("%s: 7-Zip (7z.exe) is not installed; set file_library.seven_zip", name)
          failures += 1
          continue
        t, stats = time.monotonic(), None
        try:
          stats = sync_source(ctx, name, conf)
        except SourceError as exc:
          ctx.con.rollback()
          log.error("%s: skipped: %s", name, exc)
          failures += 1
        except Exception:
          ctx.con.rollback()
          log.exception("%s: failed", name)
          failures += 1
        took = time.monotonic() - t
        if stats is not None:
          failures += 1 if stats.failed else 0
          log.info("%s: %s (%.1f s%s)", name, stats.summary(), took,
                   f", {stats.work:.1f} s of it on what changed" if stats.work >= 0.05 else "")
        if not args.dry_run:
          _record_check(ctx, name, conf, run_began, took - (stats.work if stats else 0.0))
  except AlreadyRunning as exc:
    log.error("%s", exc)
    return 3
  finally:
    ctx.con.close()
  log.info("library_sync done in %.1f s%s", time.monotonic() - started,
           f", {failures} source(s) with failures" if failures else "")
  return 1 if failures else 0





if __name__ == "__main__":
  sys.exit(main())
