"""library.py: the search language, the catalogue, and what may be served."""
import dataclasses
import os
import random
import shutil
import sqlite3
import tempfile
import unittest
from unittest import mock

import _setup  # noqa: F401  (paths, config)

import library
from library import QueryError, parse_query


def make_library(top):
  """A Library in *top*: the usual folders, and one linked source 'pics'."""
  files = os.path.join(top, "files")
  pics = os.path.join(top, "pics")
  os.makedirs(pics)
  lib = library.Library(files_dir=files, pending_dir=os.path.join(files, "pending"),
                        zips_dir=os.path.join(files, "zips"), repos_dir=os.path.join(files, "repos"),
                        catalog=os.path.join(files, "catalog", "library.db"),
                        roots={library.UPLOADS: files, library.PENDING: os.path.join(files, "pending"),
                               library.ZIPS: os.path.join(files, "zips"), "pics": pics},
                        sysop_handle="Sysop")
  library.ensure_schema(lib)
  return lib


class Parsing(unittest.TestCase):
  def test_precedence_and_grouping(self):
    def shape(node):
      if isinstance(node, library.Term):
        return (node.field, node.pattern)
      return (node.kind,) + tuple(shape(p) for p in node.parts)
    self.assertEqual(shape(parse_query("a b or c")), ("or", ("and", (None, "a"), (None, "b")), (None, "c")))
    self.assertEqual(shape(parse_query("a and (b or c)")), ("and", (None, "a"), ("or", (None, "b"), (None, "c"))))
    self.assertEqual(shape(parse_query("not a b")), ("and", ("not", (None, "a")), (None, "b")))
    self.assertEqual(shape(parse_query("not (a or b)")), ("not", ("or", (None, "a"), (None, "b"))))
    self.assertEqual(shape(parse_query("tag:(art or nature) not tag:x")),
                     ("and", ("or", ("tag", "art"), ("tag", "nature")), ("not", ("tag", "x"))))
    self.assertEqual(shape(parse_query("tag:(a filename:b)")), ("and", ("tag", "a"), ("filename", "b")))
    self.assertEqual(shape(parse_query("AND_x")), (None, "andx"))  # (a word, not the keyword)
    self.assertEqual(shape(parse_query('"and" OR "not"')), ("or", (None, "and"), (None, "not")))
    self.assertEqual(shape(parse_query("tag:not")), ("tag", "not"))
    self.assertEqual(shape(parse_query("tag: art")), ("tag", "art"))

  def test_fields_and_their_other_names(self):
    for typed, field in (("tag", "tag"), ("TAGS", "tag"), ("uploader", "uploader"), ("by", "uploader"),
                         ("filename", "filename"), ("name", "filename"), ("file", "filename"),
                         ("description", "description"), ("desc", "description")):
      self.assertEqual(parse_query(f"{typed}:x").field, field, typed)

  def test_values_are_normalised(self):
    self.assertEqual(parse_query('filename:"Dirty Fork"').pattern, "dirtyfork")
    self.assertEqual(parse_query("filename:dirty_fork-1.zip").pattern, "dirtyfork1.zip")
    self.assertEqual(parse_query("description:**a***b*").pattern, "*a*b*")
    self.assertEqual(parse_query("ＤＩＲＴＹ").pattern, "dirty")  # (full-width letters)
    self.assertEqual(parse_query("tag:[a]?").pattern, "a")      # (no GLOB metacharacter survives)

  def test_what_cant_be_read_says_why(self):
    for text, says in (("", "Type something"), ("   ", "Type something"), ('"abc', "quotation mark"),
                       ("and x", "before it"), ("x and", "after it"), ("x or", "after it"),
                       ("x and or y", "after it"), ("not", "after it"), ("(x", "not closed"),
                       ("x)", "without a ("), ("()", "nothing between"), ("foo:bar", "There is no 'foo:'"),
                       ("tag:", "needs something"), ("tag:)", "needs something"), ("---", "no letters"),
                       ('filename:""', "nothing between the quotation"), ('" "', "nothing between the quotation"),
                       ("x " * 41, "too many")):
      with self.subTest(text=text):
        with self.assertRaises(QueryError) as cm:
          parse_query(text)
        self.assertIn(says, str(cm.exception))

  def test_nesting_is_limited(self):
    parse_query("(" * 20 + "x" + ")" * 20)
    with self.assertRaises(QueryError):
      parse_query("(" * 21 + "x" + ")" * 21)
    with self.assertRaises(QueryError):
      parse_query("not " * 21 + "x")

  def test_nothing_typed_crashes_it(self):
    rng = random.Random(1)
    alphabet = ['(', ')', '"', ':', '*', ' ', 'a', 'b', 'tag', 'and', 'or', 'not', 'filename', '-', '\\', 'é']
    for _ in range(5000):
      text = "".join(rng.choice(alphabet) for _ in range(rng.randrange(1, 25)))
      try:
        node = parse_query(text)
      except QueryError:
        continue
      sql, params = library.query_sql(node)
      self.assertEqual(sql.count("?"), len(params), text)


