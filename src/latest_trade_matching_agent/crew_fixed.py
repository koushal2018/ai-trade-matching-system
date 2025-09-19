from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import FileReadTool, FileWriterTool
from typing import List
import os
import time
import random
import litellm
from dotenv import load_dotenv
from .tools.trade_tools import TradeStorageTool, PDFExtractorTool, TradeRetrievalTool, MatchingStatusTool

load_dotenv()

# Disable LiteLLM cost tracking
os.environ["LITELLM_LOG"] = "ERROR"

# Initialize tools
pdf_extractor = PDFExtractorTool()
trade_storage = TradeStorageTool()
trade_retrieval = TradeRetrievalTool()
matching_status = MatchingStatusTool()
file_reader = FileReadTool()
file_writer = FileWriterTool()

# Configure LiteLLM with retry settings and rate limiting
litellm.set_verbose = False
litellm.default_max_retries = 5
litellm.default_timeout = 120

# Custom wrapper class for rate limiting
class RateLimitedLLM(LLM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_request_time = 0
        self.min_request_interval = 2.0  # Minimum 2 seconds between requests

    def _wait_if_needed(self):
        """Add delay to respect rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def call(self, messages, **kwargs):
        """Override call method with rate limiting and exponential backoff"""
        max_retries = 5
        base_delay = 2.0

        for attempt in range(max_retries):
            try:
                self._wait_if_needed()
                return super().call(messages, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                if "rate limit" in error_str or "too many requests" in error_str or "429" in error_str:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"Rate limit hit, retrying in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                raise e

        raise Exception(f"Failed after {max_retries} attempts due to rate limiting")

# Dynamic LLM configuration based on environment
def get_llm():
    """Get LLM instance based on LLM_PROVIDER environment variable"""
    provider = os.getenv("LLM_PROVIDER", "bedrock").lower()
    
    if provider == "bedrock":
        # AWS Bedrock configuration
        model = os.getenv("BEDROCK_MODEL", "amazon.nova-pro-v1:0")
        return RateLimitedLLM(
            model=f"bedrock/{model}",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            max_retries=5,
            timeout=120,
            request_timeout=120
        )
    elif provider == "anthropic":
        # Anthropic configuration
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        return RateLimitedLLM(
            model=f"anthropic/{model}",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_retries=5,
            timeout=120,
            request_timeout=120
        )
    elif provider == "openai":
        # OpenAI configuration
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        return RateLimitedLLM(
            model=f"openai/{model}",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=5,
            timeout=120,
            request_timeout=120
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers: bedrock, anthropic, openai")

# Initialize LLM based on environment configuration
llm = get_llm()

@CrewBase
class LatestTradeMatchingAgent:
    """LatestTradeMatchingAgent crew"""
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=llm,
            tools=[pdf_extractor],
            verbose=True
        )


    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            llm=llm,
            tools=[file_reader, trade_storage],
            verbose=True
        )

    @agent
    def matching_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['matching_analyst'],
            llm=llm,
            tools=[file_reader, file_writer, trade_storage, trade_retrieval, matching_status],
            verbose=True
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
            memory=False,
            verbose=True
        )
