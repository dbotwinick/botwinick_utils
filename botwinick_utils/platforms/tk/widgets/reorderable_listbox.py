# based on following sources:
# ref: https://stackoverflow.com/questions/14459993/tkinter-listbox-drag-and-drop-with-python
# ref: https://stackoverflow.com/a/53823708
# and then further adjusted over time

import tkinter as tk


class ReorderableListbox(tk.Listbox):
    shifting = False
    """ A Tkinter listbox with drag & drop reordering of lines """

    def __init__(self, master, on_order_change_listener, **kwargs):
        if 'selectmode' not in kwargs:
            kwargs['selectmode'] = tk.EXTENDED
        tk.Listbox.__init__(self, master, kwargs)
        self._set_bindings()
        self.selection_clicked = False
        self.left = False
        self.unlock_shifting()
        self.ctrl_clicked = False
        self._on_change_listener = on_order_change_listener

    def _set_bindings(self):
        self.bind('<Button-1>', self.set_current)
        self.bind('<Control-1>', self.toggle_selection)
        self.bind('<B1-Motion>', self.shift_selection)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Enter>', self.on_enter)

        # if tkinterdnd2 installed and setup
        try:
            # noinspection PyUnresolvedReferences
            self.dnd_bind('<<Drag>>', self.shift_selection)
        except AttributeError:
            # but don't throw error if it's not...
            pass

        return

    def on_order_changed_event_handler(self):
        if self._on_change_listener:
            self._on_change_listener()
        pass

    # noinspection PyUnusedLocal
    def on_leave(self, event):
        # prevents changing selection when dragging
        # already selected items beyond the edge of the listbox
        if self.selection_clicked:
            self.left = True
            return 'break'

    # noinspection PyUnusedLocal
    def on_enter(self, event):
        self.left = False

    def set_current(self, event):
        self.ctrl_clicked = False
        i = self.nearest(event.y)
        self.selection_clicked = self.selection_includes(i)
        if self.selection_clicked:
            return 'break'

    # noinspection PyUnusedLocal
    def toggle_selection(self, event):
        self.ctrl_clicked = True

    def move_element(self, source, target):
        if not self.ctrl_clicked:
            element = self.get(source)
            self.delete(source)
            self.insert(target, element)

    def unlock_shifting(self):
        self.shifting = False

    def lock_shifting(self):
        # prevent moving processes from disturbing each other
        # and prevent scrolling too fast
        # when dragged to the top/bottom of visible area
        self.shifting = True

    def shift_selection(self, event):
        if self.ctrl_clicked:
            return
        selection = self.curselection()
        # if not self.selectionClicked or len(selection) == 0:
        #     return

        selection_range = range(min(selection), max(selection))
        current_index = self.nearest(event.y)

        if self.shifting:
            return 'break'

        line_height = 15
        bottom_y = self.winfo_height()
        if event.y >= bottom_y - line_height:
            self.lock_shifting()
            self.see(self.nearest(bottom_y - line_height) + 1)
            self.master.after(500, self.unlock_shifting)
        if event.y <= line_height:
            self.lock_shifting()
            self.see(self.nearest(line_height) - 1)
            self.master.after(500, self.unlock_shifting)

        if current_index < min(selection):
            self.lock_shifting()
            not_in_selection_index = 0
            for i in selection_range[::-1]:
                if not self.selection_includes(i):
                    self.move_element(i, max(selection) - not_in_selection_index)
                    not_in_selection_index += 1
            current_index = min(selection) - 1
            self.move_element(current_index, current_index + len(selection))
            self.on_order_changed_event_handler()
        elif current_index > max(selection):
            self.lock_shifting()
            not_in_selection_index = 0
            for i in selection_range:
                if not self.selection_includes(i):
                    self.move_element(i, min(selection) + not_in_selection_index)
                    not_in_selection_index += 1
            current_index = max(selection) + 1
            self.move_element(current_index, current_index - len(selection))
            self.on_order_changed_event_handler()
        self.unlock_shifting()
        return 'break'
