from django.contrib.auth.models import User

from germanium.test_cases.auth import UserProxy


class HelperTestCase:

    user_index = 1
    issue_index = 1

    def get_pk(self, resp):
        return self.deserialize(resp).get('id')

    def get_user_data(self, prefix=''):
        result = {
            'username': '%suser_%s' % (prefix, self.user_index),
            'email': '%suser_%s@test.cz' % (prefix, self.user_index),
            'password': 'super secret password'
        }
        self.user_index += 1
        return result

    def get_issue_data(self, prefix='', exclude=None):
        exclude = exclude or []
        result = {
            'name': 'Issue %s' % self.issue_index,
            'created_by': self.get_user_data(prefix),
            'leader': self.get_user_data(prefix)
        }
        self.issue_index += 1
        for field in exclude:
            del result[field]
        return result

    def get_user_obj(self, is_superuser=False):
        user_data = self.get_user_data()
        return User.objects._create_user(user_data.get('username'), user_data.get('email'),
                                         user_data.get('password'), is_staff=False, is_superuser=is_superuser)


class AsSuperuserTestCase:

    def get_user(self, is_superuser, is_staff=True):
        username = 'user'
        password = 'super secret password'
        email = 'user@test.cz'
        return UserProxy(username, password,
                         User.objects._create_user(username, email, password, is_staff=is_staff,
                                                   is_superuser=is_superuser))
