#!/usr/bin/env python3
"""
Universal Package Installer
Instalador universal de pacotes para Linux
Suporta: Debian (.deb), Arch (.pkg.tar.xz), Fedora (.rpm), Alpine (.apk)
"""

import sys
import os

# 👉 Redirecionar stderr para suprimir Gtk-WARNINGs
sys.stderr = open(os.devnull, 'w')

# Suprimir warnings Python
import warnings
warnings.simplefilter("ignore")

# Suprimir logs do PyGObject
import logging
logging.getLogger('gi').setLevel(logging.ERROR)

# Suprimir mensagens de debug do GLib/GTK
os.environ['G_MESSAGES_DEBUG'] = 'none'

# GTK
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio
from src.installer_window import InstallerWindow
from src.package_detector import PackageDetector

class PackageInstallerApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id='com.installium.app',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        self.connect('activate', self.on_activate)
        self.connect('open', self.on_open)
        self.package_file = None
        
    def on_activate(self, app):
        if len(sys.argv) > 1:
            package_file_arg = sys.argv[1]
            if os.path.exists(package_file_arg):
                detector = PackageDetector()
                package_type = detector.detect_package_type(package_file_arg)
                if package_type:
                    self.package_file = os.path.abspath(package_file_arg)
                    print(f"Abrindo com pacote: {self.package_file}")
                else:
                    print(f"Aviso: {package_file_arg} não é um tipo de pacote suportado")
            else:
                print(f"Erro: Arquivo não encontrado: {package_file_arg}")
        
        win = InstallerWindow(application=app, package_file=self.package_file)
        win.present()
    
    def on_open(self, app, files, n_files, hint):
        if files and len(files) > 0:
            file_path = files[0].get_path()
            if file_path and os.path.exists(file_path):
                detector = PackageDetector()
                package_type = detector.detect_package_type(file_path)
                if package_type:
                    self.package_file = file_path
                    print(f"Abrindo arquivo: {file_path}")
                else:
                    print(f"Aviso: {file_path} não é um tipo de pacote suportado")
        
        win = InstallerWindow(application=app, package_file=self.package_file)
        win.present()

def main():
    app = PackageInstallerApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    main()
