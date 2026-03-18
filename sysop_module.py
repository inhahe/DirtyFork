"""
Sysop module — user key management and key group editing.
Accessible only to users with the 'sysop' key.
"""

import sqlite3
import paths
from config import get_config
import config as config_module
from definitions import RetVals, success, null, white, black, green, red, cr, lf
from input_fields import InputFields, show_message_box
from input_output import send, ansi_cls, ansi_color, ansi_move_deferred
from ruamel.yaml import YAML

config = get_config()

def _get_db():
    con = sqlite3.connect(paths.resolve_data(str(config.database)))
    con.row_factory = sqlite3.Row
    return con, con.cursor()


def _load_yaml():
    """Load the main config yaml with ruamel (preserves comments/formatting)."""
    yml = YAML()
    yml.preserve_quotes = True
    with open(config_module.main_path, "r") as f:
        return yml, yml.load(f)


def _save_yaml(yml, data):
    """Write the config yaml back to disk."""
    with open(config_module.main_path, "w") as f:
        yml.dump(data, f)


async def _lookup_handle(user, style_conf, title):
    """Prompt for a handle and look it up in the DB.
    Returns (handle, user_id) or (None, None) if the user pressed Back."""
    while True:
        await ansi_cls(user)
        ansi_color(user, fg=white, bg=black, fg_br=True)
        await send(user, title + cr + lf + cr + lf, drain=False)
        ansi_color(user, fg=white, bg=black, fg_br=False)
        await send(user, "Handle: ", drain=True)

        fields1 = InputFields(user)
        await fields1.add_field(conf=style_conf, width=30, max_length=50)
        await send(user, cr + lf + cr + lf, drain=False)
        lookup_btn = await fields1.add_button("lookup", content="Look Up")
        cancel_col = lookup_btn.col_offset + lookup_btn.width + (1 if lookup_btn.outline else 0) + 1
        cancel_row = lookup_btn.row_offset - (1 if lookup_btn.outline else 0)
        await ansi_move_deferred(user, row=cancel_row, col=cancel_col, drain=True)
        await fields1.add_button("back", content="Back")

        r1 = await fields1.run()
        if r1.button == "back":
            return None, None

        handle = r1.fields[0].content.strip()
        if not handle:
            continue

        con, db = _get_db()
        try:
            row = db.execute(
                "SELECT id, handle FROM users WHERE handle = ? COLLATE NOCASE", (handle,)
            ).fetchone()
        finally:
            con.close()

        if not row:
            await show_message_box(user, f"User '{handle}' not found.",
                                   title="Not Found", fg=white, fg_br=True, bg=black,
                                   outline_fg=red, outline_fg_br=True)
            continue

        return row["handle"], row["id"]


async def _edit_user_keys(user, style_conf, global_data):
    """Look up a user and edit their keys."""
    from common import Destinations, expand_keys

    while True:
        handle, user_id = await _lookup_handle(user, style_conf, "Sysop - User Key Management")
        if handle is None:
            return

        # --- Phase 2: edit keys ---
        con, db = _get_db()
        try:
            key_rows = db.execute(
                "SELECT key FROM user_keys WHERE user_id = ?", (user_id,)
            ).fetchall()
        finally:
            con.close()

        current_keys = ", ".join(kr["key"] for kr in key_rows)

        await ansi_cls(user)
        ansi_color(user, fg=white, bg=black, fg_br=True)
        await send(user, "Sysop - User Key Management" + cr + lf + cr + lf, drain=False)
        ansi_color(user, fg=white, bg=black, fg_br=False)
        await send(user, f"Handle: {handle}" + cr + lf + cr + lf, drain=False)
        await send(user, "Keys (comma-separated): ", drain=True)

        fields2 = InputFields(user)
        await fields2.add_field(conf=style_conf, width=50, max_length=500, content=current_keys)
        await send(user, cr + lf + cr + lf, drain=False)
        save_btn = await fields2.add_button("save", content="Save")
        cancel_col = save_btn.col_offset + save_btn.width + (1 if save_btn.outline else 0) + 1
        cancel_row = save_btn.row_offset - (1 if save_btn.outline else 0)
        await ansi_move_deferred(user, row=cancel_row, col=cancel_col, drain=True)
        await fields2.add_button("cancel", content="Cancel")

        r2 = await fields2.run()
        if r2.button == "cancel":
            continue

        new_keys = [k.strip() for k in r2.fields[0].content.split(",") if k.strip()]

        con, db = _get_db()
        try:
            db.execute("DELETE FROM user_keys WHERE user_id = ?", (user_id,))
            for key in new_keys:
                db.execute("INSERT INTO user_keys (user_id, key) VALUES (?, ?)", (user_id, key))
            con.commit()
        finally:
            con.close()

        # Update live session immediately if user is currently online
        live = global_data.users.get(handle.lower())
        if live:
            live.keys = expand_keys(set(new_keys))

        await show_message_box(user, f"Keys for '{handle}' updated successfully.",
                               title="Saved", fg=white, fg_br=True, bg=black,
                               outline_fg=green, outline_fg_br=True)


