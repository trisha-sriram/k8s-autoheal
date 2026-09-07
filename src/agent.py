from kubernetes import client, config, watch

config.load_kube_config()

v1 = client.CoreV1Api()

#adding a basic prompt function to grab the event
def build_prompt(event_obj):
    #starting with basic problem
    return f"A pod named {event_obj.involved_object.name} had this problem: {event_obj.message}"


#watching for pod events
w = watch.Watch()
for event in w.stream(v1.list_event_for_all_namespaces, _request_timeout=60):
    obj = event['object']
    print("Event: %s %s/%s: %s" % (event['type'], obj.involved_object.kind, obj.involved_object.name, obj.message))

    #calling my prompt function
    prompt = build_prompt(obj)
    print(prompt)
    print()