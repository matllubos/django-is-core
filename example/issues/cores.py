from django.contrib.auth.models import User

from is_core.main import UIRestModelISCore

from .models import Issue


class IssueIsCore(UIRestModelISCore):
    model = Issue


class UserIsCore(UIRestModelISCore):
    model = User