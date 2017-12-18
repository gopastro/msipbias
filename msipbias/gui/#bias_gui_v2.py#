import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from msipbias.biasmodule import BiasModule
from .biastab_gui import BiasGridWindow

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='FileQuit' />
    </menu>
    <menu action='EditMenu'>
      <menuitem action='EditCopy' />
      <menuitem action='EditPaste' />
    </menu>
    <menu action='HelpMenu'>
      <menuitem action='HelpAbout' />
    </menu>
  </menubar>
  <toolbar name='ToolBar'>
    <toolitem action='FileQuit' />
    <toolitem action='Cheetah' action='justify-right'/>
  </toolbar>
  <popup name='PopupMenu'>
    <menuitem action='EditCopy' />
    <menuitem action='EditPaste' />
  </popup>
</ui>
"""

class MSIP1mmGUI(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title='MSIP 1mm Bias System')
        self.set_default_size(1024, 768)

        action_group = Gtk.ActionGroup("my_actions")

        self.add_file_menu_actions(action_group)
        self.add_edit_menu_actions(action_group)
        self.add_help_menu_actions(action_group)
        self.add_cheetah_action(action_group)
        
        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        menubar = uimanager.get_widget("/MenuBar")
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.pack_start(menubar, False, False, 0)

        toolbar = uimanager.get_widget("/ToolBar")
        self.box.pack_start(toolbar, False, False, 0)

        self.notebook = Gtk.Notebook()
        self.box.pack_start(self.notebook, False, False, 0)

        self.biasgrid = {}
        for polarization in range(2):
            self.biasgrid[polarization] = BiasGridWindow(polarization=polarization)
            self.notebook.append_page(self.biasgrid[polarization],
                                      Gtk.Label('Pol %d' % polarization))
        
        eventbox = Gtk.EventBox()
        eventbox.connect("button-press-event", self.on_button_press_event)
        self.box.pack_start(eventbox, True, True, 0)

        #label = Gtk.Label("Right-click to see the popup menu.")
        #eventbox.add(label)

        self.popup = uimanager.get_widget("/PopupMenu")

        self.add(self.box)

        
    def add_file_menu_actions(self, action_group):
        action_filemenu = Gtk.Action("FileMenu", "File", None, None)
        action_group.add_action(action_filemenu)

        action_filequit = Gtk.Action("FileQuit", None, None, Gtk.STOCK_QUIT)
        action_filequit.connect("activate", self.on_menu_file_quit)
        action_group.add_action(action_filequit)

    def add_edit_menu_actions(self, action_group):
        action_group.add_actions([
            ("EditMenu", None, "Edit"),
            ("EditCopy", Gtk.STOCK_COPY, None, None, None,
             self.on_menu_others),
            ("EditPaste", Gtk.STOCK_PASTE, None, None, None,
             self.on_menu_others),
        ])

    def add_help_menu_actions(self, action_group):
        action_group.add_actions([
            ("HelpMenu", None, "Help"),
            ("HelpAbout", Gtk.STOCK_ABOUT, None, None, None,
             self.on_about_menu_activate),
            ])
    
    def add_cheetah_action(self, action_group):
        action_group.add_actions([
            ("Cheetah", Gtk.STOCK_CONNECT, None, None, None,
             self.on_cheetah_activate),
            ])

    def on_cheetah_activate(self, widget):
        print("Cheetah Menu item " + widget.get_name() + " was selected")
    
    def create_ui_manager(self):
        uimanager = Gtk.UIManager()

        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

    def on_menu_file_quit(self, widget):
        Gtk.main_quit()

    def on_menu_others(self, widget):
        print("Menu item " + widget.get_name() + " was selected")        

    def on_about_menu_activate(self, menuitem, data=None):
        about = Gtk.AboutDialog()
        about.set_program_name("MSIP 1mm Bias System")
        about.set_version("0.1")
        about.set_copyright("(c) Gopal Narayanan <gopal@astro.umass.edu>")
        about.set_comments("A GUI for monitor and control of 1mm\nSIS Receiver System for LMT")
        about.set_logo(Gtk.IconTheme.get_default().load_icon('computer', 100, 0))
            #Gtk.Gdk.pixbuf_new_from_file("battery.png"))
        about.run()
        about.destroy()

    def on_button_press_event(self, widget, event):
        # Check if right mouse button was preseed
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.popup.popup(None, None, None, None, event.button, event.time)
            return True # event has been handled
        
