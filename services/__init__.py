import docker
import os
import time

from lib.task_status import TaskStatus

RUNNING = "running"


class Service:
    IMAGE_NAME = "repository/image"
    CONTAINER_NAME = "container"
    PORTS = {"tcp/7777"}
    HOME_FOLDER = ""
    ENVIRONMENT = {}
    MOUNTS = [{}]
    COMMAND_EXIT = ""

    @property
    def container(self):
        try:
            container = self._docker.containers.get(self.CONTAINER_NAME)
        except docker.errors.NotFound:
            container = None
        return container

    def __init__(self):
        self._docker = docker.from_env()
        self._os = os

    def start(self, restart=False):
        if self.is_running() and not restart:
            return False
        if self._container_exist():
            self.container.remove(force=True)
        try:
            self._docker.containers.run(
                self.IMAGE_NAME,
                detach=True,
                name=self.CONTAINER_NAME,
                restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
                ports=self.PORTS,
                environment=self.ENVIRONMENT,
                mounts=self.MOUNTS,
            )
        except Exception as e:
            return False
        return True

    def stop(self, countdown=True, restart=False, wait=True):
        if not self.is_running():
            return False
        self.socket_send(self.COMMAND_EXIT)
        if wait and self.wait_stopped():
            self.container.remove(force=True)
            return True
        elif not wait:
            return True
        else:
          return False

    def restart(self):
        self.stop(True)
        self.start(True)

    def status(self):
        pass

    def update(self):
        try:
            image = self._docker.images.get(self.IMAGE_NAME)
        except docker.errors.ImageNotFound:
            return False

        current_version = self._version(image)

        try:
            image = self._docker.images.pull(IMAGE_NAME, tag="latest")
        except Exception:
            return False

        new_version = self._version(image)

        return current_version != new_version

    def wait_stopped(self):
        timeout = time.time() + 45
        while True:
            if self.is_running():
                time.sleep(0.5)
            else:
                return True
            if time.time() > timeout:
                return False

    def backup(self, filename):
        pass

    def upload(self):
        pass

    def wait_started(self):
      pass

    def is_running(self):
        container = self.container
        if container is None:
            return False
        state = container.attrs["State"]
        return state["Status"] == RUNNING

    def _version(self, image):
        return image.history()[0].get("Created")

    def _container_exist(self):
        return self.container != None

    def socket_send(self, command, **kwargs):
        socket = self._docker.containers.get(self.CONTAINER_NAME).attach_socket(
            params={"stdin": 1, "stream": 1}
        )
        socket._sock.send(command.format(kwargs).encode("UTF8"))
        socket.close()
