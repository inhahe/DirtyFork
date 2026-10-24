"""library_sync.py: what each source lists, titles, and syncing the catalogue
(with 7-Zip and git where installed)."""
import os
import shutil
import sqlite3
import subprocess
import tempfile
import time
import unittest
import zipfile
from unittest import mock

import _setup  # noqa: F401  (paths, config)

import library
import library_sync as S
from config import Config, ConfigView
from test_library import make_library, make_v1_catalogue

SEVEN_ZIP = S.find_seven_zip()
GIT = shutil.which("git")


def conf(**values):
  """A source's config, as the BBS's config gives it (missing keys: null)."""
  return ConfigView(Config(values))


def write(path, data=b"x"):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "wb") as f:
    f.write(data.encode("utf-8") if isinstance(data, str) else data)
  return path


def page(title, body=""):
  return f"<html><head><title>{title}</title></head><body>{body}</body></html>"


class Scratch(unittest.TestCase):
  def setUp(self):
    self.top = tempfile.mkdtemp(prefix="library-sync-")

  def tearDown(self):
    shutil.rmtree(self.top, ignore_errors=True)

  def path(self, *parts):
    return os.path.join(self.top, *parts)


class Titles(Scratch):
  def test_page_titles(self):
    write(self.path("a.html"), page("  Tom &amp; Jerry\n  — the  end "))
    write(self.path("b.htm"), b'<meta charset="iso-8859-1"><title>Caf\xe9</title>')
    write(self.path("c.html"), "﻿<title>Wide</title>".encode("utf-16"))
    write(self.path("d.html"), "<p>no title</p>")
    self.assertEqual(S.html_title(self.path("a.html")), "Tom & Jerry — the end")
    self.assertEqual(S.html_title(self.path("b.htm")), "Café")
    self.assertEqual(S.html_title(self.path("c.html")), "Wide")
    self.assertEqual(S.html_title(self.path("d.html")), "")
    self.assertEqual(S.html_title(self.path("missing.html")), "")

  def test_through_httrack_to_the_sites_own_title(self):
    site = self.path("Mirror")
    write(os.path.join(site, "index.html"),
          '<title>List of available projects - HTTrack Website Copier</title><a href="Mirror/index.html">x</a>')
    write(os.path.join(site, "Mirror", "index.html"),
          '<title>Local index - HTTrack Website Copier</title><A HREF="www.example.org/index.html">x</A>')
    write(os.path.join(site, "Mirror", "www.example.org", "index.html"),
          '<META HTTP-EQUIV="Refresh" CONTENT="0; URL=home.html"><title>Page has moved</title>')
    write(os.path.join(site, "Mirror", "www.example.org", "home.html"), page("Example Home"))
    self.assertEqual(S.site_title(site), "Example Home")

  def test_a_dead_end_gives_the_mirrored_hosts(self):
    site = self.path("Chad")
    write(os.path.join(site, "index.html"), '<title>Local index - HTTrack</title><a href="x/index.html">x</a>')
    write(os.path.join(site, "x", "index.html"),
          '<META HTTP-EQUIV="Refresh" CONTENT="0; URL=index.html"><title>Page has moved</title>')
    os.makedirs(os.path.join(site, "wiki.example.org"))
    self.assertEqual(S.site_title(site), "wiki.example.org")

  def test_folders_without_an_index_page(self):
    write(self.path("one", "only", "Main.html"), page("Main page"))
    write(self.path("one", "only", "Other.html"), page("Other page"))
    self.assertEqual(S.site_title(self.path("one")), "Main page")  # (its one folder, its first page)
    write(self.path("two", "figures", "f.gif"))
    write(self.path("two", "poster", "index.htm"), page("The Poster"))
    self.assertEqual(S.site_title(self.path("two")), "The Poster")  # (an index page a folder down)
    write(self.path("three", "doc.docx"))
    self.assertEqual(S.site_title(self.path("three")), "")

  def test_video_titles(self):
    self.assertEqual(S.video_title("A： B ｜ C？ [siXY6QNn_AQ].webm"), "A: B | C?")
    self.assertEqual(S.video_title("80⧸20 and Beyond [TsnSssZuNSs].mp4"), "80/20 and Beyond")
    self.assertEqual(S.video_title("no id here.mkv"), "no id here")

  def test_module_titles(self):
    it = b"IMPM" + b"Song of IT\0\0".ljust(26, b"\0") + b"\0" * 100
    xm = b"Extended Module: " + b"XM Song".ljust(20, b" ") + b"\x1a" + b"\0" * 100
    s3m = b"S3M Song".ljust(28, b"\0") + b"\x1a\x10" + b"\0" * 14 + b"SCRM" + b"\0" * 100
    mod = b"mod song".ljust(20, b"\0") + b"\0" * 1100
    mtm = b"MTM\x10" + b"MTM title".ljust(20, b"\0") + b"\0" * 100
    self.assertEqual(S.module_title(it, "it"), "Song of IT")
    self.assertEqual(S.module_title(it, "mptm"), "Song of IT")
    self.assertEqual(S.module_title(xm, "xm"), "XM Song")
    self.assertEqual(S.module_title(s3m, "s3m"), "S3M Song")
    self.assertEqual(S.module_title(mod, "mod"), "mod song")
    self.assertEqual(S.module_title(mtm, "mtm"), "MTM title")
    self.assertEqual(S.module_title(xm, "it"), "")      # (not what it says it is)
    self.assertEqual(S.module_title(b"\x01\x02", "mod"), "")
    self.assertEqual(S.module_title(b"IMPM\x07bell\x00", "it"), "bell")

  def test_module_zips(self):
    single = self.path("song.xm.zip")
    with zipfile.ZipFile(single, "w") as z:
      z.writestr("song.xm", b"Extended Module: " + b"Zipped".ljust(20) + b"\0" * 300)
      z.writestr("song.xm.info", b"about it")
    self.assertEqual(S.mod_description(single, "xm"), "Zipped")
    bundle = self.path("A0.zip")
    with zipfile.ZipFile(bundle, "w") as z:
      for n in ("a.mod.zip", "b.xm.zip"):
        z.writestr(n, b"zip")
    self.assertEqual(S.bundle_description(bundle), "2 modules: a.mod, b.xm")
    write(self.path("bad.zip"), b"not a zip")
    self.assertEqual(S.mod_description(self.path("bad.zip"), "xm"), "")
    self.assertEqual(S.bundle_description(self.path("bad.zip")), "")

  def test_thumbsup_keys_match_nodes(self):
    # computed by thumbsup2's hashFile arithmetic in Node (sec * 1e3 + nsec / 1e6)
    for name, size, ns, key in (
        ("nebula.jpg", 12345, 1471984068_000000000, "4045af622637d5b871bd84ffcf920b4508f28530"),
        ("ünïcode – x.png", 1, 1792589175_742070400, "9ffcb813dcd18ec0db8a93f71018098804d3f6b7"),
        ("a.gif", 7, 1735959330_705230600, "5aecbfbf36f9886138a67bf92c587edc895e2127"),
        ("b.jpg", 99, 1700000000_000000001, "fdbca7b365432ade1429f68a1ac18a854e1baa38")):
      self.assertEqual(S.thumbsup_key(name, size, ns), key, name)


