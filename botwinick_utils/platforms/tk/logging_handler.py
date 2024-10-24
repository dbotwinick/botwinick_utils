import logging
import tkinter as tk


class TkWidgetLogHandler(logging.Handler):
    """Custom logging handler to write logs to a Tkinter Text widget with a maximum buffer size."""

    def __init__(self, text_widget, max_buffer_size=5000, level=logging.INFO):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.config(state=tk.DISABLED)
        self.max_buffer_size = max_buffer_size  # Maximum number of characters in the text widget
        self.setLevel(level)

    def emit(self, record):
        msg = self.format(record)

        # Insert the new log message
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)  # Scroll to the end

        # Enforce the max buffer size by deleting old logs if necessary
        if int(self.text_widget.index('end-1c').split('.')[0]) > self.max_buffer_size:
            self.text_widget.delete('1.0', '2.0')  # Delete the first line

        self.text_widget.config(state=tk.DISABLED)  # Make text widget read-only again
