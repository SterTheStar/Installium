"""
Janela de configurações
Interface para configurações do aplicativo
"""

import os
from gi.repository import Gtk, Adw, GLib
from .translator import get_translator, _

class SettingsWindow(Adw.PreferencesWindow):
    """Janela de configurações do aplicativo"""
    
    def __init__(self, parent_window):
        super().__init__()
        
        self.parent_window = parent_window
        self.translator = get_translator()
        
        # Configurações da janela
        self.set_title(_("settings"))
        self.set_default_size(600, 500)
        self.set_transient_for(parent_window)
        self.set_modal(True)
        
        # Armazenar referências para elementos que precisam ser atualizados
        self.language_page = None
        self.about_page = None
        self.language_group = None
        self.language_row = None
        self.app_info_group = None
        self.tech_info_group = None
        self.app_description = None
        self.formats_row = None
        self.developer_row = None
        self.github_row = None
        self.license_row = None
        
        # Construir interface
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface da janela de configurações"""
        
        # Página de Idioma
        self.language_page = Adw.PreferencesPage()
        self.language_page.set_title(_("language"))
        self.language_page.set_icon_name("preferences-desktop-locale-symbolic")
        
        # Grupo de seleção de idioma
        self.language_group = Adw.PreferencesGroup()
        self.language_group.set_title(_("language_selection"))
        self.language_group.set_description(_("language_selection_description"))
        
        # Row para seleção de idioma
        self.language_row = Adw.ComboRow()
        self.language_row.set_title(_("interface_language"))
        self.language_row.set_subtitle(_("language_restart_note"))
        
        # Criar modelo de idiomas
        language_model = Gtk.StringList()
        languages = [
            _("automatic"),
            "English",
            "Português",
            "Русский",
            "中文"
        ]
        
        for lang in languages:
            language_model.append(lang)
        
        self.language_row.set_model(language_model)
        
        # Definir seleção atual
        current_lang = self.translator.current_language
        if current_lang == 'auto':
            self.language_row.set_selected(0)
        elif current_lang == 'en':
            self.language_row.set_selected(1)
        elif current_lang == 'pt':
            self.language_row.set_selected(2)
        elif current_lang == 'ru':
            self.language_row.set_selected(3)
        elif current_lang == 'zh':
            self.language_row.set_selected(4)
        else:
            self.language_row.set_selected(0)  # Default to automatic
        
        # Conectar sinal de mudança
        self.language_row.connect("notify::selected", self._on_language_changed)
        
        self.language_group.add(self.language_row)
        self.language_page.add(self.language_group)
        
        # Página Sobre
        self.about_page = Adw.PreferencesPage()
        self.about_page.set_title(_("about"))
        self.about_page.set_icon_name("help-about-symbolic")
        
        # Grupo de informações do aplicativo
        self.app_info_group = Adw.PreferencesGroup()
        self.app_info_group.set_title(_("application_info"))
        
        # Logo e nome do aplicativo
        app_header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        app_header.set_halign(Gtk.Align.CENTER)
        app_header.set_margin_top(20)
        app_header.set_margin_bottom(20)
        
        # Ícone do aplicativo
        app_icon = Gtk.Image()
        app_icon.set_from_icon_name("package-x-generic")
        app_icon.set_pixel_size(64)
        app_header.append(app_icon)
        
        # Nome do aplicativo
        app_name = Gtk.Label()
        app_name.set_markup("<span size='x-large' weight='bold'>Installium</span>")
        app_header.append(app_name)
        
        # Versão
        app_version = Gtk.Label()
        app_version.set_markup("<span size='small'>v1.0.0</span>")
        app_version.add_css_class("dim-label")
        app_header.append(app_version)
        
        # Descrição
        self.app_description = Gtk.Label()
        self.app_description.set_text(_("app_description"))
        self.app_description.set_wrap(True)
        self.app_description.set_justify(Gtk.Justification.CENTER)
        self.app_description.set_margin_top(10)
        app_header.append(self.app_description)
        
        # Adicionar header ao grupo
        self.app_info_group.add(app_header)
        
        # Informações técnicas
        self.tech_info_group = Adw.PreferencesGroup()
        self.tech_info_group.set_title(_("technical_info"))
        
        # Suporte a formatos
        self.formats_row = Adw.ActionRow()
        self.formats_row.set_title(_("supported_formats"))
        self.formats_row.set_subtitle("Debian (.deb), Arch (.pkg.tar.xz/.pkg.tar.zst), Fedora (.rpm), Alpine (.apk)")
        self.formats_row.set_icon_name("application-x-archive-symbolic")
        self.tech_info_group.add(self.formats_row)
        
        # Desenvolvedor
        self.developer_row = Adw.ActionRow()
        self.developer_row.set_title(_("developer"))
        self.developer_row.set_subtitle("Esther (SterTheStar)")
        self.developer_row.set_icon_name("avatar-default-symbolic")
        self.tech_info_group.add(self.developer_row)
        
        # GitHub
        self.github_row = Adw.ActionRow()
        self.github_row.set_title("GitHub")
        self.github_row.set_subtitle("https://github.com/SterTheStar/Installium")
        self.github_row.set_icon_name("web-browser-symbolic")
        self.tech_info_group.add(self.github_row)
        
        # Licença
        self.license_row = Adw.ActionRow()
        self.license_row.set_title(_("license"))
        self.license_row.set_subtitle("GPL v3.0")
        self.license_row.set_icon_name("text-x-copying-symbolic")
        self.tech_info_group.add(self.license_row)
        
        self.about_page.add(self.app_info_group)
        self.about_page.add(self.tech_info_group)
        
        # Adicionar páginas à janela
        self.add(self.language_page)
        self.add(self.about_page)
    
    def _update_translations(self):
        """Atualiza todas as traduções da interface"""
        # Atualizar título da janela
        self.set_title(_("settings"))
        
        # Atualizar páginas
        if self.language_page:
            self.language_page.set_title(_("language"))
        if self.about_page:
            self.about_page.set_title(_("about"))
        
        # Atualizar grupos
        if self.language_group:
            self.language_group.set_title(_("language_selection"))
            self.language_group.set_description(_("language_selection_description"))
        
        if self.app_info_group:
            self.app_info_group.set_title(_("application_info"))
        
        if self.tech_info_group:
            self.tech_info_group.set_title(_("technical_info"))
        
        # Atualizar language row (sem recriar o modelo para evitar conflitos)
        if self.language_row:
            self.language_row.set_title(_("interface_language"))
            self.language_row.set_subtitle(_("language_restart_note"))
        
        # Atualizar descrição do app
        if self.app_description:
            self.app_description.set_text(_("app_description"))
        
        # Atualizar rows de informações técnicas
        if self.formats_row:
            self.formats_row.set_title(_("supported_formats"))
        
        if self.developer_row:
            self.developer_row.set_title(_("developer"))
        
        if self.license_row:
            self.license_row.set_title(_("license"))
    
    def _update_translations_safe(self):
        """Versão segura da atualização de traduções"""
        try:
            self._update_translations()
        except Exception as e:
            print(f"Error updating translations: {e}")
        return False  # Remove from idle queue
    
    def _on_language_changed(self, combo_row, param):
        """Callback para mudança de idioma"""
        selected = combo_row.get_selected()
        
        # Mapear seleção para código de idioma
        language_codes = ['auto', 'en', 'pt', 'ru', 'zh']
        
        if selected < len(language_codes):
            new_language = language_codes[selected]
            
            # Evitar loop infinito - verificar se realmente mudou
            current_lang = self.translator.current_language
            if new_language == current_lang:
                return
            
            # Salvar configuração
            self._save_language_setting(new_language)
            
            # Aplicar mudança de idioma
            if new_language == 'auto':
                # Detectar idioma do sistema
                self.translator.detect_system_language()
            else:
                self.translator.set_language(new_language)
            
            # Usar GLib.idle_add para atualizar a interface de forma segura
            GLib.idle_add(self._update_translations_safe)
            
            # Atualizar interface da janela principal
            if hasattr(self.parent_window, '_update_translations'):
                GLib.idle_add(self.parent_window._update_translations)
            
            # Mostrar toast de confirmação
            GLib.idle_add(self._show_language_changed_toast)
    
    def _save_language_setting(self, language_code):
        """Salva a configuração de idioma (implementação básica)"""
        try:
            config_dir = os.path.expanduser("~/.config/installium")
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, "settings.conf")
            with open(config_file, 'w') as f:
                f.write(f"language={language_code}\n")
        except Exception as e:
            print(f"Error saving language setting: {e}")
    
    def _show_language_changed_toast(self):
        """Mostra toast de confirmação de mudança de idioma"""
        toast = Adw.Toast()
        toast.set_title(_("language_changed"))
        toast.set_timeout(3)
        
        # Adicionar toast à janela principal se possível
        if hasattr(self.parent_window, 'add_toast'):
            self.parent_window.add_toast(toast)
    
    @staticmethod
    def load_language_setting():
        """Carrega a configuração de idioma salva"""
        try:
            config_file = os.path.expanduser("~/.config/installium/settings.conf")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.startswith('language='):
                            return line.split('=', 1)[1].strip()
        except Exception as e:
            print(f"Error loading language setting: {e}")
        
        return 'auto'  # Default