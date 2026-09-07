from kubernetes import client, config, watch

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

    #stating problem with logs to feed into the prompt
    return f"A pod named {pod_name} had this problem: {event_obj.message}\n\nThe pod's logs state:\n{logs}"

    


#watching for pod events
w = watch.Watch()
for event in w.stream(v1.list_event_for_all_namespaces, _request_timeout=60):
    obj = event['object']
    print("Event: %s %s/%s: %s" % (event['type'], obj.involved_object.kind, obj.involved_object.name, obj.message))
    print()

    #calling my prompt function
    prompt = build_prompt(obj)
    print(prompt)
    print()