from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools.aws.s3 import S3ReaderTool, S3WriterTool
from typing import List
from crewai_tools import PDFSearchTool, FileWriterTool, FileReadTool
from .tools.trade_tools import PDFExtractorTool, TradeStorageTool
import litellm
import boto3
from dotenv import load_dotenv

load_dotenv()

litellm._turn_on_debug()

# Initialize tools following CrewAI official patterns
pdf_extractor = PDFExtractorTool()
trade_storage = TradeStorageTool()
file_writer = FileWriterTool()
file_reader = FileReadTool()

s3_reader = S3ReaderTool(
    name="S3 Reader",
    description="Reads content from an S3 bucket",
    bucket_name="otc-menat-2025",
    file_name="s3://otc-menat-2025/BANK/FAB_26933659.pdf"
)
s3_writer = S3WriterTool(
    name="S3 Writer",
    description="Writes content to an S3 bucket",
    bucket_name="otc-menat-2025",
    file_name="*.json"
)
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

# Create LLM using CrewAI's documented approach
sagemaker_llm = LLM(
    model="sagemaker/jumpstart-dft-meta-vlm-llama-3-2-11-20250913-124222",
    aws_region_name="me-central-1",
)

@CrewBase
class LatestTradeMatchingAgent():
    """LatestTradeMatchingAgent crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            llm=sagemaker_llm,
            tools=[pdf_extractor, file_writer],
            verbose=True
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'], # type: ignore[index]
            llm=sagemaker_llm,
            tools=[file_reader, trade_storage],
            verbose=True
        )
    @agent
    def matching_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['matching_analyst'],
            llm=sagemaker_llm,
            tools=[file_reader, trade_storage],
            verbose=True
        )
           
           

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'], # type: ignore[index]
                )
        
    @task
    def matching_task(self) -> Task:
        return Task(
            config=self.tasks.config('matching_task')
            
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LatestTradeMatchingAgent crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
