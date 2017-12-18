import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from msipbias.biasmodule import BiasModule
from msipbias.gui.biastab_gui import BiasGridWindow
import pkg_resources

class MSIP1mmGUI():
        def on_mainwindow_destroy(self, object, data=None):
                print "quit with cancel"
                Gtk.main_quit()
                                  
        def on_gtk_quit_activate(self, menuitem, data=None):
                print "quit from menu"
                Gtk.main_quit()

        def on_about_menu_activate(self, menuitem, data=None):
                self.response = self.aboutdialog.run()
                self.aboutdialog.hide()

        def __init__(self):
                #self.gladefile = "GUI/msip1mm_gui.glade" # store the file name
                self.gladeXML = pkg_resources.resource_string(__name__, 'msip1mm_gui.glade')
                self.builder = Gtk.Builder() # create an instance of the gtk.Builder
                #self.builder.add_from_file(self.gladefile) # add the xml file to the Builder
                self.builder.add_from_string(self.gladeXML) # add the xml file to the Builder
                self.builder.connect_signals(self)
                
                self.mainwindow = self.builder.get_object("mainwindow")
                self.accelgroup = self.builder.get_object("accelgroup")
                self.mainwindow.add_accel_group(self.accelgroup)
                self.aboutdialog = self.builder.get_object('aboutdialog')

                self.biasboxes = self.builder.get_object('biasboxes')
                self.notebook = Gtk.Notebook()
                self.biasboxes.add(self.notebook)
                self.biasgrid = {}
                for polarization in range(2):
                        self.biasgrid[polarization] = BiasGridWindow(polarization=polarization)
                        self.notebook.append_page(self.biasgrid[polarization],
                                                  Gtk.Label('Pol %d' % polarization))

                self.mainwindow.show_all()
