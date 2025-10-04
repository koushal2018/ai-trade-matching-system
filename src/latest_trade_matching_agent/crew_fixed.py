from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional, Dict, Any
from .tools import PDFToImageTool
from crewai_tools import DirectoryReadTool,FileReadTool,FileWriterTool,S3ReaderTool,S3WriterTool,OCRTool

import os
from dotenv import load_dotenv
import logging

# Optional OpenLit integration
# try:
#     import openlit
#     openlit.init()
# except ImportError:
#     # OpenLit not available, continue without it
#     pass

load_dotenv()

# Set dummy OpenAI API key to bypass CrewAI validation (we use AWS Bedrock)
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-bedrock-usage"

# Disable LiteLLM cost tracking
os.environ["LITELLM_LOG"] = "ERROR"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure AWS Bedrock LLM
bedrock_model = os.getenv('BEDROCK_MODEL', 'anthropic.claude-sonnet-4-20250514-v1:0')
aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

llm = LLM(
    model=f"bedrock/{bedrock_model}",
    aws_region_name=aws_region
)

# Initialize standard tools
pdf_tool = PDFToImageTool()
ocr_tool = OCRTool(llm)
file_reader = FileReadTool()
file_writer = FileWriterTool()
directory_read_tool = DirectoryReadTool()
s3_file_reader = S3ReaderTool(bucket_name=os.getenv('S3_BUCKET_NAME', 'fab-otc-reconciliation-deployment'))
s3_file_writer = S3WriterTool(bucket_name=os.getenv('S3_BUCKET_NAME', 'fab-otc-reconciliation-deployment'))




@CrewBase
class LatestTradeMatchingAgent:
    """Enhanced LatestTradeMatchingAgent crew for EKS deployment"""
    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self, dynamodb_tools: Optional[List] = None, request_context: Optional[Dict[str, Any]] = None):
        """
        Initialize the crew with optional DynamoDB tools and request context.

        Args:
            dynamodb_tools: List of MCP tools from the DynamoDB adapter
            request_context: Request context from EKS API containing dynamic parameters
        """
        self.dynamodb_tools = dynamodb_tools or []
        self.request_context = request_context or {}

        # Environment-based configuration with dynamic overrides
        self.config = {
            's3_bucket': os.getenv('S3_BUCKET_NAME',
                                  self.request_context.get('s3_bucket', 'fab-otc-reconciliation-deployment')),
            'dynamodb_bank_table': os.getenv('DYNAMODB_BANK_TABLE', 'BankTradeData'),
            'dynamodb_counterparty_table': os.getenv('DYNAMODB_COUNTERPARTY_TABLE', 'CounterpartyTradeData'),
            'max_rpm': int(os.getenv('MAX_RPM', '10')),
            'max_execution_time': int(os.getenv('MAX_EXECUTION_TIME', '1200')),
            'aws_region': os.getenv('AWS_REGION', 'us-east-1')
        }

        if self.dynamodb_tools:
            logger.info(f"Initialized with {len(self.dynamodb_tools)} DynamoDB tools")
        if self.request_context:
            logger.info(f"Initialized with request context: {list(self.request_context.keys())}")

    @agent
    def document_processor(self) -> Agent:
        return Agent(
            config=self.agents_config['document_processor'],
            llm=llm,
            tools=[pdf_tool, file_writer,s3_file_writer],
            verbose=True,
            max_rpm=self.config['max_rpm'],
            max_iter=3,
            max_execution_time=self.config['max_execution_time'],
            multimodal=True
        )
    
    @agent
    def trade_entity_extractor(self) -> Agent:
        # Build tools list conditionally
        tools_list = [ocr_tool,file_writer, file_reader, directory_read_tool,s3_file_reader,s3_file_writer]
        
        return Agent(
            config=self.agents_config['trade_entity_extractor'],
            llm=llm,
            tools=tools_list,
            verbose=True,
            max_rpm=self.config['max_rpm'],
            max_iter=5,
            max_execution_time=self.config['max_execution_time'],
            multimodal=True
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Agent with DynamoDB access for storing trade data"""
        tools_list = [file_reader, file_writer,s3_file_reader,s3_file_writer]
        # Add DynamoDB tools if available
        if self.dynamodb_tools:
            tools_list.extend(self.dynamodb_tools)

        return Agent(
            config=self.agents_config['reporting_analyst'],
            llm=llm,
            tools=tools_list,
            verbose=True,
            max_rpm=self.config['max_rpm'],
            max_iter=5,
            max_execution_time=self.config['max_execution_time'],
            multimodal=True
        )

    @agent
    def matching_analyst(self) -> Agent:
        """Agent with DynamoDB access for matching trades"""
        tools_list = [file_reader, file_writer,s3_file_writer,s3_file_reader]
        # Add DynamoDB tools if available
        if self.dynamodb_tools:
            tools_list.extend(self.dynamodb_tools)

        return Agent(
            config=self.agents_config['matching_analyst'],
            llm=llm,
            tools=tools_list,
            verbose=True,
            max_rpm=self.config['max_rpm'],
            max_iter=8,
            max_execution_time=self.config['max_execution_time'],
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

    def set_request_context(self, context: Dict[str, Any]):
        """Update request context for dynamic task configuration"""
        self.request_context = context

    def _step_callback(self, step):
        """Callback for monitoring step execution"""
        logger.info(f"Crew step executed: {step}")

    def _task_callback(self, task):
        """Callback for monitoring task completion"""
        logger.info(f"Task completed: {task.description[:100] if hasattr(task, 'description') else str(task)[:100]}...")

    @crew
    def crew(self) -> Crew:
        """Creates the enhanced LatestTradeMatchingAgent crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            verbose=True,
            max_rpm=self.config['max_rpm'],
            share_crew=False,
            step_callback=self._step_callback,
            task_callback=self._task_callback
        )