# -*- coding: utf-8 -*-

import re
import requests


class GithubUserSpider(object):

    URL_DB = {

        "home": "https://github.com/username",
        "stars": "https://github.com/stars/username",
        "followers": "https://github.com/username/followers",
        "following": "https://github.com/username/following",
        "repositories": "https://github.com/username?tab=repositories",
    }

    RE_PATTEN_DB = {

        "fork_repo": 'class="repo-list-item public fork"(.*?)</poll-include-fragment>',
        "source_repo": 'class="repo-list-item public source"(.*?)</poll-include-fragment>',

        "repo_name": 'itemprop="name codeRepository">(.*?)</a>',
        "repo_desc": 'itemprop="description">(.*?)</p>',
        "repo_lang": 'itemprop="programmingLanguage">(.*?)</span>',

        "repo_forks": 'aria-label="Forks">(.*?)</a>',
        "repo_stars": 'aria-label="Stargazers">(.*?)</a>',
        "repo_updated": 'class="repo-list-meta">(.*?)</relative-time>',

        "user_organization": 'aria-label="Organization"(.*?)</li>',
        "user_location": 'aria-label="Home location"(.*?)</li>',
        "user_email": 'aria-label="Email"(.*?)</li>',
        "user_blog": 'aria-label="Blog or website"(.*?)</li>',
        "user_join_date": 'aria-label="Member since"(.*?)</li>',
    }

    def __init__(self, username):
        assert isinstance(username, str), "username TypeError:{0:s}".format(type(username))

        self.__username = username

    def get_re_patten(self, info):
        """Get specified user info re patten

        :param info: want knows infomaction
        :return: return re patten
        """

        if info not in self.RE_PATTEN_DB:
            return None

        return self.RE_PATTEN_DB.get(info)

    def get_page(self, info):
        """Get user specified information

        :param info: such as repositories, stars, followers etc
        :return: success return information page text error return ""
        """

        if info not in self.URL_DB:
            return None

        base = self.URL_DB.get(info)
        if not isinstance(base, str):
            return None

        url = base.replace("username", self.__username)

        try:

            page = requests.get(url)
            return page.text

        except requests.RequestException, e:

            print "Get user:{0:s}, {1:s} info error:{2:s}".format(self.__username, info, e)
            return None

    def get_info(self, text, key):
        try:

            if key in self.RE_PATTEN_DB:
                value = re.search(self.get_re_patten(key), text, re.S)
            else:
                value = re.search(key, text, re.S)

            if value is None:
                return ""

            return value.group(1).strip()

        except re.error, e:

            print "Get info:{0:s} error:{1:s}".format(key, e)
            return ""

    def get_repo_detail(self, repo):
        if not isinstance(repo, unicode):
            return None

        detail = dict()
        detail["name"] = self.get_info(repo, "repo_name")
        detail["desc"] = self.get_info(repo, "repo_desc")
        detail["forks"] = self.get_info(self.get_info(repo, "repo_forks"), '</svg>(.*)')
        detail["stars"] = self.get_info(self.get_info(repo, "repo_stars"), '</svg>(.*)')
        detail["update"] = self.get_info(self.get_info(repo, "repo_updated"), '>(.*)')
        detail["language"] = self.get_info(repo, "repo_lang")

        return detail

    def __get_repository_list(self, key):
        page = self.get_page("repositories")
        pattern = self.get_re_patten(key)

        if page is None or pattern is None:
            return []

        repo_list = re.findall(pattern, page, re.S)

        repositories = list()
        for repo in repo_list:
            repositories.append(self.get_repo_detail(repo))

        return repositories

    def get_fork_repo(self):
        return self.__get_repository_list("fork_repo")

    def get_source_repo(self):
        return self.__get_repository_list("source_repo")

    def get_user_info(self):
        info = dict()
        home = self.get_page("home")

        if home is None:
            return info

        info["blog"] = self.get_info(self.get_info(home, "user_blog"), 'class="url" rel="nofollow me">(.*?)</a>')
        info["email"] = self.get_info(self.get_info(home, "user_email"), '>([^@]+@[^@]+.[^@])</a>')
        info["organization"] = self.get_info(self.get_info(home, "user_organization"), '<div>(.*?)</div>')
        info["localtion"] = self.get_info(self.get_info(home, "user_location"), '</svg>(.*)')
        info["join_date"] = self.get_info(self.get_info(home, "user_join_date"), '<local-time.*?>(.*?)</local-time>')
        return info


spider = GithubUserSpider("amaork")
# for repo in spider.get_source_repo() + spider.get_fork_repo():
#     print repo
print spider.get_user_info()
