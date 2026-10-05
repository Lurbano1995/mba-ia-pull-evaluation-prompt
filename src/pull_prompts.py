"""
Faz pull do prompt semente do LangSmith Prompt Hub e o normaliza para YAML local.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"


def _message_template(message):
    """Extrai o template de uma mensagem LangChain."""
    template = getattr(message, "prompt", None)
    if template is not None:
        return getattr(template, "template", str(template))
    return getattr(message, "content", str(message))


def pull_prompts_from_langsmith():
    """Baixa o prompt semente e salva sua representação YAML."""
    client = Client()
    prompt = client.pull_prompt(
        PROMPT_NAME,
        dangerously_pull_public_prompt=True,
    )

    messages = getattr(prompt, "messages", None)
    if not messages:
        raise ValueError("O prompt retornado pelo LangSmith não possui mensagens.")

    system_prompt = ""
    user_prompt = ""
    for message in messages:
        role = getattr(message, "type", "")
        content = _message_template(message)
        if role == "system" and not system_prompt:
            system_prompt = content
        elif role in ("human", "user") and not user_prompt:
            user_prompt = content

    if not system_prompt:
        raise ValueError("Não foi encontrada mensagem system no prompt retornado.")
    if not user_prompt:
        user_prompt = "{bug_report}"

    data = {
        "bug_to_user_story_v1": {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if not save_yaml(data, str(OUTPUT_PATH)):
        raise RuntimeError(f"Não foi possível salvar {OUTPUT_PATH}")

    return data


def main():
    """Valida o ambiente, executa o pull e retorna código de saída."""
    print_section_header("PULL DE PROMPT DO LANGSMITH HUB")
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    try:
        pull_prompts_from_langsmith()
        print(f"✓ Prompt salvo em: {OUTPUT_PATH}")
        return 0
    except Exception as exc:
        print(f"❌ Falha no pull: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
