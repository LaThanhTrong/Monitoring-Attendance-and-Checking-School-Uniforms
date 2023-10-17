import psutil
import sysinfo
from PyQt5.QtCore import QThread, pyqtSignal

class HardwareInfo(QThread):
    cpu = pyqtSignal(float)
    ram = pyqtSignal(tuple)
    gpu = pyqtSignal(float)

    def run(self):
        self.ThreadActive = True
        while self.ThreadActive:
            cpu = sysinfo.getCPU()
            ram = sysinfo.getRAM()
            gpu = sysinfo.getGPU()
            self.cpu.emit(cpu)
            self.ram.emit(ram)
            if(gpu is not None):
                self.gpu.emit(gpu)
            else:
                self.gpu.emit(0)
    
    def stop(self):
        self.ThreadActive = False
        self.quit()