"""
Exception Delegation System

This module implements delegation logic for routing exceptions to appropriate
handlers, creating tracking records, and sending notifications.

Requirements: 8.3, 8.4
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import boto3
from ..models.exception import (
    ExceptionRecord,
    TriageResult,
    DelegationResult,
    RoutingDestination,
    ResolutionStatus
)


class ExceptionDelegator:
    """
    Handles delegation of exceptions to appropriate queues and handlers.
    
    Requirements:
        - 8.3: Delegate to appropriate handler based on routing
        - 8.3: Create tracking record with SLA deadline
        - 8.3: Send notifications
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize the exception delegator.
        
        Args:
            region_name: AWS region name
        """
        self.region_name = region_name
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        
        # Queue URLs (these would be configured via environment variables in production)
        self.queue_urls = {
            RoutingDestination.OPS_DESK: self._get_queue_url("ops-desk-queue"),
            RoutingDestination.SENIOR_OPS: self._get_queue_url("senior-ops-queue"),
            RoutingDestination.COMPLIANCE: self._get_queue_url("compliance-queue"),
            RoutingDestination.ENGINEERING: self._get_queue_url("engineering-queue"),
        }
    
    def _get_queue_url(self, queue_name: str) -> Optional[str]:
        """
        Get SQS queue URL by name.
        
        Args:
            queue_name: Name of the queue
        
        Returns:
            Optional[str]: Queue URL or None if not found
        """
        try:
            response = self.sqs.get_queue_url(QueueName=queue_name)
            return response['QueueUrl']
        except self.sqs.exceptions.QueueDoesNotExist:
            print(f"Warning: Queue {queue_name} does not exist")
            return None
        except Exception as e:
            print(f"Error getting queue URL for {queue_name}: {e}")
            return None


def delegate_exception(
    exception: ExceptionRecord,
    triage_result: TriageResult,
    delegator: Optional[ExceptionDelegator] = None
) -> DelegationResult:
    """
    Delegate an exception to the appropriate handler.
    
    This function:
    1. Sends the exception to the appropriate SQS queue
    2. Creates a tracking record in DynamoDB
    3. Sends notifications to the assigned team
    
    Args:
        exception: Exception to delegate
        triage_result: Triage result with routing information
        delegator: Optional ExceptionDelegator instance (for testing)
    
    Returns:
        DelegationResult: Result of the delegation
        
    Requirements:
        - 8.3: Assign to appropriate handler based on routing
        - 8.3: Create tracking record with SLA deadline
        - 8.3: Send notifications
    
    Examples:
        >>> exc = ExceptionRecord(...)
        >>> triage = TriageResult(...)
        >>> result = delegate_exception(exc, triage)
        >>> result.status
        'DELEGATED'
    """
    
    # Initialize delegator if not provided
    if delegator is None:
        delegator = ExceptionDelegator()
    
    # Generate tracking ID
    tracking_id = f"track_{uuid.uuid4().hex[:12]}"
    
    # Calculate SLA deadline
    sla_deadline = datetime.utcnow() + timedelta(hours=triage_result.sla_hours)
    
    # Handle AUTO_RESOLVE routing (no delegation needed)
    if triage_result.routing == RoutingDestination.AUTO_RESOLVE:
        return _handle_auto_resolve(
            exception, triage_result, tracking_id, sla_deadline
        )
    
    # Send to appropriate SQS queue
    queue_sent = _send_to_queue(
        exception, triage_result, delegator
    )
    
    # Create tracking record in DynamoDB
    tracking_created = _create_tracking_record(
        exception, triage_result, tracking_id, sla_deadline, delegator
    )
    
    # Send notification
    notification_sent = _send_notification(
        exception, triage_result, tracking_id, delegator
    )
    
    # Determine delegation status
    if queue_sent and tracking_created:
        status = "DELEGATED"
    else:
        status = "FAILED"
    
    return DelegationResult(
        exception_id=exception.exception_id,
        status=status,
        assigned_to=triage_result.assigned_to or "unassigned",
        tracking_id=tracking_id,
        queue_name=_get_queue_name(triage_result.routing),
        sla_deadline=sla_deadline,
        notification_sent=notification_sent
    )


def _handle_auto_resolve(
    exception: ExceptionRecord,
    triage_result: TriageResult,
    tracking_id: str,
    sla_deadline: datetime
) -> DelegationResult:
    """
    Handle auto-resolve routing (no delegation needed).
    
    Args:
        exception: Exception record
        triage_result: Triage result
        tracking_id: Tracking ID
        sla_deadline: SLA deadline
    
    Returns:
        DelegationResult: Result indicating auto-resolve
    """
    return DelegationResult(
        exception_id=exception.exception_id,
        status="AUTO_RESOLVED",
        assigned_to="system_auto_resolver",
        tracking_id=tracking_id,
        queue_name=None,
        sla_deadline=sla_deadline,
        notification_sent=False
    )


def _send_to_queue(
    exception: ExceptionRecord,
    triage_result: TriageResult,
    delegator: ExceptionDelegator
) -> bool:
    """
    Send exception to appropriate SQS queue.
    
    Args:
        exception: Exception record
        triage_result: Triage result
        delegator: Exception delegator
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        # Get queue URL
        queue_url = delegator.queue_urls.get(triage_result.routing)
        
        if not queue_url:
            print(f"Warning: No queue URL for routing {triage_result.routing}")
            return False
        
        # Prepare message
        message_body = {
            "exception_id": exception.exception_id,
            "exception_type": exception.exception_type.value,
            "event_type": exception.event_type,
            "trade_id": exception.trade_id,
            "agent_id": exception.agent_id,
            "reason_codes": exception.reason_codes,
            "error_message": exception.error_message,
            "match_score": exception.match_score,
            "context": exception.context,
            "triage": {
                "severity": triage_result.severity.value,
                "severity_score": triage_result.severity_score,
                "priority": triage_result.priority,
                "sla_hours": triage_result.sla_hours,
                "classification": triage_result.classification.value,
                "recommended_action": triage_result.recommended_action,
            },
            "timestamp": exception.timestamp.isoformat(),
            "correlation_id": exception.correlation_id,
        }
        
        # Send message to SQS
        response = delegator.sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                'exception_id': {
                    'StringValue': exception.exception_id,
                    'DataType': 'String'
                },
                'severity': {
                    'StringValue': triage_result.severity.value,
                    'DataType': 'String'
                },
                'priority': {
                    'StringValue': str(triage_result.priority),
                    'DataType': 'Number'
                }
            }
        )
        
        print(f"Sent exception {exception.exception_id} to queue {queue_url}")
        return True
        
    except Exception as e:
        print(f"Error sending exception to queue: {e}")
        return False