class Discovery(Scratch):
  """What each handler yields, without building anything."""

  def items(self, handler, c, stats=None):
    ctx = S.Context(lib=None, con=None)
    return {i.key: i for i in handler(ctx, "src", c, stats or S.Stats())}

  def test_websites(self):
    root = self.path("websites")
    write(os.path.join(root, "index.html"), "<title>List of available projects - HTTrack</title>")  # (left out)
    write(os.path.join(root, "backblue.gif"))
    write(os.path.join(root, "Loose page.htm"), page("A loose page"))
    write(os.path.join(root, "Loose page_files", "img.png"))
    write(os.path.join(root, "Site A", "index.html"), page("Site A"))
    write(os.path.join(root, "Group", "inner.org", "index.html"), page("Inner"))
    write(os.path.join(root, "Group", "notes.docs", "x.docx"))
    write(os.path.join(root, "Group", "blog.html"), page("Blog"))
    write(os.path.join(root, "Videos", "v.webm"))
    os.makedirs(os.path.join(root, "Empty"))
    items = self.items(S.handle_websites, conf(dir=root, containers=["Group"], skip=["Videos"]))
    self.assertEqual(set(items), {"Loose page.htm", "Site A", "Group/inner.org", "Group/notes.docs",
                                  "Group/blog.html"})
    self.assertEqual(items["Site A"].path, "src/Site A.zip")
    self.assertEqual(items["Site A"].tags, ["web", "website"])
    self.assertEqual(items["Group/inner.org"].path, "src/Group - inner.org.zip")
    self.assertEqual(items["Group/blog.html"].path, "src/Group - blog.zip")
    self.assertEqual(items["Group/blog.html"].tags, ["web", "webpage"])
    self.assertEqual(items["Loose page.htm"].describe(), "A loose page")
    self.assertEqual(items["Group/inner.org"].describe(), "Inner")

  def test_webpages(self):
    root = self.path("pages")
    write(os.path.join(root, "One.html"), page("Page one"))
    write(os.path.join(root, "One_files", "a.css"))
    write(os.path.join(root, "One_files.2", "stale.css"))            # (a copy: no page of its own)
    write(os.path.join(root, "Twin.htm"), page("htm"))
    write(os.path.join(root, "Twin.html"), page("html"))
    write(os.path.join(root, "reviews", "Film.html"), page("Film review"))
    write(os.path.join(root, "reviews", "Film_files", "p.jpg"))
    write(os.path.join(root, "mirror", "index.html"), page("A mirrored site"))
    write(os.path.join(root, "mirror", "sub", "x.html"), page("x"))
    write(os.path.join(root, "poster", "html", "fig1.html"), page("fig"))  # (pages only below: a site)
    write(os.path.join(root, "poster", "figures", "f.gif"))
    write(os.path.join(root, "pics only", "a.jpg"))
    items = self.items(S.handle_webpages, conf(dir=root))
    self.assertEqual(set(items), {"One.html", "Twin.htm", "Twin.html", "reviews/Film.html", "mirror", "poster"})
    self.assertEqual(items["One.html"].path, "src/One.zip")
    self.assertEqual(items["Twin.htm"].path, "src/Twin.htm.zip")
    self.assertEqual(items["Twin.html"].path, "src/Twin.html.zip")
    self.assertEqual(items["reviews/Film.html"].path, "src/reviews/Film.zip")
    self.assertEqual(items["reviews/Film.html"].tags, ["web", "webpage"])
    self.assertEqual(items["mirror"].tags, ["web", "website"])
    self.assertEqual(items["mirror"].describe(), "A mirrored site")
    with_tags = self.items(S.handle_webpages, conf(dir=root, hierarchy_tags=True))
    self.assertEqual(with_tags["reviews/Film.html"].tags, ["reviews", "web", "webpage"])

  def test_folder_tags_are_the_folders_a_page_or_site_is_in(self):
    root = self.path("pages")
    write(os.path.join(root, "Top.html"), page("top"))
    write(os.path.join(root, "reviews", "Film.html"), page("film"))
    write(os.path.join(root, "reviews", "old site", "index.html"), page("a site"))
    write(os.path.join(root, "a site", "index.html"), page("another"))
    items = self.items(S.handle_webpages, conf(dir=root, hierarchy_tags=True))
    self.assertEqual({k: i.tags for k, i in items.items()}, {
      "Top.html": ["web", "webpage"],
      "reviews/Film.html": ["reviews", "web", "webpage"],
      "reviews/old site": ["reviews", "web", "website"],  # (not its own name: it isn't in that folder)
      "a site": ["web", "website"]})

  def test_a_page_changing_or_its_files_changing_is_a_change(self):
    root = self.path("pages")
    write(os.path.join(root, "One.html"), page("Page one"))
    write(os.path.join(root, "One_files", "a.css"), "a")
    before = self.items(S.handle_webpages, conf(dir=root))["One.html"].fingerprint
    self.assertEqual(self.items(S.handle_webpages, conf(dir=root))["One.html"].fingerprint, before)
    write(os.path.join(root, "One_files", "b.css"), "b")
    self.assertNotEqual(self.items(S.handle_webpages, conf(dir=root))["One.html"].fingerprint, before)

  def test_samples_and_instruments(self):
    root = self.path("modarchive_")
    for rel in ("samples/kick.flac", "samples/kick.flac.txt", "samples/song - ogg sample.ogg",
                "instr/FM bass.s3i", "instr/FM bass.sbi", "instr/FM bass.txt",
                "other/kiarchive/CATEGORY/BASS/acbs01.xi", "other/pack/readme.txt", "other/pack/file_id.diz",
                "other/pack/0index"):
      write(os.path.join(root, *rel.split("/")))
    stats = S.Stats()
    items = self.items(S.handle_samples, conf(dir=root, hierarchy_tags=True), stats)
    self.assertEqual({k: i.tags for k, i in items.items()}, {
      "samples/kick.flac": ["sample", "samples"],
      "samples/song - ogg sample.ogg": ["sample", "samples"],
      "instr/FM bass.s3i": ["instrument", "s3i", "instr"],
      "instr/FM bass.sbi": ["instrument", "sbi", "instr"],
      "other/kiarchive/CATEGORY/BASS/acbs01.xi": ["sample", "other", "kiarchive", "CATEGORY", "BASS"]})
    self.assertEqual(stats.skipped, {"txt": 3, "diz": 1, "": 1})
    self.assertEqual(items["samples/kick.flac"].root, "src")
    flat = self.items(S.handle_samples, conf(dir=root))
    self.assertEqual(flat["samples/kick.flac"].tags, ["sample"])

  def test_gallery(self):
    root = self.path("gallery")
    pic = write(os.path.join(root, "art", "fractals", "f.jpg"), "jpg")
    write(os.path.join(root, "art", "clip.mp4"))
    write(os.path.join(root, "top.png"))
    write(os.path.join(root, "Thumbs.db"))
    captions = self.path("thumbsup.db")
    con = sqlite3.connect(captions)
    st = os.stat(pic)
    con.execute("CREATE TABLE ai_descriptions (hash TEXT PRIMARY KEY, caption TEXT, ocr TEXT)")
    con.execute("INSERT INTO ai_descriptions VALUES (?, ?, '')",
                (S.thumbsup_key("f.jpg", st.st_size, st.st_mtime_ns), "a fractal"))
    con.commit()
    con.close()
    items = self.items(S.handle_gallery, conf(dir=root, captions=captions))
    self.assertEqual({k: (i.tags, i.description) for k, i in items.items()}, {
      "art/fractals/f.jpg": (["pic", "art", "fractals"], "a fractal"),
      "art/clip.mp4": (["video", "art"], ""),
      "top.png": (["pic"], "")})

  def test_videos_and_mods(self):
    root = self.path("v")
    write(os.path.join(root, "A： B [abcdefghijk].webm"))
    write(os.path.join(root, "notes.txt"))
    items = self.items(S.handle_videos, conf(dir=root, tags=["youtube"]))
    self.assertEqual({k: (i.tags, i.description) for k, i in items.items()},
                     {"A： B [abcdefghijk].webm": (["video", "youtube"], "A: B")})
    mods = self.path("mods")
    with zipfile.ZipFile(write(os.path.join(mods, "x.it (modarchive_2019_additions).zip")), "w") as z:
      z.writestr("x.it", b"IMPM" + b"Title".ljust(26, b"\0"))
    with zipfile.ZipFile(write(os.path.join(mods, "A0.zip")), "w") as z:
      z.writestr("a.mod.zip", b"zip")
    write(os.path.join(mods, "download.py"))
    items = self.items(S.handle_mods, conf(dir=mods))
    self.assertEqual({k: (i.tags, i.describe()) for k, i in items.items()},
                     {"x.it (modarchive_2019_additions).zip": (["mod", "it"], "Title"),
                      "A0.zip": (["mod", "collection"], "1 modules: a.mod")})

  def test_a_missing_folder_is_a_source_error(self):
    for handler in (S.handle_websites, S.handle_webpages, S.handle_gallery, S.handle_samples, S.handle_mods):
      with self.assertRaises(S.SourceError):
        self.items(handler, conf(dir=self.path("not mounted")))


