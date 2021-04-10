import pytest

from services.terraria import Terraria

@pytest.fixture
def terraria():
  return Terraria()

def test_it_should_be_running_and_stopped(terraria):
  assert terraria.start() == True
  assert terraria.is_running() == True
  terraria.wait_started()
  assert terraria.stop() == True
  assert terraria.is_running() == False

def test_it_should_not_be_stopped_when_not_running(terraria):
  assert(terraria.stop()) == False
  assert(terraria.is_running()) == False

def test_it_should_not_be_started_when_already_running(terraria):
  terraria.start()
  assert terraria.start() == False
  assert terraria.is_running() == True
  terraria.wait_started()
  terraria.stop(wait=False)