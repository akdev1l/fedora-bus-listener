FROM fedora:44

RUN dnf install -y \
        rpkg \
        pyproject-rpm-macros \
        python3-devel && \
    dnf clean all

WORKDIR /build
COPY . .

RUN git init && \
    git config user.email "build@localhost" && \
    git config user.name "build" && \
    git add . && \
    git commit -m "build"

RUN rpkg local

CMD ["cp", "-r", "noarch", "/output"]
