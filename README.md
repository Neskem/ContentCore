# Deployment of Content Core

### 1. Deploy K8s related env file 
* Create CC env file
```
$ cd /kubernetes/env/
$ kubeclt apply -f content-core-namespace.yaml
$ cd /kubernetes/env/<environment>/
$ kubectl apply -f content-core-secret.yaml -n content-core
```
* Create nginx config file
```
$ cd /kubernetes/nginx
$ kubectl create configmap nginx-config --from-file=nginx.conf -n content-core
$ kubectl create configmap nginx-cc --from-file=default.conf -n content-core
```

* Create ssl authorization
```
$ cd /kubernetes/ssl
$ kubectl create secret tls breaktime-tls --cert breaktime_cert.pem --key breaktime_key.pem -n content-core
```

* Create docker tls secret file 
```
$ kubectl create secret docker-registry regcred \
--docker-server=https://index.docker.io/v1/ \
--docker-username=<docker_account_name> \
--docker-password=<docker_account_name> \
--docker-email=<docker_account_email> \
-n content-core
```
p.s If you don't use docker hub, --docker-server can replace by your docker-server.

### 2. Deploy K8s main components 
* Create k8s main components
```
$ cd /kubernetes/main
$ kubectl apply -f . -n content-core
```

* Check pod is running or not
```
$ kubectl get pod --watch
```

### 3. Create fluentd daemon set 
* Create fluentd main components
```
$ cd /kubernetes/fluentd
$ kubectl apply -f .
```

* Check fluentd daemon set is running or not
 ```
$ kubectl get ds -n kube-system
```