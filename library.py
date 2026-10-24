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

import contextlib
import os
import re
import shutil
import sqlite3
import tempfile
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
SCHEMA_VERSION = 2
# Whose a file's description and tags are (files.edited): the sync's or the
# uploader's; a sysop's (set_details), which nothing else writes over; or
# a sysop's given back to the sync (reset_details), which sets them afresh
# at its next run, even if the file hasn't changed.
SYNCED, EDITED, RESET = 0, 1, 2
# The sync_state key of when library_sync last checked a source, and what
# that cost (library_sync.next_check); without it, the source is due.
CHECKED = "checked"
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
  legacy_meta: str = ""  # the YAML catalogue the library had before (read_legacy_meta)

  @property
  def sync_lock(self):
    """The file library_sync.py holds locked while it runs."""
    return os.path.join(os.path.dirname(os.path.abspath(self.catalog)), SYNC_LOCK)

  def reserved_names(self):
    """Names (lower case) an upload may not take in the library folder, and
    that are never catalogued from it: the folders the library keeps there
    (which may not exist yet), the old catalogue (read_legacy_meta) and, if
    the catalogue was put there itself, its files and the sync's lock."""
    names = set()
    folder = os.path.normcase(os.path.abspath(self.files_dir))
    if self.legacy_meta and os.path.normcase(os.path.dirname(os.path.abspath(self.legacy_meta))) == folder:
      names.add(os.path.basename(self.legacy_meta).lower())
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
      roots[name] = source_dir(sc)
    sources[name] = sc
  return Library(files_dir=files_dir, pending_dir=roots[PENDING], zips_dir=roots[ZIPS],
                 repos_dir=folder("repos_dir", "repos"),
                 catalog=folder("catalog", os.path.join("catalog", "library.db")),
                 roots=roots, sources=sources,
                 upload_key=str(fl.upload_key) if fl and fl.upload_key else DEFAULT_UPLOAD_KEY,
                 sysop_handle=str(cfg.sysop_handle) if cfg.sysop_handle else "",
                 legacy_meta=paths.resolve_project(str(cfg.files_meta)) if cfg.files_meta
                 else os.path.join(files_dir, "meta.yaml"))


def source_dir(sc):
  """A source's folder (its dir, relative to the project, as the BBS's own paths are)."""
  return os.path.normpath(paths.resolve_project(str(sc.dir)))


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
  "A word finds files whose tags, name, description or uploader have it.",
  "Words side by side must all match. Join with and, or, not; group with ( ).",
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
ANY_FIELD = ("tag", "filename", "description", "uploader")  # what a word without a field: matches
# (an uploader only of uploads: _term_sql)
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


def _term_sql(field, pattern, alone=False):
  """*alone*: the word was typed without a field."""
  wild = "*" in pattern
  if field == "tag":
    op = "GLOB" if wild else "="
    return f"f.id IN (SELECT file_id FROM file_tags WHERE tag_norm {op} ?)", [pattern]
  column = {"filename": "f.name_norm", "description": "f.desc_norm", "uploader": "f.uploader_norm"}[field]
  if wild:
    sql = f"{column} GLOB ?"
  elif field == "uploader":
    sql = f"{column} = ?"
  else:
    sql = f"instr({column}, ?) > 0"
  if field == "uploader" and alone:
    # (the uploader of a file someone uploaded: every file a source lists
    # has the sysop's handle, which would otherwise find all of them)
    sql = f"(f.source IS NULL AND {sql})"
  return sql, [pattern]


def query_sql(node):
  """(SQL condition on files f, its parameters) for a parse_query tree.
  Without a *, a tag or an uploader must equal the term, and a name or a
  description must contain it; with one, the pattern must match all of it."""
  if isinstance(node, Term):
    fields = (node.field,) if node.field else ANY_FIELD
    parts = [_term_sql(f, node.pattern, alone=not node.field) for f in fields]
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
  edited INTEGER NOT NULL DEFAULT 0,   -- whose its description and tags are: SYNCED, EDITED or RESET
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


def empty_catalogue():
  """An empty catalogue in memory (a dry run's, where there is none yet)."""
  con = sqlite3.connect(":memory:")
  con.row_factory = sqlite3.Row
  con.executescript(_SCHEMA)
  return con


def connect(lib):
  """A connection to the catalogue (rows by column name, foreign keys on;
  waits up to 30 s for a writer). Close it when done; use it in one thread."""
  con = sqlite3.connect(lib.catalog, timeout=30)
  con.row_factory = sqlite3.Row
  con.execute("PRAGMA foreign_keys = ON")
  return con


