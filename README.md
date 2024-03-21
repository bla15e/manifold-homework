# Live Demo
You can access a live instance of this running on Kubernetes at:
https://hw.ise.international/ping

## Homework-Server
Python server using FastAPI.
Running a compose stack locally:
```bash
# The server will be reachable at localhost:4000
./scripts/.dev-compose-up.sh

```
### Rate Limiting
Sliding Window Rate Limiting implemented with Redis.
Rate is calculated for the entire application, clients are not individually throttled. 

Default Parameters: 
Max Requests in Window: 3
Window Duration: 10 seconds

## k8s
Kubernetes Resource definitions

Uses a locally running docker registry with the `homework-server` image build and available.
This is so we can deploy our container without publishing through an external registry

Installing on a Cluster:
```bash
./scripts/run-image-registry-local.sh
## In Another Terminal...
./scripts/build-push-image-local.sh
cd k8s
kubectl apply --recursive -f .

```
