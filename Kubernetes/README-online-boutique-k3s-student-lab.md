# Kubernetes Distributed Systems Lab: Online Boutique on k3s

## 1. Lab Overview

In this lab, you will troubleshoot a distributed microservices application running on a multi-node **k3s Kubernetes cluster**.

The application is **Google Online Boutique**, also known as **microservices-demo**:

<https://github.com/GoogleCloudPlatform/microservices-demo/tree/main>

Online Boutique is a web-based e-commerce demo application. Users can browse products, add items to a shopping cart, and complete a mock checkout flow. The application is built as a set of independent microservices that communicate through Kubernetes Services and gRPC.

Your goal is to work in your assigned group, inspect your assigned Kubernetes YAML files, troubleshoot the deployed system, apply a fix, and help make the full website work correctly.

---

## 2. What Is Deployed on the k3s Cluster?

The lab is deployed on a 6-node k3s cluster:

```text
k3s-master      172.16.0.100
k3s-worker-1    172.16.0.101
k3s-worker-2    172.16.0.102
k3s-worker-3    172.16.0.103
k3s-worker-4    172.16.0.104
k3s-worker-5    172.16.0.105
```

The application runs in the Kubernetes namespace:

```text
online-boutique
```

The website is exposed through the frontend service.

Your instructor will provide the access address, usually similar to:

```text
http://172.16.0.100:30080
```

---

## 3. How Kubernetes Deploys This Application

The application is described using Kubernetes YAML files.

Each YAML file can define resources such as:

```text
Deployment
Service
ServiceAccount
```

A **Deployment** tells Kubernetes how to run application pods.

A **Service** gives stable networking to pods and allows one microservice to call another.

A **ServiceAccount** provides an identity for a pod inside Kubernetes.

Important: the YAML file does not run directly on the worker where it is stored. When you run `kubectl apply`, the YAML is sent to the Kubernetes API server on the master node. Then the Kubernetes scheduler decides which node should run each pod.

The flow is:

```text
YAML file
  ↓
kubectl apply
  ↓
Kubernetes API server
  ↓
scheduler
  ↓
worker nodes run the pods
```

So even though your group file is stored on a worker VM, the pod may be scheduled on any node in the cluster.

---

## 4. Microservices in the Website

The application includes multiple services. Some examples:

```text
frontend
cartservice
checkoutservice
currencyservice
productcatalogservice
shippingservice
paymentservice
emailservice
recommendationservice
adservice
redis-cart
loadgenerator
```

These services work together to provide the shopping website.

For example:

```text
frontend receives user requests
productcatalogservice provides product data
cartservice stores cart items
redis-cart stores cart data
checkoutservice coordinates checkout
paymentservice mocks payment
shippingservice mocks shipping
emailservice mocks confirmation email
currencyservice handles currency conversion
recommendationservice suggests products
adservice provides ads
```

If one service is misconfigured, the website may still load partially, but some actions such as cart, checkout, product loading, or pricing may fail.

---

## 5. Lab File Structure

Your instructor has split the original large manifest into separate YAML files so groups do not edit the same file at the same time.

The correct base structure is:

```text
00-base-other-services.yaml
group-1-checkoutservice.yaml
group-2-cartservice.yaml
group-2-redis-cart.yaml
group-3-shippingservice.yaml
group-4-currencyservice.yaml
group-4-productcatalogservice.yaml
```

Each group works only inside its assigned worker VM and assigned YAML file or files.

---

## 6. Group Assignments

### Group 1

```text
Worker: k3s-worker-1
Files:
  ~/online-boutique-task/group-1-checkoutservice.yaml
```

### Group 2

```text
Worker: k3s-worker-2
Files:
  ~/online-boutique-task/group-2-cartservice.yaml
  ~/online-boutique-task/group-2-redis-cart.yaml
```

### Group 3

```text
Worker: k3s-worker-3
Files:
  ~/online-boutique-task/group-3-shippingservice.yaml
```

### Group 4

```text
Worker: k3s-worker-4
Files:
  ~/online-boutique-task/group-4-currencyservice.yaml
  ~/online-boutique-task/group-4-productcatalogservice.yaml
```

---

## 7. Number of Intentional Mistakes

There are **4 intentional configuration mistakes** in the lab.

