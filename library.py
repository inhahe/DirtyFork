"""
The file library's catalogue: every file the library lists, where it is, its
tags, description and uploader, and searching it.

The catalogue is an SQLite database (file_library.catalog). A file is named
by a root and a path under it, never by an absolute path. The roots are

  uploads  the library folder (files_dir): uploads, and files the sysop puts there
  pending  uploads waiting for the sysop's approval (never offered to callers)
  zips     the zips library_sync.py makes (of websites, webpages, repositories)
  <source> the folder of each source whose files are listed where they are
           (file_library.sources of a type in LINKED_TYPES, by the source's name)

resolve() turns an entry into a path only inside its root's folder, so an
entry naming a root the config doesn't have, or a path leading out of its
root, is never served. Uploads are written to the library folder or to the
pending folder only (file.py's upload policy), never to a linked source's.

Searching: parse_query() turns what a caller types into a tree (QueryError
when it can't), and search_ids() runs it. QUERY_HELP describes the language.
Names, descriptions, tags and uploaders are compared normalised (norm): case,
spaces and punctuation don't count, so filename:"dirty fork" finds
DirtyFork.zip.

The BBS opens a connection per piece of work (connect), in a thread, so a
slow query never holds up other callers; library_sync.py writes in batches,
in WAL mode, so callers can read meanwhile.
"""

import os
import re
import sqlite3
import time
import unicodedata
from array import array
from dataclasses import dataclass, field

import paths

UPLOADS, PENDING, ZIPS = "uploads", "pending", "zips"
LINKED_TYPES = frozenset({"gallery", "videos", "samples", "mods"})  # listed in place, not zipped
SOURCE_TYPES = LINKED_TYPES | {"websites", "webpages", "github"}
DEFAULT_UPLOAD_KEY = "trusted_uploader"
SYNC_LOCK = "library_sync.lock"
SCHEMA_VERSION = 1
_SOURCE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Library:
  """Where the library's parts are (from_config).

  roots: root name -> its folder, for every root a catalogue entry may name.
  sources: source name -> its config (file_library.sources), for library_sync.py.
  upload_key: the key whose holders' uploads are listed at once (a sysop's
  too); anyone else's wait in pending_dir for the sysop's approval.
  sysop_handle: the uploader recorded for files the sysop adds (by putting
  them in the library folder, or through library_sync.py).
  """
  files_dir: str
  pending_dir: str
  zips_dir: str
  repos_dir: str
  catalog: str
  roots: dict
  upload_key: str = DEFAULT_UPLOAD_KEY
  sysop_handle: str = ""
  sources: dict = field(default_factory=dict)

  @property
  def sync_lock(self):
    """The file library_sync.py holds locked while it runs."""
    return os.path.join(os.path.dirname(os.path.abspath(self.catalog)), SYNC_LOCK)

  def reserved_names(self):
    """Names (lower case) an upload may not take in the library folder, and
    that are never catalogued from it: the folders the library keeps there
    (which may not exist yet), and, if the catalogue was put there itself,
    its files and the sync's lock."""
    names = set()
    folder = os.path.normcase(os.path.abspath(self.files_dir))
    catalog_dir = os.path.dirname(os.path.abspath(self.catalog))
    if os.path.normcase(catalog_dir) == folder:
      base = os.path.basename(self.catalog).lower()
      names.update({base, base + "-wal", base + "-shm", base + "-journal", SYNC_LOCK})
    for d in (self.pending_dir, self.zips_dir, self.repos_dir, catalog_dir):
      if os.path.normcase(os.path.dirname(os.path.abspath(d))) == folder:
        names.add(os.path.basename(d).lower())
    return frozenset(names)


