from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from .tools import PDFToImageTool
from crewai_tools import FileReadTool, FileWriterTool,OCRTool,DirectoryReadTool
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Disable LiteLLM cost tracking
os.environ["LITELLM_LOG"] = "ERROR"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


llm = LLM(
    model="bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0"
)
# Initialize tools
pdf_tool = PDFToImageTool()
file_reader = FileReadTool()
file_writer = FileWriterTool()
directory_read_tool = DirectoryReadTool()
ocr_tool = OCRTool(llm)


@CrewBase
class LatestTradeMatchingAgent:
    """LatestTradeMatchingAgent crew"""
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def document_processor(self) -> Agent:
        return Agent(
            config=self.agents_config['document_processor'],
            llm=llm,
            tools=[pdf_tool, file_writer],
            verbose=True,
            max_rpm=2,
            max_iter=3,
            max_execution_time=180,
            multimodal=True
        )
    @agent
    def trade_entity_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['trade_entity_extractor'],
            llm=llm,
            tools=[ocr_tool, file_writer, file_reader,directory_read_tool],
            verbose=True,
            max_rpm=2,
            max_iter=5,
            max_execution_time=300,
            multimodal=True
        )


    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            llm=llm,
            tools=[file_reader, file_writer,directory_read_tool],
            verbose=True,
            max_rpm=2,
            max_iter=5,
            max_execution_time=300,
            multimodal=True
        )

    @agent
    def matching_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['matching_analyst'],
            llm=llm,
            tools=[file_reader, file_writer,directory_read_tool],
            verbose=True,
            max_rpm=2,
            max_iter=8,
            max_execution_time=600,
            multimodal=True
        )

    @task
    def document_processing_task(self) -> Task:
        return Task(
            config=self.tasks_config['document_processing_task'],
            agent=self.document_processor()
        )
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['trade_entity_extractor_task'],
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task']
        )

    @task
    def matching_task(self) -> Task:
        return Task(
            config=self.tasks_config['matching_task']
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LatestTradeMatchingAgent crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,  # Disable memory to reduce context size
            verbose=True,
            max_rpm=3,  # Limit requests per minute
            share_crew=False  # Don't share telemetry
        )