class Syncing(Scratch):
  """sync_source against a scratch catalogue."""

  def setUp(self):
    super().setUp()
    self.lib = make_library(self.path("bbs"))
    self.lib.roots["src"] = self.path("data")
    self.con = S.open_catalogue(self.lib)
    self.ctx = S.Context(lib=self.lib, con=self.con, seven_zip=SEVEN_ZIP, git=GIT)

  def tearDown(self):
    self.con.close()
    super().tearDown()

  def listed(self, source="src"):
    return {k: (e.tags, e.size, e.description) for k, e in library.source_entries(self.con, source).items()}

  def test_linked_files(self):
    data = self.path("data")
    write(os.path.join(data, "a", "one.flac"), "1")
    write(os.path.join(data, "two.flac"), "22")
    c = conf(type="samples", dir=data, hierarchy_tags=True)
    stats = S.sync_source(self.ctx, "src", c)
    self.assertEqual((stats.new, stats.changed, stats.removed), (2, 0, 0))
    self.assertEqual(self.listed(), {"a/one.flac": (("sample", "a"), 1, ""), "two.flac": (("sample",), 2, "")})
    self.assertEqual(library.get(self.con, library.source_entries(self.con, "src")["two.flac"].id).uploader,
                     "Sysop")
    stats = S.sync_source(self.ctx, "src", c)
    self.assertEqual((stats.new, stats.changed, stats.updated, stats.removed), (0, 0, 0, 0))
    write(os.path.join(data, "two.flac"), "333")
    os.remove(os.path.join(data, "a", "one.flac"))
    stats = S.sync_source(self.ctx, "src", c)
    self.assertEqual((stats.new, stats.changed, stats.removed), (0, 1, 1))
    self.assertEqual(self.listed(), {"two.flac": (("sample",), 3, "")})
    stats = S.sync_source(self.ctx, "src", conf(type="samples", dir=data, tags=["extra"]))
    self.assertEqual(stats.updated, 1)
    self.assertEqual(self.listed(), {"two.flac": (("sample", "extra"), 3, "")})

  def test_a_source_that_cant_be_read_forgets_nothing(self):
    data = self.path("data")
    write(os.path.join(data, "two.flac"), "22")
    S.sync_source(self.ctx, "src", conf(type="samples", dir=data))
    shutil.rmtree(data)
    with self.assertRaises(S.SourceError):
      S.sync_source(self.ctx, "src", conf(type="samples", dir=data))
    self.con.rollback()
    self.assertEqual(set(self.listed()), {"two.flac"})

  def test_the_bbs_can_write_while_a_zip_is_made(self):
    # The BBS catalogues an upload while the sync zips: the sync must not
    # hold the write lock across a build (the BBS waits only so long).
    pages = self.path("pages")
    write(os.path.join(pages, "A.html"), page("a"))
    write(os.path.join(pages, "B.html"), page("b"))
    writes = []

    def zip_files(ctx, final, cwd, names):
      bbs = sqlite3.connect(self.lib.catalog, timeout=0.2)
      try:
        bbs.execute("INSERT INTO settings (key, value) VALUES (?, 'x')", (names[0],))
        bbs.commit()
        writes.append(names[0])
      except sqlite3.OperationalError as exc:
        writes.append(f"{names[0]}: {exc}")
      finally:
        bbs.close()
      write(final, "zip")
    with mock.patch.object(S, "zip_files", zip_files):
      stats = S.sync_source(self.ctx, "pg", conf(type="webpages", dir=pages))
    self.assertEqual((stats.new, stats.failed), (2, 0))
    self.assertEqual(writes, ["A.html", "B.html"])  # (B's while A was catalogued already)

  def test_the_bbs_writing_throughout_a_sync_fails_neither(self):
    import threading
    data = self.path("data")
    for i in range(3000):
      write(os.path.join(data, f"{i:04}.flac"), "x")
    stop, failures, done = threading.Event(), [], [0]

    def bbs():  # catalogues uploads as fast as it can, as the BBS would (its own connection, 30 s wait)
      con = library.connect(self.lib)
      try:
        while not stop.is_set():
          try:
            library.put(con, root="uploads", path=f"up{done[0]}.zip", size=1, uploader="alice")
            con.commit()
            done[0] += 1
          except sqlite3.OperationalError as exc:
            con.rollback()
            failures.append(str(exc))
      finally:
        con.close()
    t = threading.Thread(target=bbs)
    t.start()
    try:
      stats = S.sync_source(self.ctx, "src", conf(type="samples", dir=data))
    finally:
      stop.set()
      t.join()
    self.assertEqual((stats.new, stats.failed), (3000, 0))
    self.assertEqual(failures, [])
    self.assertGreater(done[0], 0)

  def test_a_sysops_details_outlast_the_sync(self):
    data = self.path("data")
    path = write(os.path.join(data, "a.flac"), "1")
    c = conf(type="samples", dir=data)
    S.sync_source(self.ctx, "src", c)
    file_id = library.source_entries(self.con, "src")["a.flac"].id
    library.set_details(self.con, file_id, "a kick drum", ["drums"], by_sysop=True)
    self.con.commit()
    S.sync_source(self.ctx, "src", c)                       # unchanged
    S.sync_source(self.ctx, "src", conf(type="samples", dir=data, tags=["new"]))  # its tags would change
    write(path, "22")
    S.sync_source(self.ctx, "src", c)                       # the file changed
    e = library.get(self.con, file_id)
    self.assertEqual((e.description, e.tags, e.edited, e.size), ("a kick drum", ("drums",), library.EDITED, 2))
    library.reset_details(self.con, file_id)
    self.con.commit()
    S.sync_source(self.ctx, "src", c)
    self.assertEqual(self.listed(), {"a.flac": (("sample",), 2, "")})

  def pages(self, *names):
    """A webpages source "pg" of these pages (each titled by its name);
    sync() syncs it, its zips made by zip_files (default: an empty file)."""
    pages = self.path("pages")
    for name in names:
      write(os.path.join(pages, name), page(f"title of {name}"))

    def sync(zip_files=None, **more):
      def make(ctx, final, cwd, names):
        if zip_files:
          zip_files(names)
        write(final, "zip")
      with mock.patch.object(S, "zip_files", make):
        return S.sync_source(self.ctx, "pg", conf(type="webpages", dir=pages, **more))
    return pages, sync

  def test_details_given_back_are_described_afresh(self):
    # (a page's description is its title, read only when the page is new
    # or changed: given back, it is read again though the page is not)
    pages, sync = self.pages("Film.html")
    sync()
    file_id = library.source_entries(self.con, "pg")["Film.html"].id
    library.set_details(self.con, file_id, "my notes", ["mine"], by_sysop=True)
    library.reset_details(self.con, file_id)
    self.con.commit()
    stats = sync()
    self.assertEqual((stats.changed, stats.updated), (0, 1))
    e = library.get(self.con, file_id)
    self.assertEqual((e.description, e.tags, e.edited), ("title of Film.html", ("web", "webpage"), library.SYNCED))
    self.assertEqual(sync().updated, 0)  # (and then left be)

  def test_details_given_back_without_a_caption_to_hand(self):
    pics = self.path("data")  # (the root of source "src")
    path = write(os.path.join(pics, "a.jpg"))
    captions = self.path("thumbsup.db")
    c = conf(type="gallery", dir=pics, captions=captions, tags=["more"])
    S.sync_source(self.ctx, "src", c)  # (no captions yet: none to read)
    file_id = library.source_entries(self.con, "src")["a.jpg"].id
    library.set_details(self.con, file_id, "my words", ["mine"], by_sysop=True)
    library.reset_details(self.con, file_id)
    self.con.commit()
    S.sync_source(self.ctx, "src", c)  # (the tags are the sync's again; the description, unknown, kept)
    e = library.get(self.con, file_id)
    self.assertEqual((e.description, e.tags, e.edited), ("my words", ("pic", "more"), library.SYNCED))
    con = sqlite3.connect(captions)
    st = os.stat(path)
    con.execute("CREATE TABLE ai_descriptions (hash TEXT PRIMARY KEY, caption TEXT, ocr TEXT)")
    con.execute("INSERT INTO ai_descriptions VALUES (?, 'a picture', '')",
                (S.thumbsup_key("a.jpg", st.st_size, st.st_mtime_ns),))
    con.commit()
    con.close()
    S.sync_source(self.ctx, "src", c)  # (and the caption, once it can be read)
    self.assertEqual(library.get(self.con, file_id).description, "a picture")

  def test_unchanged_tags_are_not_written_again(self):
    data = self.path("data")
    write(os.path.join(data, "a.flac"))
    S.sync_source(self.ctx, "src", conf(type="samples", dir=data))
    file_id = library.source_entries(self.con, "src")["a.flac"].id
    with mock.patch.object(library, "set_tags", wraps=library.set_tags) as set_tags:
      self.con.execute("UPDATE files SET description = 'stale' WHERE id = ?", (file_id,))  # (redescribed)
      self.con.commit()
      self.assertEqual(S.sync_source(self.ctx, "src", conf(type="samples", dir=data)).updated, 1)
    set_tags.assert_not_called()
    self.assertEqual(library.get(self.con, file_id).description, "")

  def test_a_sysop_editing_during_the_batch(self):
    # The sync reads a batch's entries once, then releases the write lock
    # for every zip it makes: a sysop's edits meanwhile must hold.
    pages, sync = self.pages("A.html", "B.html", "C.html", "D.html")
    sync()
    ids = {k: e.id for k, e in library.source_entries(self.con, "pg").items()}
    library.set_details(self.con, ids["D.html"], "mine", ["mine"], by_sysop=True)
    self.con.commit()
    write(os.path.join(pages, "A.html"), page("A, changed"))  # (A is zipped again: B, C and D come after)
    write(os.path.join(pages, "C.html"), page("C, changed"))
    write(os.path.join(pages, "D.html"), page("D, changed"))

    def sysop(names):
      if names[0] != "A.html":
        return
      bbs = library.connect(self.lib)
      try:
        library.set_details(bbs, ids["B.html"], "B, mine", ["mine"], by_sysop=True)  # (B: only retagged)
        library.set_details(bbs, ids["C.html"], "C, mine", ["mine"], by_sysop=True)  # (C: changed)
        library.reset_details(bbs, ids["D.html"])                                     # (D: changed)
        bbs.commit()
      finally:
        bbs.close()
    sync(sysop, tags=["more"])
    got = {k: (e.description, e.tags, e.edited) for k, e in library.source_entries(self.con, "pg").items()}
    self.assertEqual(got["B.html"], ("B, mine", ("mine",), library.EDITED))
    self.assertEqual(got["C.html"], ("C, mine", ("mine",), library.EDITED))
    self.assertEqual(got["D.html"], ("D, changed", ("web", "webpage", "more"), library.SYNCED))

  def test_a_renamed_zip_is_the_same_entry(self):
    pages, sync = self.pages("x.htm", "x.html")  # (x.htm.zip and x.html.zip)
    sync()
    file_id = library.source_entries(self.con, "pg")["x.htm"].id
    library.set_details(self.con, file_id, "mine", ["mine"], by_sysop=True)
    self.con.commit()
    os.remove(os.path.join(pages, "x.html"))  # (x.htm is x.zip now)
    sync()
    e = library.get(self.con, file_id)
    self.assertEqual((e.path, e.description), ("pg/x.zip", "mine"))
    self.assertEqual(sorted(os.listdir(os.path.join(self.lib.zips_dir, "pg"))), ["x.zip"])

  def test_a_page_renamed_in_case_keeps_its_zip(self):
    # (on Windows X.zip is the forgotten x.zip: deleting that would delete it)
    pages, sync = self.pages("x.html")
    sync()
    os.rename(os.path.join(pages, "x.html"), os.path.join(pages, "X.html"))
    stats = sync()
    self.assertEqual((stats.new, stats.removed), (1, 1))
    e = library.source_entries(self.con, "pg")["X.html"]
    self.assertIsNotNone(library.resolve(self.lib, e), e.path)  # (None: no such file)

  def test_the_handler_starts_without_the_write_lock(self):
    # (fetching repositories, fingerprinting sites: slow, and the BBS must
    # be able to catalogue an upload meanwhile)
    data = self.path("data")
    write(os.path.join(data, "a.flac"))
    writes = []
    real = S.HANDLERS["samples"]

    def slow_start(ctx, source, conf, stats):
      bbs = sqlite3.connect(self.lib.catalog, timeout=0.2)
      try:
        bbs.execute("INSERT INTO settings (key, value) VALUES ('bbs', 'x')")
        bbs.commit()
        writes.append("ok")
      except sqlite3.OperationalError as exc:
        writes.append(str(exc))
      finally:
        bbs.close()
      yield from real(ctx, source, conf, stats)
    with mock.patch.dict(S.HANDLERS, {"samples": slow_start}):
      S.sync_source(self.ctx, "src", conf(type="samples", dir=data))
    self.assertEqual(writes, ["ok"])

  def test_a_folder_that_cant_be_read_makes_it_forget_nothing(self):
    data = self.path("data")
    write(os.path.join(data, "a", "one.flac"))
    write(os.path.join(data, "b", "two.flac"))
    c = conf(type="samples", dir=data)
    S.sync_source(self.ctx, "src", c)
    real = os.scandir

    def scandir(path):
      if os.path.basename(os.path.normpath(path)) == "a":
        raise PermissionError(13, "Access is denied", path)
      return real(path)
    os.remove(os.path.join(data, "b", "two.flac"))
    with mock.patch("os.scandir", scandir):
      stats = S.sync_source(self.ctx, "src", c)
    self.assertTrue(stats.incomplete)
    self.assertEqual((stats.removed, set(self.listed())), (0, {"a/one.flac", "b/two.flac"}))
    stats = S.sync_source(self.ctx, "src", c)  # (readable again)
    self.assertEqual((stats.removed, set(self.listed())), (1, {"a/one.flac"}))

  @unittest.skipUnless(os.name == "nt", "file attributes")
  def test_hidden_and_system_files_are_left_out(self):
    import ctypes
    data = self.path("data")
    write(os.path.join(data, "seen.flac"))
    hidden = write(os.path.join(data, "Thumbs.flac"))
    write(os.path.join(data, "$RECYCLE.BIN", "$R123.flac"))
    ctypes.windll.kernel32.SetFileAttributesW(hidden, 0x2 | 0x4)  # (hidden, system)
    ctypes.windll.kernel32.SetFileAttributesW(os.path.join(data, "$RECYCLE.BIN"), 0x10 | 0x2 | 0x4)
    S.sync_source(self.ctx, "src", conf(type="samples", dir=data))
    self.assertEqual(set(self.listed()), {"seen.flac"})

  def test_unreadable_captions_keep_those_catalogued(self):
    pics = self.path("data")
    pic = write(os.path.join(pics, "p.jpg"), "jpg")
    captions = self.path("thumbsup.db")
    con = sqlite3.connect(captions)
    st = os.stat(pic)
    con.execute("CREATE TABLE ai_descriptions (hash TEXT PRIMARY KEY, caption TEXT, ocr TEXT)")
    con.execute("INSERT INTO ai_descriptions VALUES (?, 'a picture', '')",
                (S.thumbsup_key("p.jpg", st.st_size, st.st_mtime_ns),))
    con.commit()
    con.close()
    S.sync_source(self.ctx, "src", conf(type="gallery", dir=pics, captions=captions))
    self.assertEqual(self.listed()["p.jpg"][2], "a picture")
    stats = S.sync_source(self.ctx, "src", conf(type="gallery", dir=pics, captions=self.path("gone.db")))
    self.assertEqual((stats.updated, self.listed()["p.jpg"][2]), (0, "a picture"))

  def test_a_damaged_module_zip_has_no_description_but_is_listed(self):
    mods = self.path("data")
    path = os.path.join(mods, "bad.xm.zip")
    os.makedirs(mods)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
      z.writestr("bad.xm", b"Extended Module: " + os.urandom(4000))
    with open(path, "rb") as f:
      data = bytearray(f.read())
    data[40:80] = b"\xff" * 40  # (the deflate stream, just after the member's header)
    write(path, bytes(data))
    self.assertEqual(S.mod_description(path, "xm"), "")
    stats = S.sync_source(self.ctx, "src", conf(type="mods", dir=mods))
    self.assertEqual((stats.new, stats.failed), (1, 0))

  def test_a_source_gone_from_the_config_is_forgotten(self):
    import dataclasses
    data = self.path("data")
    write(os.path.join(data, "a.flac"))
    S.sync_source(self.ctx, "src", conf(type="samples", dir=data))
    kept = dataclasses.replace(self.lib, sources={"src": conf(type="samples", dir=data)})
    S.forget_unconfigured(S.Context(lib=kept, con=self.con))
    self.assertEqual(set(self.listed()), {"a.flac"})
    S.forget_unconfigured(S.Context(lib=self.lib, con=self.con, dry_run=True))
    self.assertEqual(set(self.listed()), {"a.flac"})
    S.forget_unconfigured(S.Context(lib=self.lib, con=self.con))  # (no sources configured)
    self.assertEqual(self.listed(), {})
    self.assertIsNone(library.get_state(self.con, "src", "type"))

  def test_a_source_changed_from_linked_to_zipped_forgets_its_old_entries(self):
    data, pages = self.path("data"), self.path("pages")
    write(os.path.join(data, "a.flac"))
    os.makedirs(pages)
    S.sync_source(self.ctx, "src", conf(type="samples", dir=data))
    self.assertEqual(set(self.listed()), {"a.flac"})
    S.sync_source(self.ctx, "src", conf(type="webpages", dir=pages))  # (the same name, now zipped)
    self.assertEqual(self.listed(), {})
    self.assertEqual(library.get_state(self.con, "src", "type"), "webpages")

  @unittest.skipUnless(SEVEN_ZIP, "7-Zip is not installed")
  def test_a_zip_source_gone_from_the_config_takes_its_zips(self):
    pages = self.path("pages")
    write(os.path.join(pages, "P.html"), page("p"))
    S.sync_source(self.ctx, "pg", conf(type="webpages", dir=pages))
    zip_path = library.resolve(self.lib, library.source_entries(self.con, "pg")["P.html"])
    self.assertTrue(os.path.isfile(zip_path))
    S.forget_unconfigured(self.ctx)
    self.assertEqual(library.source_entries(self.con, "pg"), {})
    self.assertFalse(os.path.exists(os.path.join(self.lib.zips_dir, "pg")))

  def test_zip_names_never_clash(self):
    root = self.path("websites")
    write(os.path.join(root, "A - B", "index.html"), page("top"))   # a site called "A - B" ...
    write(os.path.join(root, "A", "B", "index.html"), page("inner"))  # ... and container A's site B
    items = {i.key: i for i in S.handle_websites(S.Context(lib=None, con=None), "w",
                                                  conf(dir=root, containers=["A"]), S.Stats())}
    self.assertEqual(sorted(i.path for i in items.values()), ["w/A - B (2).zip", "w/A - B.zip"])
    pages = self.path("pages")
    write(os.path.join(pages, "x.htm"), page("a page"))                     # stem "x" ...
    write(os.path.join(pages, "x", "index.html"), page("a site"))           # ... so "x (website).zip" ...
    write(os.path.join(pages, "x (website)", "index.html"), page("another"))  # ... which this one is too
    items = {i.key: i for i in S.handle_webpages(S.Context(lib=None, con=None), "p", conf(dir=pages), S.Stats())}
    paths = sorted(i.path.lower() for i in items.values())
    self.assertEqual(paths, ["p/x (website) (2).zip", "p/x (website).zip", "p/x.htm.zip"])

  def test_a_dry_run_changes_nothing(self):
    data = self.path("data")
    write(os.path.join(data, "two.flac"), "22")
    self.ctx.dry_run = True
    stats = S.sync_source(self.ctx, "src", conf(type="samples", dir=data))
    self.assertEqual(stats.new, 1)
    self.assertEqual(self.listed(), {})

  @unittest.skipUnless(SEVEN_ZIP, "7-Zip is not installed")
  def test_websites_are_zipped_and_kept_up_to_date(self):
    sites = self.path("sites")
    write(os.path.join(sites, "Site", "index.html"), page("The Site"))
    write(os.path.join(sites, "Site", "old.html"), page("old"))
    write(os.path.join(sites, "Site", "hts-cache", "new.zip"), "cache")
    write(os.path.join(sites, "Site", "hts-log.txt"), "log")
    write(os.path.join(sites, "Page.html"), page("A page"))
    write(os.path.join(sites, "Page_files", "s.css"), "css")
    c = conf(type="websites", dir=sites)
    stats = S.sync_source(self.ctx, "web", c)
    self.assertEqual((stats.new, stats.failed), (2, 0))
    entries = library.source_entries(self.con, "web")
    self.assertEqual(entries["Site"].description, "The Site")
    site_zip = library.resolve(self.lib, entries["Site"])
    with zipfile.ZipFile(site_zip) as z:
      self.assertEqual(sorted(n for n in z.namelist() if not n.endswith("/")), ["Site/index.html", "Site/old.html"])
    with zipfile.ZipFile(library.resolve(self.lib, entries["Page.html"])) as z:
      self.assertEqual(sorted(n for n in z.namelist() if not n.endswith("/")), ["Page.html", "Page_files/s.css"])
    self.assertEqual(entries["Site"].size, os.path.getsize(site_zip))

    os.remove(os.path.join(sites, "Site", "old.html"))
    write(os.path.join(sites, "Site", "new.html"), page("new"))
    stats = S.sync_source(self.ctx, "web", c)
    self.assertEqual((stats.changed, stats.failed), (1, 0))
    with zipfile.ZipFile(site_zip) as z:
      self.assertEqual(sorted(n for n in z.namelist() if not n.endswith("/")), ["Site/index.html", "Site/new.html"])
    self.assertEqual([n for n in os.listdir(os.path.dirname(site_zip)) if S.TEMP_SUFFIX in n], [])

    write(os.path.join(self.lib.zips_dir, "web", "stray.zip"), "left by a crash")
    shutil.rmtree(os.path.join(sites, "Site"))
    stats = S.sync_source(self.ctx, "web", c)
    self.assertEqual(stats.removed, 1)
    self.assertFalse(os.path.exists(site_zip))
    self.assertFalse(os.path.exists(os.path.join(self.lib.zips_dir, "web", "stray.zip")))
    self.assertEqual(set(library.source_entries(self.con, "web")), {"Page.html"})

  @unittest.skipUnless(SEVEN_ZIP, "7-Zip is not installed")
  def test_a_zip_being_downloaded_is_kept_and_tried_again(self):
    pages = self.path("pages")
    write(os.path.join(pages, "P.html"), page("one"))
    c = conf(type="webpages", dir=pages)
    S.sync_source(self.ctx, "pg", c)
    entry = library.source_entries(self.con, "pg")["P.html"]
    write(os.path.join(pages, "P.html"), page("two"))
    with mock.patch.object(S, "put_in_place", side_effect=PermissionError("in use")):
      stats = S.sync_source(self.ctx, "pg", c)
    self.assertEqual(stats.failed, 1)
    self.assertEqual(library.source_entries(self.con, "pg")["P.html"].fingerprint, entry.fingerprint)
    stats = S.sync_source(self.ctx, "pg", c)
    self.assertEqual((stats.changed, stats.failed), (1, 0))
    self.assertEqual(library.source_entries(self.con, "pg")["P.html"].description, "two")