class Catalogue(unittest.TestCase):
  """Searching and browsing a small catalogue."""

  @classmethod
  def setUpClass(cls):
    cls.top = tempfile.mkdtemp(prefix="library-")
    cls.lib = make_library(cls.top)
    cls.con = library.connect(cls.lib)
    files = [  # (root, path, tags, description, uploader)
      ("zips", "github/DirtyFork.zip", ["github"], "DirtyFork BBS", "Sysop"),
      ("zips", "github/fastpy.zip", ["github"], "A Python compiler", "Sysop"),
      ("zips", "pages/Dirty fork recipes.zip", ["web", "webpage"], "Forks of the dirty kind", "Sysop"),
      ("pics", "space/nebula.jpg", ["pic", "space"], "a nebula in space", "Sysop"),
      ("pics", "space/rocket.mp4", ["video", "space"], "", "Sysop"),
      ("pics", "art/knight.png", ["pic", "art"], "a knight on a horse", "Sysop"),
      ("uploads", "song.xm", ["mod", "xm"], "Space oddity", "alice"),
      ("uploads", "plain.txt", [], "", "bob"),
      ("pending", "secret.zip", ["github", "space"], "not yet approved", "mallory"),
    ]
    cls.ids = {}
    for root, path, tags, desc, who in files:
      cls.ids[path.rsplit("/", 1)[-1]] = library.put(cls.con, root=root, path=path, size=1, tags=tags,
                                                     description=desc, uploader=who)
    cls.con.commit()

  @classmethod
  def tearDownClass(cls):
    cls.con.close()
    shutil.rmtree(cls.top, ignore_errors=True)

  def names(self, text):
    entries = library.fetch(self.con, library.search_ids(self.con, parse_query(text)))
    return [e.name for e in entries]

  def test_fields(self):
    self.assertEqual(self.names("tag:github"), ["DirtyFork.zip", "fastpy.zip"])
    self.assertEqual(self.names("uploader:alice"), ["song.xm"])
    self.assertEqual(self.names("uploader:ALI"), [])  # (an uploader must match whole)
    self.assertEqual(self.names("filename:fast"), ["fastpy.zip"])
    self.assertEqual(self.names("description:nebula"), ["nebula.jpg"])

  def test_names_ignore_case_spaces_and_punctuation(self):
    both = ["DirtyFork.zip", "Dirty fork recipes.zip"]  # (by name, normalised: "dirtyfork.zip" first)
    self.assertEqual(self.names('filename:"dirty fork"'), both)
    self.assertEqual(self.names("filename:dirtyfork"), both)
    self.assertEqual(self.names("filename:DIRTY_FORK"), both)

  def test_wildcards_match_the_whole_value(self):
    self.assertEqual(self.names("filename:*.zip"), ["DirtyFork.zip", "Dirty fork recipes.zip", "fastpy.zip"])
    self.assertEqual(self.names("filename:dirty*"), ["DirtyFork.zip", "Dirty fork recipes.zip"])
    self.assertEqual(self.names("filename:dirty"), ["DirtyFork.zip", "Dirty fork recipes.zip"])
    self.assertEqual(self.names("filename:dirty*fork"), [])  # (the name goes on: .zip)
    self.assertEqual(self.names("description:a*"), ["fastpy.zip", "knight.png", "nebula.jpg"])
    self.assertEqual(self.names("tag:s*"), ["nebula.jpg", "rocket.mp4"])
    self.assertEqual(self.names("uploader:a*"), ["song.xm"])

  def test_a_word_alone_matches_tags_names_and_descriptions_not_uploaders(self):
    self.assertEqual(self.names("space"), ["nebula.jpg", "rocket.mp4", "song.xm"])
    self.assertEqual(self.names("knight"), ["knight.png"])
    self.assertEqual(self.names("alice"), [])

  def test_and_or_not(self):
    self.assertEqual(self.names("space not tag:video"), ["nebula.jpg", "song.xm"])
    self.assertEqual(self.names("tag:pic and tag:space"), ["nebula.jpg"])
    self.assertEqual(self.names("tag:pic tag:space"), ["nebula.jpg"])
    self.assertEqual(self.names("tag:(art or space) and not tag:video"), ["knight.png", "nebula.jpg"])
    self.assertEqual(self.names("not (tag:pic or tag:video or tag:github or tag:web)"), ["plain.txt", "song.xm"])

  def test_uploads_awaiting_approval_are_never_found(self):
    for text in ("secret", "tag:github", "uploader:mallory", "filename:*", "description:*approved*"):
      self.assertNotIn("secret.zip", self.names(text), text)
    self.assertNotIn(self.ids["secret.zip"], library.all_ids(self.con))
    self.assertEqual(list(library.pending_ids(self.con)), [self.ids["secret.zip"]])
    self.assertEqual(library.pending_count(self.con), 1)

  def test_by_name(self):
    self.assertEqual(list(library.ids_named(self.con, "dirtyfork.ZIP")), [self.ids["DirtyFork.zip"]])
    self.assertEqual(list(library.ids_named(self.con, "secret.zip")), [])

  def test_browsing_the_tag_tree(self):
    dirs, ids = library.browse(self.con, [])
    self.assertEqual(dict(dirs), {"art": 1, "github": 2, "mod": 1, "pic": 2, "space": 2, "video": 1,
                                  "web": 1, "webpage": 1, "xm": 1})  # (secret.zip not counted)
    self.assertEqual([e.name for e in library.fetch(self.con, ids)], ["plain.txt"])  # (untagged)
    dirs, ids = library.browse(self.con, ["space"])
    self.assertEqual(dict(dirs), {"pic": 1, "video": 1})
    self.assertEqual(list(ids), [])  # (nothing has exactly the tag space)
    dirs, ids = library.browse(self.con, ["SPACE", "pic"])
    self.assertEqual(dirs, [])
    self.assertEqual([e.name for e in library.fetch(self.con, ids)], ["nebula.jpg"])
    dirs, ids = library.browse(self.con, ["github"])
    self.assertEqual([e.name for e in library.fetch(self.con, ids)], ["DirtyFork.zip", "fastpy.zip"])

  def test_entries_keep_their_tags_in_order(self):
    e = library.get(self.con, self.ids["knight.png"])
    self.assertEqual(e.tags, ("pic", "art"))
    self.assertEqual(e.uploader, "Sysop")
    self.assertEqual(library.fetch(self.con, [self.ids["plain.txt"], 999999, self.ids["song.xm"]])[1].name,
                     "song.xm")


