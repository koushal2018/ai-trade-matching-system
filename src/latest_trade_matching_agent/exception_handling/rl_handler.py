"""
Reinforcement Learning Exception Handler

This module implements RL-based exception handling that learns optimal
routing policies from historical resolution outcomes.

Requirements: 8.2, 8.3, 8.4, 8.5
"""

import json
import pickle
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
import numpy as np
from ..models.exception import (
    ExceptionRecord,
    ResolutionOutcome,
    RoutingDestination
)


class RLExceptionHandler:
    """
    RL agent that learns optimal exception routing policies.
    
    Uses a simple Q-learning approach with supervised learning from
    historical human decisions.
    
    Requirements:
        - 8.2: Learn from historical patterns
        - 8.3: Integrate RL policy for routing decisions
        - 8.4: Track resolution outcomes
        - 8.5: Learn from resolution patterns
    
    Attributes:
        q_table: Q-table mapping states to action values
        replay_buffer: Buffer of recent episodes for experience replay
        learning_rate: Learning rate for Q-learning
        discount_factor: Discount factor for future rewards
        epsilon: Exploration rate for epsilon-greedy policy
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        epsilon: float = 0.1,
        buffer_size: int = 1000
    ):
        """
        Initialize the RL exception handler.
        
        Args:
            learning_rate: Learning rate for Q-learning (default: 0.1)
            discount_factor: Discount factor for future rewards (default: 0.9)
            epsilon: Exploration rate (default: 0.1)
            buffer_size: Size of replay buffer (default: 1000)
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.buffer_size = buffer_size
        
        # Q-table: maps (state_hash, action) -> Q-value
        self.q_table: Dict[Tuple[str, str], float] = {}
        
        # Replay buffer: stores (state, action, reward, next_state) tuples
        self.replay_buffer: deque = deque(maxlen=buffer_size)
        
        # Episode tracking: maps exception_id -> episode data
        self.pending_episodes: Dict[str, Dict[str, Any]] = {}
        
        # Action space (routing destinations)
        self.actions = [
            RoutingDestination.AUTO_RESOLVE.value,
            RoutingDestination.OPS_DESK.value,
            RoutingDestination.SENIOR_OPS.value,
            RoutingDestination.COMPLIANCE.value,
            RoutingDestination.ENGINEERING.value,
        ]
    
    def record_episode(
        self,
        exception_id: str,
        state: Dict[str, Any],
        action: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Record a state-action pair for later reward assignment.
        
        This is called when an exception is triaged and delegated.
        The reward will be assigned later when the exception is resolved.
        
        Args:
            exception_id: Unique exception identifier
            state: State representation of the exception
            action: Action taken (routing destination)
            context: Full exception context
            
        Requirements:
            - 8.2: Record state-action pairs for learning
        
        Examples:
            >>> handler = RLExceptionHandler()
            >>> state = {"exception_type": "MATCHING_EXCEPTION", "severity": 0.75}
            >>> handler.record_episode("exc_123", state, "OPS_DESK", {})
            >>> "exc_123" in handler.pending_episodes
            True
        """
        # Store episode data
        self.pending_episodes[exception_id] = {
            "state": state,
            "action": action,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        print(f"Recorded episode for exception {exception_id}: action={action}")
    
    def update_with_resolution(
        self,
        exception_id: str,
        resolution_outcome: ResolutionOutcome
    ) -> None:
        """
        Update RL model when an exception is resolved.
        
        This computes the reward based on the resolution outcome and
        updates the Q-table using Q-learning.
        
        Args:
            exception_id: Exception identifier
            resolution_outcome: Resolution outcome with timing and correctness
            
        Requirements:
            - 8.4: Update model with resolution outcomes
            - 8.5: Learn from resolution patterns
        
        Examples:
            >>> handler = RLExceptionHandler()
            >>> handler.record_episode("exc_123", {...}, "OPS_DESK", {})
            >>> outcome = ResolutionOutcome(
            ...     exception_id="exc_123",
            ...     resolved_at=datetime.utcnow(),
            ...     resolution_time_hours=2.5,
            ...     resolved_within_sla=True,
            ...     routing_was_correct=True
            ... )
            >>> handler.update_with_resolution("exc_123", outcome)
        """
        # Check if episode exists
        if exception_id not in self.pending_episodes:
            print(f"Warning: No pending episode for exception {exception_id}")
            return
        
        # Get episode data
        episode = self.pending_episodes[exception_id]
        state = episode["state"]
        action = episode["action"]
        
        # Compute reward
        reward = self.compute_reward(resolution_outcome)
        
        # Convert state to hash for Q-table lookup
        state_hash = self._hash_state(state)
        
        # Update Q-table using Q-learning
        self._update_q_value(state_hash, action, reward)
        
        # Add to replay buffer
        self.replay_buffer.append({
            "state": state,
            "state_hash": state_hash,
            "action": action,
            "reward": reward,
            "resolution_outcome": resolution_outcome,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Supervised learning: if human made a different decision, learn from it
        if resolution_outcome.human_decision and resolution_outcome.human_decision != action:
            self.supervised_update(state, resolution_outcome.human_decision)
        
        # Remove from pending episodes
        del self.pending_episodes[exception_id]
        
        print(f"Updated RL model for exception {exception_id}: reward={reward:.2f}")
    
    def compute_reward(self, outcome: ResolutionOutcome) -> float:
        """
        Compute reward based on resolution outcome.
        
        Reward function:
        - +1.0: Resolved within SLA, correct routing
        - +0.5: Resolved within SLA, suboptimal routing
        - -0.5: Resolved late, correct routing
        - -1.0: Resolved late, incorrect routing
        
        Args:
            outcome: Resolution outcome
        
        Returns:
            float: Reward value
            
        Requirements:
            - 8.4: Compute reward based on SLA compliance and routing correctness
        
        Examples:
            >>> handler = RLExceptionHandler()
            >>> outcome = ResolutionOutcome(
            ...     exception_id="exc_123",
            ...     resolved_at=datetime.utcnow(),
            ...     resolution_time_hours=2.5,
            ...     resolved_within_sla=True,
            ...     routing_was_correct=True
            ... )
            >>> handler.compute_reward(outcome)
            1.0
        """
        if outcome.resolved_within_sla and outcome.routing_was_correct:
            return 1.0
        elif outcome.resolved_within_sla and not outcome.routing_was_correct:
            return 0.5
        elif not outcome.resolved_within_sla and outcome.routing_was_correct:
            return -0.5
        else:  # Late and incorrect routing
            return -1.0
    
    def predict(self, state: Dict[str, Any]) -> str:
        """
        Predict best action for a given state using epsilon-greedy policy.
        
        Args:
            state: State representation
        
        Returns:
            str: Recommended action (routing destination)
            
        Requirements:
            - 8.3: Use RL policy for routing decisions
        
        Examples:
            >>> handler = RLExceptionHandler()
            >>> state = {"exception_type": "MATCHING_EXCEPTION", "severity": 0.75}
            >>> action = handler.predict(state)
            >>> action in ["AUTO_RESOLVE", "OPS_DESK", "SENIOR_OPS", "COMPLIANCE", "ENGINEERING"]
            True
        """
        # Epsilon-greedy: explore with probability epsilon
        if np.random.random() < self.epsilon:
            # Explore: random action
            return np.random.choice(self.actions)
        
        # Exploit: best action from Q-table
        state_hash = self._hash_state(state)
        
        # Get Q-values for all actions
        q_values = {
            action: self.q_table.get((state_hash, action), 0.0)
            for action in self.actions
        }
        
        # Return action with highest Q-value
        best_action = max(q_values.items(), key=lambda x: x[1])[0]
        return best_action
    
    def supervised_update(self, state: Dict[str, Any], correct_action: str) -> None:
        """
        Supervised learning update from human decision.
        
        When a human makes a routing decision, we learn from it by
        increasing the Q-value for that state-action pair.
        
        Args:
            state: State representation
            correct_action: Action chosen by human expert
            
        Requirements:
            - 8.5: Integrate supervised learning from human decisions
        
        Examples:
            >>> handler = RLExceptionHandler()
            >>> state = {"exception_type": "MATCHING_EXCEPTION", "severity": 0.75}
            >>> handler.supervised_update(state, "SENIOR_OPS")
        """
        state_hash = self._hash_state(state)
        
        # Increase Q-value for the correct action
        current_q = self.q_table.get((state_hash, correct_action), 0.0)
        
        # Supervised learning: move Q-value towards +1.0 (positive reward)
        new_q = current_q + self.learning_rate * (1.0 - current_q)
        
        self.q_table[(state_hash, correct_action)] = new_q
        
        print(f"Supervised update: state={state_hash[:8]}..., action={correct_action}, Q={new_q:.2f}")
    
    def _update_q_value(self, state_hash: str, action: str, reward: float) -> None:
        """
        Update Q-value using Q-learning update rule.
        
        Q(s,a) = Q(s,a) + α * (reward - Q(s,a))
        
        Args:
            state_hash: Hashed state representation
            action: Action taken
            reward: Reward received
        """
        # Get current Q-value
        current_q = self.q_table.get((state_hash, action), 0.0)
        
        # Q-learning update (simplified: no next state since episodes are terminal)
        new_q = current_q + self.learning_rate * (reward - current_q)
        
        # Update Q-table
        self.q_table[(state_hash, action)] = new_q
    
    def _hash_state(self, state: Dict[str, Any]) -> str:
        """
        Convert state dictionary to hash string for Q-table lookup.
        
        Args:
            state: State dictionary
        
        Returns:
            str: Hash string representing the state
        """
        # Create a canonical string representation of the state
        # Sort keys for consistency
        state_str = json.dumps(state, sort_keys=True)
        
        # Use hash for compact representation
        import hashlib
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the RL model.
        
        Returns:
            dict: Statistics including Q-table size, buffer size, etc.
        """
        return {
            "q_table_size": len(self.q_table),
            "replay_buffer_size": len(self.replay_buffer),
            "pending_episodes": len(self.pending_episodes),
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "epsilon": self.epsilon,
            "actions": self.actions,
        }
    
    def save_model(self, filepath: str) -> None:
        """
        Save RL model to file.
        
        Args:
            filepath: Path to save the model
        """
        model_data = {
            "q_table": self.q_table,
            "replay_buffer": list(self.replay_buffer),
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "epsilon": self.epsilon,
            "actions": self.actions,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Saved RL model to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """
        Load RL model from file.
        
        Args:
            filepath: Path to load the model from
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.q_table = model_data["q_table"]
        self.replay_buffer = deque(model_data["replay_buffer"], maxlen=self.buffer_size)
        self.learning_rate = model_data["learning_rate"]
        self.discount_factor = model_data["discount_factor"]
        self.epsilon = model_data["epsilon"]
        self.actions = model_data["actions"]
        
        print(f"Loaded RL model from {filepath}")
    
    def get_severity_adjustment(self, exception: ExceptionRecord) -> float:
        """
        Get RL-based severity adjustment for an exception.
        
        This analyzes historical patterns to adjust severity scores.
        
        Args:
            exception: Exception record
        
        Returns:
            float: Severity adjustment (-0.2 to +0.2)
            
        Requirements:
            - 8.2: Integrate historical patterns from RL
        """
        # Convert exception to state
        state = exception.to_state_vector()
        state_hash = self._hash_state(state)
        
        # Look for similar states in replay buffer
        similar_outcomes = [
            episode for episode in self.replay_buffer
            if episode["state_hash"] == state_hash
        ]
        
        if not similar_outcomes:
            return 0.0  # No adjustment if no historical data
        
        # Compute average reward for similar states
        avg_reward = np.mean([
            episode["reward"] for episode in similar_outcomes
        ])
        
        # Convert reward to severity adjustment
        # Negative rewards (bad outcomes) -> increase severity
        # Positive rewards (good outcomes) -> decrease severity
        adjustment = -avg_reward * 0.1  # Scale to [-0.2, +0.2]
        
        return max(-0.2, min(0.2, adjustment))


def create_default_rl_handler() -> RLExceptionHandler:
    """
    Create a default RL exception handler with standard parameters.
    
    Returns:
        RLExceptionHandler: Initialized handler
    """
    return RLExceptionHandler(
        learning_rate=0.1,
        discount_factor=0.9,
        epsilon=0.1,
        buffer_size=1000
    )