@unittest.skipUnless(SEVEN_ZIP and GIT, "needs 7-Zip and git")
class GitHub(Scratch):
  """A repository's zip follows its commits, file by file."""

  def setUp(self):
    super().setUp()
    self.lib = make_library(self.path("bbs"))
    self.con = S.open_catalogue(self.lib)
    self.ctx = S.Context(lib=self.lib, con=self.con, seven_zip=SEVEN_ZIP, git=GIT)
    self.work = self.path("work")
    os.makedirs(self.work)
    self.g("init", "-q", "-b", "main")
    self.g("config", "user.email", "t@example.org")
    self.g("config", "user.name", "T")
    self.repos = []

  def tearDown(self):
    self.con.close()
    super().tearDown()

  def g(self, *args):
    subprocess.run([GIT, *args], cwd=self.work, check=True, capture_output=True)

  def commit(self, files, delete=()):
    for name, data in files.items():
      write(os.path.join(self.work, *name.split("/")), data)
    for name in delete:
      os.remove(os.path.join(self.work, *name.split("/")))
    self.g("add", "-A")
    self.g("commit", "-q", "-m", "change")

  def listing(self, repo, language=None):
    self.repos = [{"name": "proj", "default_branch": "main", "clone_url": self.work, "pushed_at": str(time.time()),
                   "description": "A project", "private": False, "fork": False,
                   "language": language}] if repo else []
    return self.repos

  def test_a_repository_is_tagged_with_its_language(self):
    self.commit({"a.cpp": "int main() {}"})
    self.listing(True, language="C++")
    self.sync()
    self.assertEqual(library.source_entries(self.con, "gh")["proj"].tags, ("github", "cpp"))
    self.repos[0]["language"] = "C#"  # (GitHub's guess changed, nothing pushed)
    self.assertEqual(self.sync().updated, 1)
    self.assertEqual(library.source_entries(self.con, "gh")["proj"].tags, ("github", "csharp"))

  def test_language_tags(self):
    for language, tag in (("Python", "python"), ("C++", "cpp"), ("C#", "csharp"), ("C", "c"), ("F#", "fsharp"),
                          ("Objective-C++", "objective-cpp"), ("Jupyter Notebook", "jupyter-notebook"),
                          ("Visual Basic .NET", "visual-basic-.net"), ("QuickBASIC", "quickbasic")):
      self.assertEqual(S.language_tag(language), tag)
    self.assertEqual(len({library.norm(S.language_tag(n)) for n in ("C", "C++", "C#")}), 3)  # (three tags to search)

  def sync(self, pushed=None):
    with mock.patch.object(S, "github_repos", lambda user: self.repos):
      return S.sync_source(self.ctx, "gh", conf(type="github", user="someone"))

  def contents(self):
    path = library.resolve(self.lib, library.source_entries(self.con, "gh")["proj"])
    with zipfile.ZipFile(path) as z:
      return {n: z.read(n).decode() for n in z.namelist() if not n.endswith("/")}

  def test_updates_replace_only_what_changed(self):
    self.commit({"a.txt": "A1", "b.txt": "B1", "dir/c.txt": "C1"})
    self.listing(True)
    stats = self.sync()
    self.assertEqual((stats.new, stats.failed), (1, 0))
    self.assertEqual(self.contents(), {"proj/a.txt": "A1", "proj/b.txt": "B1", "proj/dir/c.txt": "C1"})
    entry = library.source_entries(self.con, "gh")["proj"]
    self.assertEqual((entry.description, entry.tags), ("A project", ("github",)))

    self.assertEqual(self.sync().changed, 0)  # (pushed_at unchanged: not even fetched)

    self.commit({"a.txt": "A2", "dir/d.txt": "D1"}, delete=["b.txt"])
    self.listing(True)
    with self.assertLogs("library_sync", "INFO") as logs:
      stats = self.sync()
    self.assertEqual((stats.changed, stats.failed), (1, 0))
    self.assertTrue(any("2 changed, 1 deleted" in line for line in logs.output), logs.output)
    self.assertEqual(self.contents(), {"proj/a.txt": "A2", "proj/dir/c.txt": "C1", "proj/dir/d.txt": "D1"})

  def test_an_empty_repository_is_left_out_until_pushed_to(self):
    empty = self.path("empty.git")
    subprocess.run([GIT, "init", "-q", "--bare", "-b", "main", empty], check=True, capture_output=True)
    self.repos = [{"name": "nothing", "default_branch": "main", "clone_url": empty, "pushed_at": "2025-04-30",
                   "description": "", "private": False, "fork": False}]
    stats = self.sync()
    self.assertEqual((stats.listed, stats.failed), (0, 0))
    calls = []
    real_git = S.git
    with mock.patch.object(S, "git", lambda ctx, *a, **k: calls.append(a[0]) or real_git(ctx, *a, **k)):
      self.sync()
      self.assertEqual(calls, [])  # (not tried again: not pushed to since)
      self.repos[0]["pushed_at"] = "2026-01-01"
      self.sync()
      self.assertEqual(calls, ["clone"])

  def test_a_zip_made_by_another_recipe_is_made_again(self):
    self.commit({"a.txt": "A1"})
    self.listing(True)
    self.sync()
    with mock.patch.object(S, "REPO_RECIPE", "git2"), self.assertLogs("library_sync", "INFO") as logs:
      stats = self.sync()  # (not pushed to since)
    self.assertEqual(stats.changed, 1)
    self.assertTrue(any("zipped whole" in line for line in logs.output), logs.output)
    self.assertTrue(library.source_entries(self.con, "gh")["proj"].fingerprint.startswith("git2:"))

  def test_a_repository_gone_takes_its_zip_and_clone(self):
    self.commit({"a.txt": "A1"})
    self.listing(True)
    self.sync()
    zip_path = library.resolve(self.lib, library.source_entries(self.con, "gh")["proj"])
    self.listing(False)
    self.assertEqual(self.sync().removed, 1)
    self.assertFalse(os.path.exists(zip_path))
    self.assertFalse(os.path.exists(os.path.join(self.lib.repos_dir, "gh", "proj")))


