"""
Policy Evaluation Engine
Evaluates events against DLP policies with complex condition logic
"""

import re
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PolicyEvaluator:
    """
    Evaluates DLP events against policies
    """

    def __init__(self):
        self.policies: List[Dict[str, Any]] = []
        self.state_tracker: Dict[str, List[Dict]] = {}  # For stateful rules

    def load_policy(self, policy_yaml: str) -> None:
        """
        Load policy from YAML

        Args:
            policy_yaml: YAML policy definition
        """
        try:
            policy = yaml.safe_load(policy_yaml)
            self.policies.append(policy)
            # Sort by priority (higher first)
            self.policies.sort(key=lambda p: p.get('priority', 100), reverse=True)
            logger.info(f"Loaded policy: {policy.get('name')}")
        except Exception as e:
            logger.error(f"Failed to load policy: {e}")
            raise

    def evaluate_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate event against all policies

        Args:
            event: DLP event

        Returns:
            List of matching policies and actions
        """
        matches = []

        for policy in self.policies:
            if not policy.get('enabled', True):
                continue

            if self._evaluate_conditions(event, policy.get('conditions', {})):
                # Check stateful conditions if present
                if 'stateful' in policy:
                    if not self._evaluate_stateful(event, policy):
                        continue

                # Policy matched
                match_info = {
                    'policy_id': policy.get('id'),
                    'policy_name': policy.get('name'),
                    'priority': policy.get('priority', 100),
                    'actions': policy.get('actions', []),
                    'compliance_tags': policy.get('compliance_tags', []),
                }

                matches.append(match_info)
                logger.info(
                    f"Policy matched: {policy.get('name')} for event {event.get('id')}"
                )

        return matches

    def _evaluate_conditions(
        self,
        event: Dict[str, Any],
        conditions: Dict[str, Any]
    ) -> bool:
        """
        Evaluate policy conditions

        Args:
            event: Event data
            conditions: Policy conditions

        Returns:
            True if conditions match
        """
        # Handle 'all' (AND logic)
        if 'all' in conditions:
            return all(
                self._evaluate_condition(event, cond)
                for cond in conditions['all']
            )

        # Handle 'any' (OR logic)
        if 'any' in conditions:
            return any(
                self._evaluate_condition(event, cond)
                for cond in conditions['any']
            )

        # Handle 'not' (NOT logic)
        if 'not' in conditions:
            return not self._evaluate_conditions(event, conditions['not'])

        # Single condition
        return self._evaluate_condition(event, conditions)

    def _evaluate_condition(
        self,
        event: Dict[str, Any],
        condition: Dict[str, Any]
    ) -> bool:
        """
        Evaluate single condition

        Args:
            event: Event data
            condition: Single condition

        Returns:
            True if condition matches
        """
        field = condition.get('field', '')
        operator = condition.get('operator', '==')
        value = condition.get('value')

        # Get field value from event (support nested fields)
        event_value = self._get_nested_value(event, field)

        # Evaluate based on operator
        operators = {
            '==': lambda ev, v: ev == v,
            '!=': lambda ev, v: ev != v,
            '>': lambda ev, v: ev > v,
            '>=': lambda ev, v: ev >= v,
            '<': lambda ev, v: ev < v,
            '<=': lambda ev, v: ev <= v,
            'contains': lambda ev, v: v in ev if isinstance(ev, (list, str)) else False,
            'not contains': lambda ev, v: v not in ev if isinstance(ev, (list, str)) else True,
            'in': lambda ev, v: ev in v if isinstance(v, list) else False,
            'not in': lambda ev, v: ev not in v if isinstance(v, list) else True,
            'regex': lambda ev, v: bool(re.search(v, str(ev))),
            'exists': lambda ev, v: ev is not None,
        }

        eval_func = operators.get(operator)
        if not eval_func:
            logger.warning(f"Unknown operator: {operator}")
            return False

        try:
            result = eval_func(event_value, value)
            return result
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False

    def _evaluate_stateful(
        self,
        event: Dict[str, Any],
        policy: Dict[str, Any]
    ) -> bool:
        """
        Evaluate stateful conditions (frequency/threshold)

        Args:
            event: Event data
            policy: Policy definition

        Returns:
            True if stateful conditions match
        """
        stateful = policy.get('stateful', {})
        window_seconds = self._parse_duration(stateful.get('window', '5m'))
        threshold = stateful.get('threshold', {})
        count_threshold = threshold.get('count', 1)
        distinct_field = threshold.get('distinct_field')

        policy_id = policy.get('id')
        if policy_id not in self.state_tracker:
            self.state_tracker[policy_id] = []

        # Add current event to state
        self.state_tracker[policy_id].append({
            'timestamp': datetime.utcnow(),
            'event': event,
        })

        # Clean old events outside window
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        self.state_tracker[policy_id] = [
            item for item in self.state_tracker[policy_id]
            if item['timestamp'] > cutoff_time
        ]

        # Count events in window
        events_in_window = self.state_tracker[policy_id]

        if distinct_field:
            # Count distinct values
            distinct_values = set(
                self._get_nested_value(item['event'], distinct_field)
                for item in events_in_window
            )
            count = len(distinct_values)
        else:
            # Count all events
            count = len(events_in_window)

        # Check threshold
        return count >= count_threshold

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """
        Get nested value from dictionary using dot notation

        Args:
            data: Dictionary
            path: Dot-separated path (e.g., 'classification.score')

        Returns:
            Value at path or None
        """
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

            if value is None:
                return None

        return value

    def _parse_duration(self, duration: str) -> int:
        """
        Parse duration string to seconds

        Args:
            duration: Duration string (e.g., '5m', '1h', '30s')

        Returns:
            Duration in seconds
        """
        units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
        }

        match = re.match(r'(\d+)([smhd])', duration)
        if match:
            value, unit = match.groups()
            return int(value) * units.get(unit, 1)

        return 300  # Default 5 minutes


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    evaluator = PolicyEvaluator()

    # Example policy YAML
    policy_yaml = """
policy:
  id: "pol-001-pci-dss"
  name: "Block Credit Card Exfiltration"
  version: "1.2.0"
  enabled: true
  priority: 100

  conditions:
    all:
      - field: "classification.labels"
        operator: "contains"
        value: "PAN"
      - field: "classification.score"
        operator: ">="
        value: 0.85
      - field: "event.direction"
        operator: "=="
        value: "outbound"

  stateful:
    window: "5m"
    threshold:
      count: 3
      distinct_field: "user_id"

  actions:
    - type: "block"
      notify:
        - "security-team@company.com"
    - type: "log"
      severity: "critical"

  compliance:
    - "PCI-DSS 3.4"
    - "GDPR Article 32"
"""

    evaluator.load_policy(policy_yaml)

    # Example event
    test_event = {
        "id": "evt-12345",
        "classification": {
            "score": 0.92,
            "labels": ["PAN", "HIGH_ENTROPY"]
        },
        "event": {
            "direction": "outbound"
        },
        "user_id": "user-123"
    }

    # Evaluate
    matches = evaluator.evaluate_event(test_event)
    print(f"Matching policies: {len(matches)}")
    for match in matches:
        print(f"  - {match['policy_name']}: {match['actions']}")
