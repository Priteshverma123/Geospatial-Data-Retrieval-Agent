from langchain_openai import ChatOpenAI

from  utils.config import config, load_env_variables

env_name = load_env_variables()
OPENAI_API_KEY = config[env_name].OPENAI_API_KEY
temperature=config[env_name].TEMPERATURE

def get_llm_model(model_provider: str, model_name: str, temperature):
    try:
        return openai_llm_model(api_key=OPENAI_API_KEY, model_name=model_name, temperature=temperature)
    except:
        raise ValueError(f"Unknown LLM model: {model_provider}")


def openai_llm_model(
        api_key,
        model_name="gpt-4o",
        temperature: float = 0):
    return ChatOpenAI(
        api_key=api_key,
        model_name=model_name,
        temperature=temperature)
