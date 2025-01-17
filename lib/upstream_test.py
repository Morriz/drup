import os
import sys
import unittest
from unittest import TestCase, mock
from unittest.mock import Mock, call

from lib.models import Env, Project

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.data import Service
from lib.upstream import update_upstream, update_upstreams, write_upstream


class DirEntry:
    def __init__(self, path: str):
        self.path = path

    def is_dir(self) -> bool:
        return True


_ret_tpl = """
---
version: '3.8'

networks:
  proxynet:
    name: proxynet
    external: true

services:

  test-master:
    image: morriz/hello-world:main
    networks:
      - default
      - proxynet
    restart: unless-stopped
    environment:
      TARGET: cost concerned people
      INFORMANT: http://test-informant:8080
      
    expose:
      - '8080'
    
    volumes:
      - ./data/bla:/data/bla
      - ./etc/dida:/etc/dida
      
  test-informant:
    image: morriz/hello-world:main
    networks:
      - default
      - proxynet
    restart: unless-stopped
    environment:
      TARGET: boss
      
    expose:
      - '8080'"""

_ret_projects = [
    Project(
        name="my-project",
        entrypoint="service1",
        services=[
            Service(host="service1", port=8080),
            Service(host="service2", port=8080),
        ],
    ),
    Project(
        enabled=False,
        name="another-project",
        entrypoint="service1",
        services=[
            Service(host="service1", port=8080),
        ],
    ),
]


class TestUpdateUpstream(TestCase):
    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=_ret_tpl)
    def test_write_upstream(
        self,
        mock_open: Mock,
    ) -> None:

        project = Project(
            name="test",
            services=[
                Service(
                    image="morriz/hello-world:main",
                    host="master",
                    port=8080,
                    env=Env(**{"TARGET": "cost concerned people", "INFORMANT": "http://test-informant:8080"}),
                    volumes=["./data/bla:/data/bla", "./etc/dida:/etc/dida"],
                ),
                Service(image="morriz/hello-world:main", host="informant", port=8080, env=Env(**{"TARGET": "boss"})),
            ],
        )

        # Call the function under test
        write_upstream(project)

        # Assert that the subprocess.Popen was called with the correct arguments
        mock_open.return_value.write.assert_called_once_with(_ret_tpl)

    @mock.patch("lib.upstream.rollout_service")
    @mock.patch("lib.upstream.run_command")
    @mock.patch(
        "lib.upstream.get_projects",
        return_value=[_ret_projects[0]],
    )
    @mock.patch("lib.upstream.get_project", return_value=_ret_projects[0])
    def test_update_upstream_enabled(
        self,
        _: Mock,
        _2: Mock,
        mock_run_command: Mock,
        mock_rollout_service: Mock,
    ) -> None:

        # Call the function under test
        update_upstream(
            "my-project",
            "service1",
            rollout=True,
        )

        # Assert that the subprocess.Popen was called with the correct arguments
        mock_run_command.assert_has_calls(
            [
                call(
                    ["docker", "compose", "pull"],
                    cwd="upstream/my-project",
                ),
                call(
                    ["docker", "compose", "up", "-d"],
                    cwd="upstream/my-project",
                ),
            ]
        )

        # Assert that the rollout_service function is called correctly
        # with the correct arguments
        mock_rollout_service.assert_called_once_with("my-project", "service1")

    @mock.patch("lib.upstream.rollout_service")
    @mock.patch("lib.upstream.run_command")
    @mock.patch(
        "lib.upstream.get_projects",
        return_value=[],
    )
    @mock.patch("lib.upstream.get_project", return_value=_ret_projects[1])
    def test_update_upstream_disabled(
        self,
        _: Mock,
        _2: Mock,
        mock_run_command: Mock,
        mock_rollout_service: Mock,
    ) -> None:

        # Call the function under test
        update_upstream(
            "another-project",
            "service1",
            rollout=True,
        )

        # Assert that the subprocess.Popen was called with the correct arguments
        mock_run_command.assert_has_calls(
            [
                call(
                    ["docker", "compose", "down"],
                    cwd="upstream/another-project",
                ),
            ]
        )

        # Assert that the rollout_service function is called correctly
        # with the correct arguments
        mock_rollout_service.assert_not_called()

    @mock.patch("lib.upstream.rollout_service")
    @mock.patch("lib.upstream.run_command")
    @mock.patch("lib.upstream.get_project", return_value=_ret_projects[0])
    def test_update_upstream_no_rollout(self, _: Mock, _2: Mock, mock_rollout_service: Mock) -> None:

        # Call the function under test
        update_upstream(
            "my-project",
            "my-service",
            rollout=False,
        )

        # Assert that the rollout_service function is not called
        mock_rollout_service.assert_not_called()

    @mock.patch("os.scandir")
    @mock.patch("lib.upstream.update_upstream")
    @mock.patch("lib.upstream.run_command")
    @mock.patch("lib.upstream.get_project", return_value=_ret_projects[0])
    def test_update_upstreams(self, _: Mock, _2: Mock, mock_update_upstream: Mock, mock_scandir: Mock) -> None:
        mock_scandir.return_value = [DirEntry("upstream/my-project")]

        # Call the function under test
        update_upstreams()

        mock_update_upstream.assert_called_once_with(
            "my-project",
            rollout=False,
        )


if __name__ == "__main__":
    unittest.main()
