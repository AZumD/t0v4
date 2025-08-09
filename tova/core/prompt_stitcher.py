"""Dynamic prompt assembly system"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class PromptStitcher:
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Load configurations
        self.core_personality = self._load_yaml("personalities/tova_core.yaml")
        self.moods = self._load_moods()
        self.functions = self._load_functions()
    
    def _load_yaml(self, relative_path: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            file_path = self.config_path / relative_path
            if file_path.exists():
                with open(file_path, 'r') as file:
                    return yaml.safe_load(file) or {}
            else:
                self.logger.warning(f"Config file not found: {file_path}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load {relative_path}: {e}")
            return {}
    
    def _load_moods(self) -> Dict[str, Dict]:
        """Load all mood configurations"""
        moods = {}
        mood_dir = self.config_path / "moods"
        
        if mood_dir.exists():
            for mood_file in mood_dir.glob("*.yaml"):
                mood_name = mood_file.stem
                moods[mood_name] = self._load_yaml(f"moods/{mood_file.name}")
        
        return moods
    
    def _load_functions(self) -> Dict[str, Dict]:
        """Load all function configurations"""
        functions = {}
        function_dir = self.config_path / "functions"
        
        if function_dir.exists():
            for func_file in function_dir.glob("*.yaml"):
                func_name = func_file.stem
                functions[func_name] = self._load_yaml(f"functions/{func_file.name}")
        
        return functions
    
    async def build_prompt(
        self,
        message: str,
        mood: Optional[str] = None,
        function: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> str:
        """Build complete prompt from components"""
        
        # Start with core personality
        prompt_parts = [self.core_personality.get("prompt", "You are TOVA, a helpful AI assistant.")]
        
        # Add mood layer
        if mood and mood in self.moods:
            mood_prompt = self.moods[mood].get("prompt_addition", "")
            if mood_prompt:
                prompt_parts.append(f"\n{mood_prompt}")
        
        # Add function layer  
        if function and function in self.functions:
            func_prompt = self.functions[function].get("prompt_addition", "")
            if func_prompt:
                prompt_parts.append(f"\n{func_prompt}")
        
        # Add context if available
        if context:
            context_str = self._format_context(context)
            if context_str:
                prompt_parts.append(f"\nRelevant Context:\n{context_str}")
        
        # Add the actual user message
        prompt_parts.append(f"\nUser: {message}\nTova:")
        
        return "".join(prompt_parts)
    
    def _format_context(self, context: Dict) -> str:
        """Format context dictionary into readable string"""
        if not context:
            return ""
        
        formatted = []
        for key, value in context.items():
            if value:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted) 