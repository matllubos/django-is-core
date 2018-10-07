import factory
from factory import fuzzy

from django.contrib.auth.models import User

from issue_tracker import models


class UserFactory(factory.django.DjangoModelFactory):

    username = factory.Sequence(lambda n: 'john.doe{0}'.format(n))
    first_name = factory.Sequence(lambda n: 'John{0}'.format(n))
    last_name = factory.Sequence(lambda n: 'Doe{0}'.format(n))
    email = factory.Sequence(lambda n: 'joh_doe_{0}@example.com'.format(n).lower())

    class Meta:
        model = User


class IssueFactory(factory.django.DjangoModelFactory):

    name = factory.fuzzy.FuzzyText(length=100)
    created_by = factory.SubFactory('issue_tracker.tests.factories.UserFactory')
    leader = factory.SubFactory('issue_tracker.tests.factories.UserFactory')

    class Meta:
        model = models.Issue