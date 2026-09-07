'''
Basing this off guide: https://github.com/kubernetes-client/python but continously 
watching it instead of capping it at 10 events.
'''

from kubernetes import client, config, watch

config.load_kube_config()

v1 = client.CoreV1Api()
w = watch.Watch()
for event in w.stream(v1.list_event_for_all_namespaces, _request_timeout=60):
    obj = event['object']
    print("Event: %s %s/%s: %s" % (event['type'], obj.involved_object.kind, obj.involved_object.name, obj.message))

print("Ended.")