class CommandLine(Scratch):
  """main(): what it does to the process (data dir, working directory, the
  main config) is put back after each test."""

  def setUp(self):
    super().setUp()
    import config
    import paths
    self.saved = (paths.data_dir, os.getcwd(), config.main_path)
    self.logging = mock.patch.object(S, "_setup_logging")
    self.logging.start()

  def tearDown(self):
    import config
    import paths
    self.logging.stop()
    paths.data_dir, cwd, config.main_path = self.saved
    os.chdir(cwd)
    super().tearDown()

  def test_unknown_sources_and_the_lock(self):
    self.assertEqual(S.main([os.path.join(_setup.PROJECT, "DirtyFork.yaml"), "nosuchsource", "--dry-run",
                             "--data-dir", self.top]), 2)
    lock = self.path("x.lock")
    with S.single_instance(lock):
      with self.assertRaises(S.AlreadyRunning):
        with S.single_instance(lock):
          pass

  def test_a_dry_run_makes_nothing(self):
    files, data = self.path("files"), self.path("data")
    write(os.path.join(data, "a.flac"))
    cfg = write(self.path("bbs.yaml"), f"files_dir: '{files}'\nfile_library:\n  sources:\n"
                                       f"    s: {{type: samples, dir: '{data}'}}\n")
    with self.assertLogs("library_sync", "INFO") as logs:
      self.assertEqual(S.main([cfg, "--dry-run", "--all", "--data-dir", self.top]), 0)
    self.assertFalse(os.path.exists(files))
    self.assertTrue(any("s: 1 listed, 1 new" in line for line in logs.output), logs.output)

  def test_a_dry_run_reads_an_older_catalogue(self):
    files, data = self.path("files"), self.path("data")
    write(os.path.join(data, "a.flac"))
    make_v1_catalogue(os.path.join(files, "catalog", "library.db"))
    cfg = write(self.path("bbs.yaml"), f"files_dir: '{files}'\nfile_library:\n  sources:\n"
                                       f"    s: {{type: samples, dir: '{data}'}}\n")
    with self.assertLogs("library_sync", "INFO") as logs:
      self.assertEqual(S.main([cfg, "--dry-run", "--all", "--data-dir", self.top]), 0)
    self.assertTrue(any("s: 1 listed, 1 new" in line for line in logs.output), logs.output)
    con = sqlite3.connect(os.path.join(files, "catalog", "library.db"))
    try:
      self.assertEqual(con.execute("SELECT path, edited FROM files").fetchall(), [("old.zip", 0)])  # (no entry changed)
    finally:
      con.close()

  def test_a_dry_run_needs_no_7zip(self):
    files, pages = self.path("files"), self.path("pages")
    write(os.path.join(pages, "P.html"), page("p"))
    cfg = write(self.path("bbs.yaml"), f"files_dir: '{files}'\nfile_library:\n  sources:\n"
                                       f"    w: {{type: webpages, dir: '{pages}'}}\n")
    with mock.patch.object(S, "find_seven_zip", lambda configured=None: None), \
         self.assertLogs("library_sync", "INFO") as logs:
      self.assertEqual(S.main([cfg, "--dry-run", "--data-dir", self.top]), 0)
    self.assertTrue(any("w: 1 listed, 1 new" in line for line in logs.output), logs.output)

  def samples_config(self, *names, pace=None, tags=None):
    """Write a config with a samples source of each name (one file each;
    *tags*: a source's more tags, by name) and *pace*; returns its path,
    a new one each time (config.get_config keeps what it read by path)."""
    sources = ""
    for name in names:
      write(self.path(name, "a.flac"))
      more = f", tags: [{(tags or {})[name]}]" if name in (tags or {}) else ""
      sources += f"    {name}: {{type: samples, dir: '{self.path(name)}'{more}}}\n"
    self.configs = getattr(self, "configs", 0) + 1
    return write(self.path(f"bbs{self.configs}.yaml"), f"files_dir: '{self.path('files')}'\nfile_library:\n"
                                        + (f"  sync_pace: {pace}\n" if pace is not None else "")
                                        + f"  sources:\n{sources}")

  def checks(self):
    """{source: (when its check's run began, its cost, its settings' key)}, as recorded."""
    con = sqlite3.connect(self.path("files", "catalog", "library.db"))
    try:
      rows = con.execute("SELECT source, value FROM sync_state WHERE key = ?", (library.CHECKED,)).fetchall()
    finally:
      con.close()
    return {source: (float(v.split()[0]), float(v.split()[1]), v.split()[2]) for source, v in rows}

  def set_check(self, source, began, cost):
    """Record a check of *source* as made at *began*, costing *cost* (its settings' key kept)."""
    key = self.checks()[source][2]
    con = sqlite3.connect(self.path("files", "catalog", "library.db"))
    try:
      con.execute("UPDATE sync_state SET value = ? WHERE source = ? AND key = ?",
                  (f"{began:.0f} {cost} {key}", source, library.CHECKED))
      con.commit()
    finally:
      con.close()

  def run_logged(self, *args, code=0):
    with self.assertLogs("library_sync", "INFO") as logs:
      self.assertEqual(S.main(list(args) + ["--data-dir", self.top]), code)
    return logs.output

  def checked(self, logs, source):
    """Whether a run with these logs checked *source*."""
    return any(line.startswith(f"INFO:library_sync:{source}: ") for line in logs)

  def test_a_scheduled_run_checks_a_source_only_when_due(self):
    cfg = self.samples_config("slow", "quick")
    self.run_logged(cfg)
    self.assertEqual(set(self.checks()), {"slow", "quick"})
    now = time.time()
    self.set_check("slow", now - 10, 100.0)  # (due 3000 s after)
    self.set_check("quick", now - 10, 0.1)   # (due 3 s after)
    logs = self.run_logged(cfg)
    self.assertIn("library_sync: quick; not due: slow (at ", logs[0])
    self.assertEqual((self.checked(logs, "slow"), self.checked(logs, "quick")), (False, True))
    self.assertEqual(self.checks()["slow"][:2], (round(now - 10), 100.0))  # (left as it was)
    self.assertTrue(self.checked(self.run_logged(cfg, "--all"), "slow"))  # (--all, or a source named: at once)
    self.set_check("slow", now - 10, 100.0)
    self.assertTrue(self.checked(self.run_logged(cfg, "slow"), "slow"))

  def test_a_source_due_within_minutes_is_checked_now(self):
    # (runs start late by varying amounts: one due a little after this run began would
    # otherwise wait a whole interval, every time)
    cfg = self.samples_config("s")
    self.run_logged(cfg)
    self.set_check("s", time.time() - 1, (S.EARLY - 60) / S.PACE)  # (due in under EARLY seconds)
    self.assertTrue(self.checked(self.run_logged(cfg), "s"))
    self.set_check("s", time.time() - 1, (S.EARLY + 600) / S.PACE)
    self.assertFalse(self.checked(self.run_logged(cfg), "s"))

  def test_when_a_source_is_checked_next(self):
    con = library.empty_catalogue()
    now, c = 1_000_000, conf(type="samples", dir="x")
    key = S._settings_key(c)
    self.assertEqual(S.next_check(con, "s", c, 30, now), 0)  # (never checked)
    library.set_state(con, "s", library.CHECKED, f"{now - 100} 2.5 {key}")
    self.assertEqual(S.next_check(con, "s", c, 30, now), now - 100 + 75)
    library.set_state(con, "s", library.CHECKED, f"{now - 100} 10000 {key}")
    self.assertEqual(S.next_check(con, "s", c, 30, now), now - 100 + S.MAX_GAP)  # (at least daily)
    self.assertEqual(S.next_check(con, "s", conf(type="samples", dir="y"), 30, now), 0)  # (its settings changed)
    library.set_state(con, "s", library.CHECKED, f"{now + 3600} 1 {key}")
    self.assertEqual(S.next_check(con, "s", c, 30, now), 0)  # (the clock went back)
    for nonsense in ("nonsense", f"{now} 1"):
      library.set_state(con, "s", library.CHECKED, nonsense)
      self.assertEqual(S.next_check(con, "s", c, 30, now), 0)

  def test_changed_settings_make_a_source_due(self):
    cfg = self.samples_config("s")
    self.run_logged(cfg)
    self.set_check("s", time.time() - 10, 100.0)
    self.assertFalse(self.checked(self.run_logged(cfg), "s"))
    cfg = self.samples_config("s", tags={"s": "more"})
    self.assertTrue(self.checked(self.run_logged(cfg), "s"))

  def test_every_check_is_recorded_but_a_dry_runs(self):
    cfg = self.samples_config("ok", "gone")
    shutil.rmtree(self.path("gone"))  # (its folder missing: it fails)
    self.run_logged(cfg, code=1)
    recorded = self.checks()
    self.assertEqual(set(recorded), {"ok", "gone"})  # (a failed check too: else it would be checked every run)
    self.set_check("ok", time.time() - 10, 0.0)
    before = self.checks()
    self.run_logged(cfg, "--dry-run", code=1)
    self.assertEqual(self.checks(), before)

  def test_a_check_that_cant_be_recorded_stops_nothing_else(self):
    cfg = self.samples_config("a", "b")
    real = library.set_state

    def set_state(con, source, key, value):
      if (source, key) == ("a", library.CHECKED):
        raise sqlite3.OperationalError("database is locked")  # (the BBS holding the lock too long)
      return real(con, source, key, value)
    with mock.patch.object(library, "set_state", set_state):
      logs = self.run_logged(cfg)
    self.assertTrue(self.checked(logs, "b"), logs)
    self.assertTrue(any("a: could not record its check" in line for line in logs), logs)
    self.assertEqual(set(self.checks()), {"b"})

  def test_the_pace_setting(self):
    cfg = self.samples_config("s", pace=0)  # (0: every source at every run)
    self.run_logged(cfg)
    self.set_check("s", time.time() - 10, 100.0)
    self.assertTrue(self.checked(self.run_logged(cfg), "s"))
    for unreadable in ("-1", "lots", ".nan"):
      cfg = self.samples_config("s", pace=unreadable)
      self.set_check("s", time.time() - 10, 100.0)
      logs = self.run_logged(cfg)
      self.assertTrue(any("sync_pace" in line and "using 30" in line for line in logs), (unreadable, logs))
      self.assertFalse(self.checked(logs, "s"), unreadable)  # (paced as by default)

  def test_work_on_changes_is_not_counted_in_a_checks_cost(self):
    pages = self.path("pages")
    write(os.path.join(pages, "P.html"), page("p"))
    cfg = write(self.path("bbs.yaml"), f"files_dir: '{self.path('files')}'\nfile_library:\n  sources:\n"
                                       f"    w: {{type: webpages, dir: '{pages}'}}\n")

    def zip_files(ctx, final, cwd, names):
      time.sleep(0.5)  # (a slow zip)
      write(final, "zip")
    with mock.patch.object(S, "find_seven_zip", lambda configured=None: "7z"), \
         mock.patch.object(S, "zip_files", zip_files):
      logs = self.run_logged(cfg)
    self.assertTrue(any("of it on what changed" in line for line in logs), logs)
    self.assertLess(self.checks()["w"][1], 0.25)  # (not 0.5: Windows' clocks may measure the sleep a little short)

  def test_a_failure_before_any_source_is_logged(self):
    with self.assertLogs("library_sync", "ERROR") as logs:
      self.assertEqual(S.main([self.path("no such config.yaml"), "--data-dir", self.top]), 1)
    self.assertIn("library_sync failed", logs.output[0])


if __name__ == "__main__":
  unittest.main()