def _schema_version(con):
  """The catalogue's schema version, or None if it has no tables yet."""
  tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
  if "files" not in tables:
    return None
  row = con.execute("SELECT value FROM settings WHERE key = 'schema'").fetchone() if "settings" in tables else None
  # (No version: made by the first schema, which created its tables one by
  # one and then stamped them, and was stopped before it was done.)
  return int(row[0]) if row else 1


# What each schema version adds to the one before: a catalogue an older
# DirtyFork made is brought up to date by update_schema. (_SCHEMA is the
# latest, for a new catalogue.)
_MIGRATIONS = {
  2: ["ALTER TABLE files ADD COLUMN edited INTEGER NOT NULL DEFAULT 0"],
}


def ensure_schema(lib):
  """Create the catalogue and its folders if need be, or bring an older
  one's schema up to date (at startup)."""
  for d in (lib.files_dir, lib.pending_dir, os.path.dirname(os.path.abspath(lib.catalog))):
    os.makedirs(d, exist_ok=True)
  update_schema(lib)


def _statements(script):
  """The SQL statements of *script*, one by one (a comment may hold a ;)."""
  out, pending = [], ""
  for line in script.splitlines(keepends=True):
    pending += line
    if sqlite3.complete_statement(pending):
      out.append(pending.strip())
      pending = ""
  assert not pending.strip(), pending  # (every statement ends with its ;)
  return out


def update_schema(lib):
  """Create the catalogue's tables if it has none, or bring an older one's
  schema up to date (which changes no entry). One that is up to date is
  only read: writing takes the write lock, which a sync may be holding."""
  con = connect(lib)

  def check(version):
    if version is not None and version > SCHEMA_VERSION:
      raise RuntimeError(f"{lib.catalog} is from a newer DirtyFork (schema {version})")
    return version == SCHEMA_VERSION
  try:
    version = _schema_version(con)
    if check(version):
      return
    if version is None:
      con.execute("PRAGMA journal_mode = WAL")  # (not in a transaction)
    # One transaction, so tables never exist without their version; the
    # version is read again under the lock (another process may have done
    # this meanwhile).
    con.execute("BEGIN IMMEDIATE")
    version = _schema_version(con)
    if check(version):
      con.rollback()
      return
    if version is not None:  # (tables of an older schema)
      for step in range(version + 1, SCHEMA_VERSION + 1):
        for statement in _MIGRATIONS[step]:
          con.execute(statement)
    # (then whatever is missing: all of it for a new catalogue, the rest of
    # one the first schema was stopped making)
    for statement in _statements(_SCHEMA):
      con.execute(statement)
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
  edited: int = SYNCED  # whose its description and tags are

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
               fingerprint=row["fingerprint"], tags=tuple(tags), edited=row["edited"])


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
        source_key=None, fingerprint=None, replace=True, edited=SYNCED):
  """Catalogue the file at *path* under *root* (or, with replace, update it
  if it is catalogued already; without, leave it be). source_key, what the
  file is in its source, is stored only when it isn't *path*. *edited*:
  whose the description and tags are. The entry there already keeps a
  sysop's, unless these are a sysop's too, when it is the same file a
  source lists (the same source and key; a file an upload brings is a new
  one, whatever was there). Returns its id, or None when it was there
  already and replace is false. The caller commits."""
  name = _name(path)
  if source_key == path:
    source_key = None
  now = int(time.time())
  keep = (f"files.edited = {EDITED} AND excluded.edited != {EDITED} AND files.source = excluded.source "
          "AND files.source_key IS excluded.source_key")
  conflict = ("DO UPDATE SET size = excluded.size, mtime = excluded.mtime, "
              f"description = CASE WHEN {keep} THEN files.description ELSE excluded.description END, "
              f"desc_norm = CASE WHEN {keep} THEN files.desc_norm ELSE excluded.desc_norm END, "
              f"edited = CASE WHEN {keep} THEN files.edited ELSE excluded.edited END, "
              "uploader = excluded.uploader, source = excluded.source, source_key = excluded.source_key, "
              "fingerprint = excluded.fingerprint, name_norm = excluded.name_norm, "
              "uploader_norm = excluded.uploader_norm"
              if replace else "DO NOTHING")
  row = con.execute(
    "INSERT INTO files (root, path, size, mtime, description, uploader, added, source, source_key, "
    "fingerprint, edited, name_norm, desc_norm, uploader_norm) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
    f"ON CONFLICT (root, path) {conflict} RETURNING id, edited",
    (root, path, size, mtime, description, uploader, now, source, source_key, fingerprint, edited,
     norm(name), norm(description), norm(uploader))).fetchone()
  if row is None:
    return None
  if not (row[1] == EDITED and edited != EDITED):  # (a sysop's tags, kept)
    set_tags(con, row[0], tags)
  return row[0]