def from_config(cfg):
  """The Library a config describes. ValueError (naming the fault) for a
  source that can't be used, so a bad config stops the BBS at startup
  instead of misbehaving later."""
  fl = cfg.file_library
  files_dir = paths.resolve_project(str(cfg.files_dir or "files"))

  def folder(key, default):
    value = fl[key] if fl else None
    return paths.resolve_project(str(value)) if value else os.path.join(files_dir, default)

  roots = {UPLOADS: files_dir, PENDING: folder("pending_dir", "pending"), ZIPS: folder("zips_dir", "zips")}
  sources = {}
  for name, sc in ((fl.sources.items() if fl and fl.sources else ())):
    name = str(name)
    kind = str(sc.type) if sc and sc.type else ""
    if not _SOURCE_NAME.match(name) or name in (UPLOADS, PENDING, ZIPS):
      raise ValueError(f"file_library.sources: '{name}' can't be a source's name "
                       f"(letters, digits, - and _ only; not {UPLOADS}, {PENDING} or {ZIPS})")
    if kind not in SOURCE_TYPES:
      raise ValueError(f"file_library.sources.{name}: type '{kind}' is not one of "
                       f"{', '.join(sorted(SOURCE_TYPES))}")
    if kind != "github" and not sc.dir:
      raise ValueError(f"file_library.sources.{name}: a {kind} source needs a dir")
    if kind in LINKED_TYPES:
      roots[name] = os.path.abspath(str(sc.dir))
    sources[name] = sc
  return Library(files_dir=files_dir, pending_dir=roots[PENDING], zips_dir=roots[ZIPS],
                 repos_dir=folder("repos_dir", "repos"),
                 catalog=folder("catalog", os.path.join("catalog", "library.db")),
                 roots=roots, sources=sources,
                 upload_key=str(fl.upload_key) if fl and fl.upload_key else DEFAULT_UPLOAD_KEY,
                 sysop_handle=str(cfg.sysop_handle) if cfg.sysop_handle else "")


# ---------------------------------------------------------------------------
# Normalising
# ---------------------------------------------------------------------------

_NOT_KEPT = re.compile(r"[^\w.]|_")
_NOT_KEPT_IN_PATTERN = re.compile(r"[^\w.*]|_")
_STARS = re.compile(r"\*+")


def norm(text):
  """*text* as the catalogue compares it: compatibility-normalised (a
  full-width letter is the letter), case-folded, letters, digits and dots
  only. "Dirty Fork", "dirty_fork" and "DirtyFork" are all "dirtyfork"."""
  return _NOT_KEPT.sub("", unicodedata.normalize("NFKC", str(text)).casefold())


def norm_pattern(text):
  """norm() for a search term, keeping its * wildcards (runs of them as one).
  The result has no other GLOB metacharacter: norm drops ? [ and ]."""
  return _STARS.sub("*", _NOT_KEPT_IN_PATTERN.sub("", unicodedata.normalize("NFKC", str(text)).casefold()))


def clean_tags(tags):
  """*tags* without blanks and repeats (by norm), first spelling and order kept."""
  seen, result = set(), []
  for tag in tags:
    tag = " ".join(str(tag).split())
    key = norm(tag)
    if key and key not in seen:
      seen.add(key)
      result.append(tag)
  return result


# ---------------------------------------------------------------------------
# The search language
# ---------------------------------------------------------------------------

QUERY_HELP = [
  "A word finds files whose tags, name or description have it. Words side by",
  "side must all match. Join them with and, or, not, and group with ( ).",
  "tag:pic  filename:dirtyfork  description:knight  uploader:sysop",
  'Quotes keep words together: filename:"dirty fork". Case, spaces and',
  "punctuation are ignored. * matches anything: filename:*.zip  description:a*",
]
QUERY_EXAMPLES = [
  "space not tag:video",
  "tag:mod and (tag:xm or tag:it)",
  'tag:webpage description:"movie review*"',
  "tag:(sample or instrument) not filename:*.flac",
]

FIELDS = {"tag": "tag", "tags": "tag", "uploader": "uploader", "by": "uploader",
          "filename": "filename", "name": "filename", "file": "filename",
          "description": "description", "desc": "description"}
ANY_FIELD = ("tag", "filename", "description")  # what a word without a field: matches
MAX_TERMS = 40
MAX_DEPTH = 20


class QueryError(ValueError):
  """A search that can't be run; the message says why, for the caller."""


@dataclass(frozen=True)
class Term:
  """One thing to match: field is tag, uploader, filename, description, or
  None for any of ANY_FIELD; pattern is norm_pattern(what was typed)."""
  field: str
  pattern: str
  text: str  # as typed, for messages


@dataclass(frozen=True)
class Op:
  """kind 'and' or 'or' over parts, or 'not' of its one part."""
  kind: str
  parts: tuple


