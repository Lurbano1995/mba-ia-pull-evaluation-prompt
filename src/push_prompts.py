"""
Valida e publica o prompt otimizado no LangSmith Prompt Hub.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """Valida estrutura, template e metadados do prompt."""
    errors = []
    valid, structure_errors = validate_prompt_structure(prompt_data)
    errors.extend(structure_errors)

    system_prompt = prompt_data.get("system_prompt", "")
    user_prompt = prompt_data.get("user_prompt", "")

    if "{bug_report}" not in system_prompt and "{bug_report}" not in user_prompt:
        errors.append("O template deve conter a variável {bug_report}.")
    if not user_prompt.strip():
        errors.append("user_prompt está vazio.")
    if not isinstance(prompt_data.get("techniques_applied"), list):
        errors.append("techniques_applied deve ser uma lista.")
    if len(prompt_data.get("techniques_applied", [])) < 2:
        errors.append("Liste pelo menos 2 técnicas em techniques_applied.")

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """Faz push público do prompt e seus metadados."""
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return False

    try:
        client = Client()
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ])

        description = prompt_data.get("description", "")
        techniques = prompt_data.get("techniques_applied", [])
        tags = list(prompt_data.get("tags", []))
        tags.extend(f"technique:{technique.lower().replace(' ', '-')}" for technique in techniques)

        url = client.push_prompt(
            prompt_name,
            object=prompt,
            is_public=True,
            description=description,
            tags=list(dict.fromkeys(tags)),
        )

        print(f"✓ Prompt publicado: {prompt_name}")
        print(f"  URL: {url}")
        return True
    except Exception as exc:
        print(f"❌ Falha no push: {exc}")
        return False


def main():
    """Valida o YAML, carrega o prompt e publica a v2."""
    print_section_header("PUSH DE PROMPT OTIMIZADO PARA O LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    prompt_data_root = load_yaml(str(PROMPT_PATH))
    if not prompt_data_root:
        return 1

    prompt_data = prompt_data_root.get("bug_to_user_story_v2")
    if not isinstance(prompt_data, dict):
        print("❌ Chave 'bug_to_user_story_v2' não encontrada no YAML.")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/bug_to_user_story_v2"

    return 0 if push_prompt_to_langsmith(prompt_name, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
