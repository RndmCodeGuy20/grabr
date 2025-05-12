FROM mcr.microsoft.com/devcontainers/python:3.12-slim

# Install Playwright deps manually
RUN apt-get update && apt-get install -y \
    libwoff1 libopus0 libwebpdemux2 libharfbuzz-icu0 libwebpmux3 \
    libenchant-2-2 libhyphen0 libegl1 libglx0 libgudev-1.0-0 \
    libevdev2 libgles2 libx264-155 \
    && apt-get clean

# Install playwright and browsers
RUN pip install playwright && playwright install
