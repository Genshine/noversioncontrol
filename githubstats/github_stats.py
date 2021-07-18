# coding: utf-8

# Copyright 2015 Donne Martin. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from collections import OrderedDict
from operator import itemgetter
import os
import pickle
import re
import time

import click
import geocoder

from githubstats.lib.github import GitHub
from githubstats.repo import Repo
from githubstats.user import User
from githubstats.user_geocoder import UserGeocoder


class GitHubStats(object):
    """Provides stats for users, orgs, and repos by stars.

    :type cached_users: dict {user_id: :class:`githubstats.user.User`}
    :param cached_users: Cached users saved to disk to avoid always having
        to call the GitHub API.  This cache should be refreshed with fresh data
        from the GitHub API regularly.

    :type CFG_USERS_PATH: str (constant)
    :param CFG_USERS_PATH: The users data directory path.

    :type CFG_SLEEP_TIME: int (constant)
    :param CFG_SLEEP_TIME: The time in seconds to sleep between generating
        stats for each language to avoid hitting the GitHub API rate limit.

    :type CFG_MAX_DESC: int (constant)
    :param CFG_MAX_DESC: The max description length before truncation.

    :type CFG_MAX_ITEMS: int (constant)
    :param CFG_MAX_ITEMS: The max number of items to display per section.

    :type CFG_MIN_STARS: int (constant)
    :param CFG_MIN_STARS: The min number of repo stars used as a cutoff to
        filter repos with GitHub search.

    :type github: :class:`githubstats.lib.GitHub`
    :param github: Provides integration with the GitHub API.

    :type languages: list
    :param languages: Programming languages tracked.

    :type overall_repos: list of :class:`githubstats.repo.Repo`
    :param overall_repos: Overall listing of repos.

    :type overall_devs: list of :class:`githubstats.user.User`
    :param overall_devs: Overall listing of devs.  Note duplicates can exist in
        this list if a dev has popular repos in different languages.

    :type overall_devs_grouped: list of :class:`githubstats.user.User`
    :param overall_devs_grouped: Overall listing of devs, grouped by language
        and sorted by stars.  Note duplicates can exist in this list if a dev
        has popular repos in different languages.

    :type overall_orgs: list of :class:`githubstats.user.User`
    :param overall_orgs: Overall listing of orgs.  Note duplicates can exist in
        this list if a dev has popular repos in different languages.

    :type overall_orgs_grouped: list of :class:`githubstats.user.User`
    :param overall_orgs_grouped: Overall listing of orgs, grouped by language
        and sorted by stars.  Note duplicates can exist in this list if a dev
        has popular repos in different languages.

    :type user_geocodes_map: dict {user_id: :class`geocoder.google.Google`}
    :param user_geocodes_map: Maps the user_id to a Google Geocode object.

    :type user_repos_map: dict
    :param user_repos_map: Maps the user_id and repos.
    """

    CFG_MAX_DESC = 50
    CFG_MAX_ITEMS = 500
    CFG_MIN_STARS = 100
    CFG_SLEEP_TIME = 5

    def __init__(self, github=None):
        self.github = github if github else GitHub()
        self.cached_users = {}
        self.overall_repos = []
        self.overall_devs = []
        self.overall_orgs = []
        self.overall_devs_grouped = []
        self.overall_orgs_grouped = []
        self.user_repos_map = {}
        self.user_geocodes_map = {}
        self.languages = 