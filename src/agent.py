import os
from google import genai
from kubernetes import client, config, watch

llm_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def main():
    # Automatically loads your local personal 'kind' config
    config.load_kube_config()
    v1 = client.CoreV1Api()
    w = watch.Watch()

    print("Monitoring cluster for container failures...")

    already_diagnosed = set()

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
                key = (namespace, pod_name, c_status.restart_count)
                if key in already_diagnosed:
                    continue
                already_diagnosed.add(key)

                reason = state.waiting.reason
                print(f"\n ALERT: Pod [{pod_name}] in [{namespace}] failed: {reason}!")

                try:
                    print("Writing logs...")
                    logs = v1.read_namespaced_pod_log(
                        name=pod_name, 
                        namespace=namespace, 
                        tail_lines=50
                    )
                except Exception as e:
                    logs = f"Could not retrieve logs: {str(e)}"

                context = str(status)

                diagnose_with_llm(pod_name, reason, logs, context)




def diagnose_with_llm(pod_name, reason, logs, context):
    print(f"Passing {pod_name} failure telemetry to LLM...")

    prompt = f"""A Kubernetes pod has failed with reason: {reason}

    Pod name: {pod_name}

    Last 50 lines of logs:
     {logs}

     Pod status:
     {context}

    Diagnose the root cause and suggest a concrete fix."""

    response = llm_client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
    )

    print(f"🩺 Diagnosis:\n{response.text}")


if __name__ == "__main__":
    main()