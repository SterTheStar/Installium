"""
Instalador de pacotes
Gerencia a instalação de diferentes tipos de pacotes
"""

import subprocess
import threading
from typing import Callable, Optional
from gi.repository import GLib
from .translator import get_translator, _

class PackageInstaller:
    """Classe para instalar pacotes de diferentes distribuições"""
    
    def __init__(self):
        self.is_installing = False
        self.process = None
    
    def install_package(self, file_path: str, package_type: str, 
                       progress_callback: Callable[[str], None],
                       completion_callback: Callable[[bool, str], None]):
        """
        Instala um pacote de forma assíncrona
        
        Args:
            file_path: Caminho para o arquivo do pacote
            package_type: Tipo do pacote (debian, arch, fedora, alpine)
            progress_callback: Callback para atualizações de progresso
            completion_callback: Callback para conclusão (sucesso, mensagem)
        """
        if self.is_installing:
            completion_callback(False, _("installation_in_progress"))
            return
        
        self.is_installing = True
        
        # Executar instalação em thread separada
        thread = threading.Thread(
            target=self._install_worker,
            args=(file_path, package_type, progress_callback, completion_callback)
        )
        thread.daemon = True
        thread.start()
    
    def _install_worker(self, file_path: str, package_type: str,
                       progress_callback: Callable[[str], None],
                       completion_callback: Callable[[bool, str], None]):
        """Worker thread para instalação"""
        try:
            # Determinar comando de instalação
            cmd = self._get_install_command(file_path, package_type)
            if not cmd:
                GLib.idle_add(completion_callback, False, 
                            _("unsupported_package_type_install", type=package_type))
                return
            
            # Atualizar progresso
            GLib.idle_add(progress_callback, _("starting_installation"))
            
            # Executar comando
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Ler saída linha por linha
            output_lines = []
            while True:
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None:
                    break
                
                if line:
                    line = line.strip()
                    output_lines.append(line)
                    # Atualizar progresso com a linha atual
                    GLib.idle_add(progress_callback, _("installing_progress", progress=line[:50]))
            
            # Verificar resultado
            return_code = self.process.poll()
            
            if return_code == 0:
                GLib.idle_add(completion_callback, True, _("package_installed_successfully"))
            else:
                error_msg = "\n".join(output_lines[-5:])  # Últimas 5 linhas
                GLib.idle_add(completion_callback, False, 
                            _("installation_error", error=error_msg))
                
        except Exception as e:
            GLib.idle_add(completion_callback, False, _("installation_exception", error=str(e)))
        
        finally:
            self.is_installing = False
            self.process = None
    
    def _get_install_command(self, file_path: str, package_type: str) -> Optional[list]:
        """Retorna o comando de instalação apropriado"""
        commands = {
            'debian': ['pkexec', 'dpkg', '-i', file_path],
            'arch': ['pkexec', 'pacman', '-U', file_path, '--noconfirm'],
            'fedora': ['pkexec', 'rpm', '-i', file_path],
            'alpine': ['pkexec', 'apk', 'add', '--allow-untrusted', file_path]
        }
        
        return commands.get(package_type)
    
    def cancel_installation(self):
        """Cancela a instalação em andamento"""
        if self.process and self.is_installing:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            
            self.is_installing = False
            self.process = None
            return True
        return False
    
    def check_dependencies(self, package_type: str) -> tuple[bool, str]:
        """Verifica se as dependências necessárias estão instaladas"""
        dependencies = {
            'debian': ['dpkg', 'pkexec'],
            'arch': ['pacman', 'pkexec'],
            'fedora': ['rpm', 'pkexec'],
            'alpine': ['apk', 'pkexec']
        }
        
        required = dependencies.get(package_type, [])
        missing = []
        
        for dep in required:
            try:
                subprocess.run(['which', dep], check=True, 
                             capture_output=True)
            except subprocess.CalledProcessError:
                missing.append(dep)
        
        if missing:
            return False, _("dependencies_missing", deps=', '.join(missing))
        
        return True, _("all_dependencies_available")