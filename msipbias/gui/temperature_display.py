import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio, Pango

from msipbias.biasmodule import BiasModule
from msipbias.utils import MSIPGeneralError
#from .biastab_gui import BiasGridWindow
import pkg_resources
import datetime
import threading
import time

# Matplotlib stuff
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar
import matplotlib.animation as animation

import numpy

class MSIPTemperatureGUI(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        Gtk.ApplicationWindow.__init__(self, *args, **kwargs)
        self.set_default_size(1024, 768)

        # This will be in the windows group and have the "win" prefix
        max_action = Gio.SimpleAction.new_stateful("maximize", None,
                                           GLib.Variant.new_boolean(False))
        max_action.connect("change-state", self.on_maximize_toggle)
        self.add_action(max_action)

        # Keep it in sync with the actual state
        self.connect("notify::is-maximized",
                            lambda obj, pspec: max_action.set_state(
                                               GLib.Variant.new_boolean(obj.props.is_maximized)))

        self.bm_found = False
        self.temperature = {}
        self.monitor_timeout = 10.0 # seconds
        self.bm_lock = False  # true if bias module is in use
        self.monitor_loop = False  # true if monitor loop is in use

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)
        self.add_top_box()
        self.add_temperature_sensors()
        self.add_logging_window()
        self.add_statusbar()
        #self.temperature_label[1].set_label('100 K')
        #self.bm_switch.set_active(True)
        self.open_cheetah()
        self.show_temperatures()
        self.show_all()

    def add_top_box(self):
        tbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label()
        label.set_markup("<b>1mm MSIP SIS Temperature Display System</b>")
        tbox.pack_start(label, True, True, 0)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label("Cheetah USB Module")
        hbox.pack_start(label, False, False, 0)
        self.bm_switch = Gtk.Switch()
        self.bm_switch.set_active(False)
        self.bm_switch.set_sensitive(False)
        hbox.pack_end(self.bm_switch, False, False, 10)
        tbox.pack_end(hbox, True, True, 0)
        self.box.pack_start(tbox, False, False, 0)
        
    def add_temperature_sensors(self):
        frame = Gtk.Frame()
        frame.set_label('Temperatures')
        tgrid = Gtk.Grid()
        row = 0
        self.temperature_label = {}
        for pol in range(2):
            col = 0
            for temp in range(3):
                label = Gtk.Label('Temperature %d: ' % (pol*3 + temp + 1))
                tgrid.attach(label, col, row, 1, 1)
                self.temperature_label[pol*3 + temp + 1] = Gtk.Label()
                self.markup_label(self.temperature_label[pol*3 + temp + 1],
                                  "T%d K" % (pol*3 + temp +1))
                #self.temperature_label[pol*3 + temp + 1].set_markup("""<span foreground="blue">T%d K</span>""" % (pol*3 + temp + 1))
                self.temperature_label[pol*3 + temp + 1].set_padding(20, 20)
                tgrid.attach(self.temperature_label[pol*3 + temp + 1], col+1, row, 1, 1)
                col += 2
            row += 1
        self.temp_monitor_btn = Gtk.Button.new_with_label("Start Temperature Monitoring")
        tgrid.attach(self.temp_monitor_btn, 6, 0, 2, 2)
        self.temp_monitor_btn.connect("clicked", self.toggle_temperature_monitor)
        
        frame.add(tgrid)
        self.box.pack_start(frame, False, False, 10)
        
    def add_logging_window(self):
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_border_width(10)
        # there is always the scrollbar (otherwise: AUTOMATIC - only if needed
        # - or NEVER)
        self.scrolled_window.set_policy(
            Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
        self.scrolled_window.set_size_request(1024, 300)
        self.textview = Gtk.TextView()
        self.textview.set_cursor_visible(True)
        self.textbuffer = self.textview.get_buffer()
        self.tag_bold = self.textbuffer.create_tag("bold",
                                                   weight=Pango.Weight.BOLD)
        self.tag_italic = self.textbuffer.create_tag("italic",
                                                     style=Pango.Style.ITALIC)
        self.tag_underline = self.textbuffer.create_tag("underline",
                                                        underline=Pango.Underline.SINGLE)
        self.tag_found = self.textbuffer.create_tag("found",
                                                    background="yellow")
        self.print1("1mm MSIP Temperature GUI Started")
        self.scrolled_window.add(self.textview)
        
        # add the scrolledwindow to the window
        self.box.pack_start(self.scrolled_window, False, False, 0)

    def add_statusbar(self):
        self.statusbar = Gtk.Statusbar()
        self.statusbar.set_size_request(-1, 10)
        self.status_id = self.statusbar.get_context_id("example")
        self.statusprint("Started GUI...")
        self.box.pack_start(self.statusbar, True, True, 0)
        
    def open_cheetah(self):
        try:
            #self.bm = BiasModule(debug=True, gui_logger=self.print1)
            self.bm = BiasModule(debug=False, gui_logger=self.print1)
            self.print1("%d device(s) found: " % (self.bm.numdevices))
            for dev in self.bm.device_info:
                self.print1("    port = %d  %s (Ser: %s)" % (dev.port, dev.inuse, dev.serial_number))
            self.print1("Opened Cheetah Unit: port %d with interface %s" % (self.bm.port, self.bm.interface), tag=self.tag_found)
            self.bm_switch.set_active(True)
            for pol in range(2):
                self.bm.set_10MHz_mode(polar=pol)
            self.print1("Setting both polarizations to 10 MHz mode")
            self.bm_found = True
        except MSIPGeneralError:
            self.statusprint("Could not open Cheetah unit")
            self.print1("Error opening Cheetah Unit", tag=self.tag_found)
            self.bm_switch.set_active(False)
            self.bm_found = False
            
    def on_maximize_toggle(self, action, value):
        action.set_state(value)
        if value.get_boolean():
            self.maximize()
        else:
            self.unmaximize()        

    def statusprint(self, text):
        """This function prints text into the statusbar"""
        self.statusbar.push(self.status_id, text)

    def print1(self, text, tag=None):
        """This function prints text into the Commands statustext
        window"""
        enditer = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(enditer, "%s: " % datetime.datetime.now().ctime(), self.tag_bold)
        enditer = self.textbuffer.get_end_iter()
        if tag is None:
            self.textbuffer.insert(enditer, "%s\n" % text)
        else:
            self.textbuffer.insert_with_tags(enditer, "%s\n" % text, tag)
        self.textview.scroll_to_mark(self.textbuffer.get_insert(), 0.05, True, 0.0, 1.0)

    def markup_label(self, widget, text, color='blue'):
        widget.set_markup("""<span foreground="%s" size="large">%s</span>""" % (color, text))

    def toggle_temperature_monitor(self, button):
        if self.monitor_loop:
            self.print1("Stopping Temperature Monitor Loop")
            self.statusprint("Stopping Temperature Monitor Loop")
        self.monitor_loop = not self.monitor_loop
        label = button.get_child()
        if not self.bm_found:
            self.print1("Temperature cannot be monitored. Cheetah offline", self.tag_found)
            self.monitor_loop = False
        if self.monitor_loop:
            txt = "Stop Temperature Monitoring"
        else:
            txt = "Start Temperature Monitoring"
        label.set_markup("""<span foreground="red">%s</span>""" % txt)
        if self.monitor_loop:
            self.print1("Starting Temperature Monitor Loop")
            self.statusprint("Starting Temperature Monitor Loop")
        if self.monitor_loop:
            thread = threading.Thread(target=self.run_temperature_loop)
            thread.daemon = True
            thread.start()

    def run_temperature_loop(self):
        while self.monitor_loop:
            if self.bm_found:
                self.bm.gui_logger_pause = True
            self.show_temperatures()
            time.sleep(self.monitor_timeout)
        self.bm.gui_logger_pause = False
        
    def show_temperatures(self):
        if self.bm_found:
            for pol in (0, 1):
                for temp in range(3):
                    if self.monitor_loop:
                        while not self.bm_lock:
                            self.bm_lock = True
                            self.temperature[pol * 3 + temp + 1] = self.bm.get_temperature(sensor=temp+1, polar=pol)
                            self.markup_label(self.temperature_label[pol*3 + temp + 1],
                                          "%.2f K" % (self.temperature[pol*3 + temp + 1]))
                        self.bm_lock = False
                    else:
                        return

class Application(Gtk.Application):

    def __init__(self, *args, **kwargs):
        Gtk.Application.__init__(self, *args, application_id="org.example.myapp",
                                flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
                                **kwargs)
        self.window = None

        self.add_main_option("test", ord("t"), GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Command line test", None)
                    
    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about_menu_activate)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        action = Gio.SimpleAction.new("preferences", None)
        action.connect("activate", self.on_preferences_menu_activate)
        self.add_action(action)
        
        menu_bar_string = pkg_resources.resource_string(__name__, 'menu.ui')
        #builder = Gtk.Builder.new_from_string(MENU_BAR, -1)
        builder = Gtk.Builder.new_from_string(menu_bar_string, -1)
        #self.set_app_menu(builder.get_object("app-menu"))
        self.set_menubar(builder.get_object("menubar"))

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = MSIPTemperatureGUI(application=self, title="MSIP 1mm Bias System")

        self.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()

        if options.contains("test"):
            # This is printed on the main instance
            print("Test argument recieved")

        self.activate()
        return 0

    def on_about_menu_activate(self, menuitem, data=None):
        about = Gtk.AboutDialog(transient_for=self.window, modal=True)
        about.set_program_name("MSIP 1mm Temperature Monitor System")
        about.set_version("0.1")
        about.set_copyright("(c) Gopal Narayanan <gopal@astro.umass.edu>")
        about.set_comments("A GUI for monitor and control of 1mm\nSIS Receiver System Temperatures\nfor LMT")
        about.set_logo(Gtk.IconTheme.get_default().load_icon('computer', 100, 0))
            #Gtk.Gdk.pixbuf_new_from_file("battery.png"))
        about.run()
        about.destroy()

    def on_preferences_menu_activate(self, menuitem, data=None):
        prefs_dialog = Gtk.Dialog("Preferences", self.window, 0,
                                  (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                   Gtk.STOCK_OK, Gtk.ResponseType.OK),
                                  transient_for=self.window, modal=True)
        box = prefs_dialog.get_content_area()
        grid = Gtk.Grid()
        label = Gtk.Label("Monitor Timeout:  ")
        self.monitor_timeout_entry = Gtk.Entry()
        self.monitor_timeout_entry.set_text("%s" % self.window.monitor_timeout)
        self.monitor_timeout_entry.connect("activate", self.monitor_timeout_entry_activated)
        grid.attach(label, 0, 0, 1, 1)
        grid.attach(self.monitor_timeout_entry, 1, 0, 1, 1)
        box.add(grid)
        prefs_dialog.show_all()
        prefs_dialog.run()
        prefs_dialog.destroy()

    def monitor_timeout_entry_activated(self, widget, data=None):
        try:
            self.window.monitor_timeout = float(self.monitor_timeout_entry.get_text())
            self.window.print1("Monitor Timeout set to %.3f seconds" % self.window.monitor_timeout)
        except ValueError:
            self.window.print1("Monitor Timeout should be a float not %s" % self.monitor_timeout_entry.get_text(), self.window.tag_found)

    def on_quit(self, action, param):
        self.quit()

if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)
    
