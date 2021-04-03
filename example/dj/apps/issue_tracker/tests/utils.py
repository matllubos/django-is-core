from django.contrib.auth.models import User
from django.test import RequestFactory

from germanium.test_cases.default import GermaniumTestCase
from germanium.tools import assert_equal, assert_raises, assert_is_none

from is_core.utils import (
    get_field_label_from_path, get_field_from_model_or_none, get_field_widget_from_path,
    get_readonly_field_value_from_path
)
from is_core.forms.utils import ReadonlyValue
from is_core.utils.field_api import (
    GetFieldDescriptorException, get_field_value_from_path, GetFieldDescriptorValueError,
    get_field_descriptors_from_path
)
from is_core.forms.widgets import (
    ReadonlyWidget, ManyToManyReadonlyWidget, ModelObjectReadonlyWidget, ModelMultipleReadonlyWidget,
    ModelChoiceReadonlyWidget
)

from issue_tracker.cores.views import UserDetailView
from issue_tracker.models import Issue

from .factories import IssueFactory, UserFactory


__all__ =(
    'UtilsTestCase',
)


class UtilsTestCase(GermaniumTestCase):

    def set_up(self):
        self.factory = RequestFactory()

    def test_get_field_label_from_path_should_return_right_descriptors(self):
        issue_name_descriptors = get_field_descriptors_from_path(Issue, 'name')
        assert_equal(len(issue_name_descriptors), 1)
        assert_equal(issue_name_descriptors[0].field_name, 'name')

        issue_solver_watching_issues_count_descriptors = get_field_descriptors_from_path(
            Issue, 'solver__watching_issues_count'
        )
        assert_equal(len(issue_solver_watching_issues_count_descriptors), 2)
        assert_equal(issue_solver_watching_issues_count_descriptors[0].field_name, 'solver')
        assert_equal(issue_solver_watching_issues_count_descriptors[1].field_name, 'watching_issues_count')

    def test_get_field_label_from_path_should_return_right_field_label(self):
        assert_equal(get_field_label_from_path(Issue, 'name'), 'Name')
        assert_equal(get_field_label_from_path(Issue, 'name', field_labels={'name': 'another name'}), 'another name')
        assert_equal(get_field_label_from_path(User, 'created_issues_count'), 'created issues count')
        assert_equal(get_field_label_from_path(Issue, '_obj_name'), 'object name')
        assert_equal(get_field_label_from_path(Issue, 'solver___obj_name'), 'Solver')
        assert_equal(
            get_field_label_from_path(Issue, 'solver___obj_name', field_labels={'solver': None}), 'object name'
        )
        assert_equal(
            get_field_label_from_path(Issue, 'solver___obj_name', field_labels={'solver__': None}), 'object name'
        )
        assert_equal(
            get_field_label_from_path(Issue, 'solver', field_labels={'solver': None}), ''
        )
        assert_equal(
            get_field_label_from_path(Issue, 'solver__watching_issues_count'), 'Solver - watching count'
        )
        assert_equal(
            get_field_label_from_path(User, 'leading_issue_name', view=UserDetailView()), 'leading issue name'
        )

    def test_get_field_label_from_path_should_raise_exception_for_invalid_field_name(self):
        with assert_raises(GetFieldDescriptorException):
            get_field_label_from_path(Issue, 'invalid')

        with assert_raises(GetFieldDescriptorException):
            get_field_label_from_path(Issue, 'solver__invalid')

    def test_get_field_from_model_or_none_should_return_model_field(self):
        assert_equal(get_field_from_model_or_none(Issue, 'name'), Issue._meta.get_field('name'))
        assert_equal(get_field_from_model_or_none(Issue, 'solver'), Issue._meta.get_field('solver'))

    def test_get_field_from_model_or_none_should_return_none_for_missing_field(self):
        assert_is_none(get_field_from_model_or_none(Issue, 'invalid'))

    def test_get_field_widget_from_path_should_return_right_wiget(self):
        assert_equal(get_field_widget_from_path(Issue, 'name'), ReadonlyWidget)
        assert_equal(get_field_widget_from_path(User, 'created_issues'), ManyToManyReadonlyWidget)
        assert_equal(get_field_widget_from_path(Issue, 'watched_by'), ModelMultipleReadonlyWidget)
        assert_equal(get_field_widget_from_path(Issue, 'solver'), ModelChoiceReadonlyWidget)
        assert_equal(get_field_widget_from_path(User, 'solving_issue'), ModelObjectReadonlyWidget)
        assert_equal(get_field_widget_from_path(User, 'solving_issue__name'), ReadonlyWidget)
        assert_equal(get_field_widget_from_path(Issue, 'related_object'), ReadonlyWidget)

    def test_get_field_widget_from_path_should_raise_exception_for_invalid_field_name(self):
        with assert_raises(GetFieldDescriptorException):
            get_field_widget_from_path(Issue, 'invalid')

    def test_get_field_value_from_path_should_return_right_value_from_model_instance(self):
        solver = UserFactory()
        leader = UserFactory()
        issue = IssueFactory(solver=solver, leader=leader, created_by=leader)
        issue.watched_by.add(solver, leader)
        assert_equal(get_field_value_from_path(issue, 'name'), issue.name)
        assert_equal(get_field_value_from_path(issue, 'is_issue'), True)
        assert_equal(
            get_field_value_from_path(issue, 'watched_by_string'), ', '.join([str(u) for u in (solver, leader)])
        )
        assert_equal(get_field_value_from_path(issue, 'created_by__first_name'), leader.first_name)
        assert_equal(
            get_field_value_from_path(issue, 'watched_by_method__first_name'), [solver.first_name, leader.first_name]
        )

    def test_get_field_value_from_path_should_return_right_value_from_resource_method(self):
        solver = UserFactory()
        leader = UserFactory()
        issue = IssueFactory(solver=solver, leader=leader, created_by=leader)
        issue.watched_by.add(solver, leader)
        request = self.factory.get('')
        with assert_raises(GetFieldDescriptorValueError):
            get_field_value_from_path(issue, 'solver__watching_issues_count')
        assert_equal(get_field_value_from_path(issue, 'solver__watching_issues_count', request=request), 1)

    def test_get_field_value_from_path_should_return_right_value_from_core_method(self):
        solver = UserFactory()
        leader = UserFactory()
        issue = IssueFactory(solver=solver, leader=leader, created_by=leader)
        issue.watched_by.add(solver, leader)
        request = self.factory.get('')
        with assert_raises(GetFieldDescriptorValueError):
            get_field_value_from_path(issue, 'leader__created_issues_count')
        assert_equal(get_field_value_from_path(issue, 'leader__created_issues_count', request=request), 1)

    def test_get_field_value_from_path_should_return_right_value_from_view_method(self):
        assert_equal(
            get_field_value_from_path(UserFactory(), 'leading_issue_name', view=UserDetailView()), 'No leading issue'
        )

    def test_get_field_value_from_path_should_raise_exception_invalid_field_name(self):
        with assert_raises(GetFieldDescriptorException):
            get_field_label_from_path(Issue, 'invalid')

    def test_get_readonly_field_value_from_path_should_return_right_value_from_model_instance(self):
        solver = UserFactory()
        leader = UserFactory()
        issue = IssueFactory(solver=solver, leader=leader, created_by=leader, related_object=solver)
        issue.watched_by.add(solver, leader)
        assert_equal(get_readonly_field_value_from_path(issue, 'name'), issue.name, None)
        assert_equal(get_readonly_field_value_from_path(issue, 'is_issue'), True)
        assert_equal(
            get_readonly_field_value_from_path(issue, 'watched_by_string'),
            ', '.join([str(u) for u in (solver, leader)])
        )
        assert_equal(get_readonly_field_value_from_path(issue, 'created_by__first_name'), leader.first_name)
        assert_equal(
            list(
                get_readonly_field_value_from_path(
                    issue, 'watched_by_method__first_name'
                )
            ),
            [solver.first_name, leader.first_name]
        )
        assert_equal(get_readonly_field_value_from_path(issue, 'related_object'), solver, None)
