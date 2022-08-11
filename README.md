# Prometheus Docker Dynamic Service Targets
## Prometheus | Blackbox Exporter | Docker Swarm dynamic services

This is a base PoC that automates Docker Swarm service discovery for Prometheus using file service discovery with a Blackbox Exporter that runs on a schedule and interacts with the target file (volume mapped to the host)

This python script was written to get service names for specific docker swarm services and send it to BlackBox exporter using file service discovery in the Prometheus and check e.g tcp connectivity in apps.
In this README I'll show you how to automatically add new apps (New Docker swarm services) to the Prometheus for BlacBox Exporter, in our case for tcp connectivity checking.

## Building image
In order to build the image - please execute the following
```bash
$ git clone https://github.com/graypit/Prometheus-Docker-Swarm-Dynamic-Services.git
$ cd Prometheus-Docker-Swarm-Dynamic-Services/
$ docker build -t <your_container_registry>/prometheus-docker-dynamic-svc-targets:dev .
$ docker push <your_container_registry>/prometheus-docker-dynamic-svc-targets:dev .
```

## Create swarm service (stack) & integrate with Prometheus
Create new directory with the `.env` and `docker-compose.yml` file. 
Add the following variables to the `.env` file:
```bash
# to set REG_URI for dev environment
REG_URI=<your_container_registry>
# to set the image tag
DST_VER=dev
```
### Add the following service into `docker-compose.yml` file:
```yaml
  dynamic-svc-targets:
    image: ${REG_URI}/prometheus-docker-dynamic-svc-targets:${DST_VER}
    networks:
      - default # as blackbox-exporter container
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "1"
    deploy:
      mode: global
      restart_policy:
        condition: on-failure
      placement:
        constraints:
          - node.role == manager # deploy replicas only on manager
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /etc/prometheus/gen_targets.yml:/app/gen_targets.yml # Map Prometheus target file into the container
    #command: python app.py -s backend-app -p 50051
    command:
      - '-s backend-app' # Service(apps) name prefix
      - '-p 80' # Apps port to check
```
As you see in the above commands,we can easily set `-s <services_name_prefix>` and `-p <port_number>` whatever we want to check

### Add the following service into prometheus service's `volume` section into `docker-compose.yml` file:
```
      - /etc/prometheus/gen_targets.yml:/app/gen_targets.yml:ro
```
### Prepare the mounted targets file:
```bash
$ mkdir /etc/prometheus 2>/dev/null ; touch /etc/prometheus/gen_targets.yml
```
### Start the Docker Swarm Stack:
```bash
$ env $(cat .env | grep ^[A-Z] | xargs) docker stack deploy --with-registry-auth --compose-file docker-compose.yml dynamic-svc-targets
```
## Prometheus Configuration
### Add the job configs for Blackbox Exporter into Prometheus config file `prometheus/conf/prometheus.yml`:
```yaml
# Check nlu apps status
  - job_name: 'blackbox-dynamic-services'
    scrape_interval: 5s
    metrics_path: /probe
    params:
      module: [http_2xx]  # Look for a HTTP 200 response.
    file_sd_configs:
    - files:
      - '/etc/prometheus/gen_targets.yml'
      refresh_interval: 1m
    relabel_configs:
        - source_labels: [__address__]
          regex: ([^,]*),(.*)
          replacement: $1
          target_label: __param_module
        - source_labels: [__address__]
          regex: ([^,]*),(.*)
          replacement: $2
          target_label: __param_target
        - source_labels: [__param_module]
          target_label: probe
        - source_labels: [__param_target]
          target_label: instance
        - target_label: __address__
          replacement: blackbox-exporter:8770  # The blackbox exporter's real hostname:port.
```
- Reload the Prometheus

### Check the logs:
```bash
[azureuser@test-dev-manager-vmss-000001 ~]$ docker service logs dynamic-svc-targets_dynamic-svc-targets -f
monitoring_dynamic-svc-targets.0.7ilv3nplbimp@test-dev-manager-vmss-000001    | Prometheus Docker Dynamic Targets gathering has been started...
monitoring_dynamic-svc-targets.0.7ilv3nplbimp@test-dev-manager-vmss-000001    | Service name: backend-app
monitoring_dynamic-svc-targets.0.7ilv3nplbimp@test-dev-manager-vmss-000001    | Service port: 80
monitoring_dynamic-svc-targets.0.7ilv3nplbimp@test-dev-manager-vmss-000001    | 10/08/2022 15:20:49 Targets file has been successfully updated for nlu-app services
```
