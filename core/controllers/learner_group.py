# Copyright 2022 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Controllers for the learner groups."""

from __future__ import annotations

from core import feconf
from core.constants import constants
from core.controllers import acl_decorators
from core.controllers import base
from core.domain import config_domain
from core.domain import learner_group_fetchers
from core.domain import learner_group_services
from core.domain import story_fetchers
from core.domain import subtopic_page_services
from core.domain import user_services


LEARNER_GROUP_SCHEMA = {
    'group_title': {
        'schema': {
            'type': 'basestring'
        },
        'default_value': None
    },
    'group_description': {
        'schema': {
            'type': 'basestring',
        },
        'default_value': None
    },
    'student_usernames': {
        'schema': {
            'type': 'list',
            'items': {
                'type': 'basestring',
                'validators': [{
                    'id': 'has_length_at_most',
                    'max_value': constants.MAX_USERNAME_LENGTH
                }]
            }
        },
        'default_value': []
    },
    'invited_student_usernames': {
        'schema': {
            'type': 'list',
            'items': {
                'type': 'basestring',
                'validators': [{
                    'id': 'has_length_at_most',
                    'max_value': constants.MAX_USERNAME_LENGTH
                }]
            }
        },
        'default_value': []
    },
    'subtopic_page_ids': {
        'schema': {
            'type': 'list',
            'items': {
                'type': 'basestring'
            }
        },
        'default_value': []
    },
    'story_ids': {
        'schema': {
            'type': 'list',
            'items': {
                'type': 'basestring'
            }
        },
        'default_value': []
    }
}


class CreateLearnerGroupHandler(base.BaseHandler):
    """Handles creation of a new learner group."""

    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'POST': LEARNER_GROUP_SCHEMA
    }

    @acl_decorators.can_access_learner_groups
    def post(self):
        """Creates a new learner group."""

        title = self.normalized_payload.get('group_title')
        description = self.normalized_payload.get('group_description')
        invited_student_usernames = self.normalized_payload.get(
            'invited_student_usernames')
        subtopic_page_ids = self.normalized_payload.get('subtopic_page_ids')
        story_ids = self.normalized_payload.get('story_ids')

        invited_student_ids = user_services.get_multi_user_ids_from_usernames(
            invited_student_usernames)

        new_learner_grp_id = learner_group_fetchers.get_new_learner_group_id()

        learner_group = learner_group_services.create_learner_group(
            new_learner_grp_id, title, description, [self.user_id],
            invited_student_ids, subtopic_page_ids, story_ids
        )

        self.render_json({
            'id': learner_group.group_id,
            'title': learner_group.title,
            'description': learner_group.description,
            'facilitator_usernames': user_services.get_usernames(
                learner_group.facilitator_user_ids),
            'student_usernames': user_services.get_usernames(
                learner_group.student_user_ids),
            'invited_student_usernames': user_services.get_usernames(
                learner_group.invited_student_user_ids),
            'subtopic_page_ids': learner_group.subtopic_page_ids,
            'story_ids': learner_group.story_ids
        })


class LearnerGroupHandler(base.BaseHandler):
    """Handles operations related to the learner groups."""

    URL_PATH_ARGS_SCHEMAS = {
        'learner_group_id': {
            'schema': {
                'type': 'basestring',
                'validators': [{
                    'id': 'is_regex_matched',
                    'regex_pattern': constants.LEARNER_GROUP_ID_REGEX
                }]
            },
            'default_value': None
        }
    }

    HANDLER_ARGS_SCHEMAS = {
        'PUT': LEARNER_GROUP_SCHEMA,
        'DELETE': {}
    }

    @acl_decorators.can_access_learner_groups
    def put(self, learner_group_id):
        """Updates an existing learner group."""

        title = self.normalized_payload.get('group_title')
        description = self.normalized_payload.get('group_description')
        student_usernames = self.normalized_payload.get('student_usernames')
        invited_student_usernames = self.normalized_payload.get(
            'invited_student_usernames')
        subtopic_page_ids = self.normalized_payload.get('subtopic_page_ids')
        story_ids = self.normalized_payload.get('story_ids')

        # Check if user is the facilitator of the learner group, as only
        # facilitators have the right to update a learner group.
        is_valid_request = learner_group_services.is_user_facilitator(
            self.user_id, learner_group_id
        )
        if not is_valid_request:
            raise self.UnauthorizedUserException(
                'You are not a facilitator of this learner group.')

        student_ids = user_services.get_multi_user_ids_from_usernames(
            student_usernames
        )
        invited_student_ids = user_services.get_multi_user_ids_from_usernames(
            invited_student_usernames
        )

        learner_group = learner_group_services.update_learner_group(
            learner_group_id, title, description, [self.user_id],
            student_ids, invited_student_ids, subtopic_page_ids, story_ids
        )

        self.render_json({
            'id': learner_group.group_id,
            'title': learner_group.title,
            'description': learner_group.description,
            'facilitator_usernames': user_services.get_usernames(
                learner_group.facilitator_user_ids),
            'student_usernames': user_services.get_usernames(
                learner_group.student_user_ids),
            'invited_student_usernames': user_services.get_usernames(
                learner_group.invited_student_user_ids),
            'subtopic_page_ids': learner_group.subtopic_page_ids,
            'story_ids': learner_group.story_ids
        })

    @acl_decorators.can_access_learner_groups
    def delete(self, learner_group_id):
        """Deletes a learner group."""

        is_valid_request = learner_group_services.is_user_facilitator(
            self.user_id, learner_group_id
        )
        if not is_valid_request:
            raise self.UnauthorizedUserException(
                'You do not have the rights to delete this learner group '
                'as you are not its facilitator.')

        learner_group_services.remove_learner_group(learner_group_id)

        self.render_json({
            'success': True
        })


