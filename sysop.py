"""
Sysop module — user key management.
Accessible only to users with the 'sysop' key.
"""

import sqlite3
import paths
from config import get_config
from definitions import RetVals, success, null, white, black, green, red, cr, lf
from input_fields import InputFields, show_message_box
from input_output import send, ansi_cls, ansi_color

config = get_config()

def _get_db():
    con = sqlite3.connect(paths.resolve_data(str(config.database)))
    con.row_factory = sqlite3.Row
    return con, con.cursor()

async def run(user, dest_conf, menu_item=None):
    from common import Destinations, global_data

    style_conf = config.input_fields.input_field

    while True:
        # --- Phase 1: look up a handle ---
        await ansi_cls(user)
        ansi_color(user, fg=white, bg=black, fg_br=True)
        await send(user, "Sysop — User Key Management" + cr + lf + cr + lf, drain=False)
        ansi_color(user, fg=white, bg=black, fg_br=False)
        await send(user, "Handle: ", drain=True)

        fields1 = InputFields(user)
        await fields1.add_field(conf=style_conf, width=30, max_length=50)
        await send(user, cr + lf + cr + lf, drain=False)
        await fields1.add_button("lookup", content="Look Up")
        await send(user, "  ", drain=False)
        await fields1.add_button("cancel", content="Cancel")

        r1 = await fields1.run()
        if r1.button == "cancel":
            return RetVals(status=success, next_destination=Destinations.main, next_menu_item=null)

        handle = r1.fields[0].content.strip()
        if not handle:
            continue

        con, db = _get_db()
        try:
            row = db.execute(
                "SELECT id FROM users WHERE cmd_line_handle = ?", (handle.lower(),)
            ).fetchone()
        finally:
            con.close()

        if not row:
            await show_message_box(user, f"User '{handle}' not found.",
                                   title="Not Found", fg=white, fg_br=True, bg=black,
                                   outline_fg=red, outline_fg_br=True)
            continue

        user_id = row["id"]

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
        await send(user, "Sysop — User Key Management" + cr + lf + cr + lf, drain=False)
        ansi_color(user, fg=white, bg=black, fg_br=False)
        await send(user, f"Handle: {handle}" + cr + lf + cr + lf, drain=False)
        await send(user, "Keys (comma-separated): ", drain=True)

        fields2 = InputFields(user)
        await fields2.add_field(conf=style_conf, width=50, max_length=500, content=current_keys)
        await send(user, cr + lf + cr + lf, drain=False)
        await fields2.add_button("save", content="Save")
        await send(user, "  ", drain=False)
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
            live.keys = set(new_keys)

        await show_message_box(user, f"Keys for '{handle}' updated successfully.",
                               title="Saved", fg=white, fg_br=True, bg=black,
                               outline_fg=green, outline_fg_br=True)