def _create_tracking_record(
    exception: ExceptionRecord,
    triage_result: TriageResult,
    tracking_id: str,
    sla_deadline: datetime,
    delegator: ExceptionDelegator
) -> bool:
    """
    Create tracking record in DynamoDB ExceptionsTable.
    
    Args:
        exception: Exception record
        triage_result: Triage result
        tracking_id: Tracking ID
        sla_deadline: SLA deadline
        delegator: Exception delegator
    
    Returns:
        bool: True if created successfully, False otherwise
    """
    try:
        # Get ExceptionsTable
        table = delegator.dynamodb.Table("ExceptionsTable")
        
        # Create tracking record
        item = {
            "exception_id": exception.exception_id,
            "tracking_id": tracking_id,
            "timestamp": exception.timestamp.isoformat(),
            "exception_type": exception.exception_type.value,
            "event_type": exception.event_type,
            "trade_id": exception.trade_id or "N/A",
            "agent_id": exception.agent_id,
            "reason_codes": exception.reason_codes,
            "error_message": exception.error_message,
            "match_score": exception.match_score,
            "retry_count": exception.retry_count,
            "correlation_id": exception.correlation_id or "N/A",
            # Triage information
            "severity": triage_result.severity.value,
            "severity_score": triage_result.severity_score,
            "routing": triage_result.routing.value,
            "priority": triage_result.priority,
            "sla_hours": triage_result.sla_hours,
            "sla_deadline": sla_deadline.isoformat(),
            "classification": triage_result.classification.value,
            "recommended_action": triage_result.recommended_action,
            "assigned_to": triage_result.assigned_to or "unassigned",
            # Resolution tracking
            "resolution_status": ResolutionStatus.PENDING.value,
            "assigned_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
            "resolution_notes": None,
            # Metadata
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # Put item in DynamoDB
        table.put_item(Item=item)
        
        print(f"Created tracking record for exception {exception.exception_id}")
        return True
        
    except Exception as e:
        print(f"Error creating tracking record: {e}")
        return False


def _send_notification(
    exception: ExceptionRecord,
    triage_result: TriageResult,
    tracking_id: str,
    delegator: ExceptionDelegator
) -> bool:
    """
    Send notification to assigned team.
    
    In a production system, this would send emails, Slack messages, or
    other notifications. For now, we just log the notification.
    
    Args:
        exception: Exception record
        triage_result: Triage result
        tracking_id: Tracking ID
        delegator: Exception delegator
    
    Returns:
        bool: True if notification sent successfully
    """
    try:
        # In production, this would use SNS, SES, or other notification service
        notification = {
            "to": triage_result.assigned_to,
            "subject": f"Exception {exception.exception_id} - {triage_result.severity.value} Priority",
            "body": f"""
Exception Alert

Exception ID: {exception.exception_id}
Tracking ID: {tracking_id}
Severity: {triage_result.severity.value} (Score: {triage_result.severity_score})
Priority: {triage_result.priority}
Classification: {triage_result.classification.value}

Error: {exception.error_message}
Reason Codes: {', '.join(exception.reason_codes)}

Recommended Action: {triage_result.recommended_action}

SLA Deadline: {triage_result.sla_hours} hours
Trade ID: {exception.trade_id or 'N/A'}
Agent: {exception.agent_id}

Please review and resolve this exception according to the recommended action.
            """.strip()
        }
        
        print(f"Notification sent to {triage_result.assigned_to} for exception {exception.exception_id}")
        # In production: send via SNS/SES
        
        return True
        
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False


def _get_queue_name(routing: RoutingDestination) -> Optional[str]:
    """
    Get queue name for routing destination.
    
    Args:
        routing: Routing destination
    
    Returns:
        Optional[str]: Queue name
    """
    queue_map = {
        RoutingDestination.OPS_DESK: "ops-desk-queue",
        RoutingDestination.SENIOR_OPS: "senior-ops-queue",
        RoutingDestination.COMPLIANCE: "compliance-queue",
        RoutingDestination.ENGINEERING: "engineering-queue",
        RoutingDestination.AUTO_RESOLVE: None,
    }
    
    return queue_map.get(routing)


def update_exception_status(
    exception_id: str,
    status: ResolutionStatus,
    resolution_notes: Optional[str] = None,
    region_name: str = "us-east-1"
) -> bool:
    """
    Update exception resolution status in DynamoDB.
    
    Args:
        exception_id: Exception ID
        status: New resolution status
        resolution_notes: Optional resolution notes
        region_name: AWS region name
    
    Returns:
        bool: True if updated successfully
        
    Requirements:
        - 8.4: Update audit trail when resolved
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)
        table = dynamodb.Table("ExceptionsTable")
        
        # Prepare update expression
        update_expr = "SET resolution_status = :status, updated_at = :updated"
        expr_values = {
            ":status": status.value,
            ":updated": datetime.utcnow().isoformat(),
        }
        
        # Add resolution timestamp if resolved
        if status == ResolutionStatus.RESOLVED:
            update_expr += ", resolved_at = :resolved"
            expr_values[":resolved"] = datetime.utcnow().isoformat()
        
        # Add resolution notes if provided
        if resolution_notes:
            update_expr += ", resolution_notes = :notes"
            expr_values[":notes"] = resolution_notes
        
        # Update item
        table.update_item(
            Key={"exception_id": exception_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        print(f"Updated exception {exception_id} status to {status.value}")
        return True
        
    except Exception as e:
        print(f"Error updating exception status: {e}")
        return False
