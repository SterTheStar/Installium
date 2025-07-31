"""
Sistema de tradução para o instalador
Suporta múltiplos idiomas através de arquivos JSON
"""

import json
import os
import locale
from pathlib import Path
from typing import Dict, Optional

class Translator:
    """Classe para gerenciar traduções"""
    
    def __init__(self):
        self.translations: Dict[str, str] = {}
        self.current_language = 'en'
        self.translations_dir = Path(__file__).parent.parent / 'translations'
        
        # Detectar idioma do sistema
        self._detect_system_language()
        
        # Carregar traduções
        self.load_language(self.current_language)
    
    def _detect_system_language(self):
        """Detecta o idioma do sistema automaticamente"""
        try:
            # Tentar múltiplas fontes para detectar o idioma
            detected_lang = None
            
            # 1. Tentar locale.getdefaultlocale()
            try:
                system_locale = locale.getdefaultlocale()[0]
                if system_locale:
                    detected_lang = system_locale[:2].lower()
            except:
                pass
            
            # 2. Tentar variáveis de ambiente se o primeiro método falhar
            if not detected_lang:
                import os
                for env_var in ['LANG', 'LANGUAGE', 'LC_ALL', 'LC_MESSAGES']:
                    env_value = os.environ.get(env_var)
                    if env_value:
                        detected_lang = env_value[:2].lower()
                        break
            
            # 3. Tentar locale.getlocale()
            if not detected_lang:
                try:
                    loc = locale.getlocale()
                    if loc[0]:
                        detected_lang = loc[0][:2].lower()
                except:
                    pass
            
            # Mapear códigos de idioma para arquivos disponíveis
            language_map = {
                'pt': 'pt',  # Português
                'en': 'en',  # Inglês
                'zh': 'zh',  # Chinês
                'ru': 'ru',  # Russo
                'es': 'pt',  # Espanhol -> Português (similar)
                'fr': 'en',  # Francês -> Inglês
                'de': 'en',  # Alemão -> Inglês
                'it': 'en',  # Italiano -> Inglês
                'ja': 'zh',  # Japonês -> Chinês (caracteres similares)
                'ko': 'zh',  # Coreano -> Chinês
            }
            
            if detected_lang and detected_lang in language_map:
                # Verificar se o arquivo de tradução existe
                candidate_lang = language_map[detected_lang]
                translation_file = self.translations_dir / f"{candidate_lang}.json"
                
                if translation_file.exists():
                    self.current_language = candidate_lang
                else:
                    self.current_language = 'en'  # Fallback para inglês
            else:
                self.current_language = 'en'  # Fallback para inglês
                
        except Exception as e:
            print(f"Erro ao detectar idioma do sistema: {e}")
            # Fallback para inglês se houver erro
            self.current_language = 'en'
    
    def load_language(self, language_code: str) -> bool:
        """
        Carrega traduções para um idioma específico
        
        Args:
            language_code: Código do idioma (en, pt, zh)
            
        Returns:
            bool: True se carregou com sucesso, False caso contrário
        """
        translation_file = self.translations_dir / f"{language_code}.json"
        
        try:
            if translation_file.exists():
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                self.current_language = language_code
                return True
            else:
                # Se arquivo não existe, tentar carregar inglês como fallback
                if language_code != 'en':
                    return self.load_language('en')
                return False
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erro ao carregar traduções para {language_code}: {e}")
            # Tentar carregar inglês como fallback
            if language_code != 'en':
                return self.load_language('en')
            return False
    
    def get(self, key: str, **kwargs) -> str:
        """
        Obtém uma tradução para uma chave
        
        Args:
            key: Chave da tradução
            **kwargs: Parâmetros para formatação da string
            
        Returns:
            str: Texto traduzido ou a chave se não encontrada
        """
        text = self.translations.get(key, key)
        
        # Aplicar formatação se houver parâmetros
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                # Se formatação falhar, retornar texto sem formatação
                pass
        
        return text
    
    def set_language(self, language_code: str) -> bool:
        """
        Muda o idioma atual
        
        Args:
            language_code: Código do novo idioma
            
        Returns:
            bool: True se mudou com sucesso, False caso contrário
        """
        return self.load_language(language_code)
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        Retorna lista de idiomas disponíveis
        
        Returns:
            Dict[str, str]: Mapeamento código -> nome do idioma
        """
        languages = {
            'en': 'English',
            'pt': 'Português',
            'zh': '中文',
            'ru': 'Русский'
        }
        
        available = {}
        for code, name in languages.items():
            translation_file = self.translations_dir / f"{code}.json"
            if translation_file.exists():
                available[code] = name
        
        return available
    
    def get_current_language(self) -> str:
        """Retorna o código do idioma atual"""
        return self.current_language
    
    def get_current_language_name(self) -> str:
        """Retorna o nome do idioma atual"""
        languages = self.get_available_languages()
        return languages.get(self.current_language, 'English')

# Instância global do tradutor
_translator = None

def get_translator() -> Translator:
    """Obtém a instância global do tradutor"""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator

def _(key: str, **kwargs) -> str:
    """
    Função de conveniência para tradução
    
    Args:
        key: Chave da tradução
        **kwargs: Parâmetros para formatação
        
    Returns:
        str: Texto traduzido
    """
    return get_translator().get(key, **kwargs)