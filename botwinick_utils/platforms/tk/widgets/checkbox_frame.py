import tkinter as tk


class CheckBoxFrame(tk.Frame):
    def __init__(self, parent, keys=None, listener=None, **pack_options):
        """
        Initializes the CheckBoxRow widget, creating checkboxes for the given keys.

        Parameters:
            parent: The parent frame where this widget will be placed.
            keys: The initial list of keys for creating checkboxes.
            listener: the listener function that gets called on checkbox state change. See `set_listener()` for details.
            pack_options: options for packing widgets [ default --> side=tk.LEFT, padx=5 ]
                (e.g. side: the pack side for this frame (basically going to be tk.LEFT or tk.TOP to control if horizontal or vertical))
        """
        super().__init__(parent)
        self.check_vars = {}  # To store the BooleanVar for each key (checkbox state)
        self.checkboxes = {}  # To store the actual checkbox widgets
        self.listener = listener  # Listener function for checkbox state changes

        # handle pack options
        if 'side' not in pack_options:
            pack_options['side'] = tk.LEFT
        if 'padx' not in pack_options:
            pack_options['padx'] = 5
        self._pack_options = pack_options

        # create checkboxes if defined
        self.create_checkboxes(keys or [])

    def create_checkboxes(self, keys):
        """Creates a checkbox for each key in the given list."""
        for key in keys:
            if key not in self.checkboxes:
                # Create a BooleanVar to store the state of the checkbox
                var = tk.BooleanVar()
                var.trace_add("write", self._on_checkbox_change)  # Attach a trace to detect changes
                self.check_vars[key] = var

                # Create the checkbox and add it to the frame
                checkbox = tk.Checkbutton(self, text=key, variable=var)
                checkbox.pack(**self._pack_options)
                self.checkboxes[key] = checkbox

    def _on_checkbox_change(self, *args):
        """Internal method called when any checkbox state changes."""
        if self.listener:
            self.listener(self.get_checked_keys())

    def get_checked_keys(self):
        """Returns a list of keys that are currently checked."""
        return [key for key, var in self.check_vars.items() if var.get()]

    def update_keys(self, new_keys):
        """
        Updates the list of checkboxes based on the new keys.
        It adds checkboxes for new keys and removes checkboxes for missing keys.

        The checked status of existing keys is preserved.
        """
        # Add new checkboxes for keys not already present
        for key in new_keys:
            if key not in self.checkboxes:
                self.create_checkboxes([key])

        # Remove checkboxes for keys that are no longer in the updated list
        for key in list(self.checkboxes.keys()):  # Use list() to avoid modification during iteration
            if key not in new_keys:
                self.checkboxes[key].pack_forget()  # Remove the checkbox from the frame
                del self.checkboxes[key]  # Remove it from the checkboxes dictionary
                del self.check_vars[key]  # Remove its variable as well

    def set_listener(self, listener_func):
        """
        Registers a listener function that gets called when any checkbox state changes.

        Parameters:
            listener_func: A function that takes a single argument of the list of currently checked keys.
        """
        self.listener = listener_func

    def set_checked_keys(self, checked_keys):
        """
        Updates the checked status of the checkboxes to match the provided list of checked keys.

        Parameters:
            checked_keys: A list of keys that should be checked.
        """
        for key, var in self.check_vars.items():
            if key in checked_keys:
                var.set(True)  # Check the checkbox
            else:
                var.set(False)  # Uncheck the checkbox