def _tokens(text):
  """(kind, value) pairs: ('(', None), (')', None), ('kw', 'and'/'or'/'not'),
  ('field', name), ('word', text) for a bare word, ('quoted', text)."""
  out, i, n = [], 0, len(text)
  while i < n:
    c = text[i]
    if c.isspace():
      i += 1
    elif c in "()":
      out.append((c, None))
      i += 1
    elif c == '"':
      end = text.find('"', i + 1)
      if end < 0:
        raise QueryError('A quotation mark (") is not closed.')
      out.append(("quoted", text[i + 1:end]))
      i = end + 1
    else:
      j = i
      while j < n and not text[j].isspace() and text[j] not in '()"':
        j += 1
      word = text[i:j]
      i = j
      prefix, colon, rest = word.partition(":")
      if colon and prefix:
        name = FIELDS.get(prefix.lower())
        if name is None:
          raise QueryError(f"There is no '{prefix}:'. Use tag:, filename:, description: or "
                           "uploader: (or put the word in quotes).")
        out.append(("field", name))
        if rest:
          out.append(("word", rest))
      elif word.lower() in ("and", "or", "not"):
        out.append(("kw", word.lower()))
      else:
        out.append(("word", word))
  return out


def parse_query(text):
  """The tree (Term/Op) for a search typed by a caller. QueryError, with a
  message for them, when it can't be read."""
  tokens = _tokens(text)
  if not tokens:
    raise QueryError("Type something to search for.")
  pos = 0
  terms = 0

  def peek():
    return tokens[pos] if pos < len(tokens) else (None, None)

  def ends_part(tok):
    return tok[0] in (None, ")") or tok == ("kw", "or") or tok == ("kw", "and")

  def either(field, depth):
    nonlocal pos
    parts = [both(field, depth)]
    while peek() == ("kw", "or"):
      pos += 1
      if ends_part(peek()):
        raise QueryError("'or' needs something to search for after it.")
      parts.append(both(field, depth))
    return parts[0] if len(parts) == 1 else Op("or", tuple(parts))

  def both(field, depth):
    nonlocal pos
    parts = [negated(field, depth)]
    while True:
      tok = peek()
      if tok[0] in (None, ")") or tok == ("kw", "or"):
        break
      if tok == ("kw", "and"):
        pos += 1
        if ends_part(peek()):
          raise QueryError("'and' needs something to search for after it.")
      parts.append(negated(field, depth))
    return parts[0] if len(parts) == 1 else Op("and", tuple(parts))

  def negated(field, depth):
    nonlocal pos
    if peek() == ("kw", "not"):
      pos += 1
      if ends_part(peek()):
        raise QueryError("'not' needs something to search for after it.")
      if depth >= MAX_DEPTH:
        raise QueryError("That search is nested too deeply.")
      return Op("not", (negated(field, depth + 1),))
    return single(field, depth)

  def single(field, depth):
    nonlocal pos, terms
    kind, value = peek()
    if kind is None:
      raise QueryError("The search ends too soon.")
    if kind == "(":
      if depth >= MAX_DEPTH:
        raise QueryError("That search is nested too deeply.")
      pos += 1
      if peek()[0] == ")":
        raise QueryError("There is nothing between ( and ).")
      node = either(field, depth + 1)
      if peek()[0] != ")":
        raise QueryError("A ( is not closed with ).")
      pos += 1
      return node
    if kind == ")":
      raise QueryError("There is a ) without a ( before it.")
    if kind == "kw":
      raise QueryError(f"'{value}' needs something to search for before it.")
    if kind == "field":
      pos += 1
      after = peek()[0]
      if after not in ("word", "quoted", "("):
        raise QueryError(f"{value}: needs something to search for after it.")
      return single(value, depth)
    pos += 1
    if not value.strip():
      raise QueryError("There is nothing between the quotation marks.")
    pattern = norm_pattern(value)
    if not pattern:
      raise QueryError(f"'{value}' has no letters or digits to search for.")
    terms += 1
    if terms > MAX_TERMS:
      raise QueryError(f"That search has too many words (at most {MAX_TERMS}).")
    return Term(field, pattern, value)

  node = either(None, 0)
  if pos < len(tokens):
    raise QueryError("There is a ) without a ( before it.")  # (nothing else ends a part early)
  return node