Each group is responsible for investigating its assigned YAML file or files and identifying the problem affecting its part of the application.

The mistakes are related to Kubernetes and distributed-service configuration. They may involve service communication, ports, readiness, or service routing.

The exact locations of the mistakes are not provided. You must discover them using Kubernetes troubleshooting commands.

---

## 8. Team Workflow

Each group should follow this workflow:

```text
1. Log into your assigned worker VM.
2. Go to your task directory.
3. Inspect your assigned YAML file or files.
4. Check the current Kubernetes state.
5. Use kubectl commands to find symptoms.
6. Compare pods, services, deployments, endpoints, and logs.
7. Edit only your assigned YAML file or files.
8. Apply your fixed YAML file.
9. Verify that your service becomes healthy.
10. Report your root cause and fix to the class.
```

Only edit your assigned files. Do not edit files assigned to other groups.

---

## 9. Student Working Directory

On your assigned worker VM:

```text
~/online-boutique-task
```

Your group YAML files are stored there.

---

## 10. Apply Your Group File

Use this command from your group directory:

```bash
kubectl apply -f <your-file.yaml>
```

If your group has two files, apply both:

```bash
kubectl apply -f <your-first-file.yaml>
kubectl apply -f <your-second-file.yaml>
```

---

## 11. General Kubernetes Troubleshooting Commands

Use the following commands to inspect the application.

### Check pods

```bash
kubectl get pods
```

```bash
kubectl get pods -o wide
```

### Check services

```bash
kubectl get svc
```

```bash
kubectl describe svc <service-name>
```

### Check endpoints

```bash
kubectl get endpoints
```

```bash
kubectl get endpoints <service-name> -o yaml
```

### Check deployments

```bash
kubectl get deployment
```

```bash
kubectl describe deployment <deployment-name>
```

```bash
kubectl get deployment <deployment-name> -o yaml
```

### Check pods with labels

```bash
kubectl get pods --show-labels
```

### Describe a pod

```bash
kubectl describe pod <pod-name>
```

### View logs

```bash
kubectl logs deployment/<deployment-name>
```

```bash
kubectl logs <pod-name>
```

```bash
kubectl logs <pod-name> --previous
```

### Check events

```bash
kubectl get events --sort-by=.lastTimestamp
```

### Restart a deployment after changing a Deployment YAML

```bash
kubectl rollout restart deployment/<deployment-name>
```

### Check rollout status

```bash
kubectl rollout status deployment/<deployment-name>
```

---

## 12. Useful Verification Commands

After applying your fix, use:

```bash
kubectl get pods -o wide
```

```bash
kubectl get svc
```

```bash
kubectl get endpoints
```

```bash
kubectl get events --sort-by=.lastTimestamp
```

If all groups fixed their parts correctly, the important pods should be running and ready.

---

## 13. What a Working Result Looks Like

A healthy deployment should have the main application pods in this state:

```text
READY 1/1
STATUS Running
```

Example services that should be healthy include:

```text
frontend
cartservice
checkoutservice
currencyservice
productcatalogservice
shippingservice
paymentservice
emailservice
recommendationservice
adservice
redis-cart
```

The website should allow a user to:

```text
open the homepage
browse products
open a product page
add a product to cart
view cart
complete mock checkout
```

---

## 14. What to Submit

Each group should submit a short report containing:

```text
Group number
Assigned file or files
Observed symptoms
Commands used
Evidence from Kubernetes output
Root cause
YAML change made
Verification after fix
What Kubernetes concept was involved
What distributed systems concept was involved
```

Do not submit only the final answer. Show how you found the problem.

---

## 15. Important Rules

```text
Do not edit another group’s files.
Do not delete the namespace.
Do not delete other groups’ deployments.
Do not randomly change image names.
Do not restart the whole cluster.
Do not modify the k3s system namespace.
```

Use Kubernetes evidence before making a change.

---

## 16. Key Concepts Practiced

This lab practices:

```text
Kubernetes Deployments
Kubernetes Services
Service discovery
Endpoints
Pod labels and selectors
Readiness and health
gRPC microservice communication
Distributed dependency chains
Troubleshooting with logs and events
Team-based debugging
```

The main lesson is that a distributed system can look partially healthy while one small configuration mistake breaks an important part of the application.
