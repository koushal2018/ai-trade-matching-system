"""
CloudWatch Metrics Service for Bedrock AgentCore Observability

Pulls real metrics from CloudWatch that are emitted by the Strands SDK
and Bedrock AgentCore agents.

Metrics emitted by Strands SDK (from strands.telemetry.metrics_constants):
- strands.event_loop.cycle_count
- strands.event_loop.cycle_duration
- strands.event_loop.input.tokens
- strands.event_loop.output.tokens
- strands.event_loop.latency
- strands.tool.call_count
- strands.tool.duration
- strands.tool.error_count
- strands.tool.success_count

GenAI metrics (from OTEL auto-instrumentation):
- gen_ai.client.token.usage
- gen_ai.client.operation.duration
"""

import boto3
from datetime import datetime, timezone, timedelta

# Configuration
NAMESPACE = "bedrock-agentcore"
REGION = "us-east-1"


class CloudWatchMetricsService:
    def __init__(self, region: str = REGION):
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.region = region

    def get_metric_sum(
        self,
        metric_name: str,
        dimensions: list[dict] | None = None,
        period_hours: int = 24,
    ) -> float:
        """Get sum of a metric over a time period."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=period_hours)

        params = {
            "Namespace": NAMESPACE,
            "MetricName": metric_name,
            "StartTime": start_time,
            "EndTime": end_time,
            "Period": period_hours * 3600,  # Full period
            "Statistics": ["Sum"],
        }

        if dimensions:
            params["Dimensions"] = dimensions

        try:
            response = self.cloudwatch.get_metric_statistics(**params)
            datapoints = response.get("Datapoints", [])
            if datapoints:
                return datapoints[0].get("Sum", 0)
        except Exception as e:
            print(f"Error fetching metric {metric_name}: {e}")

        return 0

    def get_metric_average(
        self,
        metric_name: str,
        dimensions: list[dict] | None = None,
        period_hours: int = 24,
    ) -> float:
        """Get average of a metric over a time period."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=period_hours)

        params = {
            "Namespace": NAMESPACE,
            "MetricName": metric_name,
            "StartTime": start_time,
            "EndTime": end_time,
            "Period": period_hours * 3600,
            "Statistics": ["Average"],
        }

        if dimensions:
            params["Dimensions"] = dimensions

        try:
            response = self.cloudwatch.get_metric_statistics(**params)
            datapoints = response.get("Datapoints", [])
            if datapoints:
                return datapoints[0].get("Average", 0)
        except Exception as e:
            print(f"Error fetching metric {metric_name}: {e}")

        return 0

    def get_agentcore_metrics(self, period_hours: int = 48) -> dict:
        """
        Get aggregated metrics from Bedrock AgentCore Observability.

        Returns metrics similar to what's shown in the CloudWatch GenAI Observability console.
        Uses Strands SDK metrics and GenAI OTEL metrics.

        Queries are made separately to avoid pagination issues with many dimension combinations.
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=period_hours)
        period_seconds = min(period_hours * 3600, 86400)

        results = {
            "total_tokens": 0,
            "operation_duration": 0,
            "operation_count": 0,
            "tool_calls": 0,
            "tool_errors": 0,
            "tool_success": 0,
            "cycle_duration": 0,
            "cycle_count": 0,
        }

        # Query each metric type separately to avoid pagination issues
        metric_configs = [
            ("total_tokens", "gen_ai.client.token.usage", "Sum"),
            ("operation_duration", "gen_ai.client.operation.duration", "Average"),
            ("tool_calls", "strands.tool.call_count", "Sum"),
            ("tool_errors", "strands.tool.error_count", "Sum"),
            ("tool_success", "strands.tool.success_count", "Sum"),
            ("cycle_duration", "strands.event_loop.cycle_duration", "Average"),
        ]

        try:
            for result_key, metric_name, stat in metric_configs:
                try:
                    response = self.cloudwatch.get_metric_data(
                        MetricDataQueries=[
                            {
                                "Id": "m1",
                                "Expression": f"SEARCH('Namespace=\"{NAMESPACE}\" MetricName=\"{metric_name}\"', '{stat}', {period_seconds})",
                                "ReturnData": True,
                            },
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                    )

                    # Aggregate all time series
                    total = 0
                    count = 0
                    for metric_result in response.get("MetricDataResults", []):
                        values = metric_result.get("Values", [])
                        if values:
                            total += sum(values)
                            count += len(values)

                    if stat == "Average" and count > 0:
                        # For averages, store count for proper averaging later
                        results[result_key] = total
                        results[f"{result_key}_count"] = count
                    else:
                        results[result_key] = total

                except Exception as e:
                    print(f"Error fetching {metric_name}: {e}")

            # Calculate derived metrics
            total_tool_calls = results.get("tool_calls", 0) or 0
            tool_errors = results.get("tool_errors", 0) or 0

            error_rate = 0
            if total_tool_calls > 0:
                error_rate = (tool_errors / total_tool_calls) * 100

            success_rate = 100 - error_rate

            # Calculate averages properly
            op_count = results.get("operation_duration_count", 1) or 1
            latency_ms = (results.get("operation_duration", 0) / op_count) * 1000

            cycle_dur_count = results.get("cycle_duration_count", 1) or 1
            avg_cycle_duration_ms = (results.get("cycle_duration", 0) / cycle_dur_count) * 1000

            return {
                "totalTokens": int(results.get("total_tokens", 0)),
                "avgLatencyMs": int(latency_ms),
                "toolCalls": int(total_tool_calls),
                "toolErrors": int(tool_errors),
                "toolSuccess": int(results.get("tool_success", 0)),
                "avgCycleDurationMs": int(avg_cycle_duration_ms),
                "errorRate": round(error_rate, 3),
                "successRate": round(success_rate, 3),
                "periodHours": period_hours,
                "source": "cloudwatch",
            }

        except Exception as e:
            print(f"Error fetching AgentCore metrics: {e}")
            return {
                "totalTokens": 0,
                "avgLatencyMs": 0,
                "toolCalls": 0,
                "toolErrors": 0,
                "toolSuccess": 0,
                "avgCycleDurationMs": 0,
                "errorRate": 0,
                "successRate": 100,
                "periodHours": period_hours,
                "source": "cloudwatch",
                "error": str(e),
            }


    def sync_metrics_to_agent_registry(self, table_name: str, period_hours: int = 24) -> dict:
        """
        Fetch metrics from CloudWatch and update the agent registry in DynamoDB.

        This keeps the agent health panel in sync with real observability data.
        """
        import boto3
        from decimal import Decimal

        metrics = self.get_agentcore_metrics(period_hours=period_hours)

        if metrics.get("error"):
            return {"success": False, "error": metrics["error"]}

        dynamodb = boto3.resource("dynamodb", region_name=self.region)
        table = dynamodb.Table(table_name)
        current_time = datetime.now(timezone.utc).isoformat()

        # Calculate per-agent metrics (distribute evenly for now)
        agent_ids = [
            "pdf_adapter_agent",
            "trade_extraction_agent",
            "trade_matching_agent",
            "exception_management_agent",
            "orchestrator_agent",
        ]

        num_agents = len(agent_ids)
        tokens_per_agent = metrics["totalTokens"] // num_agents
        error_rate = Decimal(str(metrics["errorRate"] / 100))
        success_rate = Decimal(str(metrics["successRate"] / 100))

        updated = []
        for agent_id in agent_ids:
            try:
                table.update_item(
                    Key={"agent_id": agent_id},
                    UpdateExpression="""
                        SET last_heartbeat = :hb,
                            updated_at = :ua,
                            avg_latency_ms = :lat,
                            total_tokens = :tokens,
                            error_rate = :err,
                            success_rate = :succ
                    """,
                    ExpressionAttributeValues={
                        ":hb": current_time,
                        ":ua": current_time,
                        ":lat": metrics["avgLatencyMs"],
                        ":tokens": tokens_per_agent,
                        ":err": error_rate,
                        ":succ": success_rate,
                    },
                )
                updated.append(agent_id)
            except Exception as e:
                print(f"Error updating {agent_id}: {e}")

        return {
            "success": True,
            "updated_agents": updated,
            "metrics": metrics,
        }


    def get_per_agent_metrics(self, period_hours: int = 24) -> dict:
        """
        Get metrics for each agent from AWS/Bedrock-AgentCore namespace.

        Returns per-agent metrics including invocations, latency, errors, and resource usage.
        Metrics require three dimensions: Resource (ARN), Operation, and Name.
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=period_hours)

        # Map agent names to our internal IDs
        # Based on deployed AgentCore runtimes:
        # - http_agent_orchestrator → orchestrator
        # - agent_matching_ai → trade extraction
        # - trade_matching_ai → trade matching
        # - pdf_adapter_agent → pdf adapter
        # - exception_manager → exception management
        agent_mapping = {
            "pdf_adapter_agent::DEFAULT": "pdf_adapter_agent",
            "agent_matching_ai::DEFAULT": "trade_extraction_agent",  # Extraction agent
            "trade_matching_ai::DEFAULT": "trade_matching_agent",  # Matching agent
            "exception_manager::DEFAULT": "exception_management_agent",
            "http_agent_orchestrator::DEFAULT": "orchestrator_agent",
        }

        # Metrics to fetch per agent with their statistics
        metric_configs = [
            ("Invocations", "Sum", "invocations"),
            ("Latency", "Average", "avgLatencyMs"),
            ("Duration", "Average", "avgDurationMs"),
            ("SystemErrors", "Sum", "systemErrors"),
            ("UserErrors", "Sum", "userErrors"),
            ("Throttles", "Sum", "throttles"),
            ("Sessions", "Sum", "sessions"),
        ]

        agent_metrics = {}

        try:
            # First, discover agents with full dimension sets from Invocations metric
            response = self.cloudwatch.list_metrics(
                Namespace="AWS/Bedrock-AgentCore",
                MetricName="Invocations",
            )

            # Build a map of agent name -> full dimensions (Resource, Operation, Name)
            agent_dimensions = {}
            for metric in response.get("Metrics", []):
                dims = {d["Name"]: d["Value"] for d in metric.get("Dimensions", [])}

                # Only process InvokeAgentRuntime operations with Name dimension
                if dims.get("Operation") == "InvokeAgentRuntime" and "Name" in dims:
                    agent_name = dims["Name"]
                    if agent_name in agent_mapping:
                        # Store full dimension list for querying
                        agent_dimensions[agent_name] = [
                            {"Name": "Resource", "Value": dims.get("Resource", "")},
                            {"Name": "Operation", "Value": "InvokeAgentRuntime"},
                            {"Name": "Name", "Value": agent_name},
                        ]

            print(f"Found {len(agent_dimensions)} agents with metrics: {list(agent_dimensions.keys())}")

            # Query metrics for each discovered agent
            for agent_name, dimensions in agent_dimensions.items():
                internal_id = agent_mapping.get(agent_name)
                if not internal_id:
                    continue

                # Initialize or merge into existing agent data
                if internal_id not in agent_metrics:
                    agent_metrics[internal_id] = {
                        "agentName": agent_name,
                        "invocations": 0,
                        "avgLatencyMs": 0,
                        "avgDurationMs": 0,
                        "systemErrors": 0,
                        "userErrors": 0,
                        "throttles": 0,
                        "sessions": 0,
                        "errorRate": 0,
                    }

                agent_data = agent_metrics[internal_id]

                for metric_name, stat, field in metric_configs:
                    try:
                        response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/Bedrock-AgentCore",
                            MetricName=metric_name,
                            Dimensions=dimensions,
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=period_hours * 3600,
                            Statistics=[stat],
                        )

                        datapoints = response.get("Datapoints", [])
                        if datapoints:
                            value = datapoints[0].get(stat, 0)
                            # For counts, accumulate; for averages, take latest
                            if stat == "Sum":
                                agent_data[field] += int(value)
                            else:
                                agent_data[field] = int(value) if value else agent_data[field]

                    except Exception as e:
                        print(f"Error fetching {metric_name} for {agent_name}: {e}")

                # Calculate error rate
                total_errors = agent_data["systemErrors"] + agent_data["userErrors"]
                if agent_data["invocations"] > 0:
                    agent_data["errorRate"] = round(
                        (total_errors / agent_data["invocations"]) * 100, 3
                    )

        except Exception as e:
            print(f"Error fetching per-agent metrics: {e}")

        return {
            "agents": agent_metrics,
            "periodHours": period_hours,
            "source": "AWS/Bedrock-AgentCore",
        }

    def sync_per_agent_metrics_to_registry(self, table_name: str, period_hours: int = 24) -> dict:
        """
        Sync per-agent metrics from CloudWatch to the agent registry.

        Each agent gets its own real metrics from AWS/Bedrock-AgentCore.
        """
        import boto3
        from decimal import Decimal

        metrics = self.get_per_agent_metrics(period_hours=period_hours)
        agent_metrics = metrics.get("agents", {})

        if not agent_metrics:
            return {"success": False, "error": "No agent metrics found"}

        dynamodb = boto3.resource("dynamodb", region_name=self.region)
        table = dynamodb.Table(table_name)
        current_time = datetime.now(timezone.utc).isoformat()

        updated = []
        for agent_id, data in agent_metrics.items():
            try:
                error_rate = Decimal(str(data.get("errorRate", 0) / 100))
                success_rate = Decimal(str(1 - float(error_rate)))

                table.update_item(
                    Key={"agent_id": agent_id},
                    UpdateExpression="""
                        SET last_heartbeat = :hb,
                            updated_at = :ua,
                            avg_latency_ms = :lat,
                            error_rate = :err,
                            success_rate = :succ,
                            throughput_per_hour = :tput
                    """,
                    ExpressionAttributeValues={
                        ":hb": current_time,
                        ":ua": current_time,
                        ":lat": data.get("avgLatencyMs", 0),
                        ":err": error_rate,
                        ":succ": success_rate,
                        ":tput": data.get("invocations", 0),
                    },
                )
                updated.append(agent_id)
            except Exception as e:
                print(f"Error updating {agent_id}: {e}")

        return {
            "success": True,
            "updated_agents": updated,
            "metrics": agent_metrics,
        }


# Singleton instance
cloudwatch_metrics_service = CloudWatchMetricsService()
