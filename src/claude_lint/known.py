"""Known-good values for validation. Override via .claude-lint.json."""

# Tool names Claude Code recognizes (as of 2026-04).
# This is a living list — extend via config `known_tools` if you use MCP tools.
KNOWN_TOOLS = {
    "Agent",
    "AskUserQuestion",
    "Bash",
    "BashOutput",
    "CronCreate",
    "CronDelete",
    "CronList",
    "Edit",
    "EnterPlanMode",
    "EnterWorktree",
    "ExitPlanMode",
    "ExitWorktree",
    "Glob",
    "Grep",
    "KillShell",
    "ListMcpResourcesTool",
    "Monitor",
    "MultiEdit",
    "NotebookEdit",
    "PushNotification",
    "Read",
    "ReadMcpResourceTool",
    "RemoteTrigger",
    "ScheduleWakeup",
    "SendMessage",
    "Skill",
    "SlashCommand",
    "Task",
    "TaskCreate",
    "TaskGet",
    "TaskList",
    "TaskOutput",
    "TaskStop",
    "TaskUpdate",
    "ToolSearch",
    "WebFetch",
    "WebSearch",
    "Write",
}

# Valid hook event names.
KNOWN_HOOK_EVENTS = {
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "Notification",
    "Stop",
    "SubagentStop",
    "PreCompact",
    "SessionStart",
    "SessionEnd",
}

# Valid / current model IDs and family prefixes.
# Anything matching a stale prefix is flagged (claude-3-*, claude-2-*).
STALE_MODEL_PREFIXES = (
    "claude-2",
    "claude-3-",
    "claude-3.5-",
    "claude-instant",
)

CURRENT_MODEL_PREFIXES = (
    "claude-opus-4",
    "claude-sonnet-4",
    "claude-haiku-4",
    "opus",
    "sonnet",
    "haiku",
    "inherit",
)
