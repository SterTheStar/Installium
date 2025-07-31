"""
Janela principal do instalador
Interface GTK4 para instalação de pacotes
"""

import os
from pathlib import Path
from gi.repository import Gtk, Adw, GLib, Gio, Gdk
from .package_detector import PackageDetector
from .package_installer import PackageInstaller
from .translator import get_translator, _

class InstallerWindow(Adw.ApplicationWindow):
    """Janela principal do instalador de pacotes"""
    
    def __init__(self, application, package_file=None):
        super().__init__(application=application)
        
        # Obter tradutor
        self.translator = get_translator()
        
        # Configurações da janela
        self.set_title(_("app_title"))
        self.set_default_size(600, 240)  # Largura reduzida
        self.set_size_request(600, 240)  # Tamanho mínimo
        self.set_resizable(False)  # Janela com tamanho fixo
        self.set_deletable(True)
        
        # Componentes
        self.detector = PackageDetector()
        self.installer = PackageInstaller()
        self.package_info = None
        self.package_file_path = None
        
        # Construir interface
        self._build_ui()
        
        # Conectar sinal para ajustar tamanho após mostrar
        self.connect('realize', self._on_window_realize)
        
        # Se um arquivo foi passado, carregá-lo
        if package_file and os.path.exists(package_file):
            self._load_package(package_file)
    
    def _on_window_realize(self, widget):
        """Callback chamado quando a janela é realizada"""
        # Aguardar um momento para a janela se ajustar
        GLib.timeout_add(100, self._finalize_window_setup)
    
    def _finalize_window_setup(self):
        """Finaliza a configuração da janela"""
        # Obter tamanho natural da janela
        natural_size = self.get_default_size()
        
        # Ajustar para um tamanho adequado
        width = max(600, natural_size[0])  # Largura mínima reduzida
        height = max(240, natural_size[1])  # Ajustado para altura menor
        
        # Definir tamanho final
        self.set_default_size(width, height)
        
        # Desabilitar redimensionamento
        self.set_resizable(False)
        
        return False  # Remove o timeout
    
    def _build_ui(self):
        """Constrói a interface do usuário"""
        # Container principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(16)  # Reduzido para eliminar espaço em branco
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Área de conteúdo principal
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        # Header com ícone e título (alinhado à esquerda)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_halign(Gtk.Align.START)
        
        # Ícone do pacote
        self.package_icon = Gtk.Image()
        self.package_icon.set_from_icon_name("package-x-generic")
        self.package_icon.set_pixel_size(64)
        self.package_icon.set_valign(Gtk.Align.START)
        header_box.append(self.package_icon)
        
        # Informações do pacote
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_valign(Gtk.Align.START)
        
        self.package_name = Gtk.Label()
        self.package_name.set_markup("<b>Nenhum pacote selecionado</b>")
        self.package_name.set_halign(Gtk.Align.START)
        info_box.append(self.package_name)
        
        self.package_version = Gtk.Label()
        self.package_version.set_text("Clique em 'Selecionar Pacote' para começar")
        self.package_version.set_halign(Gtk.Align.START)
        self.package_version.add_css_class("dim-label")
        info_box.append(self.package_version)
        
        # Status de instalação
        self.install_status = Gtk.Label()
        self.install_status.set_halign(Gtk.Align.START)
        self.install_status.set_visible(False)
        info_box.append(self.install_status)
        
        header_box.append(info_box)
        content_box.append(header_box)
        
        # Separador
        separator = Gtk.Separator()
        separator.set_margin_top(10)
        separator.set_margin_bottom(10)
        content_box.append(separator)
        
        # Área de detalhes (sempre visível)
        self.details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.details_box.set_margin_bottom(18)  # Espaçamento abaixo da info de tamanho
        self.details_box.set_visible(True)
        
        # Grid com informações detalhadas
        details_grid = Gtk.Grid()
        details_grid.set_column_spacing(12)
        details_grid.set_row_spacing(4)
        details_grid.set_halign(Gtk.Align.START)
        
        # Labels de informações
        labels = ["Tipo:", "Versão:", "Descrição:", "Mantenedor:", "Tamanho:"]
        self.detail_values = []
        
        for i, label_text in enumerate(labels):
            label = Gtk.Label()
            label.set_text(label_text)
            label.set_halign(Gtk.Align.END)
            label.set_valign(Gtk.Align.START)
            label.add_css_class("dim-label")
            details_grid.attach(label, 0, i, 1, 1)
            
            value = Gtk.Label()
            value.set_halign(Gtk.Align.START)
            value.set_valign(Gtk.Align.START)
            value.set_selectable(True)
            value.set_wrap(False)  # Desabilitar wrap para controlar truncamento
            value.set_max_width_chars(50)
            value.set_ellipsize(3)  # Pango.EllipsizeMode.END
            value.set_text("-")  # Valor inicial vazio
            details_grid.attach(value, 1, i, 1, 1)
            self.detail_values.append(value)
        
        self.details_box.append(details_grid)
        content_box.append(self.details_box)
        
        # Barra de progresso (inicialmente oculta)
        self.progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.progress_box.set_visible(False)
        
        self.progress_label = Gtk.Label()
        self.progress_label.set_text("Preparando instalação...")
        self.progress_box.append(self.progress_label)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_pulse_step(0.1)
        self.progress_box.append(self.progress_bar)
        
        content_box.append(self.progress_box)
        
        # Adicionar área de conteúdo ao container principal
        main_box.append(content_box)
        
        # Separador final
        final_separator = Gtk.Separator()
        main_box.append(final_separator)
        
        # Botões de ação (fixos na parte inferior)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_box.set_margin_top(16)
        
        # Container para botão selecionar e fechar (à esquerda)
        left_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        left_buttons_box.set_halign(Gtk.Align.START)
        
        # Botão selecionar pacote com ícone de arquivo
        self.select_button = Gtk.Button()
        self.select_button.set_icon_name("folder-open-symbolic")
        self.select_button.set_tooltip_text("Selecionar Pacote")
        self.select_button.add_css_class("suggested-action")
        self.select_button.connect("clicked", self._on_select_package)
        left_buttons_box.append(self.select_button)
        
        # Botão fechar com ícone X
        self.close_button = Gtk.Button()
        self.close_button.set_icon_name("window-close-symbolic")
        self.close_button.set_tooltip_text("Fechar")
        self.close_button.connect("clicked", self._on_close_app)
        left_buttons_box.append(self.close_button)
        
        button_box.append(left_buttons_box)
        
        # Espaçador para empurrar o botão instalar para a direita
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        button_box.append(spacer)
        
        # Botão instalar (à direita)
        self.install_button = Gtk.Button()
        self.install_button.set_label("Instalar")
        self.install_button.set_sensitive(False)
        self.install_button.connect("clicked", self._on_install_package)
        self.install_button.set_halign(Gtk.Align.END)
        button_box.append(self.install_button)
        
        main_box.append(button_box)
        
        # Adicionar ao window
        self.set_content(main_box)
        
        # Aplicar traduções iniciais
        self._update_translations()
    
        
    def _update_translations(self):
        """Atualiza todos os textos da interface com as traduções"""
        # Título da janela
        self.set_title(_("app_title"))
        
        # Textos iniciais
        if not self.package_info:
            self.package_name.set_markup(f"<b>{_('no_package_selected')}</b>")
            self.package_version.set_text(_("click_to_start"))
            # Manter apenas tooltip para o botão de seleção (sem label)
            self.select_button.set_tooltip_text(_("select_package"))
            self.install_button.set_label(_("install"))
        
        # Labels dos detalhes
        detail_labels = [
            _("package_type"),
            _("package_version"), 
            _("package_description"),
            _("package_maintainer"),
            _("package_size")
        ]
        
        # Atualizar labels se o grid já foi criado
        if hasattr(self, 'details_box') and self.details_box.get_first_child():
            grid = self.details_box.get_first_child()
            for i, label_text in enumerate(detail_labels):
                label_widget = grid.get_child_at(0, i)
                if label_widget:
                    label_widget.set_text(label_text)
        
        # Texto da barra de progresso
        self.progress_label.set_text(_("preparing_installation"))
    
    def set_language(self, language_code: str):
        """
        Muda o idioma da interface
        
        Args:
            language_code: Código do idioma (en, pt, zh)
        """
        if self.translator.set_language(language_code):
            self._update_translations()
            
            # Recarregar informações do pacote se houver
            if self.package_info:
                self._update_package_display()
                self._check_installation_status()
    
    def _on_select_package(self, button):
        """Callback para seleção de pacote"""
        dialog = Gtk.FileChooserDialog(
            title=_("select_package"),
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN
        )
        
        dialog.add_button(_("cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(_("open"), Gtk.ResponseType.ACCEPT)
        
        # Filtros de arquivo baseados na distribuição
        distro = self.detector.distro
        
        # Mapear distribuição para filtros
        distro_filters = {
            'debian': (_("debian_packages"), "*.deb"),
            'arch': (_("arch_packages"), "*.pkg.tar.xz;*.pkg.tar.zst"),
            'fedora': (_("fedora_packages"), "*.rpm"),
            'alpine': (_("alpine_packages"), "*.apk")
        }
        
        # Criar lista de filtros com o da distribuição atual primeiro
        filters = []
        default_filter = None
        
        # Adicionar filtro da distribuição atual primeiro (se conhecido)
        if distro in distro_filters:
            name, pattern = distro_filters[distro]
            file_filter = Gtk.FileFilter()
            file_filter.set_name(name)
            for p in pattern.split(';'):
                file_filter.add_pattern(p)
            filters.append(file_filter)
            default_filter = file_filter
        
        # Adicionar outros filtros
        all_filters = [
            (_("debian_packages"), "*.deb"),
            (_("arch_packages"), "*.pkg.tar.xz;*.pkg.tar.zst"),
            (_("fedora_packages"), "*.rpm"),
            (_("alpine_packages"), "*.apk"),
            (_("all_files"), "*")
        ]
        
        for name, pattern in all_filters:
            # Pular se já foi adicionado como padrão
            if distro in distro_filters and distro_filters[distro] == (name, pattern):
                continue
                
            file_filter = Gtk.FileFilter()
            file_filter.set_name(name)
            for p in pattern.split(';'):
                file_filter.add_pattern(p)
            filters.append(file_filter)
        
        # Adicionar todos os filtros ao diálogo
        for file_filter in filters:
            dialog.add_filter(file_filter)
        
        # Definir filtro padrão se disponível
        if default_filter:
            dialog.set_filter(default_filter)
        
        dialog.connect("response", self._on_file_dialog_response)
        dialog.present()
    
    def _on_file_dialog_response(self, dialog, response):
        """Callback para resposta do diálogo de arquivo"""
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            self._load_package(file_path)
        
        dialog.destroy()
    
    def _load_package(self, file_path):
        """Carrega informações do pacote"""
        self.package_file_path = file_path
        
        # Extrair informações do pacote
        self.package_info = self.detector.extract_package_info(file_path)
        
        if 'error' in self.package_info:
            self._show_error(self.package_info['error'])
            return
        
        # Atualizar interface
        self._update_package_display()
        
        # Verificar se o pacote já está instalado
        self._check_installation_status()
        
        # Verificar compatibilidade
        package_type = self.package_info.get('type')
        if not self.detector.is_compatible(package_type):
            self._show_warning(
                _("incompatible_package", type=package_type, distro=self.detector.distro)
            )
    
    def _check_installation_status(self):
        """Verifica se o pacote já está instalado e compara versões"""
        package_name = self.package_info.get('name')
        package_type = self.package_info.get('type')
        package_version = self.package_info.get('version')
        
        if package_name and package_name != 'Desconhecido':
            is_installed, status_msg = self.detector.is_package_installed(package_name, package_type)
            
            if is_installed:
                # Obter versão instalada
                installed_version = self.detector.get_installed_version(package_name, package_type)
                
                if installed_version and package_version:
                    version_comparison = self._compare_versions(package_version, installed_version)
                    
                    if version_comparison > 0:
                        # Versão do pacote é maior - mostrar "Atualizar"
                        self.install_status.set_markup(f"<span color='#f6d32d'>⚠ Versão mais recente disponível (instalada: {installed_version})</span>")
                        self.install_status.set_visible(True)
                        self.install_button.set_label("Atualizar")
                        self.install_button.add_css_class("suggested-action")
                        self.install_button.remove_css_class("destructive-action")
                    elif version_comparison < 0:
                        # Versão instalada é maior - mostrar "Downgrade"
                        self.install_status.set_markup(f"<span color='#f66151'>⚠ Versão mais antiga (instalada: {installed_version})</span>")
                        self.install_status.set_visible(True)
                        self.install_button.set_label("Downgrade")
                        self.install_button.add_css_class("destructive-action")
                        self.install_button.remove_css_class("suggested-action")
                    else:
                        # Mesma versão - mostrar "Reinstalar"
                        self.install_status.set_markup(f"<span color='#2ec27e'>✓ {status_msg}</span>")
                        self.install_status.set_visible(True)
                        self.install_button.set_label("Reinstalar")
                        self.install_button.add_css_class("destructive-action")
                        self.install_button.remove_css_class("suggested-action")
                else:
                    # Não foi possível comparar versões - usar comportamento padrão
                    self.install_status.set_markup(f"<span color='#2ec27e'>✓ {status_msg}</span>")
                    self.install_status.set_visible(True)
                    self.install_button.set_label("Reinstalar")
                    self.install_button.add_css_class("destructive-action")
                    self.install_button.remove_css_class("suggested-action")
            else:
                self.install_status.set_markup(f"<span color='#e01b24'>✗ {status_msg}</span>")
                self.install_status.set_visible(True)
                self.install_button.set_label("Instalar")
                self.install_button.add_css_class("suggested-action")
                self.install_button.remove_css_class("destructive-action")
    
    def _update_package_display(self):
        """Atualiza a exibição das informações do pacote"""
        info = self.package_info
        package_name = info.get('name', 'Desconhecido')
        package_type = info.get('type')
        
        # Tentar obter ícone do pacote instalado primeiro
        package_icon = None
        if package_name != 'Desconhecido':
            package_icon = self.detector.get_package_icon(package_name, package_type)
        
        # Atualizar ícone
        if package_icon:
            # Se encontrou ícone específico do pacote
            if package_icon.startswith('/'):
                # É um caminho de arquivo
                try:
                    self.package_icon.set_from_file(package_icon)
                except:
                    # Se falhar, usar fallback
                    self._set_fallback_icon(package_type)
            else:
                # É um nome de ícone do tema
                try:
                    self.package_icon.set_from_icon_name(package_icon)
                except:
                    # Se falhar, usar fallback
                    self._set_fallback_icon(package_type)
        else:
            # Usar ícone padrão baseado no tipo
            self._set_fallback_icon(package_type)
        
        # Atualizar textos
        self.package_name.set_markup(f"<b>{package_name}</b>")
        self.package_version.set_text(f"Versão: {info.get('version', 'Desconhecida')}")
        
        # Formatar tamanho
        formatted_size = self._format_size(info.get('size', 'Desconhecido'))
        
        # Atualizar detalhes (incluindo descrição)
        details = [
            info.get('type', 'Desconhecido').title(),
            info.get('version', 'Desconhecida'),
            info.get('description', 'Sem descrição'),
            info.get('maintainer', 'Desconhecido'),
            formatted_size
        ]
        
        for i, value in enumerate(details):
            if i < len(self.detail_values):
                # Para a descrição (índice 2), configurar tooltip se for muito longa
                if i == 2:  # Índice da descrição
                    self._set_description_with_tooltip(self.detail_values[i], str(value))
                else:
                    self.detail_values[i].set_text(str(value))
                    self.detail_values[i].set_tooltip_text("")  # Limpar tooltip para outros campos
        
        # Mostrar detalhes e habilitar instalação
        self.details_box.set_visible(True)
        self.install_button.set_sensitive(True)
        self.select_button.set_tooltip_text("Selecionar Outro Pacote")
        self.select_button.remove_css_class("suggested-action")
    
    def _set_description_with_tooltip(self, label, description):
        """
        Define a descrição no label com truncamento e tooltip se necessário
        
        Args:
            label: Widget Gtk.Label onde definir a descrição
            description: Texto da descrição
        """
        if not description or description in ['-', 'Sem descrição', 'Desconhecido']:
            label.set_text(description or '-')
            label.set_tooltip_text("")
            return
        
        # Definir limite de caracteres para uma linha (aproximadamente)
        max_chars = 60  # Ajuste baseado na largura disponível
        
        if len(description) > max_chars:
            # Truncar e adicionar reticências
            truncated = description[:max_chars].rstrip() + "..."
            label.set_text(truncated)
            # Definir tooltip com a descrição completa
            label.set_tooltip_text(description)
        else:
            # Descrição cabe em uma linha
            label.set_text(description)
            label.set_tooltip_text("")
    
    def _set_fallback_icon(self, package_type):
        """Define ícone padrão baseado no tipo de pacote"""
        icon_map = {
            'debian': 'application-x-deb',
            'arch': 'package-x-generic',
            'fedora': 'application-x-rpm',
            'alpine': 'package-x-generic'
        }
        
        icon_name = icon_map.get(package_type, 'package-x-generic')
        self.package_icon.set_from_icon_name(icon_name)
    
    def _on_install_package(self, button):
        """Callback para instalação do pacote"""
        if not self.package_file_path or not self.package_info:
            return
        
        package_type = self.package_info.get('type')
        
        # Verificar dependências
        deps_ok, deps_msg = self.installer.check_dependencies(package_type)
        if not deps_ok:
            self._show_error(f"Dependências faltando:\n{deps_msg}")
            return
        
        # Mostrar progresso e desabilitar botões
        self._show_progress(True)
        self.install_button.set_sensitive(False)
        self.select_button.set_sensitive(False)
        
        # Iniciar instalação
        self.installer.install_package(
            self.package_file_path,
            package_type,
            self._on_progress_update,
            self._on_installation_complete
        )
        
        # Iniciar animação da barra de progresso
        GLib.timeout_add(100, self._pulse_progress)
    
    def _pulse_progress(self):
        """Anima a barra de progresso"""
        if self.progress_box.get_visible():
            self.progress_bar.pulse()
            return True  # Continuar animação
        return False  # Parar animação
    
    def _on_progress_update(self, message):
        """Callback para atualizações de progresso"""
        self.progress_label.set_text(message)
    
    def _on_installation_complete(self, success, message):
        """Callback para conclusão da instalação"""
        self._show_progress(False)
        self.install_button.set_sensitive(True)
        self.select_button.set_sensitive(True)
        
        if success:
            self._show_success(message)
            # Recheck installation status after successful installation
            self._check_installation_status()
        else:
            self._show_error(message)
    
    def _show_progress(self, show):
        """Mostra/oculta a barra de progresso"""
        self.progress_box.set_visible(show)
        self.details_box.set_visible(not show)
        if show:
            self.install_status.set_visible(False)
        else:
            # Reshow install status if package is loaded
            if self.package_info:
                self.install_status.set_visible(True)
    
    def _on_cancel(self, button):
        """Callback para cancelamento"""
        if self.installer.is_installing:
            if self.installer.cancel_installation():
                self._show_progress(False)
                self.install_button.set_sensitive(True)
                self.select_button.set_sensitive(True)
                self._show_info("Instalação cancelada")
        else:
            self.close()
    
    def _on_close_app(self, button):
        """Callback para fechar o aplicativo"""
        self.close()
    
    def _show_error(self, message):
        """Mostra diálogo de erro"""
        self._show_dialog("Erro", message, "dialog-error")
    
    def _show_warning(self, message):
        """Mostra diálogo de aviso"""
        self._show_dialog("Aviso", message, "dialog-warning")
    
    def _show_success(self, message):
        """Mostra diálogo de sucesso"""
        self._show_dialog("Sucesso", message, "dialog-information")
    
    def _show_info(self, message):
        """Mostra diálogo de informação"""
        self._show_dialog("Informação", message, "dialog-information")
    
    def _compare_versions(self, version1, version2):
        """
        Compara duas versões de pacote
        Retorna: 1 se version1 > version2, -1 se version1 < version2, 0 se iguais
        """
        import re
        
        def normalize_version(version):
            """Normaliza uma string de versão para comparação"""
            if not version:
                return []
            
            # Remove caracteres não numéricos e pontos, mantendo apenas números e pontos
            version = re.sub(r'[^0-9.]', '', str(version))
            
            # Divide por pontos e converte para inteiros
            parts = []
            for part in version.split('.'):
                if part.isdigit():
                    parts.append(int(part))
                elif part:
                    # Se contém números, extrai o primeiro número
                    numbers = re.findall(r'\d+', part)
                    if numbers:
                        parts.append(int(numbers[0]))
            
            return parts
        
        try:
            v1_parts = normalize_version(version1)
            v2_parts = normalize_version(version2)
            
            # Igualar o tamanho das listas preenchendo com zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            # Comparar parte por parte
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1
            
            return 0  # Versões são iguais
            
        except (ValueError, TypeError):
            # Se não conseguir comparar, considera como iguais
            return 0
    
    def _format_size(self, size_str):
        """Formata o tamanho em KB, MB, GB"""
        if not size_str or size_str == 'Desconhecido':
            return 'Desconhecido'
        
        try:
            # Tentar extrair número do string
            import re
            numbers = re.findall(r'\d+', str(size_str))
            if not numbers:
                return size_str
            
            size_bytes = int(numbers[0])
            
            # Se o valor já parece estar em KB (comum em pacotes .deb)
            if 'k' in size_str.lower() or size_bytes < 10000:
                size_bytes *= 1024  # Converter KB para bytes
            
            # Converter para unidades apropriadas
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
                
        except (ValueError, IndexError):
            return size_str
    
    def _show_dialog(self, title, message, icon_name):
        """Mostra um diálogo genérico"""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=title,
            body=message
        )
        
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")
        
        dialog.present()