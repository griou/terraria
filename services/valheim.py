import os

class Valheim(Service):
  IMAGE_NAME = 'beardedio/terraria'
  CONTAINER_NAME = 'terraria'
  PORTS = {"tcp/7777": 7777}
  HOME_FOLDER = '$HOME/terraria/config'
  ENVIRONMENT = {"world": "Nid_stoique_des_moutons.wld"}
  VOLUMES = {HOME_FOLDER: {'bind': '/config', 'mode': 'rw'}}