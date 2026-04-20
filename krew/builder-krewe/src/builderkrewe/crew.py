from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Builderkrewe():
    """Builderkrewe crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def senior_backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_backend_engineer'], # type: ignore[index]
            verbose=True,
            llm='ollama/deepseek-v3.2:cloud'  # 671B, best for complex backend
        )

    @agent
    def frontend_developer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_developer'], # type: ignore[index]
            verbose=True
        )

    @agent
    def qa_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['qa_reviewer'], # type: ignore[index]
            verbose=True
        )

    # AI Tool Building Agents
    @agent
    def requirements_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['requirements_analyst'], # type: ignore[index]
            verbose=True
        )

    @agent
    def ai_coder(self) -> Agent:
        return Agent(
            config=self.agents_config['ai_coder'], # type: ignore[index]
            verbose=True
        )

    @agent
    def tool_validator(self) -> Agent:
        return Agent(
            config=self.agents_config['tool_validator'], # type: ignore[index]
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def backend_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['backend_development_task'], # type: ignore[index]
        )

    @task
    def frontend_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_development_task'], # type: ignore[index]
        )

    @task
    def assembly_and_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['assembly_and_review_task'], # type: ignore[index]
        )

    # AI Tool Building Tasks
    @task
    def analyze_tool_requirements_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_tool_requirements_task'], # type: ignore[index]
        )

    @task
    def generate_tool_code_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_tool_code_task'], # type: ignore[index]
        )

    @task
    def test_and_validate_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_and_validate_task'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Builderkrewe crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
