import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class BiasGridWindow(Gtk.Grid):
    def __init__(self, polarization, lnabias):
        Gtk.Grid.__init__(self)
        self.polarization = polarization
        self.lnabias = lnabias
        self.title_label = Gtk.Label('Polarization %d' % self.polarization)
        self.attach(self.title_label, 1, 0, 5, 1)
        magnet_frame = self.add_magnet_frame()
        self.attach(magnet_frame, 0, 1, 4, 4)
        sis_frame = self.add_sis_frame()
        self.attach(sis_frame, 5, 1, 4, 4)
        lna_frame = self.add_lna_frame()
        self.attach(lna_frame, 10, 1, 4, 4)

    def add_magnet_frame(self):
        magnet_frame = Gtk.Frame()
        magnet_frame.set_label('Magnets')
        mgrid = Gtk.Grid()
        magnet_frame.add(mgrid)
        col, row = 0, 0
        self.magnet_set_current_entry = {}
        self.magnet_read_voltage_label = {}
        self.magnet_read_current_label = {}
        for magnet in (1, 2):
            label = Gtk.Label('Magnet %d;  Set Current:  ' % magnet)
            self.magnet_set_current_entry[magnet] = Gtk.Entry()
            col = 0
            mgrid.attach(label, col, row, 1, 1)
            mgrid.attach(self.magnet_set_current_entry[magnet], col+1, row, 1, 1)
            self.magnet_read_voltage_label[magnet] = Gtk.Label('Voltage: ')
            self.magnet_read_current_label[magnet] = Gtk.Label('Current: ')
            col = 0
            row += 1
            mgrid.attach(self.magnet_read_voltage_label[magnet], col, row, 1, 1)
            mgrid.attach(self.magnet_read_current_label[magnet], col+1, row, 1, 1)
            row += 1
        return magnet_frame

    def add_sis_frame(self):
        sis_frame = Gtk.Frame()
        sis_frame.set_label('SIS Mixers')
        sgrid = Gtk.Grid()
        sis_frame.add(sgrid)
        col, row = 0, 0
        self.sis_set_voltage_entry = {}
        self.sis_read_voltage_label = {}
        self.sis_read_current_label = {}
        self.sis_ivsweep_button = {}
        for sis in (1, 2):
            label = Gtk.Label('SIS %d;  Set Voltage (mV):  ' % sis)
            self.sis_set_voltage_entry[sis] = Gtk.Entry()
            col = 0
            sgrid.attach(label, col, row, 1, 1)
            sgrid.attach(self.sis_set_voltage_entry[sis], col+1, row, 1, 1)
            self.sis_read_voltage_label[sis] = Gtk.Label('Voltage: ')
            self.sis_read_current_label[sis] = Gtk.Label('Current: ')
            col = 0
            row += 1
            sgrid.attach(self.sis_read_voltage_label[sis], col, row, 1, 1)
            sgrid.attach(self.sis_read_current_label[sis], col+1, row, 1, 1)
            row += 1
            self.sis_ivsweep_button[sis] = Gtk.Button.new_with_label("Do IV Sweep SIS%d" % sis)
            sgrid.attach(self.sis_ivsweep_button[sis], col, row, 3, 1)
            row += 1
        return sis_frame
    
    def add_lna_frame(self):
        lna_frame = Gtk.Frame()
        lna_frame.set_label('LNAs')
        lgrid = Gtk.Grid()
        lna_frame.add(lgrid)
        self.lna_set_drain_current_entry = {}
        self.lna_set_drain_voltage_entry = {}
        self.lna_read_drain_voltage_label = {}
        self.lna_read_drain_current_label = {}
        self.lna_read_gate_voltage_label = {}
        col = 0
        self.lnastate_switch = {}
        for lna in (1, 2):
            frame = Gtk.Frame()
            frame.set_label('LNA%d' % lna)
            lgrid.attach(frame, col*6, 0, 6, 6)
            grid = Gtk.Grid()
            frame.add(grid)
            label = Gtk.Label("LNA%d Status:" % lna)
            grid.attach(label, 0, 0, 3, 1)
            self.lnastate_switch[lna] = Gtk.Switch()
            self.lnastate_switch[lna].set_active(self.lnabias[lna].state)
            grid.attach(self.lnastate_switch[lna], 3, 0, 3, 1)
            self.lna_set_drain_current_entry[lna] = {}
            self.lna_set_drain_voltage_entry[lna] = {}
            self.lna_read_drain_voltage_label[lna] = {}
            self.lna_read_drain_current_label[lna] = {}
            self.lna_read_gate_voltage_label[lna] = {}
            icol = 0
            irow = 1
            for stage in (1, 2, 3):
                iframe = Gtk.Frame()
                iframe.set_label('Stage%d' % stage)
                grid.attach(iframe, 0, stage, 1, 1)
                igrid = Gtk.Grid()
                iframe.add(igrid)
                # row 1
                label = Gtk.Label('Set Drain Voltage:  ')
                igrid.attach(label, 0, 0, 1, 1)
                self.lna_set_drain_voltage_entry[lna][stage] = Gtk.Entry()
                igrid.attach(self.lna_set_drain_voltage_entry[lna][stage], 1, 0,
                             1, 1)
                self.lna_set_drain_voltage_entry[lna][stage].set_width_chars(8)
                label = Gtk.Label('Set Drain Current: ')
                igrid.attach(label, 2, 0, 1, 1)
                self.lna_set_drain_current_entry[lna][stage] = Gtk.Entry()
                igrid.attach(self.lna_set_drain_current_entry[lna][stage], 3, 0,
                             1, 1)
                self.lna_set_drain_current_entry[lna][stage].set_width_chars(8)
                # row 2
                self.lna_read_drain_voltage_label[lna][stage] = Gtk.Label("Vd%d" % stage)
                igrid.attach(self.lna_read_drain_voltage_label[lna][stage],
                             0, 1, 1, 1)
                self.lna_read_drain_current_label[lna][stage] = Gtk.Label("Id%d" % stage)
                igrid.attach(self.lna_read_drain_current_label[lna][stage],
                             1, 1, 1, 1)
                self.lna_read_gate_voltage_label[lna][stage] = Gtk.Label("Vg%d" % stage)
                igrid.attach(self.lna_read_gate_voltage_label[lna][stage],
                             2, 1, 1, 1)
            col += 1
        return lna_frame

