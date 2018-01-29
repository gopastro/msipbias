import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio, Pango

from msipbias.biasmodule import BiasModule
from msipbias.utils import MSIPGeneralError
from msipbias.orm.biasdata.biasvalues.models import Temperature, \
    TemperatureChannel
from .biastab_gui import BiasGridWindow
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

class LNABias(object):
    def __init__(self):
        self.Vd = {}
        self.Id = {}
        self.Vg = {}
        self.state = False
        for stage in (1, 2, 3): 
            self.Vd[stage] = 0.7
            self.Id[stage] = 3.0

class MSIP1mmGUI(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        Gtk.ApplicationWindow.__init__(self, *args, **kwargs)
        #title='MSIP 1mm Bias System')
        self.set_default_size(1024, 768)

        # This will be in the windows group and have the "win" prefix
        max_action = Gio.SimpleAction.new_stateful("maximize", None,
                                           GLib.Variant.new_boolean(False))
        max_action.connect("change-state", self.on_maximize_toggle)
        self.add_action(max_action)
        self.temperature_to_database = True
        # Keep it in sync with the actual state
        self.connect("notify::is-maximized",
                            lambda obj, pspec: max_action.set_state(
                                               GLib.Variant.new_boolean(obj.props.is_maximized)))

        self.lnabias = {}
        for polarization in (0, 1):
            self.lnabias[polarization] = {}
            for lna in (1, 2):
                self.lnabias[polarization][lna] = LNABias()

        self.bm_found = False
        self.temperature = {}
        self.monitor_timeout = 10.0 # seconds
        self.bm_lock = False  # true if bias module is in use
        self.monitor_loop = False  # true if monitor loop is in use

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)
        self.add_top_box()
        self.add_temperature_sensors()
        self.add_biasgrids()
        self.add_logging_window()
        self.add_statusbar()
        #self.temperature_label[1].set_label('100 K')
        #self.bm_switch.set_active(True)
        self.open_cheetah()
        self.show_temperatures()
        self.show_all()
        self.ivsweep_dialog = {}
        for polarization in (0, 1):
            self.ivsweep_dialog[polarization] = {}
            for sis in (1, 2):
                self.ivsweep_dialog[polarization][sis] = None
                
    def add_top_box(self):
        tbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label()
        label.set_markup("<b>1mm MSIP SIS Receiver Bias System</b>")
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
        
    def add_biasgrids(self):
        self.notebook = Gtk.Notebook()
        self.box.pack_start(self.notebook, False, False, 0)

        self.biasgrid = {}
        for polarization in range(2):
            self.biasgrid[polarization] = BiasGridWindow(polarization=polarization,
                                                         lnabias=self.lnabias[polarization])
            self.notebook.append_page(self.biasgrid[polarization],
                                      Gtk.Label('Pol %d' % polarization))
        self.setup_biasgrid_signals()

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
        self.print1("1mm MSIP Bias GUI Started")
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
        widget.set_markup("""<span foreground="%s">%s</span>""" % (color, text))

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
                            if self.temperature_to_database:
                                # Store to database
                                tempchannel = TemperatureChannel.objects.get(polarization=pol,
                                                                             sensor=temp+1)
                                temperature = Temperature(tempchannel=tempchannel,
                                                          temperature=self.temperature[pol*3 + temp + 1])
                                temperature.save()                            
                        self.bm_lock = False
                    else:
                        return

    def setup_biasgrid_signals(self):
        for polarization in range(2):
            # Magnets
            for magnet in (1, 2):
                self.biasgrid[polarization].magnet_set_current_entry[magnet].connect("activate", self.set_magnet_current, [polarization, magnet])
            # SIS Mixers
            for sis in (1, 2):
                self.biasgrid[polarization].sis_set_voltage_entry[sis].connect("activate", self.set_sis_voltage, [polarization, sis])
                self.biasgrid[polarization].sis_ivsweep_button[sis].connect("clicked", self.do_sis_ivsweep, [polarization, sis])
            # LNAs
            for lna in (1, 2):
                self.biasgrid[polarization].lnastate_switch[lna].connect("notify::active", self.on_lna_switch_activated, [polarization, lna])
                for stage in (1, 2, 3):
                    self.biasgrid[polarization].lna_set_drain_voltage_entry[lna][stage].connect("activate", self.set_lna_drain_voltage, [polarization, lna, stage])
                    self.biasgrid[polarization].lna_set_drain_current_entry[lna][stage].connect("activate", self.set_lna_drain_current, [polarization, lna, stage])

    def on_lna_switch_activated(self, switch, gparam, data):
        polarization, lna = data
        if switch.get_active():
            state = "on"
            s = True
        else:
            state = "off"
            s = False
        self.lnabias[polarization][lna].state = s
        print "Polarization %d: LNA %d Switch was turned %s" % (polarization, lna, state)
        if self.lnabias[polarization][lna].state:
            self.lna_turn_on(polarization, lna)
        else:
            self.lna_turn_off(polarization, lna)

    def lna_turn_on(self, polarization, lna):
        for stage in (1, 2, 3):
            self.biasgrid[polarization].lna_set_drain_voltage_entry[lna][stage].set_text("%.3f" % self.lnabias[polarization][lna].Vd[stage])
            self.biasgrid[polarization].lna_set_drain_current_entry[lna][stage].set_text("%.3f" % self.lnabias[polarization][lna].Id[stage])
            # First set drain current and then voltage
            self.update_and_read_lna_voltages(drain_current=self.lnabias[polarization][lna].Id[stage],
                                              polarization=polarization, lna=lna, stage=stage)
            time.sleep(0.010)
            self.update_and_read_lna_voltages(drain_voltage=self.lnabias[polarization][lna].Vd[stage],
                                              polarization=polarization, lna=lna, stage=stage)            
            time.sleep(0.010)
            self.update_and_read_lna_voltages(drain_voltage=self.lnabias[polarization][lna].Vd[stage],
                                              polarization=polarization, lna=lna, stage=stage)
            
    def lna_turn_off(self, polarization, lna):
        for stage in (1, 2, 3):
            self.biasgrid[polarization].lna_set_drain_voltage_entry[lna][stage].set_text("0.0")
            self.biasgrid[polarization].lna_set_drain_current_entry[lna][stage].set_text("0.0")
            self.update_and_read_lna_voltages(drain_current=0.0,
                                              polarization=polarization, lna=lna, stage=stage)
            time.sleep(0.010)
            self.update_and_read_lna_voltages(drain_voltage=0.0,
                                              polarization=polarization, lna=lna, stage=stage)            
            time.sleep(0.010)
            self.update_and_read_lna_voltages(drain_voltage=0.0,
                                              polarization=polarization, lna=lna, stage=stage)                        

    def set_magnet_current(self, widget, data):
        polarization, magnet = data
        try:
            magnet_current = float(widget.get_text())
        except ValueError:
            self.print1("Pol %d, magnet %d entry should be float not %s" % (polarization, magnet, widget.get_text()))
            return
        self.print1("Requesting pol: %d, magnet: %d to a current of %s mA" % (polarization, magnet, widget.get_text()))
        self.update_and_read_magnet(magnet_current, polarization, magnet)

    def update_and_read_magnet(self, magnet_current, polarization, magnet):
        if self.bm_found and not self.bm_lock:
            self.bm_lock = True
            self.bm.set_magnet_current(magnet_current, magnet=magnet, polar=polarization)
            time.sleep(0.005)
            read_volts = self.bm.get_magnet_voltage(magnet=magnet, polar=polarization)
            self.biasgrid[polarization].magnet_read_voltage_label[magnet].set_text("%.3f V" % read_volts)
            read_current = self.bm.get_magnet_current(magnet=magnet, polar=polarization)
            self.biasgrid[polarization].magnet_read_current_label[magnet].set_text("%.3f mA" % read_current)
            self.bm_lock = False

    def set_sis_voltage(self, widget, data):
        polarization, sis = data
        try:
            sis_voltage = float(widget.get_text())
        except ValueError:
            self.print1("Pol %d, SIS %d entry should be float not %s" % (polarization, sis, widget.get_text()))
            return
        self.print1("Requesting pol: %d, SIS: %d to a current of %s mA" % (polarization, sis, widget.get_text()))
        self.update_and_read_sis(sis_voltage, polarization, sis)

    def update_and_read_sis(self, sis_voltage, polarization, sis):
        if self.bm_found and not self.bm_lock:
            self.bm_lock = True
            self.bm.set_sis_mixer_voltage(sis_voltage, sis=sis, polar=polarization)
            time.sleep(0.005)
            read_volts = self.bm.get_sis_voltage(sis=sis, polar=polarization)
            self.biasgrid[polarization].sis_read_voltage_label[sis].set_text("%.3f mV" % read_volts)
            read_current = self.bm.get_sis_current(sis=sis, polar=polarization)
            self.biasgrid[polarization].sis_read_current_label[sis].set_text("%.3f uA" % read_current)
            self.bm_lock = False

    def do_sis_ivsweep(self, widget, data):
        polarization, sis = data
        self.ivsweep_dialog[polarization][sis] = Gtk.Dialog("IV Sweep Pol %d SIS %d" % (polarization, sis),
                                                            self, 0,
                                                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                                             Gtk.STOCK_OK, Gtk.ResponseType.OK),
                                                            transient_for=self, modal=True)
                
        self.ivsweep_dialog[polarization][sis].set_default_size(400, 400)
        box = self.ivsweep_dialog[polarization][sis].get_content_area()
        grid = Gtk.Grid()
        label = Gtk.Label("Sweep Range: ")
        self.sis_mixer_sweep_vmin = Gtk.Entry()
        self.sis_mixer_sweep_vmax = Gtk.Entry()
        grid.attach(label, 0, 0, 1, 1)
        grid.attach(self.sis_mixer_sweep_vmin, 1, 0, 1, 1)
        grid.attach(self.sis_mixer_sweep_vmax, 2, 0, 1, 1)
        self.sweep_now_button = Gtk.Button.new_with_label("Start IV Sweep")
        self.sweep_now_button.connect("clicked", self.do_sweep, [polarization, sis])
        grid.attach(self.sweep_now_button, 0, 1, 2, 1)
        box.add(grid)
        self.sweep_sw = Gtk.ScrolledWindow()
        self.sweep_sw.set_size_request(700, 700)
        #grid.attach(sw, 0, 2, 5, 5)
        box.add(self.sweep_sw)

        
        self.fig = Figure(figsize=(5,5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvas(self.fig)
        self.canvas.set_size_request(700, 700)
        self.sweep_sw.add_with_viewport(self.canvas)

        self.toolbar = NavigationToolbar(self.canvas, self.ivsweep_dialog[polarization][sis])
        box.pack_start(self.toolbar, False, True, 0)
        
        self.ivsweep_dialog[polarization][sis].show_all()
        self.ivsweep_dialog[polarization][sis].run()
        self.ivsweep_dialog[polarization][sis].destroy()

    def do_sweep_test(self, widget, data):
        polarization, sis = data
        #self.ax.plot([], [], marker='o', markersize=8, animated=True)
        #self.ax.set_xllabel(-10.0, 10.0)
        #self.ax.set
        self.ax.set_xlabel('Vj (mV)')
        self.ax.set_ylabel('Ij (uA)')
        for v in numpy.arange(-10., 10.0, 0.1):
            print v
            self.ax.plot(v, v/65.0, 'o', color='k', markersize=12)
            self.canvas.draw()
    
        
    def do_sweep(self, widget, data):
        polarization, sis = data
        self.sweep_polarization = polarization
        self.sweep_sis = sis
        try:
            vmin = float(self.sis_mixer_sweep_vmin.get_text())
            if vmin < -20.0:
                vmin = -20.0
        except ValueError:
            vmin = -20.0
        try:
            vmax = float(self.sis_mixer_sweep_vmax.get_text())
            if vmax > 20.0:
                vmax = 20.0
        except ValueError:
            vmax = 20.0
        self.bm.gui_logger_pause = True
        self.vj = []
        self.ij = []
        #self.start_sweep_animation(vmin, vmax, 0.1)
        self.bm.set_sis_mixer_voltage(vmin, sis=self.sweep_sis,
                                      polar=self.sweep_polarization)
        time.sleep(0.001)
        self.vj.append(self.bm.get_sis_voltage(sis=self.sweep_sis,
                                               polar=self.sweep_polarization))
        self.ij.append(1000 * self.bm.get_sis_current(sis=self.sweep_sis,
                                               polar=self.sweep_polarization))        #convert to uA

        self.ax.plot(self.vj[0], self.ij[0], 'o', color='k',
                     markersize=8)
        self.ax.set_xlabel('Vj (mV)')
        self.ax.set_ylabel('Ij (uA)')

        #self.do_sweep_animation(vmin, vmax, 0.1)
        for v in numpy.arange(vmin, vmax, 0.1):
             self.bm.set_sis_mixer_voltage(v, sis=sis, polar=polarization)
             time.sleep(0.002)
             self.vj.append(self.bm.get_sis_voltage(sis=sis, polar=polarization))
             self.ij.append(1000*self.bm.get_sis_current(sis=sis, polar=polarization))
             self.ax.plot(self.vj[-1], self.ij[-1], 'o', color='k', markersize=8)
             self.canvas.draw()
        # vj = numpy.array(vj)
        # ij = numpy.array(ij)
        # print vj.shape, ij.shape
        # 
        self.bm.gui_logger_pause = False
        #self.ax.set_xlabel('Vj (mV)')
        #self.ax.set_ylabel('Ij (uA)')
        
    # def start_sweep_animation(self):
    #     print "In init function"
    #     self.line.set_data(self.vj[0], self.ij[0])
    #     return self.line, 
    #     #ax.plot(numpy.arange(10), 'o-')

    # def animate(self, v):
    #     print "Setting voltage: %s" % v
    #     self.bm.set_sis_mixer_voltage(v, sis=self.sweep_sis,
    #                                   polar=self.sweep_polarization)
    #     self.vj.append(self.bm.get_sis_voltage(sis=self.sweep_sis,
    #                                            polar=self.sweep_polarization))
    #     self.ij.append(self.bm.get_sis_current(sis=self.sweep_sis,
    #                                            polar=self.sweep_polarization))        
    #     self.line.set_data(self.vj[-1], self.ij[-1])
    #     self.canvas.draw()
    #     return self.line, 
    
    # def do_sweep_animation(self, vmin, vmax, vres):
    #     print "In Do Sweep Animate"
    #     ani = animation.FuncAnimation(self.fig, self.animate,
    #                                   frames=numpy.arange(vmin, vmax, vres), 
    #                                   interval=25, blit=False,
    #                                   init_func=self.start_sweep_animation)

    def set_lna_drain_voltage(self, widget, data):
        polarization, lna, stage = data
        try:
            drain_voltage = float(widget.get_text())
        except ValueError:
            self.print1("Pol %d, LNA %d, Stage %d drain voltage entry should be float not %s" % (polarization, lna, stage, widget.get_text()))
            return
        self.print1("Requesting pol: %d, LNA: %d, stage: %d to a voltage of %s V" % (polarization, lna, stage, widget.get_text()))
        self.update_and_read_lna_voltages(drain_voltage=drain_voltage,
                                          polarization=polarization,
                                          lna=lna, stage=stage)

    def set_lna_drain_current(self, widget, data):
        polarization, lna, stage = data
        try:
            drain_current = float(widget.get_text())
        except ValueError:
            self.print1("Pol %d, LNA %d, Stage %d drain current entry should be float not %s" % (polarization, lna, stage, widget.get_text()))
            return
        self.print1("Requesting pol: %d, LNA: %d, stage: %d to a current of %s mA" % (polarization, lna, stage, widget.get_text()))
        self.update_and_read_lna_voltages(drain_current=drain_current,
                                          polarization=polarization,
                                          lna=lna,
                                          stage=stage)
        

    def update_and_read_lna_voltages(self, drain_voltage=None, drain_current=None,
                                     polarization=0, lna=1, stage=1):
        if self.bm_found and not self.bm_lock:
            self.bm_lock = True
            if drain_voltage is not None:
                self.bm.set_lna_drain_voltage(drain_voltage, lna=lna, stage=stage, polar=polarization)
            if drain_current is not None:
                self.bm.set_lna_drain_current(drain_current, lna=lna, stage=stage, polar=polarization)
            time.sleep(0.005)
            read_volts = self.bm.get_lna_drain_voltage(lna=lna, stage=stage, polar=polarization)
            self.biasgrid[polarization].lna_read_drain_voltage_label[lna][stage].set_text("%.3f V" % read_volts)
            read_current = self.bm.get_lna_drain_current(lna=lna, stage=stage, polar=polarization)
            self.biasgrid[polarization].lna_read_drain_current_label[lna][stage].set_text("%.3f mA" % read_current)
            read_volts = self.bm.get_lna_gate_voltage(lna=lna, stage=stage, polar=polarization)
            self.biasgrid[polarization].lna_read_gate_voltage_label[lna][stage].set_text("%.3f V" % read_volts)            
            self.bm_lock = False
        


            
        # def add_file_menu_actions(self, action_group):
    #     action_filemenu = Gtk.Action("FileMenu", "File", None, None)
    #     action_group.add_action(action_filemenu)

    #     action_filequit = Gtk.Action("FileQuit", None, None, Gtk.STOCK_QUIT)
    #     action_filequit.connect("activate", self.on_menu_file_quit)
    #     action_group.add_action(action_filequit)

    # def add_edit_menu_actions(self, action_group):
    #     action_group.add_actions([
    #         ("EditMenu", None, "Edit"),
    #         ("EditCopy", Gtk.STOCK_COPY, None, None, None,
    #          self.on_menu_others),
    #         ("EditPaste", Gtk.STOCK_PASTE, None, None, None,
    #          self.on_menu_others),
    #     ])

    # def add_help_menu_actions(self, action_group):
    #     action_group.add_actions([
    #         ("HelpMenu", None, "Help"),
    #         ("HelpAbout", Gtk.STOCK_ABOUT, None, None, None,
    #          self.on_about_menu_activate),
    #         ])
    
    # def add_cheetah_action(self, action_group):
    #     action_group.add_actions([
    #         ("Cheetah", Gtk.STOCK_CONNECT, None, None, None,
    #          self.on_cheetah_activate),
    #         ])

    # def on_cheetah_activate(self, widget):
    #     print("Cheetah Menu item " + widget.get_name() + " was selected")
    
    # def create_ui_manager(self):
    #     uimanager = Gtk.UIManager()

    #     # Throws exception if something went wrong
    #     uimanager.add_ui_from_string(UI_INFO)

    #     # Add the accelerator group to the toplevel window
    #     accelgroup = uimanager.get_accel_group()
    #     self.add_accel_group(accelgroup)
    #     return uimanager

    # def on_menu_file_quit(self, widget):
    #     Gtk.main_quit()

    # def on_menu_others(self, widget):
    #     print("Menu item " + widget.get_name() + " was selected")        

    # def on_about_menu_activate(self, menuitem, data=None):
    #     about = Gtk.AboutDialog()
    #     about.set_program_name("MSIP 1mm Bias System")
    #     about.set_version("0.1")
    #     about.set_copyright("(c) Gopal Narayanan <gopal@astro.umass.edu>")
    #     about.set_comments("A GUI for monitor and control of 1mm\nSIS Receiver System for LMT")
    #     about.set_logo(Gtk.IconTheme.get_default().load_icon('computer', 100, 0))
    #         #Gtk.Gdk.pixbuf_new_from_file("battery.png"))
    #     about.run()
    #     about.destroy()

    # def on_button_press_event(self, widget, event):
    #     # Check if right mouse button was preseed
    #     if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
    #         self.popup.popup(None, None, None, None, event.button, event.time)
    #         return True # event has been handled
        

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
            self.window = MSIP1mmGUI(application=self, title="MSIP 1mm Bias System")

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
        about.set_program_name("MSIP 1mm Bias System")
        about.set_version("0.1")
        about.set_copyright("(c) Gopal Narayanan <gopal@astro.umass.edu>")
        about.set_comments("A GUI for monitor and control of 1mm\nSIS Receiver System for LMT")
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
        label = Gtk.Label("Store to Database: ")
        self.temperature_database_btn = Gtk.CheckButton(label="Store in db")
        self.temperature_database_btn.connect("toggled", self.temperature_database_btn_toggled)
        self.temperature_database_btn.set_active(self.window.temperature_to_database)
        grid.attach(label, 0, 1, 1, 1)
        grid.attach(self.temperature_database_btn, 1, 1, 1, 1)
        box.add(grid)
        prefs_dialog.show_all()
        prefs_dialog.run()
        prefs_dialog.destroy()

    def temperature_database_btn_toggled(self, widget, data=None):
        self.window.temperature_to_database = widget.get_active()
        print "temperature databases button toggled: %d" % self.window.temperature_to_database
        
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
    
