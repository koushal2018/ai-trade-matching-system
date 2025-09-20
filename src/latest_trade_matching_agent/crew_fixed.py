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
    model="bedrock/amazon.nova-pro-v1:0"
)
# Initialize tools
pdf_tool = PDFToImageTool()
file_reader = FileReadTool()
file_writer = FileWriterTool()
ocr_tool = OCRTool(llm)
directory_read_tool = DirectoryReadTool()


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
            max_rpm=2,  # Reduce requests per minute to avoid rate limits
            max_iter=3,  # Limit iterations to prevent long loops
            max_execution_time=180,
            multimodal=True  # 3 minute timeout
        )
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=llm,
            tools=[ocr_tool, file_writer, file_reader, directory_read_tool],
            verbose=True,
            max_rpm=2,
            max_iter=10,  # Limit iterations
            max_execution_time=600,
            multimodal=True # 10 minute timeout
        )


    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            llm=llm,
            tools=[file_reader, file_writer],
            verbose=True,
            max_rpm=2,
            max_iter=10,
            max_execution_time=600,
            multimodal=True
        )

    @agent
    def matching_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['matching_analyst'],
            llm=llm,
            tools=[file_reader, file_writer],
            verbose=True,
            max_rpm=2,
            max_iter=15,  # More iterations for complex matching
            max_execution_time=900,
            multimodal=True  # 15 minute timeout
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
            config=self.tasks_config['research_task']
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
