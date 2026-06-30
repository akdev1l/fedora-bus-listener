FROM fedora:44

RUN dnf install -y \
        rpkg \
        python3-jinja2 \
        python3-boto3 \
        python3-fedora-messaging \
        systemd-rpm-macros \
        pyproject-rpm-macros \
        python3-devel && \
    dnf clean all

WORKDIR /build
COPY .git .git
COPY . .

RUN git tag -l && rpkg local --outdir /output
