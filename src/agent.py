from kubernetes import client, config, watch
from actions import choose_action

config.load_kube_config()

v1 = client.CoreV1Api()

#adding a basic prompt function to grab the event
def build_prompt(event_obj):
    pod_name = event_obj.involved_object.name
    namespace = event_obj.involved_object.namespace

    #getting pod logs for prompt
    try:
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=50)
    except Exception as e:
        logs = f"Could not retrieve logs: {e}"

    #getting container spec and exit/termination info
    try:
        #container spec
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        container = pod.spec.containers[0]
        spec_info = f"image: {container.image}, command: {container.command}, args: {container.args}"

        #resource requests/limits
        resources_info = f"requests: {container.resources.requests}, limits: {container.resources.limits}"

        #exit code
        c_status = pod.status.container_statuses[0]
        if c_status.state.terminated:
            exit_info = f"exit code: {c_status.state.terminated.exit_code}, reason: {c_status.state.terminated.reason}"
        elif c_status.state.waiting:
            exit_info = f"waiting reason: {c_status.state.waiting.reason}"
        else:
            exit_info = "container is currently running"

        #adding restart count to exit info
        exit_info += f", restart count: {c_status.restart_count}"
        
    except Exception:
        spec_info = "Could not retrieve container spec (pod may no longer exist)"
        resources_info = "Could not retrieve resource info (pod may no longer exist)"
        exit_info = "Could not retrieve exit info (pod may no longer exist)"

    #stating problem with above info to feed into the prompt
    return f"A pod named {pod_name} had this problem: {event_obj.message}\n\nContainer spec:\n{spec_info}\nResource requests/limits:\n{resources_info}\nExit info:\n{exit_info}\n\nThe pod's logs state:\n{logs}"

    
#adding metric server cpu/memory metrics later on for prompt, testing basic prompt for now

#watching for pod events
w = watch.Watch()
for event in w.stream(v1.list_event_for_all_namespaces, _request_timeout=60):
    obj = event['object']
    print("Event: %s %s/%s: %s" % (event['type'], obj.involved_object.kind, obj.involved_object.name, obj.message))
    print()

    #only build a prompt for actual pod failures, not every routine event
    if obj.involved_object.kind == "Pod" and obj.reason in ("BackOff", "Failed"):
        #calling my prompt function
        prompt = build_prompt(obj)
        print("Prompt: %s" % prompt)
        print()

        #one call gets both the diagnosis and the chosen fix
        action_name, action_args = choose_action(prompt)
        print("Diagnosis: %s" % action_args.pop("diagnosis"))
        print()
        print(f"Chosen action: {action_name} {action_args}")
        print()

        #stopping after one diagnosis for now, don't want to re-diagnose on every restart
        w.stop()
        break