class LearnerGroupStudentProgressHandler(base.BaseHandler):
    """Handles operations related to the learner group student's progress."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    URL_PATH_ARGS_SCHEMAS = {
        'learner_group_id': {
            'schema': {
                'type': 'basestring',
                'validators': [{
                    'id': 'is_regex_matched',
                    'regex_pattern': constants.LEARNER_GROUP_ID_REGEX
                }]
            },
            'default_value': None
        }
    }

    HANDLER_ARGS_SCHEMAS = {
        'GET': {
            'student_usernames': {
                'schema': {
                    'type': 'custom',
                    'obj_type': 'JsonEncodedInString'
                }
            }
        }
    }

    @acl_decorators.can_access_learner_groups
    def get(self, learner_group_id):
        """Handles GET requests for users progress through learner
        group syllabus.
        """

        student_usernames = self.normalized_request.get('student_usernames')
        student_user_ids = user_services.get_multi_user_ids_from_usernames(
            student_usernames)

        learner_group = learner_group_fetchers.get_learner_group_by_id(
            learner_group_id)
        if learner_group is None:
            raise self.InvalidInputException('No such learner group exists.')

        progress_sharing_permissions = (
            learner_group_fetchers.can_multi_students_share_progress(
                student_user_ids, learner_group_id
            )
        )
        students_with_progress_sharing_on = []
        for i, user_id in enumerate(student_user_ids):
            if progress_sharing_permissions[i]:
                students_with_progress_sharing_on.append(user_id)

        story_ids = learner_group.story_ids
        stories_progresses = (
            story_fetchers.get_multi_users_progress_in_stories(
                students_with_progress_sharing_on, story_ids
            )
        )
        subtopic_page_ids = learner_group.subtopic_page_ids
        subtopic_pages_progresses = (
            subtopic_page_services.get_multi_users_subtopic_pages_progress(
                students_with_progress_sharing_on, subtopic_page_ids
            )
        )

        all_students_progress = []
        for i, user_id in enumerate(student_user_ids):
            student_progress = {
                'username': student_usernames[i],
                'progress_sharing_is_turned_on':
                    progress_sharing_permissions[i],
                'stories_progress': [],
                'subtopic_pages_progress': []
            }

            # If progress sharing is turned off, then we don't need to
            # show the progress of the student.
            if not progress_sharing_permissions[i]:
                all_students_progress.append(student_progress)
                continue

            student_progress['stories_progress'] = stories_progresses[user_id]
            student_progress['subtopic_pages_progress'] = (
                subtopic_pages_progresses[user_id]
            )
            all_students_progress.append(student_progress)

        self.render_json({
            'students_progress': all_students_progress
        })


class LearnerGroupSearchSyllabusHandler(base.BaseHandler):
    """Handles operations related to the learner group syllabus."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    URL_PATH_ARGS_SCHEMAS = {}

    HANDLER_ARGS_SCHEMAS = {
        'GET': {
            'learner_group_id': {
                'schema': {
                    'type': 'basestring',
                },
                'default_value': ''
            },
            'search_keyword': {
                'schema': {
                    'type': 'basestring',
                },
                'default_value': ''
            },
            'search_type': {
                'schema': {
                    'type': 'basestring',
                },
                'default_value': constants.DEFAULT_ADD_SYLLABUS_FILTER
            },
            'search_category': {
                'schema': {
                    'type': 'basestring',
                },
                'default_value': constants.DEFAULT_ADD_SYLLABUS_FILTER
            },
            'search_language_code': {
                'schema': {
                    'type': 'basestring',
                },
                'default_value': constants.DEFAULT_ADD_SYLLABUS_FILTER
            }
        }
    }

    @acl_decorators.can_access_learner_groups
    def get(self):
        """Handles GET requests for learner group syllabus views."""

        search_keyword = self.normalized_request.get('search_keyword')
        search_type = self.normalized_request.get('search_type')
        search_category = self.normalized_request.get('search_category')
        search_language_code = self.normalized_request.get(
            'search_language_code')
        learner_group_id = self.normalized_request.get('learner_group_id')

        matching_syllabus = (
            learner_group_services.get_matching_learner_group_syllabus_to_add(
                learner_group_id, search_keyword,
                search_type, search_category, search_language_code
            )
        )

        self.render_json({
            'learner_group_id': learner_group_id,
            'story_summary_dicts': matching_syllabus['story_summary_dicts'],
            'subtopic_summary_dicts':
                matching_syllabus['subtopic_summary_dicts']
        })


