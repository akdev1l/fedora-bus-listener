import importlib.resources
import logging
import os

import boto3
import jinja2
from fedora_messaging import api, config

log = logging.getLogger(__name__)

KMODS = ["nvidia"]

ARCHES = {
    "x86_64": {
        "instance_type": "t3.micro",
        "ami_id": os.environ.get("AMI_X86_64", ""),
    },
    "aarch64": {
        "instance_type": "t4g.micro",
        "ami_id": os.environ.get("AMI_AARCH64", ""),
    },
}

REPO_BUCKET_NAME = os.environ.get("REPO_BUCKET_NAME", "")
GPG_SECRET_NAME = os.environ.get("GPG_SECRET_NAME", "")


def load_userdata(kmod_name: str) -> str:
    raw = (
        importlib.resources.files("fedora_bus_listener")
        .joinpath("kmod-builder-userdata.sh.j2")
        .read_text()
    )
    return jinja2.Template(raw).render(
        kmod_name=kmod_name,
        repo_bucket_name=REPO_BUCKET_NAME,
        gpg_secret_name=GPG_SECRET_NAME,
    )


def launch_instance(kmod_name: str, fedora_release: str, arch: str) -> None:
    arch_config = ARCHES[arch]
    ec2 = boto3.client("ec2")

    ami_id = arch_config["ami_id"]
    userdata = load_userdata(kmod_name)

    response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType=arch_config["instance_type"],
        MinCount=1,
        MaxCount=1,
        UserData=userdata,
        InstanceInitiatedShutdownBehavior="terminate",
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": f"akmod-{kmod_name}-f{fedora_release}-{arch}"},
                    {"Key": "kmod_name", "Value": kmod_name},
                    {"Key": "fedora_release", "Value": fedora_release},
                    {"Key": "arch", "Value": arch},
                ],
            }
        ],
    )
    instance_id = response["Instances"][0]["InstanceId"]
    log.info("Launched %s for kmod=%s fedora=%s arch=%s", instance_id, kmod_name, fedora_release, arch)


def is_kernel_update(message) -> bool:
    if "bodhi.update.complete.stable" not in message.topic:
        return False
    builds = message.body.get("update", {}).get("builds", [])
    return any(b.get("nvr", "").startswith("kernel-") for b in builds)


def callback(message) -> None:
    if not is_kernel_update(message):
        return

    release = message.body["update"]["release"]["version"]
    log.info("Kernel stable update detected for Fedora %s, triggering builds", release)

    for kmod in KMODS:
        for arch in ARCHES:
            try:
                launch_instance(kmod_name=kmod, fedora_release=release, arch=arch)
            except Exception as e:
                log.error("Failed to launch instance for kmod=%s arch=%s: %s", kmod, arch, e)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config.conf.setup_logging()

    for arch, cfg in ARCHES.items():
        if not cfg["ami_id"]:
            raise RuntimeError(f"AMI_{arch.upper()} env var is not set")
    if not REPO_BUCKET_NAME:
        raise RuntimeError("REPO_BUCKET_NAME env var is not set")
    if not GPG_SECRET_NAME:
        raise RuntimeError("GPG_SECRET_NAME env var is not set")

    bindings = [
        {
            "exchange": "amq.topic",
            "routing_keys": ["org.fedoraproject.prod.bodhi.update.complete.stable"],
        }
    ]
    log.info("Listening for kernel updates on the Fedora message bus...")
    api.consume(callback, bindings=bindings)


if __name__ == "__main__":
    main()
