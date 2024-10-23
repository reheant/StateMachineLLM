from hydra.utils import instantiate
from omegaconf import OmegaConf
from sherpa_ai.agents import QAAgent

def get_qa_agent_from_config_file(config_path: str) -> QAAgent:
    config = OmegaConf.load(config_path)

    agent_config = instantiate(config.agent_config)
    qa_agent: QAAgent = instantiate(config.qa_agent, agent_config=agent_config)

    return qa_agent