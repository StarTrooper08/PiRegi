import pulumi
import pulumi_docker as docker
import os

# Absolute path to the nginx config directory
nginx_conf_path = os.path.abspath("./nginx/conf.d")

# Docker network for shared communication
network = docker.Network("registry-network")

# Private Docker registry container
registry = docker.Container(
    "registry",
    image=docker.RemoteImage("registry-image", name="registry:2"),
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=network.name)],
    ports=[docker.ContainerPortArgs(internal=5000, external=5000)],
    restart="always"
)

# Portainer container
portainer = docker.Container(
    "portainer",
    image=docker.RemoteImage("portainer-image", name="portainer/portainer-ce:latest"),
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=network.name)],
    mounts=[
        docker.ContainerMountArgs(
            source="/var/run/docker.sock",
            target="/var/run/docker.sock",
            type="bind"
        )
    ],
    ports=[docker.ContainerPortArgs(internal=9000, external=9000)],
    restart="always"
)

# NGINX reverse proxy container
nginx = docker.Container(
    "nginx",
    image=docker.RemoteImage("nginx-image", name="nginx:alpine"),
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=network.name)],
    ports=[docker.ContainerPortArgs(internal=80, external=80)],
    mounts=[
        docker.ContainerMountArgs(
            source=nginx_conf_path,
            target="/etc/nginx/conf.d",
            type="bind"
        )
    ],
    restart="always"
)

# Export URLs
pulumi.export("registry_url", pulumi.Output.secret("http://<raspberry_pi_ip>:80/v2/"))
pulumi.export("portainer_url", pulumi.Output.secret("http://<raspberry_pi_ip>:80/portainer/"))