class Tags(unittest.TestCase):
  def test_repeats_and_blanks_go(self):
    self.assertEqual(library.clean_tags(["pic", "Pic", " ", "my  pics, etc", "my pics etc", "--", "x"]),
                     ["pic", "my pics, etc", "x"])


class Serving(unittest.TestCase):
  """resolve: only files inside their root's folder."""

  def setUp(self):
    self.top = tempfile.mkdtemp(prefix="library-")
    self.lib = make_library(self.top)
    os.makedirs(self.lib.pending_dir, exist_ok=True)
    for path in ("files/a.zip", "files/pending/p.zip", "pics/x/y.jpg", "secret.db"):
      full = os.path.join(self.top, *path.split("/"))
      os.makedirs(os.path.dirname(full), exist_ok=True)
      with open(full, "wb") as f:
        f.write(b"x")

  def tearDown(self):
    shutil.rmtree(self.top, ignore_errors=True)

  def entry(self, root, path):
    return library.Entry(id=1, root=root, path=path, name=path.rsplit("/", 1)[-1], size=1, mtime=0,
                         description="", uploader="", added=0, source=None, source_key=None,
                         fingerprint=None, tags=())

  def test_files_in_their_roots(self):
    self.assertEqual(library.resolve(self.lib, self.entry("uploads", "a.zip")),
                     os.path.realpath(os.path.join(self.top, "files", "a.zip")))
    self.assertEqual(library.resolve(self.lib, self.entry("pics", "x/y.jpg")),
                     os.path.realpath(os.path.join(self.top, "pics", "x", "y.jpg")))

  def test_nothing_outside_them(self):
    secret = os.path.join(self.top, "secret.db")
    for root, path in (("uploads", "../secret.db"), ("uploads", "..\\secret.db"), ("pics", "x/../../secret.db"),
                       ("uploads", secret), ("uploads", secret.replace("\\", "/")), ("nosuchroot", "a.zip"),
                       ("uploads", ""), ("uploads", "pending"), ("uploads", "./a.zip"), ("pics", "x"),
                       ("uploads", "missing.zip"), ("pics", "/x/y.jpg")):
      with self.subTest(root=root, path=path):
        self.assertIsNone(library.resolve(self.lib, self.entry(root, path)))

  def test_an_upload_awaiting_approval_only_for_vetting(self):
    e = self.entry("pending", "p.zip")
    self.assertIsNone(library.resolve(self.lib, e))
    self.assertIsNotNone(library.resolve(self.lib, e, allow_pending=True))


