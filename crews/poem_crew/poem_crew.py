from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class PoemCrew:
    """Poem Crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # If you would lik to add tools to your crew, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def strengths_strategyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["strengths_strategyzer"],
        )

    @agent
    def weaknesses_strategyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["weaknesses_strategyzer"],
        )

    @agent
    def competition_strengths_strategyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["competition_strengths_strategyzer"],
        )

    @agent
    def competition_weaknesses_strategyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["competition_weaknesses_strategyzer"],
        )

    @agent
    def document_creator(self) -> Agent:
        return Agent(
            config=self.agents_config["document_creator"],
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def create_strength_strategy(self) -> Task:
        return Task(
            config=self.tasks_config["create_strength_strategy"],
        )

    @task
    def create_weakness_strategy(self) -> Task:
        return Task(
            config=self.tasks_config["create_weakness_strategy"],
        )

    @task
    def analyze_competitors_strengths(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_competitors_strengths"],
        )

    @task
    def analyze_competitors_weaknesses(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_competitors_weaknesses"],
        )

    @task
    def put_everything_together(self) -> Task:
        return Task(
            config=self.tasks_config["put_everything_together"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
