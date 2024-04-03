# Generated by CodiumAI
import os
import sys
import unittest
from unittest import mock
from unittest.mock import Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.data import (
    get_project,
    get_projects,
    get_service,
    upsert_env,
    upsert_project,
    write_db,
    write_projects,
)
from lib.models import Env, Ingress, Project, Service
from lib.test_stubs import test_db, test_projects


class TestData(unittest.TestCase):

    @mock.patch("lib.data.get_db", return_value=test_db.copy())
    @mock.patch(
        "lib.data.yaml",
        return_value={"dump": mock.Mock()},
    )
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    def test_write_db(self, mock_open: Mock, mock_yaml: Mock, _: Mock) -> None:

        # Call the function under test
        write_db({"projects": test_db["projects"]})

        mock_open.assert_called_once_with("db.yml", "w", encoding="utf-8")

        # Assert that the mock functions were called correctly
        mock_yaml.dump.assert_called_once_with(
            {
                "versions": {"traefik": "v2.11", "crowdsec": "v1.6.0"},
                "plugins": test_db["plugins"],
                "projects": test_db["projects"],
            },
            mock_open(),
        )

    @mock.patch("lib.data.write_db")
    def test_write_projects(self, mock_write_db: Mock) -> None:

        # Call the function under test
        write_projects(test_projects)

        # Assert that the mock functions were called correctly
        mock_write_db.assert_called_once_with({"projects": test_db["projects"]})

    # Get projects with filter
    @mock.patch(
        "lib.data.get_db",
        return_value=test_db.copy(),
    )
    def test_get_projects_with_filter(self, _: Mock) -> None:

        # Call the function under test
        result = get_projects(lambda p, s: p.name == "whoami" and s.ingress)

        # Assert the result
        expected_result = [
            Project(
                description="whoami service",
                name="whoami",
                services=[
                    Service(image="traefik/whoami:latest", ingress=[Ingress(domain="whoami.example.com")], host="web"),
                ],
            ),
        ]
        self.assertEqual(result, expected_result)

    # Get all projects with no filter
    @mock.patch(
        "lib.data.get_db",
        return_value=test_db.copy(),
    )
    def test_get_projects_no_filter(self, mock_get_db: Mock) -> None:
        self.maxDiff = None

        # Call the function under test
        result = get_projects()

        # Assert that the mock functions were called correctly
        mock_get_db.assert_called_once()

        # Assert the result
        self.assertEqual(result, test_projects)

    # Get a project by name that does not exist
    @mock.patch(
        "lib.data.get_projects",
        return_value=test_projects.copy(),
    )
    def test_get_nonexistent_project_by_name(self, _: Mock) -> None:

        # Call the function under test
        with self.assertRaises(ValueError):
            get_project("nonexistent_project")

    # Get a service by name that does not exist
    @mock.patch(
        "lib.data.get_project",
        return_value=test_projects.copy()[0],
    )
    def test_get_nonexistent_service_by_name(self, _: Mock) -> None:

        # Call the function under test
        with self.assertRaises(ValueError):
            get_service("project1", "nonexistent_service")

    # Upsert a project that does not exist (Fixed)
    @mock.patch("lib.data.get_projects", return_value=test_projects.copy())
    @mock.patch("lib.data.write_projects")
    def test_upsert_nonexistent_project_fixed(self, mock_write_projects: Mock, mock_get_projects: Mock) -> None:

        new_project = Project(name="new_project", domain="new_domain")
        # Call the function under test
        upsert_project(new_project)

        # Assert that the mock functions were called correctly
        mock_get_projects.assert_called_once()
        mock_write_projects.assert_called_once_with(test_projects + [new_project])

    # Upsert a project's service' env
    @mock.patch("lib.data.get_project", return_value=test_projects[5].model_copy())
    @mock.patch("lib.data.get_service", return_value=test_projects[5].services[0].model_copy())
    @mock.patch("lib.data.upsert_service")
    def test_upsert_env(self, mock_upsert_service: Mock, mock_get_service: Mock, mock_get_project: Mock) -> None:

        extra_env = Env(**{"OKI": "doki"})
        # Call the function under test
        upsert_env(project="whoami", service="web", env=extra_env)

        # Assert that the mock functions were called correctly
        mock_get_project.assert_called_once()
        mock_get_service.assert_called_once()
        mock_upsert_service.assert_called_once_with(
            "whoami",
            Service(
                env=extra_env,
                image="traefik/whoami:latest",
                ingress=[Ingress(domain="whoami.example.com")],
                host="web",
            ),
        )


if __name__ == "__main__":
    unittest.main()