def _term_sql(field, pattern):
  wild = "*" in pattern
  if field == "tag":
    op = "GLOB" if wild else "="
    return f"f.id IN (SELECT file_id FROM file_tags WHERE tag_norm {op} ?)", [pattern]
  column = {"filename": "f.name_norm", "description": "f.desc_norm", "uploader": "f.uploader_norm"}[field]
  if wild:
    return f"{column} GLOB ?", [pattern]
  if field == "uploader":
    return f"{column} = ?", [pattern]
  return f"instr({column}, ?) > 0", [pattern]


def query_sql(node):
  """(SQL condition on files f, its parameters) for a parse_query tree.
  Without a *, a tag or an uploader must equal the term, and a name or a
  description must contain it; with one, the pattern must match all of it."""
  if isinstance(node, Term):
    fields = (node.field,) if node.field else ANY_FIELD
    parts = [_term_sql(f, node.pattern) for f in fields]
    if len(parts) == 1:
      return parts[0]
    return "(" + " OR ".join(sql for sql, _ in parts) + ")", [p for _, ps in parts for p in ps]
  subs = [query_sql(part) for part in node.parts]
  params = [p for _, ps in subs for p in ps]
  if node.kind == "not":
    return f"NOT ({subs[0][0]})", params
  joiner = " AND " if node.kind == "and" else " OR "
  return "(" + joiner.join(sql for sql, _ in subs) + ")", params


# ---------------------------------------------------------------------------
# The database
# ---------------------------------------------------------------------------

