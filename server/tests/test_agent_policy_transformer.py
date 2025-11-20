import types

from app.policies.agent_policy_transformer import AgentPolicyTransformer


def make_policy(
    *,
    policy_id: str,
    name: str,
    policy_type: str,
    enabled: bool = True,
    priority: int = 100,
    severity: str = "medium",
    config: dict | None = None,
    actions: dict | None = None,
):
    return types.SimpleNamespace(
        id=policy_id,
        name=name,
        type=policy_type,
        enabled=enabled,
        priority=priority,
        severity=severity,
        config=config or {},
        actions=actions or {},
        compliance_tags=[],
        updated_at=None,
        created_at=None,
    )


def test_windows_bundle_includes_supported_policies():
    transformer = AgentPolicyTransformer()
    policies = [
        make_policy(
            policy_id="p-clipboard",
            name="Clipboard Policy",
            policy_type="clipboard_monitoring",
            config={"monitoredPaths": [], "action": "alert"},
        ),
        make_policy(
            policy_id="p-files",
            name="Files Policy",
            policy_type="file_system_monitoring",
            config={"monitoredPaths": ["C:/Sensitive"], "action": "alert"},
        ),
        make_policy(
            policy_id="p-usb",
            name="USB Policy",
            policy_type="usb_file_transfer_monitoring",
            config={"monitoredPaths": ["C:/Sensitive"], "action": "block"},
        ),
    ]

    bundle = transformer.build_bundle(policies, platform="windows")

    assert bundle["policies"]["clipboard_monitoring"]
    assert bundle["policies"]["file_system_monitoring"]
    assert bundle["policies"]["usb_file_transfer_monitoring"]


def test_linux_bundle_filters_platform():
    transformer = AgentPolicyTransformer()
    policies = [
        make_policy(
            policy_id="p-clipboard",
            name="Clipboard Policy",
            policy_type="clipboard_monitoring",
            config={"monitoredPaths": [], "action": "alert"},
        ),
        make_policy(
            policy_id="p-files",
            name="Files Policy",
            policy_type="file_system_monitoring",
            config={"monitoredPaths": ["/opt/data"], "action": "alert"},
        ),
    ]

    bundle = transformer.build_bundle(policies, platform="linux")

    assert "clipboard_monitoring" not in bundle["policies"]
    assert bundle["policies"]["file_system_monitoring"][0]["config"]["monitoredPaths"] == ["/opt/data"]


def test_version_changes_when_policy_changes():
    transformer = AgentPolicyTransformer()
    policy = make_policy(
        policy_id="p-files",
        name="Files Policy",
        policy_type="file_system_monitoring",
        config={"monitoredPaths": ["C:/Docs"], "action": "alert"},
    )

    bundle_v1 = transformer.build_bundle([policy], platform="windows")
    policy.config["monitoredPaths"].append("C:/Secret")
    bundle_v2 = transformer.build_bundle([policy], platform="windows")

    assert bundle_v1["version"] != bundle_v2["version"]


