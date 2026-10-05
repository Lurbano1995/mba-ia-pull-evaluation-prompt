"""
Testes automatizados para validação do prompt otimizado.
"""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


@pytest.fixture(scope="module")
def prompt_data():
    with PROMPT_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)
    assert isinstance(data.get("bug_to_user_story_v2"), dict)
    return data["bug_to_user_story_v2"]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se system_prompt existe e não está vazio."""
        assert prompt_data.get("system_prompt", "").strip()

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona."""
        text = prompt_data["system_prompt"].lower()
        assert "você é um product manager" in text

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige Markdown ou User Story padrão."""
        text = prompt_data["system_prompt"].lower()
        assert "markdown" in text
        assert "user story" in text
        assert "como" in text and "eu quero" in text and "para que" in text

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se existem exemplos explícitos de entrada e saída."""
        text = prompt_data["system_prompt"].lower()
        assert "few-shot" in text
        assert "exemplo 1" in text
        assert "exemplo 2" in text
        assert "entrada" in text
        assert "saída esperada" in text

    def test_prompt_no_todos(self, prompt_data):
        """Garante que não existem TODOs no prompt."""
        text = yaml.safe_dump(prompt_data, allow_unicode=True)
        assert "[todo]" not in text.lower()
        assert "todo" not in text.lower()

    def test_minimum_techniques(self, prompt_data):
        """Verifica pelo menos duas técnicas nos metadados."""
        assert len(prompt_data.get("techniques_applied", [])) >= 2
        valid, errors = validate_prompt_structure(prompt_data)
        assert valid, errors


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