class Folders(unittest.TestCase):
  """reconcile_uploads, approve, reject."""

  def setUp(self):
    self.top = tempfile.mkdtemp(prefix="library-")
    self.lib = make_library(self.top)
    os.makedirs(self.lib.pending_dir, exist_ok=True)
    self.con = library.connect(self.lib)

  def tearDown(self):
    self.con.close()
    shutil.rmtree(self.top, ignore_errors=True)

  def write(self, folder, name, data=b"x"):
    with open(os.path.join(folder, name), "wb") as f:
      f.write(data)

  def catalogued(self, root):
    return {r["path"]: (r["uploader"], r["size"]) for r in self.con.execute(
      "SELECT path, uploader, size FROM files WHERE root = ?", (root,))}

  def test_reconciling_the_library_folders(self):
    self.write(self.lib.files_dir, "dropped.zip")
    self.write(self.lib.files_dir, ".upload-abc.part")    # an upload in progress
    self.write(self.lib.pending_dir, "orphan.zip")        # an upload a crash left uncatalogued
    library.put(self.con, root="uploads", path="gone.zip", size=1, uploader="alice")
    library.put(self.con, root="uploads", path="kept.zip", size=1, uploader="alice")
    self.write(self.lib.files_dir, "kept.zip", b"bigger")
    self.con.commit()
    self.assertEqual(library.reconcile_uploads(self.lib, self.con, ".upload-"), (2, 1))
    self.assertEqual(self.catalogued("uploads"), {"dropped.zip": ("Sysop", 1), "kept.zip": ("alice", 6)})
    self.assertEqual(self.catalogued("pending"), {"orphan.zip": ("", 1)})
    self.assertEqual(library.reconcile_uploads(self.lib, self.con, ".upload-"), (0, 0))

  def test_the_bbs_cataloguing_an_upload_wins_over_a_reconcile(self):
    self.write(self.lib.files_dir, "new.zip")
    library.reconcile_uploads(self.lib, self.con, ".upload-")  # (the sync ran before the BBS catalogued it)
    library.put(self.con, root="uploads", path="new.zip", size=1, uploader="alice", description="mine")
    self.con.commit()
    self.assertEqual(self.catalogued("uploads"), {"new.zip": ("alice", 1)})

  def test_approving_moves_the_file_into_the_library(self):
    self.write(self.lib.pending_dir, "up.zip")
    file_id = library.put(self.con, root="pending", path="up.zip", size=1, uploader="alice", tags=["game"])
    self.con.commit()
    self.assertIsNone(library.approve(self.lib, self.con, file_id, ".upload-"))
    self.assertTrue(os.path.isfile(os.path.join(self.lib.files_dir, "up.zip")))
    self.assertFalse(os.path.exists(os.path.join(self.lib.pending_dir, "up.zip")))
    e = library.get(self.con, file_id)
    self.assertEqual((e.root, e.path, e.uploader, e.tags), ("uploads", "up.zip", "alice", ("game",)))
    self.assertIn("no longer waiting", library.approve(self.lib, self.con, file_id, ".upload-"))

  def test_approving_never_replaces_a_file(self):
    self.write(self.lib.pending_dir, "up.zip", b"new")
    self.write(self.lib.files_dir, "UP.zip", b"old")
    file_id = library.put(self.con, root="pending", path="up.zip", size=3, uploader="alice")
    self.con.commit()
    self.assertIn("already has a file", library.approve(self.lib, self.con, file_id, ".upload-"))
    with open(os.path.join(self.lib.files_dir, "UP.zip"), "rb") as f:
      self.assertEqual(f.read(), b"old")
    self.assertTrue(library.get(self.con, file_id).pending)

  def test_rejecting_deletes_it(self):
    self.write(self.lib.pending_dir, "bad.exe")
    file_id = library.put(self.con, root="pending", path="bad.exe", size=1, uploader="mallory")
    self.con.commit()
    library.reject(self.lib, self.con, file_id)
    self.assertFalse(os.path.exists(os.path.join(self.lib.pending_dir, "bad.exe")))
    self.assertIsNone(library.get(self.con, file_id))

  def test_rejecting_only_touches_pending_uploads(self):
    self.write(self.lib.files_dir, "listed.zip")
    file_id = library.put(self.con, root="uploads", path="listed.zip", size=1)
    self.con.commit()
    library.reject(self.lib, self.con, file_id)
    self.assertTrue(os.path.exists(os.path.join(self.lib.files_dir, "listed.zip")))
    self.assertIsNotNone(library.get(self.con, file_id))

  def test_approving_across_volumes(self):
    # (no hard link and no rename between drives: a copy beside the target)
    self.write(self.lib.pending_dir, "far.zip", b"far")
    file_id = library.put(self.con, root="pending", path="far.zip", size=3, uploader="alice")
    self.con.commit()
    pending = os.path.normcase(self.lib.pending_dir)
    real_link, real_rename = os.link, os.rename

    def link(src, dst):
      if os.path.normcase(os.path.dirname(os.path.abspath(src))) == pending:
        raise OSError(18, "Invalid cross-device link")
      return real_link(src, dst)

    def rename(src, dst):
      if os.path.normcase(os.path.dirname(os.path.abspath(src))) == pending:
        raise OSError(18, "The system cannot move the file to a different disk drive")  # (EXDEV; WinError 17)
      return real_rename(src, dst)
    with mock.patch("os.link", link), mock.patch("os.rename", rename):
      self.assertIsNone(library.approve(self.lib, self.con, file_id, ".upload-"))
    with open(os.path.join(self.lib.files_dir, "far.zip"), "rb") as f:
      self.assertEqual(f.read(), b"far")
    self.assertEqual(os.listdir(self.lib.pending_dir), [])
    self.assertEqual([n for n in os.listdir(self.lib.files_dir) if n.startswith(".upload-")], [])
    self.assertEqual(library.get(self.con, file_id).root, "uploads")

  def test_approving_over_a_stale_row(self):
    # (a file of that name deleted by hand, its row not yet reconciled)
    library.put(self.con, root="uploads", path="up.zip", size=1, uploader="old")
    self.write(self.lib.pending_dir, "up.zip", b"new")
    file_id = library.put(self.con, root="pending", path="up.zip", size=3, uploader="alice")
    self.con.commit()
    self.assertIsNone(library.approve(self.lib, self.con, file_id, ".upload-"))
    self.assertEqual(self.catalogued("uploads"), {"up.zip": ("alice", 3)})

  def test_approving_or_rejecting_says_what_went_wrong_never_raises(self):
    self.write(self.lib.pending_dir, "busy.zip")
    file_id = library.put(self.con, root="pending", path="busy.zip", size=1, uploader="alice")
    self.con.commit()
    with mock.patch("os.remove", side_effect=PermissionError(13, "in use")):
      self.assertIn("could not be deleted", library.reject(self.lib, self.con, file_id))
    self.assertTrue(library.get(self.con, file_id).pending)
    with mock.patch.object(library, "move_new", side_effect=OSError(5, "denied")):
      self.assertIn("could not be moved", library.approve(self.lib, self.con, file_id, ".upload-"))
    self.assertTrue(library.get(self.con, file_id).pending)

  def old_meta(self):
    self.write(self.lib.files_dir, "old.zip")
    self.write(self.lib.files_dir, "plain.txt")
    meta = os.path.join(self.lib.files_dir, "meta.yaml")
    with open(meta, "w", encoding="utf-8") as f:
      f.write('old.zip:\n  keys: [game, dos]\n  description: "An old game"\ngone.zip:\n  keys: [x]\n')
    return meta, dataclasses.replace(self.lib, legacy_meta=meta)

  def test_the_old_meta_yaml_is_taken_once(self):
    meta, lib = self.old_meta()
    details = library.read_legacy_meta(lib)
    library.reconcile_uploads(lib, self.con, ".upload-")
    self.assertEqual(library.apply_legacy_meta(self.con, details), 1)
    entries = {e.name: e for e in library.fetch(self.con, library.all_ids(self.con))}
    self.assertEqual(set(entries), {"old.zip", "plain.txt"})  # (meta.yaml itself is never listed)
    self.assertEqual((entries["old.zip"].tags, entries["old.zip"].description), (("game", "dos"), "An old game"))
    library.retire_legacy_meta(lib, ".upload-")
    self.assertFalse(os.path.exists(meta))
    kept = os.path.join(os.path.dirname(lib.catalog), "meta.yaml.imported")
    self.assertTrue(os.path.isfile(kept))
    self.assertEqual(library.read_legacy_meta(lib), {})  # (once)
    # one put back by hand is applied, and kept again, not deleted
    shutil.copyfile(kept, meta)
    self.assertTrue(library.read_legacy_meta(lib))
    library.retire_legacy_meta(lib, ".upload-")
    self.assertFalse(os.path.exists(meta))
    self.assertEqual(len([n for n in os.listdir(os.path.dirname(lib.catalog)) if n.startswith("meta.yaml.imported")]), 2)

  def test_a_start_that_fails_keeps_the_old_meta_yaml(self):
    import file
    meta, lib = self.old_meta()
    with mock.patch.object(file, "_library", lambda: lib), \
         mock.patch.object(library, "reconcile_uploads", side_effect=sqlite3.OperationalError("database is locked")):
      file.startup()
    self.assertTrue(os.path.isfile(meta))  # (read again at the next start)
    with mock.patch.object(file, "_library", lambda: lib):
      file.startup()
    self.assertFalse(os.path.exists(meta))
    e = {e.name: e for e in library.fetch(self.con, library.all_ids(self.con))}["old.zip"]
    self.assertEqual(e.description, "An old game")

  def test_an_upload_approved_while_its_folder_is_read_is_not_forgotten(self):
    self.write(self.lib.pending_dir, "up.zip")
    file_id = library.put(self.con, root="pending", path="up.zip", size=1, uploader="alice", description="mine")
    self.con.commit()
    real_scandir = os.scandir
    pending = os.path.normcase(os.path.abspath(self.lib.pending_dir))

    def scandir(path):
      if os.path.normcase(os.path.abspath(path)) == pending:  # (the sysop approves it, just now)
        sysop = library.connect(self.lib)
        try:
          self.assertIsNone(library.approve(self.lib, sysop, file_id, ".upload-"))
        finally:
          sysop.close()
      return real_scandir(path)
    with mock.patch("os.scandir", scandir):
      library.reconcile_uploads(self.lib, self.con, ".upload-")
    e = library.get(self.con, file_id)
    self.assertEqual((e.root, e.uploader, e.description), ("uploads", "alice", "mine"))

  def test_a_move_whose_source_cant_be_removed_is_undone(self):
    self.write(self.lib.pending_dir, "busy.zip", b"data")
    source = os.path.join(self.lib.pending_dir, "busy.zip")
    target = os.path.join(self.lib.files_dir, "busy.zip")
    real_remove = os.remove

    def remove(path):
      if os.path.normcase(path) == os.path.normcase(source):
        raise PermissionError(32, "being downloaded", path)
      return real_remove(path)
    with mock.patch("os.remove", remove), self.assertRaises(PermissionError):
      library.move_new(source, target, ".upload-")
    self.assertTrue(os.path.isfile(source))
    self.assertFalse(os.path.exists(target))

  def test_an_upload_catalogued_while_the_folder_is_read_is_not_forgotten(self):
    # The BBS publishes an upload, then catalogues it. If that happens while
    # a reconcile reads the folder, the reconcile must not take the new row
    # for a file gone.
    real_scandir = os.scandir
    bbs = library.connect(self.lib)

    class Listing:
      def __init__(self, path):
        self.inner = real_scandir(path)

      def __enter__(self):
        return self.inner.__enter__()

      def __exit__(self, *exc):
        self.inner.__exit__(*exc)
        if os.path.normcase(os.path.abspath(self.inner_path)) == os.path.normcase(self.lib_dir):
          with open(os.path.join(self.lib_dir, "new.zip"), "wb") as f:  # (published after the listing)
            f.write(b"x")
          library.put(bbs, root="uploads", path="new.zip", size=1, uploader="alice")
          bbs.commit()
    def scandir(path):
      listing = Listing(path)
      listing.inner_path, listing.lib_dir = path, os.path.normcase(os.path.abspath(self.lib.files_dir))
      return listing
    try:
      with mock.patch("os.scandir", scandir):
        library.reconcile_uploads(self.lib, self.con, ".upload-")
    finally:
      bbs.close()
    self.assertEqual(self.catalogued("uploads"), {"new.zip": ("alice", 1)})

  def test_a_sysops_details_and_giving_them_back(self):
    file_id = library.put(self.con, root="pics", path="x/y.jpg", size=1, tags=["pic", "x"], source="pics",
                          description="an AI caption")
    self.con.commit()
    library.set_details(self.con, file_id, "my words", ["mine", "pic"])
    self.con.commit()
    e = library.get(self.con, file_id)
    self.assertEqual((e.description, e.tags, e.edited), ("my words", ("mine", "pic"), True))
    library.reset_details(self.con, file_id)
    self.con.commit()
    self.assertFalse(library.get(self.con, file_id).edited)

  def test_reserved_names(self):
    self.assertEqual(self.lib.reserved_names(), {"catalog", "pending", "zips", "repos"})
    beside = dataclasses.replace(self.lib, catalog=os.path.join(self.lib.files_dir, "cat.db"))
    self.assertEqual(beside.reserved_names(), {"cat.db", "cat.db-wal", "cat.db-shm", "cat.db-journal",
                                               "library_sync.lock", "pending", "zips", "repos"})
    self.write(self.lib.files_dir, "cat.db-wal")
    self.write(self.lib.files_dir, "library_sync.lock")
    self.assertEqual(library.reconcile_uploads(beside, self.con, ".upload-"), (0, 0))  # (never catalogued)