# A file's name (shown, and sent) is the last part of its path: not stored
# again. Millions of rows: every column counts.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY,
  root TEXT NOT NULL,                  -- see the module's docstring
  path TEXT NOT NULL,                  -- under the root, with / between folders
  size INTEGER NOT NULL,
  mtime INTEGER NOT NULL DEFAULT 0,    -- the file's, in ns since 1970
  description TEXT NOT NULL DEFAULT '',
  uploader TEXT NOT NULL DEFAULT '',
  added INTEGER NOT NULL,              -- when it was catalogued (Unix time)
  source TEXT,                         -- the library_sync source listing it; NULL for uploads
  source_key TEXT,                     -- what it is in that source; NULL when that is its path
  fingerprint TEXT,                    -- what the source made it from, to see a change (zips)
  tag_count INTEGER NOT NULL DEFAULT 0,
  name_norm TEXT NOT NULL,             -- norm(name): searched, and the order lists are in
  desc_norm TEXT NOT NULL,
  uploader_norm TEXT NOT NULL,
  UNIQUE (root, path)
);
CREATE INDEX IF NOT EXISTS files_by_name ON files (name_norm, id);
CREATE INDEX IF NOT EXISTS files_by_source ON files (source, source_key) WHERE source_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS files_by_tag_count ON files (tag_count);
CREATE TABLE IF NOT EXISTS file_tags (
  file_id INTEGER NOT NULL REFERENCES files (id) ON DELETE CASCADE,
  tag_norm TEXT NOT NULL,
  tag TEXT NOT NULL,                   -- as shown
  position INTEGER NOT NULL,           -- order among the file's tags
  PRIMARY KEY (file_id, tag_norm)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS file_tags_by_tag ON file_tags (tag_norm, tag);
CREATE TABLE IF NOT EXISTS sync_state (
  source TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (source, key)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def connect(lib):
  """A connection to the catalogue (rows by column name, foreign keys on;
  waits up to 30 s for a writer). Close it when done; use it in one thread."""
  con = sqlite3.connect(lib.catalog, timeout=30)
  con.row_factory = sqlite3.Row
  con.execute("PRAGMA foreign_keys = ON")
  return con


def _schema_version(con):
  if not con.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'settings'").fetchone():
    return None
  row = con.execute("SELECT value FROM settings WHERE key = 'schema'").fetchone()
  return int(row[0]) if row else None


def ensure_schema(lib):
  """Create the catalogue and its folders if need be (at startup). A
  catalogue already made is only read: creating takes the write lock, which
  a sync may be holding."""
  for d in (lib.files_dir, lib.pending_dir, os.path.dirname(os.path.abspath(lib.catalog))):
    os.makedirs(d, exist_ok=True)
  con = connect(lib)
  try:
    version = _schema_version(con)
    if version is not None and version > SCHEMA_VERSION:
      raise RuntimeError(f"{lib.catalog} is from a newer DirtyFork (schema {version})")
    if version == SCHEMA_VERSION:
      return
    con.execute("PRAGMA journal_mode = WAL")
    con.executescript(_SCHEMA)
    con.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('schema', ?)", (str(SCHEMA_VERSION),))
    con.commit()
  finally:
    con.close()


@dataclass(frozen=True)
class Entry:
  """A catalogued file. mtime is in ns; added is Unix time; tags in order."""
  id: int
  root: str
  path: str
  name: str
  size: int
  mtime: int
  description: str
  uploader: str
  added: int
  source: str
  source_key: str
  fingerprint: str
  tags: tuple

  @property
  def pending(self):
    return self.root == PENDING


def _ids(rows):
  return array("q", (row[0] for row in rows))


def _plain(con):
  """A cursor that returns tuples (much faster than Rows for many rows)."""
  cur = con.cursor()
  cur.row_factory = None
  return cur


_LISTED = "f.root <> 'pending'"
_ORDER = "ORDER BY f.name_norm, f.id"


def search_ids(con, node):
  """Ids of the listed files a parse_query tree matches, by name."""
  sql, params = query_sql(node)
  return _ids(_plain(con).execute(f"SELECT f.id FROM files f WHERE {_LISTED} AND {sql} {_ORDER}", params))


def all_ids(con):
  """Ids of every listed file, by name."""
  return _ids(_plain(con).execute(f"SELECT f.id FROM files f WHERE {_LISTED} {_ORDER}"))


def _name(path):
  return path.rsplit("/", 1)[-1]


def ids_named(con, name):
  """Ids of the listed files called *name* (any case), by id."""
  want = name.casefold()
  rows = _plain(con).execute(f"SELECT f.id, f.path FROM files f WHERE {_LISTED} AND f.name_norm = ? ORDER BY f.id",
                             (norm(name),))
  return array("q", (file_id for file_id, path in rows if _name(path).casefold() == want))


def pending_ids(con):
  """Ids of the uploads awaiting the sysop, oldest first."""
  return _ids(_plain(con).execute("SELECT id FROM files WHERE root = 'pending' ORDER BY added, id"))


def pending_count(con):
  return con.execute("SELECT COUNT(*) FROM files WHERE root = 'pending'").fetchone()[0]


def listed_count(con):
  """How many files are listed (all, less the pending: two index counts,
  not a scan of every row)."""
  return con.execute("SELECT COUNT(*) FROM files").fetchone()[0] - pending_count(con)


def browse(con, path):
  """One level of the tag tree: *path* is the tags chosen so far.

  Returns (subtags, ids): subtags is [(tag, count)] for each other tag of
  the listed files having every tag in *path* (count: how many have it as
  well), by name; ids are the listed files whose tags are exactly *path*,
  by name. At the top (no path), the untagged files."""
  norms = [norm(t) for t in path]
  has_all = " AND f.id IN (SELECT file_id FROM file_tags WHERE tag_norm = ?)" * len(norms)
  cur = _plain(con)
  if norms:
    marks = ", ".join("?" * len(norms))
    sub = cur.execute(
      f"SELECT MIN(t.tag), COUNT(*) FROM file_tags t WHERE t.tag_norm NOT IN ({marks}) AND t.file_id IN "
      f"(SELECT f.id FROM files f WHERE {_LISTED}{has_all}) GROUP BY t.tag_norm ORDER BY t.tag_norm",
      norms + norms).fetchall()
  else:
    # Every tag of every file, less those of uploads awaiting the sysop
    # (few): faster than joining files for every one of millions of tags.
    counts = {key: [tag, n] for tag, key, n in cur.execute(
      "SELECT MIN(tag), tag_norm, COUNT(*) FROM file_tags GROUP BY tag_norm")}
    for key, n in cur.execute("SELECT tag_norm, COUNT(*) FROM file_tags WHERE file_id IN "
                              "(SELECT id FROM files WHERE root = 'pending') GROUP BY tag_norm"):
      counts[key][1] -= n
    sub = [(tag, n) for key, (tag, n) in sorted(counts.items()) if n > 0]
  ids = _ids(cur.execute(f"SELECT f.id FROM files f WHERE {_LISTED} AND f.tag_count = ?{has_all} {_ORDER}",
                         [len(norms)] + norms))
  return sub, ids


def _entry(row, tags):
  return Entry(id=row["id"], root=row["root"], path=row["path"], name=_name(row["path"]), size=row["size"],
               mtime=row["mtime"], description=row["description"], uploader=row["uploader"],
               added=row["added"], source=row["source"], source_key=row["source_key"] or row["path"],
               fingerprint=row["fingerprint"], tags=tuple(tags))


def fetch(con, ids):
  """Entries for *ids*, in that order (ids no longer catalogued are left out)."""
  ids = list(ids)
  found = {}
  for start in range(0, len(ids), 500):
    chunk = ids[start:start + 500]
    marks = ", ".join("?" * len(chunk))
    tags = {}
    for file_id, tag in con.execute(f"SELECT file_id, tag FROM file_tags WHERE file_id IN ({marks}) "
                                    "ORDER BY file_id, position", chunk):
      tags.setdefault(file_id, []).append(tag)
    for row in con.execute(f"SELECT * FROM files WHERE id IN ({marks})", chunk):
      found[row["id"]] = _entry(row, tags.get(row["id"], ()))
  return [found[i] for i in ids if i in found]


def get(con, file_id):
  """The Entry with this id, or None."""
  entries = fetch(con, [file_id])
  return entries[0] if entries else None


def source_entries(con, source):
  """{source_key: Entry} for what *source* (a library_sync source) lists
  (a scan of every row: for a source of zips, or a test)."""
  ids = _ids(_plain(con).execute("SELECT id FROM files WHERE source = ?", (source,)))
  return {e.source_key: e for e in fetch(con, ids)}


def put(con, *, root, path, size, mtime=0, description="", uploader="", tags=(), source=None,
        source_key=None, fingerprint=None, replace=True):
  """Catalogue the file at *path* under *root* (or, with replace, update it
  if it is catalogued already; without, leave it be). source_key, what the
  file is in its source, is stored only when it isn't *path*. Returns its
  id, or None when it was there already and replace is false. The caller
  commits."""
  name = _name(path)
  if source_key == path:
    source_key = None
  now = int(time.time())
  conflict = ("DO UPDATE SET size = excluded.size, mtime = excluded.mtime, "
              "description = excluded.description, uploader = excluded.uploader, "
              "source = excluded.source, source_key = excluded.source_key, "
              "fingerprint = excluded.fingerprint, name_norm = excluded.name_norm, "
              "desc_norm = excluded.desc_norm, uploader_norm = excluded.uploader_norm"
              if replace else "DO NOTHING")
  row = con.execute(
    "INSERT INTO files (root, path, size, mtime, description, uploader, added, source, source_key, "
    "fingerprint, name_norm, desc_norm, uploader_norm) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
    f"ON CONFLICT (root, path) {conflict} RETURNING id",
    (root, path, size, mtime, description, uploader, now, source, source_key, fingerprint,
     norm(name), norm(description), norm(uploader))).fetchone()
  if row is None:
    return None
  set_tags(con, row[0], tags)
  return row[0]


def set_tags(con, file_id, tags):
  """Make *tags* (clean_tags) the file's tags. The caller commits."""
  tags = clean_tags(tags)
  con.execute("DELETE FROM file_tags WHERE file_id = ?", (file_id,))
  con.executemany("INSERT INTO file_tags (file_id, tag_norm, tag, position) VALUES (?, ?, ?, ?)",
                  [(file_id, norm(t), t, i) for i, t in enumerate(tags)])
  con.execute("UPDATE files SET tag_count = ? WHERE id = ?", (len(tags), file_id))


def set_description(con, file_id, description):
  """The caller commits."""
  con.execute("UPDATE files SET description = ?, desc_norm = ? WHERE id = ?",
              (description, norm(description), file_id))


def remove(con, file_id):
  """Forget a file (not delete it). The caller commits."""
  con.execute("DELETE FROM files WHERE id = ?", (file_id,))


def get_state(con, source, key, default=None):
  row = con.execute("SELECT value FROM sync_state WHERE source = ? AND key = ?", (source, key)).fetchone()
  return row[0] if row else default


def set_state(con, source, key, value):
  """The caller commits. A value of None forgets the key."""
  if value is None:
    con.execute("DELETE FROM sync_state WHERE source = ? AND key = ?", (source, key))
  else:
    con.execute("INSERT INTO sync_state (source, key, value) VALUES (?, ?, ?) "
                "ON CONFLICT (source, key) DO UPDATE SET value = excluded.value", (source, key, value))


# ---------------------------------------------------------------------------
# Files on disk
# ---------------------------------------------------------------------------

def _within(folder, path):
  """True when *path* is in *folder* (both real paths), not the folder itself."""
  folder, path = os.path.normcase(folder), os.path.normcase(path)
  try:
    return path != folder and os.path.commonpath([folder, path]) == folder
  except ValueError:  # (another drive)
    return False


def resolve(lib, entry, allow_pending=False):
  """The path of the file *entry* names, or None unless it is a file inside
  its root's folder. Uploads awaiting the sysop only with allow_pending
  (the sysop's vetting): no caller is ever sent one."""
  if entry.pending and not allow_pending:
    return None
  base = lib.roots.get(entry.root)
  parts = entry.path.split("/")
  if base is None or any(p in ("", ".", "..") for p in parts):
    return None
  base = os.path.realpath(base)
  path = os.path.realpath(os.path.join(base, *parts))
  if not _within(base, path) or not os.path.isfile(path):
    return None
  return path


def file_stamp(path):
  """(size, mtime in ns) of a file, as the catalogue records them."""
  st = os.stat(path)
  return st.st_size, st.st_mtime_ns


def reconcile_uploads(lib, con, temp_prefix):
  """Make the catalogue agree with the library and pending folders: list
  files put there without the BBS (the sysop's, as theirs; in the pending
  folder, an upload a crash left uncatalogued, with no uploader), forget
  files that are gone, update sizes. Names starting with *temp_prefix*
  (uploads in progress) and the catalogue's own files are left alone.
  Returns (added, forgotten). Commits."""
  reserved = lib.reserved_names()
  added = forgotten = 0
  for root, folder in ((UPLOADS, lib.files_dir), (PENDING, lib.pending_dir)):
    on_disk = {}
    try:
      with os.scandir(folder) as it:
        for e in it:
          if e.name.startswith(temp_prefix) or e.name.lower() in reserved or not e.is_file(follow_symlinks=False):
            continue
          st = e.stat()
          on_disk[e.name] = (st.st_size, st.st_mtime_ns)
    except FileNotFoundError:
      pass
    known = {row["path"]: row for row in con.execute(
      "SELECT id, path, size, mtime FROM files WHERE root = ?", (root,))}
    for name, (size, mtime) in on_disk.items():
      row = known.get(name)
      if row is None:
        if put(con, root=root, path=name, size=size, mtime=mtime, replace=False,
               uploader=lib.sysop_handle if root == UPLOADS else "") is not None:
          added += 1
      elif (row["size"], row["mtime"]) != (size, mtime):
        con.execute("UPDATE files SET size = ?, mtime = ? WHERE id = ?", (size, mtime, row["id"]))
    for path, row in known.items():
      if path not in on_disk:
        remove(con, row["id"])
        forgotten += 1
  con.commit()
  return added, forgotten


def _move_new(source, target):
  """Move *source* to *target*, never replacing a file. False if *target* exists."""
  try:
    os.link(source, target)  # fails if *target* exists, on every system
  except FileExistsError:
    return False
  except OSError:
    if os.path.lexists(target):
      return False
    os.rename(source, target)  # (no hard links here; on Windows this won't replace either)
    return True
  os.remove(source)
  return True


def approve(lib, con, file_id):
  """List an upload that was awaiting the sysop: move it into the library
  folder. Returns None, or why it couldn't be done. Commits."""
  entry = get(con, file_id)
  if entry is None or not entry.pending:
    return "That upload is no longer waiting for approval."
  source = resolve(lib, entry, allow_pending=True)
  if source is None:
    remove(con, file_id)
    con.commit()
    return f"{entry.name} is gone from the pending folder."
  target = os.path.join(lib.files_dir, entry.name)
  if entry.name.lower() in lib.reserved_names() or not _move_new(source, target):
    return f"The library already has a file called {entry.name}; reject this one or rename that."
  try:
    con.execute("UPDATE files SET root = ?, path = ?, added = ? WHERE id = ?",
                (UPLOADS, entry.name, int(time.time()), file_id))
    con.commit()
  except sqlite3.Error:
    con.rollback()
    _move_new(target, source)
    raise
  return None


def reject(lib, con, file_id):
  """Delete an upload that was awaiting the sysop, and forget it. Commits."""
  entry = get(con, file_id)
  if entry is None or not entry.pending:
    return
  path = resolve(lib, entry, allow_pending=True)
  if path is not None:
    os.remove(path)
  remove(con, file_id)
  con.commit()