class FacilitatorDashboardHandler(base.BaseHandler):
    """Handles operations related to the facilitator dashboard."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {}
    }

    @acl_decorators.can_access_learner_groups
    def get(self):
        """Handles GET requests for the facilitator dashboard."""

        learner_groups = (
            learner_group_fetchers.get_learner_groups_of_facilitator(
                self.user_id)
        )

        learner_groups_data = []
        for learner_group in learner_groups:
            learner_groups_data.append({
                'id': learner_group.group_id,
                'title': learner_group.title,
                'description': learner_group.description,
                'facilitator_usernames': user_services.get_usernames(
                    self.user_id),
                'students_count': len(learner_group.student_user_ids)
            })

        self.render_json({
            'learner_groups_list': learner_groups_data
        })


class FacilitatorLearnerGroupViewHandler(base.BaseHandler):
    """Handles operations related to the facilitators view of learner group."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    URL_PATH_ARGS_SCHEMAS = {
        'learner_group_id': {
            'schema': {
                'type': 'basestring',
                'validators': [{
                    'id': 'is_regex_matched',
                    'regex_pattern': constants.LEARNER_GROUP_ID_REGEX
                }]
            },
            'default_value': None
        }
    }
    HANDLER_ARGS_SCHEMAS = {
        'GET': {}
    }

    @acl_decorators.can_access_learner_groups
    def get(self, learner_group_id):
        """Handles GET requests for facilitator's view of learner group."""

        is_valid_request = learner_group_services.is_user_facilitator(
            self.user_id, learner_group_id)
        if not is_valid_request:
            raise self.UnauthorizedUserException(
                'You are not a facilitator of this learner group.')

        learner_group = learner_group_fetchers.get_learner_group_by_id(
            learner_group_id)

        self.render_json({
            'id': learner_group.group_id,
            'title': learner_group.title,
            'description': learner_group.description,
            'facilitator_usernames': user_services.get_usernames(
                learner_group.facilitator_user_ids),
            'student_usernames': user_services.get_usernames(
                learner_group.student_user_ids),
            'invited_student_usernames': user_services.get_usernames(
                learner_group.invited_student_user_ids),
            'subtopic_page_ids': learner_group.subtopic_page_ids,
            'story_ids': learner_group.story_ids
        })


class FacilitatorDashboardPage(base.BaseHandler):
    """Page showing the teacher dashboard."""

    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {}
    }

    @acl_decorators.can_access_learner_groups
    def get(self):
        """Handles GET requests."""
        if not config_domain.LEARNER_GROUPS_ARE_ENABLED.value:
            raise self.PageNotFoundException

        self.render_template('facilitator-dashboard-page.mainpage.html')


class CreateLearnerGroupPage(base.BaseHandler):
    """Page for creating a new learner group."""

    URL_PATH_ARGS_SCHEMAS = {}
    HANDLER_ARGS_SCHEMAS = {
        'GET': {}
    }

    @acl_decorators.can_access_learner_groups
    def get(self):
        """Handles GET requests."""
        if not config_domain.LEARNER_GROUPS_ARE_ENABLED.value:
            raise self.PageNotFoundException

        self.render_template('create-learner-group-page.mainpage.html')


class LearnerGroupSearchStudentHandler(base.BaseHandler):
    """Handles searching of students to invite in learner group."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    URL_PATH_ARGS_SCHEMAS = {}

    HANDLER_ARGS_SCHEMAS = {
        'GET': {
            'learner_group_id': {
                'schema': {
                    'type': 'basestring',
                },
                'default_value': ''
            },
            'username': {
                'schema': {
                    'type': 'basestring',
                },
                'default_value': ''
            }
        }
    }

    @acl_decorators.can_access_learner_groups
    def get(self):
        """Handles GET requests."""

        username: str = self.normalized_request.get('username')
        learner_group_id: str = self.normalized_request.get('learner_group_id')

        user_settings = user_services.get_user_settings_from_username(username)

        if user_settings is None:
            self.render_json({
                'username': username,
                'profile_picture_data_url': '',
                'error': ('User with username %s does not exist.' % username)
            })
            return

        if self.username.lower() == username.lower():
            self.render_json({
                'username': user_settings.username,
                'profile_picture_data_url': '',
                'error': 'You cannot invite yourself to the group'
            })
            return

        (valid_invitation, error) = learner_group_services.can_user_be_invited(
            user_settings.user_id, user_settings.username, learner_group_id
        )

        if not valid_invitation:
            self.render_json({
                'username': user_settings.username,
                'profile_picture_data_url': '',
                'error': error
            })
            return

        self.render_json({
            'username': user_settings.username,
            'profile_picture_data_url': user_settings.profile_picture_data_url,
            'error': ''
        })
