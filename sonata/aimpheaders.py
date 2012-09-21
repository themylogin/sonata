"""
This module implements AIMP-like headers for playlists, which help to distinguish
songs from different directories.
"""

import gtk
import pango
import cairo
import gobject
import glib
import os.path
import re

"""
CellRenderer for ui.treeview. Columns for songs, which need a header, must have a
gproperty "aimp_header", which contains header text. As gtk's TreeView does not support
colspans, this cell renderer can be used only in single-column mode. Also, column sizing
should be set to gtk.TREE_VIEW_COLUMN_AUTOSIZE and fixed_height_mode should be disabled.
"""
class CellRenderer(gtk.GenericCellRenderer):
    """
    Properties
    """
    __gproperties__ = {
        "markup"        :   (gobject.TYPE_STRING, "Marked up text to render",    "Marked up text to render.",    None, gobject.PARAM_READWRITE),
        "aimp_header"   :   (gobject.TYPE_STRING, "AIMP-like header, if needed", "AIMP-like header, if needed.", None, gobject.PARAM_READWRITE),
    }

    def do_set_property(self, key, value):
        self.__properties[key] = value

    def do_get_property(self, key):
        return self.__properties[key]

    def get_header(self):
        return self.get_property("aimp_header").replace("<b>", "").replace("</b>", "")

    """
    gtk.GenericCellRenderer overrides
    """
    def __init__(self):
        gtk.GenericCellRenderer.__init__(self)
        self.__properties = {}

    def on_get_size(self, widget, cell_area):
        if cell_area == None:
            if self.get_header():
                return (0, 0, 0, 34)
            else:
                return (0, 0, 0, 16)

        x = cell_area.x
        y = cell_area.y
        w = cell_area.width
        h = cell_area.height
        return (x, y, w, h)

    def on_render(self, window, widget, background_area, cell_area, expose_area, flags):
        state = gtk.STATE_NORMAL
        header_color = '#999999'
        if flags & gtk.CELL_RENDERER_SELECTED:
            header_color = '#000000'
            if widget.has_focus():
                state = gtk.STATE_SELECTED
            else:
                state = gtk.STATE_ACTIVE

        context = widget.get_pango_context()
        layout = pango.Layout(context)
        layout.set_markup(self.get_property("markup"))

        if self.get_header():
            widget.style.paint_layout(window, state, True, cell_area, widget, "", cell_area.x + 2, cell_area.y + 20, layout)

            layout = pango.Layout(context)
            layout.set_alignment(pango.ALIGN_RIGHT)
            layout.set_markup("<span color=\"" + header_color + "\" underline=\"low\" weight=\"bold\">" + glib.markup_escape_text(self.get_header()) + "</span>")
            widget.style.paint_layout(window, state, True, cell_area, widget, '', cell_area.x + 2, cell_area.y + 2, layout)
        else:
            widget.style.paint_layout(window, state, True, cell_area, widget, '', cell_area.x + 2, cell_area.y + 2, layout)
        return

    def on_activate(self, event, widget, path, background_area, cell_area, flags):
        pass

    def on_start_editing(self, event, widget, path, background_area, cell_area, flags):
        pass

gobject.type_register(CellRenderer)


"""
Get AIMP header by filename
"""
def by_filename(filename):
    bits = os.path.dirname(filename).split("/")

    try:
        # Cut CD1, CD2
        if re.match(r"^CD", bits[-1]):
            bits.pop()

        # Year - Album
        m = re.match(r"^([0-9]{4})\s*-\s*(.+)$", bits[-1])
        if m:
            album_title = m.group(2) + " (" + m.group(1) + ")"
        else:
            album_title = bits[-1]
        bits.pop()

        # Cut EPs/Singles/Albums
        if re.match(r"^(EP|Single|Album)", bits[-1]):
            bits.pop()

        return bits[-1] + " - " + album_title
    except:
        return os.path.join(bits)

"""
Get AIMP header by metadata
"""
def by_metadata(mpdh, track):
    return '%s - %s (%s)' % (mpdh.get(track, 'artist'), mpdh.get(track, 'album'), mpdh.get(track, 'date'))
