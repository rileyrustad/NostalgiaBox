from nostalgiabox.browser import DirEntry, GuideState, list_dir
from tests.helpers import make_show


# -- list_dir -----------------------------------------------------------------
def test_list_dir_dirs_before_files_and_sorted_case_insensitively(tmp_path):
    (tmp_path / "zeta").mkdir()
    (tmp_path / "Alpha").mkdir()
    (tmp_path / "b.mp4").write_bytes(b"\x00")
    (tmp_path / "A.mp4").write_bytes(b"\x00")
    entries = list_dir(tmp_path, [".mp4"])
    assert [e.name for e in entries] == ["Alpha", "zeta", "A.mp4", "b.mp4"]
    assert [e.is_dir for e in entries] == [True, True, False, False]


def test_list_dir_skips_dotfiles(tmp_path):
    (tmp_path / ".hidden_dir").mkdir()
    (tmp_path / ".hidden.mp4").write_bytes(b"\x00")
    (tmp_path / "visible.mp4").write_bytes(b"\x00")
    entries = list_dir(tmp_path, [".mp4"])
    assert [e.name for e in entries] == ["visible.mp4"]


def test_list_dir_filters_to_given_extensions(tmp_path):
    (tmp_path / "show.mp4").write_bytes(b"\x00")
    (tmp_path / "show.mkv").write_bytes(b"\x00")
    (tmp_path / "notes.txt").write_bytes(b"\x00")
    entries = list_dir(tmp_path, [".mp4"])
    assert [e.name for e in entries] == ["show.mp4"]


def test_list_dir_nonexistent_path_returns_empty(tmp_path):
    assert list_dir(tmp_path / "does_not_exist", [".mp4"]) == []


def test_list_dir_non_directory_path_returns_empty(tmp_path):
    f = tmp_path / "file.mp4"
    f.write_bytes(b"\x00")
    assert list_dir(f, [".mp4"]) == []


# -- GuideState ---------------------------------------------------------------
def _home_entries(tmp_path):
    dragon = make_show(tmp_path, "dragon", 2)
    arthur = make_show(tmp_path, "arthur", 1)
    return [
        DirEntry("Dragon", dragon, True),
        DirEntry("Arthur", arthur, True),
    ], dragon, arthur


def test_guide_starts_at_home_with_given_entries(tmp_path):
    home, _dragon, _arthur = _home_entries(tmp_path)
    gs = GuideState(home, [".mp4"])
    breadcrumb, entries, selected = gs.current_view()
    assert breadcrumb == "TV Guide"
    assert entries == home
    assert selected == 0


def test_guide_move_wraps_both_directions(tmp_path):
    home, _dragon, _arthur = _home_entries(tmp_path)
    gs = GuideState(home, [".mp4"])
    gs.move(-1)
    assert gs.current_view()[2] == len(home) - 1  # wraps backward off the start
    gs.move(1)
    assert gs.current_view()[2] == 0
    gs.move(1)
    assert gs.current_view()[2] == 1


def test_guide_enter_directory_pushes_frame_and_lists_it(tmp_path):
    home, dragon, _arthur = _home_entries(tmp_path)
    gs = GuideState(home, [".mp4"])
    result = gs.enter()  # selection starts on "Dragon"
    assert result is None
    breadcrumb, entries, selected = gs.current_view()
    assert breadcrumb == "TV Guide > Dragon"
    assert [e.name for e in entries] == sorted(p.name for p in dragon.iterdir())
    assert selected == 0


def test_guide_enter_file_returns_path_without_pushing_frame(tmp_path):
    home, _dragon, _arthur = _home_entries(tmp_path)
    gs = GuideState(home, [".mp4"])
    gs.enter()  # descend into Dragon
    _breadcrumb, entries, _selected = gs.current_view()
    file_path = entries[0].path
    result = gs.enter()  # select the first file
    assert result == file_path
    # still inside the Dragon folder - no extra frame was pushed for a file
    assert gs.current_view()[0] == "TV Guide > Dragon"


def test_guide_back_pops_one_level_and_restores_selection(tmp_path):
    home, _dragon, _arthur = _home_entries(tmp_path)
    gs = GuideState(home, [".mp4"])
    gs.move(1)  # select "Arthur"
    gs.enter()  # descend into it
    assert gs.current_view()[0] == "TV Guide > Arthur"
    assert gs.back() is True
    breadcrumb, _entries, selected = gs.current_view()
    assert breadcrumb == "TV Guide"
    assert selected == 1  # parent's selection was preserved


def test_guide_back_at_home_is_noop(tmp_path):
    home, _dragon, _arthur = _home_entries(tmp_path)
    gs = GuideState(home, [".mp4"])
    before = gs.current_view()
    assert gs.back() is False
    assert gs.current_view() == before


def test_guide_reset_to_home_collapses_from_any_depth(tmp_path):
    home, _dragon, _arthur = _home_entries(tmp_path)
    gs = GuideState(home, [".mp4"])
    gs.enter()  # descend one level
    gs.reset_to_home()
    breadcrumb, entries, selected = gs.current_view()
    assert breadcrumb == "TV Guide"
    assert entries == home
    assert selected == 0