def move(con, file_id, root, path):
  """Catalogue file *file_id* under a new root and path, as the same entry
  (its details, and when it was added, kept). An entry there already is
  forgotten: it is the file that was there. Returns whether *file_id* is
  still catalogued. The caller commits."""
  con.execute("DELETE FROM files WHERE root = ? AND path = ? AND id != ?", (root, path, file_id))
  return con.execute("UPDATE files SET root = ?, path = ?, name_norm = ? WHERE id = ?",
                     (root, path, norm(_name(path)), file_id)).rowcount > 0


def set_tags(con, file_id, tags):
  """Make *tags* (clean_tags) the file's tags. The caller commits."""
  tags = clean_tags(tags)
  con.execute("DELETE FROM file_tags WHERE file_id = ?", (file_id,))
  con.executemany("INSERT INTO file_tags (file_id, tag_norm, tag, position) VALUES (?, ?, ?, ?)",
                  [(file_id, norm(t), t, i) for i, t in enumerate(tags)])
  con.execute("UPDATE files SET tag_count = ? WHERE id = ?", (len(tags), file_id))


def set_details(con, file_id, description, tags, by_sysop=False):
  """Give a file a description and tags (None: its tags as they are): a
  sysop's (*by_sysop*), which nothing else writes over from then on, or
  the sync's or the uploader's, which are never written over a sysop's.
  Returns whether they were set (not if the file is no longer catalogued,
  or these would be written over a sysop's). The caller commits."""
  # (One write, which takes the write lock before anything is checked:
  # nothing can change the file between the check and the rest.)
  cur = con.execute("UPDATE files SET description = ?, desc_norm = ?, edited = ? WHERE id = ?"
                    + ("" if by_sysop else f" AND edited != {EDITED}"),
                    (description, norm(description), EDITED if by_sysop else SYNCED, file_id))
  if not cur.rowcount:
    return False
  if tags is not None:
    set_tags(con, file_id, tags)
  return True