async def _edit_key_groups(user, style_conf, global_data):
    """Edit key groups defined in the main config yaml."""
    from common import expand_keys

    while True:
        yml, data = _load_yaml()
        groups = data.get("key_groups") or {}

        await ansi_cls(user)
        ansi_color(user, fg=white, bg=black, fg_br=True)
        await send(user, "Sysop - Key Groups" + cr + lf + cr + lf, drain=False)
        ansi_color(user, fg=white, bg=black, fg_br=False)

        if groups:
            for name, members in groups.items():
                member_str = ", ".join(str(m) for m in members) if members else "(empty)"
                await send(user, f"  {name}: {member_str}" + cr + lf, drain=False)
        else:
            await send(user, "  (no groups defined)" + cr + lf, drain=False)

        await send(user, cr + lf + "Group name (or empty to go back): ", drain=True)

        fields1 = InputFields(user)
        await fields1.add_field(conf=style_conf, width=30, max_length=50)
        await send(user, cr + lf + cr + lf, drain=False)
        edit_btn = await fields1.add_button("edit", content="Edit")
        del_col = edit_btn.col_offset + edit_btn.width + (1 if edit_btn.outline else 0) + 1
        del_row = edit_btn.row_offset - (1 if edit_btn.outline else 0)
        await ansi_move_deferred(user, row=del_row, col=del_col, drain=True)
        del_btn = await fields1.add_button("delete", content="Delete")
        back_col = del_btn.col_offset + del_btn.width + (1 if del_btn.outline else 0) + 1
        back_row = del_btn.row_offset - (1 if del_btn.outline else 0)
        await ansi_move_deferred(user, row=back_row, col=back_col, drain=True)
        await fields1.add_button("back", content="Back")

        r1 = await fields1.run()
        if r1.button == "back":
            return

        group_name = r1.fields[0].content.strip()
        if not group_name:
            return

        if r1.button == "delete":
            if group_name not in groups:
                await show_message_box(user, f"Group '{group_name}' not found.",
                                       title="Not Found", fg=white, fg_br=True, bg=black,
                                       outline_fg=red, outline_fg_br=True)
                continue
            del groups[group_name]
            if not groups:
                data.pop("key_groups", None)
            _save_yaml(yml, data)
            _reload_config_groups()
            # Re-expand keys for all online users
            _reexpand_all_users(global_data)
            await show_message_box(user, f"Group '{group_name}' deleted.",
                                   title="Deleted", fg=white, fg_br=True, bg=black,
                                   outline_fg=green, outline_fg_br=True)
            continue

        # Edit/create group
        current_members = ""
        if group_name in groups and groups[group_name]:
            current_members = ", ".join(str(m) for m in groups[group_name])

        await ansi_cls(user)
        ansi_color(user, fg=white, bg=black, fg_br=True)
        await send(user, f"Sysop - Edit Group: {group_name}" + cr + lf + cr + lf, drain=False)
        ansi_color(user, fg=white, bg=black, fg_br=False)
        await send(user, "Keys (comma-separated): ", drain=True)

        fields2 = InputFields(user)
        await fields2.add_field(conf=style_conf, width=50, max_length=500, content=current_members)
        await send(user, cr + lf + cr + lf, drain=False)
        save_btn = await fields2.add_button("save", content="Save")
        cancel_col = save_btn.col_offset + save_btn.width + (1 if save_btn.outline else 0) + 1
        cancel_row = save_btn.row_offset - (1 if save_btn.outline else 0)
        await ansi_move_deferred(user, row=cancel_row, col=cancel_col, drain=True)
        await fields2.add_button("cancel", content="Cancel")

        r2 = await fields2.run()
        if r2.button == "cancel":
            continue

        new_members = [k.strip() for k in r2.fields[0].content.split(",") if k.strip()]

        if "key_groups" not in data:
            data["key_groups"] = {}
        data["key_groups"][group_name] = new_members
        _save_yaml(yml, data)
        _reload_config_groups()
        # Re-expand keys for all online users
        _reexpand_all_users(global_data)

        await show_message_box(user, f"Group '{group_name}' saved: {', '.join(new_members)}",
                               title="Saved", fg=white, fg_br=True, bg=black,
                               outline_fg=green, outline_fg_br=True)


def _reload_config_groups():
    """Reload key_groups from the yaml into the live config."""
    yml, data = _load_yaml()
    groups = data.get("key_groups") or {}
    # Update the live config object
    for cfg in config_module.configs.values():
        cfg["key_groups"] = dict(groups)


def _reexpand_all_users(global_data):
    """Re-expand keys for all currently online users."""
    from common import expand_keys
    for live_user in global_data.users.values():
        # Get the user's base keys from DB, then expand
        con, cur = _get_db()
        try:
            cur.execute("SELECT key FROM user_keys WHERE user_id = ?", (live_user.user_id,))
            base_keys = set(row["key"] for row in cur.fetchall())
        finally:
            con.close()
        live_user.keys = expand_keys(base_keys)


async def _edit_user_settings(user, style_conf):
    """Look up a user and edit their settings."""
    from common import Destinations
    from settings import edit_settings

    while True:
        handle, user_id = await _lookup_handle(user, style_conf, "Sysop - User Settings")
        if handle is None:
            return
        await edit_settings(user, handle, Destinations.sysop)


async def run(user, dest_conf, menu_item=None):
    from common import Destinations, global_data

    style_conf = config.input_fields.input_field
    action = None
    if menu_item and menu_item is not null:
        if isinstance(menu_item, str):
            menu_conf = config.menu_system.sysop
            if menu_conf and menu_conf.options:
                opt = menu_conf.options[menu_item]
                if opt and hasattr(opt, 'action') and opt.action:
                    action = str(opt.action).lower()
            if not action:
                action = menu_item.lower()
        elif hasattr(menu_item, 'action') and menu_item.action:
            action = str(menu_item.action).lower()

    if action == "user_keys":
        await _edit_user_keys(user, style_conf, global_data)
    elif action == "key_groups":
        await _edit_key_groups(user, style_conf, global_data)
    elif action == "user_settings":
        await _edit_user_settings(user, style_conf)

    return RetVals(status=success, next_destination=Destinations.sysop, next_menu_item=null)
