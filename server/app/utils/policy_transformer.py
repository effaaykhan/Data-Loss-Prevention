"""
Policy Transformer
Transforms frontend policy config format to backend conditions/actions format
"""

from typing import Dict, Any, List, Optional, Tuple


def transform_frontend_config_to_backend(
    policy_type: str, config: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Transform frontend config format to backend conditions/actions format

    Args:
        policy_type: Policy type ('clipboard_monitoring', 'file_system_monitoring', etc.)
        config: Frontend config dictionary

    Returns:
        Tuple of (conditions_dict, actions_dict)
    """
    if policy_type == "clipboard_monitoring":
        return _transform_clipboard_config(config)
    elif policy_type == "file_system_monitoring":
        return _transform_file_system_config(config)
    elif policy_type == "usb_device_monitoring":
        return _transform_usb_device_config(config)
    elif policy_type == "usb_file_transfer_monitoring":
        return _transform_usb_transfer_config(config)
    else:
        # Unknown type, return empty defaults
        return (
            {"match": "all", "rules": []},
            {"log": {}},
        )


def _transform_clipboard_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Transform clipboard monitoring config to backend format

    Frontend format:
    {
        "patterns": {
            "predefined": ["ssn", "credit_card", "api_key"],
            "custom": [{"regex": "...", "description": "..."}]
        },
        "action": "alert" | "log"
    }

    Backend format:
    conditions: {
        "match": "any",
        "rules": [
            {"field": "clipboard_content", "operator": "matches_regex", "value": "..."},
            ...
        ]
    }
    actions: {
        "alert": {} | "log": {}
    }
    """
    patterns = config.get("patterns", {})
    predefined = patterns.get("predefined", [])
    custom = patterns.get("custom", [])
    action = config.get("action", "log")

    # Predefined pattern regexes
    predefined_patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "api_key": r"\b[A-Za-z0-9_-]{32,}\b",
        "private_key": r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
        "password": r"(?i)(password|pwd|passwd)\s*[:=]\s*\S+",
    }

    rules = []

    # Add predefined patterns
    for pattern_id in predefined:
        if pattern_id in predefined_patterns:
            rules.append(
                {
                    "field": "clipboard_content",
                    "operator": "matches_regex",
                    "value": predefined_patterns[pattern_id],
                }
            )

    # Add custom patterns
    for custom_pattern in custom:
        regex = custom_pattern.get("regex", "")
        if regex:
            rules.append(
                {
                    "field": "clipboard_content",
                    "operator": "matches_regex",
                    "value": regex,
                }
            )

    # Build conditions
    conditions = {
        "match": "any" if len(rules) > 1 else "all",
        "rules": rules,
    }

    # Build actions
    actions = {action: {}}

    return conditions, actions


