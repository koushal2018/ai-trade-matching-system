from mcp import StdioServerParameters
from crewai_tools import MCPServerAdapter
from latest_trade_matching_agent.crew import LatestTradeMatchingAgent

def run():
    # Define your inputs
    inputs = {
        'document_path': './data/COUNTERPARTY/GCS381315_V1.pdf'
    }
    
    # Set up DynamoDB MCP server parameters
    dynamodb_params = StdioServerParameters(
        command="uvx", 
        args=["awslabs.dynamodb-mcp-server@latest"],
        env={
            "DDB-MCP-READONLY": "false",  # Set to false if you need write access
            "AWS_PROFILE": "default",
            "AWS_REGION": "us-west-2",
            "FASTMCP_LOG_LEVEL": "ERROR"
        }
    )
    
    # Use context manager to ensure proper cleanup
    with MCPServerAdapter(dynamodb_params) as dynamodb_tools:
        print(f"Connected to DynamoDB MCP server with tools: {[tool.name for tool in dynamodb_tools]}")
        
        # Create crew instance with DynamoDB tools
        crew_instance = LatestTradeMatchingAgent(dynamodb_tools=list(dynamodb_tools))
        
        # Run the crew
        result = crew_instance.crew().kickoff(inputs=inputs)
        
        print("\nCrew execution completed successfully!")
        return result

if __name__ == "__main__":
    run()