def reset_details(con, file_id):
  """Give a file's details back to the sync (a file a source lists, whose
  details a sysop set): it sets them afresh at its next run, which checks
  the source then however it is paced. Returns whether it did (not if the
  file is no longer catalogued, or its details aren't a sysop's). The
  caller commits."""
  if not con.execute(f"UPDATE files SET edited = {RESET} WHERE id = ? AND edited = {EDITED} "
                     "AND source IS NOT NULL", (file_id,)).rowcount:
    return False
  con.execute("DELETE FROM sync_state WHERE key = ? AND source = (SELECT source FROM files WHERE id = ?)",
              (CHECKED, file_id))
  return True


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
  (uploads in progress, moves) and reserved names are left alone.
  Returns (added, forgotten). Commits.

  The catalogue is read before the folder: the BBS publishes an upload and
  then catalogues it, so a row read here is for a file already there when
  the folder is listed, and an upload published meanwhile is never taken
  for one gone."""
  reserved = lib.reserved_names()
  added = forgotten = 0
  for root, folder in ((UPLOADS, lib.files_dir), (PENDING, lib.pending_dir)):
    known = {row["path"]: row for row in con.execute(
      "SELECT id, path, size, mtime FROM files WHERE root = ?", (root,))}
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
        # (by root too: an upload approved meanwhile has left this one)
        if con.execute("DELETE FROM files WHERE id = ? AND root = ?", (row["id"], root)).rowcount:
          forgotten += 1
  con.commit()
  return added, forgotten


def move_new(source, target, temp_prefix):
  """Move the file *source* to *target*, never replacing a file there:
  False (and *source* left) if *target* exists. Across volumes, where
  neither a link nor a rename works, by a copy named *temp_prefix*... beside
  *target* first (a name the library's folders leave alone). OSError when
  the move itself fails."""
  try:
    os.link(source, target)  # fails if *target* exists, on every system
  except FileExistsError:
    return False
  except OSError:
    if os.path.lexists(target):
      return False
    try:
      os.rename(source, target)  # (no hard links here; on Windows a rename never replaces either)
      return True
    except FileExistsError:
      return False
    except OSError:
      pass
    fd, temp = tempfile.mkstemp(prefix=temp_prefix, suffix=".move", dir=os.path.dirname(target))
    os.close(fd)
    try:
      shutil.copy2(source, temp)
      try:
        os.link(temp, target)  # (beside it now)
      except FileExistsError:
        return False
      except OSError:
        if os.path.lexists(target):
          return False
        os.rename(temp, target)
    finally:
      with contextlib.suppress(FileNotFoundError):
        os.remove(temp)
  try:
    os.remove(source)
  except OSError:  # (in use: undone, so the move is all or nothing)
    with contextlib.suppress(OSError):
      os.remove(target)
    raise
  return True


def approve(lib, con, file_id, temp_prefix):
  """List an upload that was awaiting the sysop: move it into the library
  folder. Returns None, or why it couldn't be done (never raising: the
  sysop is told). Commits."""
  entry = get(con, file_id)
  if entry is None or not entry.pending:
    return "That upload is no longer waiting for approval."
  source = resolve(lib, entry, allow_pending=True)
  if source is None:
    remove(con, file_id)
    con.commit()
    return f"{entry.name} is gone from the pending folder."
  if entry.name.lower() in lib.reserved_names():
    return f"{entry.name} is a name the library keeps for itself; reject it."
  target = os.path.join(lib.files_dir, entry.name)
  try:
    if not move_new(source, target, temp_prefix):
      return f"The library already has a file called {entry.name}; reject this one or rename that."
  except OSError as exc:
    return f"{entry.name} could not be moved into the library: {exc}"
  try:
    # (The name was free on disk, so an entry of that name is stale, for a
    # file deleted by hand and not yet reconciled: move forgets it.)
    if move(con, file_id, UPLOADS, entry.name):
      con.execute("UPDATE files SET added = ? WHERE id = ?", (int(time.time()), file_id))
    else:  # (forgotten meanwhile, by a sync that saw the pending folder without it)
      put(con, root=UPLOADS, path=entry.name, size=entry.size, mtime=entry.mtime, description=entry.description,
          uploader=entry.uploader, tags=entry.tags, edited=entry.edited)
    con.commit()
  except sqlite3.Error as exc:
    con.rollback()
    with contextlib.suppress(OSError):
      move_new(target, source, temp_prefix)
    return f"The catalogue could not be updated ({exc}); {entry.name} is still waiting."
  return None


def reject(lib, con, file_id):
  """Delete an upload that was awaiting the sysop, and forget it. Returns
  None, or why it couldn't be done (never raising). Commits."""
  entry = get(con, file_id)
  if entry is None or not entry.pending:
    return "That upload is no longer waiting for approval."
  path = resolve(lib, entry, allow_pending=True)
  if path is not None:
    try:
      os.remove(path)
    except FileNotFoundError:
      pass
    except OSError as exc:  # (being downloaded, say)
      return f"{entry.name} could not be deleted: {exc}"
  remove(con, file_id)
  con.commit()
  return None


def read_legacy_meta(lib):
  """The catalogue the library had before this one (files_meta, by default
  files/meta.yaml: {name: {keys: [...], description: "..."}}), as
  {name: (tags, description)}; {} if there is none. It stays where it is
  (never listed: reserved_names) until retire_legacy_meta, once its
  details are applied, so a start that fails before then tries again."""
  path = lib.legacy_meta
  if not path or not os.path.isfile(path):
    return {}
  import yaml
  try:
    with open(path, encoding="utf-8") as f:
      data = yaml.safe_load(f) or {}
  except (OSError, yaml.YAMLError, UnicodeError):
    return {}
  details = {}
  if isinstance(data, dict):
    for name, entry in data.items():
      if isinstance(entry, dict):
        tags = entry.get("keys") or entry.get("tags") or []
        details[str(name)] = ([str(t) for t in tags] if isinstance(tags, list) else [],
                              str(entry.get("description") or ""))
  return details


def retire_legacy_meta(lib, temp_prefix):
  """Move the old catalogue (read_legacy_meta) into the catalogue's folder,
  as "meta.yaml.imported" (or, if that is taken, with the time after it):
  read once, kept."""
  path = lib.legacy_meta
  if not path or not os.path.isfile(path):
    return
  kept = os.path.join(os.path.dirname(os.path.abspath(lib.catalog)), os.path.basename(path) + ".imported")
  if not move_new(path, kept, temp_prefix):
    move_new(path, kept + time.strftime("-%Y%m%d-%H%M%S"), temp_prefix)


def apply_legacy_meta(con, details):
  """Give the library folder's entries of those names the tags and
  descriptions of read_legacy_meta, where they have neither. Returns how
  many. Commits."""
  n = 0
  for row in con.execute("SELECT id, path FROM files WHERE root = ? AND tag_count = 0 AND description = ''",
                         (UPLOADS,)).fetchall():
    tags, description = details.get(row["path"], ([], ""))
    if tags or description:
      set_details(con, row["id"], description, tags)
      n += 1
  con.commit()
  return n


