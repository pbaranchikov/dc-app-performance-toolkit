import random

from selenium.webdriver.common.by import By

from selenium_ui.base_page import BasePage
from selenium_ui.conftest import print_timing
from selenium_ui.bitbucket.pages.pages import LoginPage, GetStarted, PopupManager, PullRequest, RepoPullRequests, RepositoryBranches, Repository, RepoNavigationPanel
from util.conf import BITBUCKET_SETTINGS


def app_specific_action(webdriver, datasets):
    page = BasePage(webdriver)
    rnd_repo = random.choice(datasets["repos"])

    project_key = rnd_repo[1]
    repo_slug = rnd_repo[0]

    repository_page = Repository(webdriver,
                                 project_key=datasets['project_key'],
                                 repo_slug=datasets['repo_slug'])
    repo_pull_requests_page = RepoPullRequests(webdriver, repo_slug=repository_page.repo_slug,
                                               project_key=repository_page.project_key)
    repository_branches_page = RepositoryBranches(webdriver, repo_slug=repository_page.repo_slug,
                                                  project_key=repository_page.project_key)
    navigation_panel = RepoNavigationPanel(webdriver)
    PopupManager(webdriver).dismiss_default_popup()

    # Turn on merge check
    page.go_to_url(f"{BITBUCKET_SETTINGS.server_url}/projects/{project_key}/settings/merge-checks")
    page.wait_until_visible((By.CSS_SELECTOR, 'table.hooks-table-pre-pull_request_merge tr:nth-child(2) aui-toggle')).click()
    page.execute_js('document.querySelector("table.hooks-table-pre-pull_request_merge tr:nth-child(2) aui-toggle").click()')
    page.wait_until_clickable((By.CSS_SELECTOR, '#hook-config-dialog .aui-button')).click()

    @print_timing("selenium_app_custom_action")
    def measure():

        @print_timing("selenium_create_pull_request:create_pull_request")
        def sub_measure():
            branch_from = datasets['pull_request_branch_from']
            branch_to = datasets['pull_request_branch_to']
            repository_branches_page.open_base_branch(base_branch_name=branch_from)
            fork_branch_from = repository_branches_page.create_branch_fork_rnd_name(base_branch_name=branch_from)
            navigation_panel.wait_for_navigation_panel()
            repository_branches_page.open_base_branch(base_branch_name=branch_to)
            fork_branch_to = repository_branches_page.create_branch_fork_rnd_name(base_branch_name=branch_to)
            datasets['pull_request_fork_branch_to'] = fork_branch_to
            navigation_panel.wait_for_navigation_panel()
            repo_pull_requests_page.create_new_pull_request(from_branch=fork_branch_from, to_branch=fork_branch_to)
            PopupManager(webdriver).dismiss_default_popup()
        sub_measure()

        @print_timing("selenium_app_custom_action:try-merge-pull-request")
        def sub_measure():
            PopupManager(webdriver).dismiss_default_popup()
            pull_request_page = PullRequest(webdriver)
            pull_request_page.wait_for_overview_tab()
            PopupManager(webdriver).dismiss_default_popup()

            pull_request_page.wait_merge_button_clickable()
        sub_measure()
        repository_branches_page.go_to()
        repository_branches_page.wait_for_page_loaded()
        repository_branches_page.delete_branch(branch_name=datasets['pull_request_fork_branch_to'])
    measure()

    #Turn off merge check
    page.go_to_url(f"{BITBUCKET_SETTINGS.server_url}/projects/{project_key}/settings/merge-checks")
    page.wait_until_visible((By.CSS_SELECTOR, 'table.hooks-table-pre-pull_request_merge tr:nth-child(2) aui-toggle')).click()
