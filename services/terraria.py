import os, time

from docker.types import Mount
from services import Service


class Terraria(Service):
    IMAGE_NAME = "beardedio/terraria"
    CONTAINER_NAME = "terraria"
    PORTS = {7777: 7777}
    HOME_FOLDER = "/Users/guillaumeriou/terraria/config"
    ENVIRONMENT = {"world": "Nid_stoique_des_moutons.wld"}
    MOUNTS = [Mount(target="/config", source=HOME_FOLDER, type="bind")]
    COMMAND_MESSAGE = "say {message}"
    COMMAND_EXIT = "exit"
    SERVER_READY_OUTPUT = "Server started\\r\\n"

    def send_message(self, message):
        self.socket_send(self.COMMAND_MESSAGE, {"message": message})

    def wait_started(self):
        if not self.is_running():
            return False

        timeout = time.time() + 30
        while True:
            if self.SERVER_READY_OUTPUT in str(self.container.logs(stream=False)):
                return True

            if time.time() > timeout:
                return False
