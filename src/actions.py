import json
from openai import OpenAI

llm_client = OpenAI()

#every action requires a "diagnosis" field so we get the reasoning and the
#chosen fix back from a single LLM call, instead of calling twice
DIAGNOSIS_FIELD = {
    "diagnosis": {
        "type": "string",
        "description": "Explanation of the root cause that led to choosing this action.",
    },
}

#the small, fixed set of actions the agent is allowed to take
tools = [
    {
        "type": "function",
        "name": "restart_pod",
        "description": "Delete the pod to force it to restart. Safe default for transient crashes.",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "pod_name": {"type": "string"},
                **DIAGNOSIS_FIELD,
            },
            "required": ["namespace", "pod_name", "diagnosis"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "rollback_deployment",
        "description": "Roll back the pod's owning Deployment to its previous revision. Use when a recent bad rollout looks like the cause.",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "deployment_name": {"type": "string"},
                **DIAGNOSIS_FIELD,
            },
            "required": ["namespace", "deployment_name", "diagnosis"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "scale_deployment",
        "description": "Change a Deployment's replica count. Use for resource-pressure failures.",
        "parameters": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "deployment_name": {"type": "string"},
                "replicas": {"type": "integer"},
                **DIAGNOSIS_FIELD,
            },
            "required": ["namespace", "deployment_name", "replicas", "diagnosis"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "escalate_to_human",
        "description": "No safe automated fix applies. Use for anything requiring a code change or judgment call.",
        "parameters": {
            "type": "object",
            "properties": {
                **DIAGNOSIS_FIELD,
            },
            "required": ["diagnosis"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def choose_action(prompt):
    print("Calling choose_action function, passing the prompt to llm")
    response = llm_client.responses.create(
        model="gpt-6-astra",
        input=prompt,
        tools=tools,
        tool_choice="required",
    )

    for item in response.output:
        if item.type == "function_call":
            return item.name, json.loads(item.arguments)

    return None, None
