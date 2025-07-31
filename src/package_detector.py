"""
Detector de pacotes e informações
Detecta o tipo de pacote e extrai informações relevantes
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
from .translator import get_translator, _

class PackageDetector:
    """Classe para detectar e extrair informações de pacotes"""
    
    SUPPORTED_EXTENSIONS = {
        '.deb': 'debian',
        '.pkg.tar.xz': 'arch',
        '.pkg.tar.zst': 'arch', 
        '.rpm': 'fedora',
        '.apk': 'alpine'
    }
    
    def __init__(self):
        self.distro = self._detect_distro()
    
    def _detect_distro(self) -> str:
        """Detecta a distribuição Linux atual"""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                
            if 'ubuntu' in content or 'debian' in content:
                return 'debian'
            elif 'arch' in content or 'manjaro' in content:
                return 'arch'
            elif 'fedora' in content or 'rhel' in content or 'centos' in content:
                return 'fedora'
            elif 'alpine' in content:
                return 'alpine'
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def detect_package_type(self, file_path: str) -> Optional[str]:
        """Detecta o tipo de pacote baseado na extensão"""
        file_path = Path(file_path)
        
        # Verificar extensões compostas primeiro
        if file_path.name.endswith('.pkg.tar.xz'):
            return 'arch'
        elif file_path.name.endswith('.pkg.tar.zst'):
            return 'arch'
        
        # Verificar extensões simples
        suffix = file_path.suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(suffix)
    
    def extract_package_info(self, file_path: str) -> Dict[str, str]:
        """Extrai informações do pacote"""
        package_type = self.detect_package_type(file_path)
        
        if not package_type:
            return {'error': _('unsupported_package_type')}
        
        try:
            if package_type == 'debian':
                return self._extract_deb_info(file_path)
            elif package_type == 'arch':
                return self._extract_arch_info(file_path)
            elif package_type == 'fedora':
                return self._extract_rpm_info(file_path)
            elif package_type == 'alpine':
                return self._extract_apk_info(file_path)
        except Exception as e:
            return {'error': _('error_extracting_info', error=str(e))}
        
        return {'error': _('package_not_implemented')}
    
    def _extract_deb_info(self, file_path: str) -> Dict[str, str]:
        """Extrai informações de pacotes .deb"""
        try:
            result = subprocess.run(['dpkg', '-I', file_path], 
                                  capture_output=True, text=True, check=True)
            
            info = {}
            for line in result.stdout.split('\n'):
                line = line.strip()
                if ':' in line and not line.startswith(' '):
                    key, value = line.split(':', 1)
                    info[key.strip().lower()] = value.strip()
            
            return {
                'name': info.get('package', 'Desconhecido'),
                'version': info.get('version', 'Desconhecida'),
                'description': info.get('description', 'Sem descrição'),
                'maintainer': info.get('maintainer', 'Desconhecido'),
                'size': info.get('installed-size', 'Desconhecido'),
                'type': 'debian'
            }
        except subprocess.CalledProcessError:
            return {'error': _('error_reading_deb')}
    
    def _extract_arch_info(self, file_path: str) -> Dict[str, str]:
        """Extrai informações de pacotes Arch (.pkg.tar.xz/.pkg.tar.zst)"""
        try:
            # Usar tar para extrair .PKGINFO
            with tempfile.TemporaryDirectory() as temp_dir:
                subprocess.run(['tar', '-xf', file_path, '-C', temp_dir, '.PKGINFO'], 
                             check=True, capture_output=True)
                
                pkginfo_path = os.path.join(temp_dir, '.PKGINFO')
                if os.path.exists(pkginfo_path):
                    info = {}
                    with open(pkginfo_path, 'r') as f:
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                info[key.strip()] = value.strip()
                    
                    return {
                        'name': info.get('pkgname', 'Desconhecido'),
                        'version': info.get('pkgver', 'Desconhecida'),
                        'description': info.get('pkgdesc', 'Sem descrição'),
                        'maintainer': info.get('packager', 'Desconhecido'),
                        'size': info.get('size', 'Desconhecido'),
                        'type': 'arch'
                    }
        except:
            pass
        
        return {'error': _('error_reading_arch')}
    
    def _extract_rpm_info(self, file_path: str) -> Dict[str, str]:
        """Extrai informações de pacotes .rpm"""
        try:
            result = subprocess.run(['rpm', '-qip', file_path], 
                                  capture_output=True, text=True, check=True)
            
            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip().lower()] = value.strip()
            
            return {
                'name': info.get('name', 'Desconhecido'),
                'version': info.get('version', 'Desconhecida'),
                'description': info.get('summary', 'Sem descrição'),
                'maintainer': info.get('vendor', 'Desconhecido'),
                'size': info.get('size', 'Desconhecido'),
                'type': 'fedora'
            }
        except subprocess.CalledProcessError:
            return {'error': _('error_reading_rpm')}
    
    def _extract_apk_info(self, file_path: str) -> Dict[str, str]:
        """Extrai informações de pacotes .apk (Alpine)"""
        try:
            # Alpine apk info
            result = subprocess.run(['apk', 'info', '--who-owns', file_path], 
                                  capture_output=True, text=True)
            
            # Fallback: tentar extrair com tar
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    subprocess.run(['tar', '-xzf', file_path, '-C', temp_dir], 
                                 check=True, capture_output=True)
                    
                    # Procurar por arquivos de controle
                    control_files = ['.PKGINFO', 'APKINDEX']
                    for cf in control_files:
                        cf_path = os.path.join(temp_dir, cf)
                        if os.path.exists(cf_path):
                            with open(cf_path, 'r') as f:
                                content = f.read()
                                # Parsing básico
                                return {
                                    'name': Path(file_path).stem.split('-')[0],
                                    'version': 'Desconhecida',
                                    'description': 'Pacote Alpine',
                                    'maintainer': 'Alpine Linux',
                                    'size': 'Desconhecido',
                                    'type': 'alpine'
                                }
                except:
                    pass
            
            # Fallback básico
            filename = Path(file_path).stem
            return {
                'name': filename.split('-')[0] if '-' in filename else filename,
                'version': 'Desconhecida',
                'description': 'Pacote Alpine',
                'maintainer': 'Alpine Linux',
                'size': 'Desconhecido',
                'type': 'alpine'
            }
            
        except:
            return {'error': _('error_reading_apk')}
    
    def is_compatible(self, package_type: str) -> bool:
        """Verifica se o pacote é compatível com a distribuição atual"""
        compatibility_map = {
            'debian': ['debian'],
            'arch': ['arch'],
            'fedora': ['fedora'],
            'alpine': ['alpine']
        }
        
        return self.distro in compatibility_map.get(package_type, [])
    
    def is_package_installed(self, package_name: str, package_type: str) -> tuple[bool, str]:
        """
        Verifica se um pacote já está instalado no sistema
        
        Args:
            package_name: Nome do pacote
            package_type: Tipo do pacote (debian, arch, fedora, alpine)
            
        Returns:
            tuple: (is_installed, version_or_message)
        """
        if not package_name or package_name == 'Desconhecido':
            return False, "Nome do pacote não disponível"
        
        try:
            if package_type == 'debian':
                return self._check_deb_installed(package_name)
            elif package_type == 'arch':
                return self._check_arch_installed(package_name)
            elif package_type == 'fedora':
                return self._check_rpm_installed(package_name)
            elif package_type == 'alpine':
                return self._check_apk_installed(package_name)
        except Exception as e:
            return False, _("error_checking_package", error=str(e))
        
        return False, _("unsupported_package_type")
    
    def _check_deb_installed(self, package_name: str) -> tuple[bool, str]:
        """Verifica se um pacote .deb está instalado"""
        try:
            result = subprocess.run(['dpkg', '-l', package_name], 
                                  capture_output=True, text=True, check=True)
            
            # Procurar por linha que indica instalação
            for line in result.stdout.split('\n'):
                if line.startswith('ii') and package_name in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        version = parts[2]
                        return True, _("installed_version", version=version)
            
            return False, _("package_not_installed_status")
        except subprocess.CalledProcessError:
            return False, _("package_not_installed_status")
    
    def _check_arch_installed(self, package_name: str) -> tuple[bool, str]:
        """Verifica se um pacote Arch está instalado"""
        try:
            result = subprocess.run(['pacman', '-Q', package_name], 
                                  capture_output=True, text=True, check=True)
            
            # Formato: nome versão
            if result.stdout.strip():
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    version = parts[1]
                    return True, _("installed_version", version=version)
                else:
                    return True, "Instalado (versão desconhecida)"
            
            return False, "Pacote não instalado"
        except subprocess.CalledProcessError:
            return False, "Pacote não instalado"
    
    def _check_rpm_installed(self, package_name: str) -> tuple[bool, str]:
        """Verifica se um pacote .rpm está instalado"""
        try:
            result = subprocess.run(['rpm', '-q', package_name], 
                                  capture_output=True, text=True, check=True)
            
            if result.stdout.strip() and not result.stdout.startswith('package'):
                # Formato: nome-versão-release.arch
                installed_info = result.stdout.strip()
                return True, f"Instalado: {installed_info}"
            
            return False, "Pacote não instalado"
        except subprocess.CalledProcessError:
            return False, "Pacote não instalado"
    
    def _check_apk_installed(self, package_name: str) -> tuple[bool, str]:
        """Verifica se um pacote .apk está instalado"""
        try:
            result = subprocess.run(['apk', 'info', '-e', package_name], 
                                  capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                installed_info = result.stdout.strip()
                return True, f"Instalado: {installed_info}"
            
            return False, "Pacote não instalado"
        except subprocess.CalledProcessError:
            return False, "Pacote não instalado"
    
    def get_installed_version(self, package_name: str, package_type: str) -> Optional[str]:
        """
        Obtém a versão instalada de um pacote
        
        Args:
            package_name: Nome do pacote
            package_type: Tipo do pacote (debian, arch, fedora, alpine)
            
        Returns:
            str: Versão instalada ou None se não encontrada
        """
        if not package_name or package_name == 'Desconhecido':
            return None
        
        try:
            if package_type == 'debian':
                return self._get_deb_version(package_name)
            elif package_type == 'arch':
                return self._get_arch_version(package_name)
            elif package_type == 'fedora':
                return self._get_rpm_version(package_name)
            elif package_type == 'alpine':
                return self._get_apk_version(package_name)
        except Exception:
            return None
        
        return None
    
    def _get_deb_version(self, package_name: str) -> Optional[str]:
        """Obtém a versão instalada de um pacote .deb"""
        try:
            result = subprocess.run(['dpkg', '-l', package_name], 
                                  capture_output=True, text=True, check=True)
            
            for line in result.stdout.split('\n'):
                if line.startswith('ii') and package_name in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[2]
            
            return None
        except subprocess.CalledProcessError:
            return None
    
    def _get_arch_version(self, package_name: str) -> Optional[str]:
        """Obtém a versão instalada de um pacote Arch"""
        try:
            result = subprocess.run(['pacman', '-Q', package_name], 
                                  capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    return parts[1]
            
            return None
        except subprocess.CalledProcessError:
            return None
    
    def _get_rpm_version(self, package_name: str) -> Optional[str]:
        """Obtém a versão instalada de um pacote .rpm"""
        try:
            result = subprocess.run(['rpm', '-q', '--queryformat', '%{VERSION}-%{RELEASE}', package_name], 
                                  capture_output=True, text=True, check=True)
            
            if result.stdout.strip() and not result.stdout.startswith('package'):
                return result.stdout.strip()
            
            return None
        except subprocess.CalledProcessError:
            return None
    
    def _get_apk_version(self, package_name: str) -> Optional[str]:
        """Obtém a versão instalada de um pacote .apk"""
        try:
            result = subprocess.run(['apk', 'info', package_name], 
                                  capture_output=True, text=True, check=True)
            
            # Procurar por linha com versão
            for line in result.stdout.split('\n'):
                if 'version:' in line.lower():
                    return line.split(':', 1)[1].strip()
                elif package_name in line and '-' in line:
                    # Tentar extrair versão do formato nome-versão
                    parts = line.strip().split('-')
                    if len(parts) > 1:
                        return '-'.join(parts[1:])
            
            return None
        except subprocess.CalledProcessError:
            return None
    
    def get_package_icon(self, package_name: str, package_type: str) -> Optional[str]:
        """
        Busca o ícone de um pacote instalado
        
        Args:
            package_name: Nome do pacote
            package_type: Tipo do pacote (debian, arch, fedora, alpine)
            
        Returns:
            str: Nome do ícone ou caminho para o arquivo de ícone, ou None se não encontrado
        """
        if not package_name or package_name == 'Desconhecido':
            return None
        
        try:
            if package_type == 'debian':
                return self._get_deb_icon(package_name)
            elif package_type == 'arch':
                return self._get_arch_icon(package_name)
            elif package_type == 'fedora':
                return self._get_rpm_icon(package_name)
            elif package_type == 'alpine':
                return self._get_apk_icon(package_name)
        except Exception:
            return None
        
        return None
    
    def _get_deb_icon(self, package_name: str) -> Optional[str]:
        """Busca ícone de um pacote .deb instalado"""
        # Locais comuns para ícones de aplicações
        icon_paths = [
            f"/usr/share/pixmaps/{package_name}.png",
            f"/usr/share/pixmaps/{package_name}.xpm",
            f"/usr/share/pixmaps/{package_name}.svg",
            f"/usr/share/icons/hicolor/48x48/apps/{package_name}.png",
            f"/usr/share/icons/hicolor/64x64/apps/{package_name}.png",
            f"/usr/share/icons/hicolor/scalable/apps/{package_name}.svg",
        ]
        
        # Verificar se algum arquivo de ícone existe
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                return icon_path
        
        # Tentar buscar arquivo .desktop para extrair ícone
        desktop_paths = [
            f"/usr/share/applications/{package_name}.desktop",
            f"/usr/local/share/applications/{package_name}.desktop",
        ]
        
        for desktop_path in desktop_paths:
            if os.path.exists(desktop_path):
                icon_name = self._extract_icon_from_desktop(desktop_path)
                if icon_name:
                    return icon_name
        
        return None
    
    def _get_arch_icon(self, package_name: str) -> Optional[str]:
        """Busca ícone de um pacote Arch instalado"""
        # Usar mesma lógica que Debian, já que Arch segue padrões similares
        return self._get_deb_icon(package_name)
    
    def _get_rpm_icon(self, package_name: str) -> Optional[str]:
        """Busca ícone de um pacote .rpm instalado"""
        # Usar mesma lógica que Debian, já que RPM segue padrões similares
        return self._get_deb_icon(package_name)
    
    def _get_apk_icon(self, package_name: str) -> Optional[str]:
        """Busca ícone de um pacote .apk instalado"""
        # Usar mesma lógica que Debian, já que Alpine segue padrões similares
        return self._get_deb_icon(package_name)
    
    def _extract_icon_from_desktop(self, desktop_file_path: str) -> Optional[str]:
        """Extrai o nome do ícone de um arquivo .desktop"""
        try:
            with open(desktop_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('Icon='):
                        icon_name = line.split('=', 1)[1].strip()
                        
                        # Se é um caminho absoluto, verificar se existe
                        if icon_name.startswith('/'):
                            if os.path.exists(icon_name):
                                return icon_name
                        else:
                            # É um nome de ícone, retornar para uso com tema de ícones
                            return icon_name
            
            return None
        except (IOError, UnicodeDecodeError):
            return None