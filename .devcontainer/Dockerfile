# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.155.1/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version: 3, 3.9, 3.8, 3.7, 3.6
FROM ubuntu:18.04

RUN apt update && apt install -y python python-pip build-essential git

RUN groupadd --gid 2000 vscode && useradd --uid 2000 --gid 2000 -m vscode

RUN pip install "pylint<2.0.0"