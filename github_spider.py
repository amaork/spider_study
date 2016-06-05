# -*- coding: utf-8 -*-

import re
import requests


class GithubUserSpider(object):

    URL_DB = {

        "home": "https://github.com/username",

        "starred": "https://github.com/stars/username",
        "starred_next": "https://github.com/stars/username?direction=desc&"
                        "page=page_number&sort=created&_pjax=%23js-pjax-container",

        "followers": "https://github.com/username/followers",
        "following": "https://github.com/username/following",
        "repositories": "https://github.com/username?tab=repositories",
    }

    RE_PATTEN_DB = {

        "fork_repo": 'class="repo-list-item public fork"(.*?)</poll-include-fragment>',
        "source_repo": 'class="repo-list-item public source"(.*?)</poll-include-fragment>',
        "starred_repo": 'class="repo-list-name">(.*?)</a>',

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

        "starred": 'href="/stars/.*?(.*?)Starred',
        "followers": 'href="/.*?/followers"(.*?)Followers',
        "following": 'href="/.*?/following"(.*?)Following',
        "counter": 'class="vcard-stat-count d-block">(.*?)</strong>',
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

    def __get_page(self, url, params=None):
        try:

            if not params:
                page = requests.get(url, params)
            else:
                page = requests.get(url)

            return page.text

        except requests.RequestException, e:

            print "Get user:{0:s}, {1:s} info error:{2:s}".format(self.__username, url, e)
            return None

    def get_page(self, key, params=None):
        """Get user specified information

        :param key: such as repositories, stars, followers etc
        :param params: get passing parameters
        :return: success return information page text error return ""
        """

        if key not in self.URL_DB:
            return None

        base = self.URL_DB.get(key)
        if not isinstance(base, str):
            return None

        return self.__get_page(base.replace("username", self.__username), params)

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

    def __get_repo_detail(self, repo):
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
            repositories.append(self.__get_repo_detail(repo))

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
        info["location"] = self.get_info(self.get_info(home, "user_location"), '</svg>(.*)')
        info["join_date"] = self.get_info(self.get_info(home, "user_join_date"), '<local-time.*?>(.*?)</local-time>')
        info["starred"] = self.get_info(self.get_info(home, "starred"), "counter")
        info["followers"] = self.get_info(self.get_info(home, "followers"), "counter")
        info["following"] = self.get_info(self.get_info(home, "following"), "counter")
        return info

    def __get_starred_next_page(self, page_number):
        data = {

            "direction": "desc",
            "page": str(page_number),
            "sort": "created",
            "_pjax": "#js-pjax-container",
        }

        url = self.URL_DB.get("starred_next")
        if not isinstance(url, str):
            return None

        url = url.replace("username", self.__username)
        url = url.replace("page_number", str(page_number))
        return self.get_page("starred") if page_number == 1 else self.__get_page(url, data)

    def get_starred_repo(self):
        counter = 0
        page_number = 1
        starred_repo = list()
        total = self.get_user_info().get("starred")
        pattern = self.get_re_patten("starred_repo")

        if not total:
            return []

        while counter < int(total):
            page = self.__get_starred_next_page(page_number)
            if not page:
                return starred_repo

            for repo in re.findall(pattern, page, re.S):
                name = self.get_info(repo, 'href="(.*?)">')
                starred_repo.append(name)

            page_number += 1
            counter = len(starred_repo)

        return starred_repo


spider = GithubUserSpider("amaork")
# for repo in spider.get_source_repo() + spider.get_fork_repo():
#      print repo
print len(spider.get_starred_repo())
