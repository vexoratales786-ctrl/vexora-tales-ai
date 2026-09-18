from command_router import parse_command


def test_hinglish_generation_commands():
    cmd = parse_command("Ek Short banao")
    assert cmd.intent == "generate"
    assert cmd.content_type == "short"

    cmd = parse_command("10 minute ka long video banao")
    assert cmd.intent == "generate"
    assert cmd.content_type == "long"
    assert cmd.duration_seconds == 600


def test_topic_and_plan_commands():
    cmd = parse_command("short banao topic: strange space mystery")
    assert cmd.intent == "generate"
    assert cmd.content_type == "short"
    assert cmd.topic == "strange space mystery"

    assert parse_command("30 din ka plan").intent == "plan_30"
    assert parse_command("aaj ka trend batao").intent == "trend"


def test_upload_requires_explicit_confirmation():
    assert parse_command("Upload kar do").intent == "request_upload"
    assert parse_command("YES, UPLOAD").intent == "approve_upload"
