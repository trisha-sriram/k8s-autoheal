import os
import anthropic
from kubernetes import client, config, watch

llm_client = anthropic.Anthropic()

def main():
    # Automatically loads your local personal 'kind' config
    config.load_kube_config()
    v1 = client.CoreV1Api()
    w = watch.Watch()

    print("Monitoring cluster for container failures...")

    for event in w.stream(v1.list_pod_for_all_namespaces):
        pod = event['object']
        event_type = event['type']

        if event_type == 'DELETED':
            continue

        pod_name = pod.metadata.name
        namespace = pod.metadata.namespace
        status = pod.status

        print("Event: %s %s" %(event['type'], event['object'].metadata.name))
        
        if not status.container_statuses:
            continue

        for c_status in status.container_statuses:
            state = c_status.state

            if state.waiting and state.waiting.reason in ["CrashLoopBackOff", "ImagePullBackOff"]:
                reason = state.waiting.reason
                print(f"\n🚨 ALERT: Pod [{pod_name}] in [{namespace}] failed: {reason}!")

                try:
                    print("trying logs")
                    logs = v1.read_namespaced_pod_log(
                        name=pod_name, 
                        namespace=namespace, 
                        tail_lines=50
                    )
                except Exception as e:
                    logs = f"Could not retrieve logs: {str(e)}"




def diagnose_with_llm(pod_name, reason, logs, context):
    pass
    # print(f"🧠 Passing {pod_name} failure telemetry to LLM...")

    # prompt = f"""A Kubernetes pod has failed with reason: {reason}

    # Pod name: {pod_name}

    # Last 50 lines of logs:
    # {logs}

    # Pod status:
    # {context}

    # Diagnose the root cause and suggest a concrete fix."""

    # response = llm_client.messages.create(
    #     model="claude-opus-4-8",
    #     max_tokens=1024,
    #     thinking={"type": "adaptive"},
    #     messages=[{"role": "user", "content": prompt}],
    # )

    # diagnosis = next((b.text for b in response.content if b.type == "text"), "")
    # print(f"🩺 Diagnosis:\n{diagnosis}")


if __name__ == "__main__":
    main()