class Schema(unittest.TestCase):
  # The files table as schema 1 had it: what a catalogue made before
  # schema 2 holds.
  V1_FILES = """CREATE TABLE files (id INTEGER PRIMARY KEY, root TEXT NOT NULL, path TEXT NOT NULL,
    size INTEGER NOT NULL, mtime INTEGER NOT NULL DEFAULT 0, description TEXT NOT NULL DEFAULT '',
    uploader TEXT NOT NULL DEFAULT '', added INTEGER NOT NULL, source TEXT, source_key TEXT,
    fingerprint TEXT, tag_count INTEGER NOT NULL DEFAULT 0, name_norm TEXT NOT NULL, desc_norm TEXT NOT NULL,
    uploader_norm TEXT NOT NULL, UNIQUE (root, path))"""

  def test_an_older_catalogue_is_brought_up_to_date(self):
    top = tempfile.mkdtemp(prefix="library-")
    try:
      lib = make_library(top)
      os.remove(lib.catalog)
      con = sqlite3.connect(lib.catalog)
      con.executescript(self.V1_FILES + """;
        CREATE TABLE file_tags (file_id INTEGER NOT NULL REFERENCES files (id) ON DELETE CASCADE,
          tag_norm TEXT NOT NULL, tag TEXT NOT NULL, position INTEGER NOT NULL, PRIMARY KEY (file_id, tag_norm))
          WITHOUT ROWID;
        CREATE TABLE sync_state (source TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
          PRIMARY KEY (source, key)) WITHOUT ROWID;
        CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);""")
      con.execute("INSERT INTO settings (key, value) VALUES ('schema', '1')")
      con.execute("INSERT INTO files (root, path, size, added, name_norm, desc_norm, uploader_norm) "
                  "VALUES ('uploads', 'old.zip', 1, 0, 'old.zip', '', '')")
      con.commit()
      con.close()
      library.ensure_schema(lib)
      con = library.connect(lib)
      try:
        self.assertEqual(library._schema_version(con), library.SCHEMA_VERSION)
        e = library.fetch(con, library.all_ids(con))[0]
        self.assertEqual((e.name, e.edited), ("old.zip", False))
        library.ensure_schema(lib)  # (and once up to date, left be)
      finally:
        con.close()
    finally:
      shutil.rmtree(top, ignore_errors=True)


