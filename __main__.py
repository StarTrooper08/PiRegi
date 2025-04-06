import os
import subprocess
import pulumi
import pulumi_docker as docker
import pulumi_esc as esc

# === Setup Variables ===
registry_port = 5000
proxy_port = 5001
portainer_port = 9000

nginx_conf_path = os.path.abspath("nginx/nginx.conf")
htpasswd_path = os.path.abspath("nginx/htpasswd")
portainer_data_path = os.path.abspath("portainer_data")
os.makedirs(portainer_data_path, exist_ok=True)

# === Load Secrets from Pulumi ESC ===
env = esc.Environments("local")  # ESC env name (must exist)
username = env.require_secret("dockerRegistryUser")
password = env.require_secret("dockerRegistryPass")

# === Generate htpasswd file dynamically ===
def generate_htpasswd(user, passwd):
    def create(args):
        u, p = args
        with open(htpasswd_path, "w") as f:
            subprocess.run(["htpasswd", "-Bbn", u, p], stdout=f, check=True)
        return True
    return pulumi.Output.all(user, passwd).apply(create)

generate_htpasswd(username, password)

# === Create Private Docker Registry ===
registry = docker.Container("registry",
    image="registry:2",
    ports=[docker.ContainerPortArgs(
        internal=5000,
        external=registry_port,
        host_ip="127.0.0.1"
    )],
    name="registry",
    restart="always"
)

# === Deploy Nginx Proxy with Basic Auth ===
nginx = docker.Container("nginx-proxy",
    image="nginx:latest",
    ports=[docker.ContainerPortArgs(
        internal=80,
        external=proxy_port,
    )],
    volumes=[
        docker.ContainerVolumeArgs(
            container_path="/etc/nginx/nginx.conf",
            host_path=nginx_conf_path,
            read_only=True
        ),
        docker.ContainerVolumeArgs(
            container_path="/etc/nginx/htpasswd",
            host_path=htpasswd_path,
            read_only=True
        )
    ],
    name="nginx-proxy",
    restart="always",
    links=[registry.name]
)

# === Deploy Portainer (Docker UI) ===
portainer = docker.Container("portainer",
    image="portainer/portainer-ce:latest",
    ports=[docker.ContainerPortArgs(
        internal=9000,
        external=portainer_port,
    )],
    volumes=[
        docker.ContainerVolumeArgs(
            container_path="/data",
            host_path=portainer_data_path
        ),
        docker.ContainerVolumeArgs(
            container_path="/var/run/docker.sock",
            host_path="/var/run/docker.sock"
        )
    ],
    name="portainer",
    restart="always"
)

