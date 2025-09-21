from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional
from .tools import PDFToImageTool
from crewai_tools import S3ReaderTool, S3WriterTool, OCRTool, DirectoryReadTool
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

# Initialize standard tools
pdf_tool = PDFToImageTool()
file_reader = S3ReaderTool()
file_writer = S3WriterTool()
ocr_tool = OCRTool(llm)
directory_read_tool = DirectoryReadTool()  # Add this if needed

@CrewBase
class LatestTradeMatchingAgent:
    """LatestTradeMatchingAgent crew"""
    agents: List[BaseAgent]
    tasks: List[Task]
    
    def __init__(self, dynamodb_tools: Optional[List] = None):
        """
        Initialize the crew with optional DynamoDB tools.
        
        Args:
            dynamodb_tools: List of MCP tools from the DynamoDB adapter
        """
        self.dynamodb_tools = dynamodb_tools or []
        if self.dynamodb_tools:
            logger.info(f"Initialized with {len(self.dynamodb_tools)} DynamoDB tools")

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
            tools=[ocr_tool, file_writer, file_reader, directory_read_tool],
            verbose=True,
            max_rpm=2,
            max_iter=5,
            max_execution_time=600,
            multimodal=True
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Agent with DynamoDB access for storing trade data"""
        tools_list = [file_reader, file_writer]
        # Add DynamoDB tools if available
        if self.dynamodb_tools:
            tools_list.extend(self.dynamodb_tools)
        
        return Agent(
            config=self.agents_config['reporting_analyst'],
            llm=llm,
            tools=tools_list,
            verbose=True,
            max_rpm=2,
            max_iter=5,
            max_execution_time=300,
            multimodal=True
        )

    @agent
    def matching_analyst(self) -> Agent:
        """Agent with DynamoDB access for matching trades"""
        tools_list = [file_reader, file_writer]
        # Add DynamoDB tools if available
        if self.dynamodb_tools:
            tools_list.extend(self.dynamodb_tools)
        
        return Agent(
            config=self.agents_config['matching_analyst'],
            llm=llm,
            tools=tools_list,
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
            agent=self.trade_entity_extractor()  # Add agent assignment
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
            agent=self.reporting_analyst()  # Add agent assignment
        )

    @task
    def matching_task(self) -> Task:
        return Task(
            config=self.tasks_config['matching_task'],
            agent=self.matching_analyst()  # Add agent assignment
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LatestTradeMatchingAgent crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            verbose=True,
            max_rpm=3,
            share_crew=False
        )