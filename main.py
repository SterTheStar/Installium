#!/usr/bin/env python3
"""
Universal Package Installer
Instalador universal de pacotes para Linux
Suporta: Debian (.deb), Arch (.pkg.tar.xz), Fedora (.rpm), Alpine (.apk)
"""

import sys
import os
import argparse

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
    def __init__(self, language=None):
        super().__init__(
            application_id='com.installium.app',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        self.connect('activate', self.on_activate)
        self.connect('open', self.on_open)
        self.package_file = None
        self.language = language
        
    def on_activate(self, app):
        # Processar argumentos não relacionados ao idioma
        remaining_args = []
        for arg in sys.argv[1:]:
            if not arg.startswith('--') or arg in ['--en', '--pt', '--ru', '--zh']:
                continue
            remaining_args.append(arg)
        
        # Verificar se há arquivo de pacote nos argumentos restantes
        for arg in remaining_args:
            if os.path.exists(arg):
                detector = PackageDetector()
                package_type = detector.detect_package_type(arg)
                if package_type:
                    self.package_file = os.path.abspath(arg)
                    print(f"Opening with package: {self.package_file}")
                    break
                else:
                    print(f"Warning: {arg} is not a supported package type")
            else:
                print(f"Error: File not found: {arg}")
        
        win = InstallerWindow(application=app, package_file=self.package_file)
        
        # Definir idioma se especificado
        if self.language:
            win.set_language(self.language)
            
        win.present()
    
    def on_open(self, app, files, n_files, hint):
        if files and len(files) > 0:
            file_path = files[0].get_path()
            if file_path and os.path.exists(file_path):
                detector = PackageDetector()
                package_type = detector.detect_package_type(file_path)
                if package_type:
                    self.package_file = file_path
                    print(f"Opening file: {file_path}")
                else:
                    print(f"Warning: {file_path} is not a supported package type")
        
        win = InstallerWindow(application=app, package_file=self.package_file)
        
        # Definir idioma se especificado
        if self.language:
            win.set_language(self.language)
            
        win.present()

def parse_arguments():
    """Processa argumentos de linha de comando"""
    parser = argparse.ArgumentParser(
        description='Universal Package Installer',
        add_help=False  # Desabilitar help padrão para não conflitar com GTK
    )
    
    # Argumentos de idioma
    parser.add_argument('--en', action='store_const', const='en', dest='language',
                       help='Set language to English')
    parser.add_argument('--pt', action='store_const', const='pt', dest='language',
                       help='Definir idioma para Português')
    parser.add_argument('--ru', action='store_const', const='ru', dest='language',
                       help='Установить язык на русский')
    parser.add_argument('--zh', action='store_const', const='zh', dest='language',
                       help='设置语言为中文')
    
    # Arquivo de pacote (opcional)
    parser.add_argument('package_file', nargs='?', 
                       help='Package file to open (.deb, .rpm, .pkg.tar.xz, .apk)')
    
    # Argumentos de ajuda
    parser.add_argument('-h', '--help', action='store_true',
                       help='Show this help message and exit')
    
    return parser.parse_known_args()

def show_help():
    """Mostra ajuda personalizada"""
    print("""Universal Package Installer

Usage: installium [OPTIONS] [PACKAGE_FILE]

Language Options:
  --en          Set language to English
  --pt          Definir idioma para Português  
  --ru          Установить язык на русский
  --zh          设置语言为中文

Arguments:
  PACKAGE_FILE  Package file to open (.deb, .rpm, .pkg.tar.xz, .apk)

Examples:
  installium --en                    # Open in English
  installium --pt package.deb        # Open package.deb in Portuguese
  installium --ru package.rpm        # Open package.rpm in Russian
  installium package.pkg.tar.xz      # Open package with system language
""")

def main():
    # Processar argumentos
    args, unknown = parse_arguments()
    
    # Mostrar ajuda se solicitado
    if args.help:
        show_help()
        return 0
    
    # Criar aplicação com idioma especificado
    app = PackageInstallerApp(language=args.language)
    
    # Preparar argumentos para GTK (remover argumentos de idioma)
    gtk_args = ['installium']  # Nome do programa
    
    # Adicionar argumentos desconhecidos (provavelmente arquivos)
    for arg in unknown:
        if not arg.startswith('--') or arg not in ['--en', '--pt', '--ru', '--zh']:
            gtk_args.append(arg)
    
    # Adicionar arquivo de pacote se especificado
    if args.package_file:
        gtk_args.append(args.package_file)
    
    return app.run(gtk_args)

if __name__ == '__main__':
    sys.exit(main())