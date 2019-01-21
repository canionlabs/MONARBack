from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate
from model_mommy import mommy

from apps.common.utils._tests import BaseTest, UserModel, \
    AccessToken, Application

import datetime
import pytest
import random
import uuid


BASE_QUANTITY = 4


@pytest.fixture(scope='class')
def oauth_user(request):
    user = UserModel.objects.create_user(
        username=request.instance.random_string(),
        email=request.instance.random_email(),
        password=request.instance.random_string()
    )

    non_user = UserModel.objects.create_user(
        username=request.instance.random_string(),
        email=request.instance.random_email(),
        password=request.instance.random_string()
    )

    application = Application(
            name=request.instance.random_string(),
            user=user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
    )
    application.save()

    valid_user_token = AccessToken.objects.create(
        user=user, token=uuid.uuid4().hex,
        application=application,
        expires=timezone.now() + datetime.timedelta(days=1),
        scope="read write dolphin"
    )

    valid_non_user_token = AccessToken.objects.create(
        user=non_user, token=uuid.uuid4().hex,
        application=application,
        expires=timezone.now() + datetime.timedelta(days=1),
        scope="read write dolphin"
    )

    request.cls.user = user
    request.cls.user_header = f"Bearer {valid_user_token.token}"

    request.cls.non_user = non_user
    request.cls.non_user_header = f"Bearer {valid_non_user_token.token}"


@pytest.mark.usefixtures('oauth_user')
class ProjectViewSetTests(APITestCase, BaseTest):

    NO_REQUIRED_FIELDS = ['project_id', 'script']

    def setUp(self):
        self.organization = mommy.make(
            'auth_management.Organization', make_m2m=True
        )

        self.organization.users.add(self.user)
        self.projects = mommy.make(
            'projects.Project', organization=self.organization,
            _quantity=BASE_QUANTITY
        )

    def tearDown(self):
        self.organization.delete()

    def test_list_projects(self):
        """
        GET user 'projects:project-list'
        """
        url = reverse('projects:project-list')
        response = self.client.get(url, HTTP_AUTHORIZATION=self.user_header)
        content = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert len(content) == BASE_QUANTITY

    def test_list_projects_without_organization(self):
        """
        GET non_user 'projects:project-list'
        """
        url = reverse('projects:project-list')
        response = self.client.get(
            url, HTTP_AUTHORIZATION=self.non_user_header
        )
        content = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert len(content) == 0

    def test_detail_projects(self):
        """
        GET user 'projects:project-detail'
        """
        for project in self.projects:
            url = reverse(
                'projects:project-detail',
                kwargs={'pk': project.project_id},
            )
            response = self.client.get(
                url, HTTP_AUTHORIZATION=self.user_header
            )
            assert response.status_code == status.HTTP_200_OK

            content = response.json()
            for key, value in content.items():
                assert hasattr(project, key)

                db_value = getattr(project, key)
                assert db_value == value or str(db_value) == value

    def test_detail_projects_without_organization(self):
        """
        GET non_user 'projects:project-detail'
        """
        for project in self.projects:
            url = reverse(
                'projects:project-detail',
                kwargs={'pk': project.project_id}
            )
            response = self.client.get(
                url, HTTP_AUTHORIZATION=self.non_user_header
            )
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_project(self):
        """
        POST user 'projects:project-list'
        """
        to_send = {
                'name': self.random_string(),
                'organization_id': self.organization.organization_id
        }

        url = reverse('projects:project-list')
        response = self.client.post(
            url,
            data=to_send,
            HTTP_AUTHORIZATION=self.user_header
        )
        assert response.status_code == status.HTTP_201_CREATED

        content = response.json()
        for key, value in content.items():
            if key in to_send.keys():
                assert value == to_send[key] or value == str(to_send[key])
            else:
                assert key in self.NO_REQUIRED_FIELDS

    def test_create_project_without_organization(self):
        """
        POST non_user 'projects:project-list'
        """
        to_send = {
                'name': self.random_string(),
                'organization_id': self.organization.organization_id
        }

        url = reverse('projects:project-list')
        response = self.client.post(
            url,
            data={
                'name': self.random_string(),
                'organization_id': self.organization.organization_id
            },
            HTTP_AUTHORIZATION=self.non_user_header
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_project(self):
        """
        DELETE user 'projects:detail'
        """
        project = random.choice(self.projects)
        url = reverse(
            'projects:project-detail',
            kwargs={'pk': project.project_id}
        )
        response = self.client.delete(
            url, HTTP_AUTHORIZATION=self.user_header
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_without_organization(self):
        """
        DELETE non_user 'projects:project-detail'
        """
        project = random.choice(self.projects)
        url = reverse(
            'projects:project-detail',
            kwargs={'pk': project.project_id}
        )
        response = self.client.delete(
            url, HTTP_AUTHORIZATION=self.non_user_header
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_put_project(self):
        """
        PUT user 'projects:project-detail'
        """
        to_send = {
                'name': self.random_string(),
                'organization_id': self.organization.organization_id
        }
        project = random.choice(self.projects)
        url = reverse(
            'projects:project-detail',
            kwargs={'pk': project.project_id}
        )
        response = self.client.put(
            url, data=to_send, HTTP_AUTHORIZATION=self.user_header
        )
        assert response.status_code == status.HTTP_200_OK

        content = response.json()
        for key, value in content.items():
            if key in to_send.keys():
                assert value == to_send[key] or value == str(to_send[key])
            else:
                assert key in self.NO_REQUIRED_FIELDS

    def test_put_project_without_organization(self):
        """
        PUT non_user 'projects:project-detail'
        """
        to_send = {
                'name': self.random_string(),
                'organization_id': self.organization.organization_id
        }
        project = random.choice(self.projects)
        url = reverse(
            'projects:project-detail',
            kwargs={'pk': project.project_id}
        )
        response = self.client.put(
            url, data=to_send, HTTP_AUTHORIZATION=self.non_user_header
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_project(self):
        """
        PATCH user 'projects:project-detail'
        """
        to_send = {'name': self.random_string()}
        project = random.choice(self.projects)
        url = reverse(
            'projects:project-detail',
            kwargs={'pk': project.project_id}
        )
        response = self.client.patch(
            url, data=to_send, HTTP_AUTHORIZATION=self.user_header
        )
        assert response.status_code == status.HTTP_200_OK

        content = response.json()
        for t_key, t_value in to_send.items():
            assert content[t_key] == t_value