def _transform_file_system_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Transform file system monitoring config to backend format

    Frontend format:
    {
        "monitoredPaths": ["C:\\Users\\...", "D:\\..."],
        "fileExtensions": [".pdf", ".docx"],
        "events": {
            "create": true,
            "modify": true,
            "delete": false,
            "move": true,
            "copy": false
        },
        "action": "alert" | "quarantine" | "block" | "log",
        "quarantinePath": "C:\\Quarantine" (optional)
    }

    Backend format:
    conditions: {
        "match": "all",
        "rules": [
            {"field": "file_path", "operator": "starts_with", "value": "..."},
            {"field": "event_type", "operator": "in", "value": ["create", "modify", ...]},
            {"field": "file_extension", "operator": "in", "value": [".pdf", ...]} (if specified)
        ]
    }
    actions: {
        "alert": {} | "quarantine": {"path": "..."} | "block": {} | "log": {}
    }
    """
    monitored_paths = config.get("monitoredPaths", [])
    file_extensions = config.get("fileExtensions", [])
    events = config.get("events", {})
    action = config.get("action", "log")
    quarantine_path = config.get("quarantinePath")

    rules = []

    # Add path rules (any of the monitored paths)
    if monitored_paths:
        if len(monitored_paths) == 1:
            rules.append(
                {
                    "field": "file_path",
                    "operator": "starts_with",
                    "value": monitored_paths[0],
                }
            )
        else:
            # Multiple paths - use "in" operator
            rules.append(
                {
                    "field": "file_path",
                    "operator": "matches_any_prefix",
                    "value": monitored_paths,
                }
            )

    # Add event type rules
    event_name_map = {
        "create": "file_created",
        "modify": "file_modified",
        "delete": "file_deleted",
        "move": "file_moved",
        "copy": "file_copied",
    }
    enabled_events = [
        event_name_map.get(event, event)
        for event, enabled in events.items()
        if enabled
    ]
    if enabled_events:
        rules.append(
            {
                "field": "event_subtype",
                "operator": "in",
                "value": enabled_events,
            }
        )

    # Add file extension rules (if specified)
    if file_extensions:
        rules.append(
            {
                "field": "file_extension",
                "operator": "in",
                "value": file_extensions,
            }
        )

    # Build conditions
    conditions = {
        "match": "all",
        "rules": rules,
    }

    # Build actions
    actions = {}
    if action == "quarantine" and quarantine_path:
        actions["quarantine"] = {"path": quarantine_path}
    else:
        actions[action] = {}

    return conditions, actions


def _transform_usb_device_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Transform USB device monitoring config to backend format

    Frontend format:
    {
        "events": {
            "connect": true,
            "disconnect": true,
            "fileTransfer": false
        },
        "action": "alert" | "log" | "block"
    }

    Backend format:
    conditions: {
        "match": "any",
        "rules": [
            {"field": "usb_event_type", "operator": "in", "value": ["connect", "disconnect", ...]}
        ]
    }
    actions: {
        "alert": {} | "log": {} | "block": {}
    }
    """
    events = config.get("events", {})
    action = config.get("action", "log")

    enabled_events = []
    if events.get("connect"):
        enabled_events.append("connect")
    if events.get("disconnect"):
        enabled_events.append("disconnect")
    if events.get("fileTransfer"):
        enabled_events.append("file_transfer")

    rules = []
    if enabled_events:
        rules.append(
            {
                "field": "usb_event_type",
                "operator": "in",
                "value": enabled_events,
            }
        )

    # Build conditions
    conditions = {
        "match": "any" if len(enabled_events) > 1 else "all",
        "rules": rules,
    }

    # Build actions
    actions = {action: {}}

    return conditions, actions


def _transform_usb_transfer_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Transform USB file transfer monitoring config to backend format

    Frontend format:
    {
        "monitoredPaths": ["C:\\Users\\...", "D:\\..."],
        "action": "block" | "quarantine" | "alert",
        "quarantinePath": "C:\\Quarantine" (optional, for quarantine action)
    }

    Backend format:
    conditions: {
        "match": "all",
        "rules": [
            {"field": "source_path", "operator": "matches_any_prefix", "value": [...]},
            {"field": "destination_type", "operator": "equals", "value": "removable_drive"}
        ]
    }
    actions: {
        "block": {} | "quarantine": {"path": "..."} | "alert": {}
    }
    """
    monitored_paths = config.get("monitoredPaths", [])
    action = config.get("action", "block")
    quarantine_path = config.get("quarantinePath")

    rules = []

    # Add source path rules
    if monitored_paths:
        if len(monitored_paths) == 1:
            rules.append(
                {
                    "field": "source_path",
                    "operator": "starts_with",
                    "value": monitored_paths[0],
                }
            )
        else:
            rules.append(
                {
                    "field": "source_path",
                    "operator": "matches_any_prefix",
                    "value": monitored_paths,
                }
            )

    # Add destination type rule (must be removable drive)
    rules.append(
        {
            "field": "destination_type",
            "operator": "equals",
            "value": "removable_drive",
        }
    )

    # Build conditions
    conditions = {
        "match": "all",
        "rules": rules,
    }

    # Build actions
    actions = {}
    if action == "quarantine" and quarantine_path:
        actions["quarantine"] = {"path": quarantine_path}
    else:
        actions[action] = {}

    return conditions, actions

