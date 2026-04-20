# src/research_crew/crew.py
import json
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
import ollama

@tool("OllamaWebSearch")
def ollama_web_search(query: str) -> str:
    """Searches the web using Ollama's native web search capability."""
    try:
        response = ollama.web_search(query)
        # Assuming the response has a 'results' structure as per docs
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Search failed: {str(e)}"

@tool("OllamaWebFetch")
def ollama_web_fetch(url: str) -> str:
    """Fetches the content of a specific URL using Ollama's native web fetch capability."""
    try:
        response = ollama.web_fetch(url)
        # The SDK returns a WebFetchResponse object. We can convert to string or dict
        return str(response)
    except Exception as e:
        return f"Fetch failed: {str(e)}"

@CrewBase
class ResearchCrew():
    """Research crew for comprehensive topic analysis and reporting"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            verbose=True,
            tools=[ollama_web_search, ollama_web_fetch]
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'], # type: ignore[index]
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'] # type: ignore[index]
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'], # type: ignore[index]
            output_file='output/report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the research crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )