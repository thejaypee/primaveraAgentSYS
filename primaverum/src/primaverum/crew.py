from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
import os
from dotenv import load_dotenv

load_dotenv()

@CrewBase
class Primaverum():
    """Primaverum crew: NVIDIA Native Architecture"""

    base_dir = os.path.dirname(__file__)
    agents_config = os.path.join(base_dir, 'config/agents.yaml')
    tasks_config = os.path.join(base_dir, 'config/tasks.yaml')

    # 1. NVIDIA CLOUD (NIM API) - For Heavy Thinking
    heavy_thinker = LLM(
        model="nvidia/llama-3.1-nemotron-70b-instruct",
        api_key=os.getenv("NVIDIA_API_KEY")
    )

    # 2. LOCAL NVIDIA (don1) - Trainer/Bridge
    # Using 'openai/' prefix tells LiteLLM to use the OpenAI-compatible API
    # provided by your NVIDIA local container.
    don1_trainer = LLM(
        model="openai/local-trainer",
        base_url=os.getenv("DON1_URL", "http://don1:8000/v1"),
        api_key="none"
    )
    
    # 3. LOCAL NVIDIA (don2) - LogicAgent/Core
    don2_logic = LLM(
        model="openai/local-logic-model",
        base_url=os.getenv("DON2_URL", "http://don2:8000/v1"),
        api_key="none"
    )

    @agent
    def LogicAgent(self) -> Agent:
        return Agent(
            config=self.agents_config['LogicAgent'],
            llm=self.don2_logic,
            allow_delegation=False,
            verbose=True
        )

    @agent
    def Trainer(self) -> Agent:
        return Agent(
            config=self.agents_config['Trainer'],
            llm=self.don1_trainer,
            allow_delegation=False,
            verbose=True
        )

    @task
    def agentLogicTrainingSession_proposal(self) -> Task:
        # Use the heavy thinker for the derivation phase
        proposal_agent = self.Trainer()
        proposal_agent.llm = self.heavy_thinker
        return Task(
            config=self.tasks_config['agentLogicTrainingSession_proposal'],
            agent=proposal_agent
        )

    @task
    def LogicModel_integration(self) -> Task:
        return Task(
            config=self.tasks_config['LogicModel_integration'],
            agent=self.LogicAgent()
        )

    @task
    def agentLogicTrainingSession_documentation(self) -> Task:
        return Task(
            config=self.tasks_config['agentLogicTrainingSession_documentation'],
            agent=self.Trainer(),
            output_file='LogicModel_Evolution_Log.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.Trainer(), self.LogicAgent()],
            tasks=[
                self.agentLogicTrainingSession_proposal(),
                self.LogicModel_integration(),
                self.agentLogicTrainingSession_documentation()
            ],
            process=Process.sequential,
            verbose=True,
        )