class Config(unittest.TestCase):
  def config(self, file_library):
    from config import Config as C, ConfigView
    return ConfigView(C({"files_dir": "files", "sysop_handle": "boss", "file_library": file_library}))

  def test_roots_come_from_linked_sources(self):
    lib = library.from_config(self.config({
      "upload_key": "uploader",
      "sources": {"pics": {"type": "gallery", "dir": "D:/pics"},
                  "sites": {"type": "websites", "dir": "D:/sites"},
                  "gh": {"type": "github", "user": "x"}}}))
    self.assertEqual(set(lib.roots), {"uploads", "pending", "zips", "pics"})
    self.assertEqual(lib.roots["pics"], os.path.abspath("D:/pics"))
    self.assertEqual((lib.upload_key, lib.sysop_handle), ("uploader", "boss"))
    self.assertEqual(set(lib.sources), {"pics", "sites", "gh"})

  def test_bad_sources_stop_it(self):
    for sources, says in (({"zips": {"type": "gallery", "dir": "x"}}, "can't be a source's name"),
                          ({"a b": {"type": "gallery", "dir": "x"}}, "can't be a source's name"),
                          ({"x": {"type": "nonesuch", "dir": "x"}}, "is not one of"),
                          ({"x": {"type": "samples"}}, "needs a dir")):
      with self.subTest(sources=sources):
        with self.assertRaises(ValueError) as cm:
          library.from_config(self.config({"sources": sources}))
        self.assertIn(says, str(cm.exception))

  def test_defaults(self):
    lib = library.from_config(self.config(None))
    self.assertEqual(lib.upload_key, library.DEFAULT_UPLOAD_KEY)
    self.assertEqual(lib.pending_dir, os.path.join(lib.files_dir, "pending"))
    self.assertEqual(lib.catalog, os.path.join(lib.files_dir, "catalog", "library.db"))


if __name__ == "__main__":
  unittest.main()
