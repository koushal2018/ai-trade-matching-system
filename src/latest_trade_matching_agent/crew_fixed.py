from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import FileReadTool, FileWriterTool
from typing import List, Optional, Dict, Any
import os
import time
import random
import litellm
from dotenv import load_dotenv
from .tools.trade_tools import TradeStorageTool, PDFExtractorTool, TradeRetrievalTool, MatchingStatusTool
import logging

load_dotenv()

# Disable LiteLLM cost tracking
os.environ["LITELLM_LOG"] = "ERROR"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize tools
pdf_extractor = PDFExtractorTool()
trade_storage = TradeStorageTool()
trade_retrieval = TradeRetrievalTool()
matching_status = MatchingStatusTool()
file_reader = FileReadTool()
file_writer = FileWriterTool()

# Configure LiteLLM with retry settings and rate limiting
litellm.set_verbose = False
litellm.default_max_retries = 10
litellm.default_timeout = 180
litellm.request_timeout = 180
litellm.suppress_debug_info = True

# Custom wrapper class for rate limiting with improved error handling
class RateLimitedLLM(LLM):
    def __init__(self, *args, **kwargs):
        # Extract custom parameters
        self.min_request_interval = kwargs.pop('min_request_interval', 8.0)  # Increased to 8 seconds
        self.max_context_tokens = kwargs.pop('max_context_tokens', 8000)  # Limit context size
        super().__init__(*args, **kwargs)
        self.last_request_time = 0
        self.consecutive_errors = 0
        self.error_backoff_multiplier = 1.0

    def _wait_if_needed(self):
        """Add delay to respect rate limits with adaptive backoff"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Apply error backoff multiplier
        effective_interval = self.min_request_interval * self.error_backoff_multiplier
        
        if time_since_last < effective_interval:
            sleep_time = effective_interval - time_since_last
            logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds (backoff: {self.error_backoff_multiplier:.1f}x)")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _truncate_messages_if_needed(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Truncate messages to stay within token limits"""
        # Simple heuristic: estimate ~4 chars per token
        total_chars = sum(len(str(msg.get('content', ''))) for msg in messages)
        estimated_tokens = total_chars / 4
        
        if estimated_tokens > self.max_context_tokens:
            logger.warning(f"Context too large ({estimated_tokens:.0f} tokens), truncating...")
            # Keep system message and truncate others
            if messages and messages[0].get('role') == 'system':
                system_msg = messages[0]
                other_msgs = messages[1:]
                # Take last few messages that fit
                truncated_msgs = [system_msg]
                char_count = len(str(system_msg.get('content', '')))
                for msg in reversed(other_msgs):
                    msg_chars = len(str(msg.get('content', '')))
                    if (char_count + msg_chars) / 4 < self.max_context_tokens:
                        truncated_msgs.insert(1, msg)
                        char_count += msg_chars
                    else:
                        break
                return truncated_msgs
        return messages

    def call(self, messages, **kwargs):
        """Override call method with improved rate limiting and error handling"""
        max_retries = 8
        base_delay = 10.0  # Increased base delay
        
        # Truncate messages if needed
        messages = self._truncate_messages_if_needed(messages)
        
        # Remove unsupported parameters from kwargs
        # CrewAI's LLM class doesn't support these parameters directly
        kwargs.pop('max_tokens', None)
        kwargs.pop('temperature', None)

        for attempt in range(max_retries):
            try:
                self._wait_if_needed()
                result = super().call(messages, **kwargs)
                
                # Reset error tracking on success
                if self.consecutive_errors > 0:
                    logger.info("LLM call successful, resetting error backoff")
                    self.consecutive_errors = 0
                    self.error_backoff_multiplier = 1.0
                
                return result
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check for rate limit or token limit errors
                if any(err in error_str for err in [
                    "rate limit", "too many requests", "429", 
                    "too many tokens", "context length", "maximum context"
                ]):
                    self.consecutive_errors += 1
                    self.error_backoff_multiplier = min(4.0, 1.5 ** self.consecutive_errors)
                    
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 5)
                        delay = min(delay, 120)  # Cap at 2 minutes
                        
                        logger.warning(f"LLM error: {error_str[:100]}...")
                        logger.info(f"Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        
                        # If it's a token error, reduce context further
                        if "token" in error_str:
                            self.max_context_tokens = int(self.max_context_tokens * 0.8)
                            logger.info(f"Reducing max context to {self.max_context_tokens} tokens")
                            messages = self._truncate_messages_if_needed(messages)
                        
                        continue
                
                # For other errors, raise immediately
                logger.error(f"LLM call failed: {e}")
                raise e

        raise Exception(f"Failed after {max_retries} attempts due to rate limiting or token limits")

# Dynamic LLM configuration based on environment
def get_llm():
    """Get LLM instance based on LLM_PROVIDER environment variable"""
    provider = os.getenv("LLM_PROVIDER", "bedrock").lower()
    
    if provider == "bedrock":
        # AWS Bedrock configuration with optimized settings
        model = os.getenv("BEDROCK_MODEL", "amazon.nova-pro-v1:0")
        return RateLimitedLLM(
            model=f"bedrock/{model}",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            max_retries=10,
            timeout=180,
            request_timeout=180,
            min_request_interval=10.0,  # Longer interval for Bedrock
            max_context_tokens=6000  # Smaller context for Bedrock
        )
    elif provider == "anthropic":
        # Anthropic configuration
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        return RateLimitedLLM(
            model=f"anthropic/{model}",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_retries=8,
            timeout=180,
            request_timeout=180,
            min_request_interval=5.0,
            max_context_tokens=10000
        )
    elif provider == "openai":
        # OpenAI configuration
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        return RateLimitedLLM(
            model=f"openai/{model}",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=8,
            timeout=180,
            request_timeout=180,
            min_request_interval=3.0,
            max_context_tokens=12000
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
            verbose=True,
            max_iter=10,  # Limit iterations
            max_execution_time=600  # 10 minute timeout
        )


    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            llm=llm,
            tools=[file_reader, trade_storage],
            verbose=True,
            max_iter=10,
            max_execution_time=600
        )

    @agent
    def matching_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['matching_analyst'],
            llm=llm,
            tools=[file_reader, file_writer, trade_storage, trade_retrieval, matching_status],
            verbose=True,
            max_iter=15,  # More iterations for complex matching
            max_execution_time=900  # 15 minute timeout
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
            memory=False,  # Disable memory to reduce context size
            verbose=True,
            max_rpm=5,  # Limit requests per minute
            share_crew=False  # Don't share telemetry
        )
