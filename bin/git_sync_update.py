#!/usr/bin/env python3
"""
Script to keep a copy of some external repositories localy.
"""
import sys
import os
from pprint import pformat
import shutil
import subprocess
from shlex import shlex
from datetime import datetime

from github import Github
# from dulwich.repo import Repo

# repo_amx is in KB
repo_max = 120000
repo_max = 50000
my_key = []
my_repos = []

for line in subprocess.check_output("find . -type d \( -name 'unrelated' -o -name 'vanished' \) -prune -o -type d -name '.git' -print | sed -e 's/\/.git//' -e 's/^.\///'", shell=True).splitlines():
    # print(line)
    my_key.append(line)

# print("-----")
# print(my_key)

my_base = 'github.com'
my_base_gist = 'gist.github.com'

pwd = os.path.dirname(os.path.realpath(__file__))
# one line per organisation without subscribing
orga_file = open(os.path.join(pwd, 'organisations.txt'), 'r')
organisations = orga_file.readlines()
orga_file.close()

token_file = open(os.path.join(pwd, 'github_token.txt'), 'r')
token = token_file.readlines()[0]
token_file.close()

g = Github(token)

# print(g)
''' empty
for follower in g.get_user().get_followers():
    print(follower)
'''

for o in organisations:
    o = o.strip()

    org = g.get_organization(o)
    print(org)

    for repo in org.get_repos():
        basepath = os.path.join(my_base, repo.full_name)
        if basepath in my_key:
            print("skipping my repo " + repo.full_name)
            continue
        print("my_repo " + repo.full_name)
        if repo.size > repo_max:
            continue
        my_repos.append({
            'name': repo.name,
            'full_name': repo.full_name,
            'clone_url': repo.clone_url,
            'git_url': repo.git_url,
            'size': repo.size,
            'path': basepath
        })
        my_key.append(basepath)


for gist in g.get_user().get_starred_gists():
    '''
    print(gist)
    pp.pprint(gist)
    print("my_repo " + str(gist.id))
    print("my_repo " + str(gist.owner))
    print("my_repo " + str(gist.owner.id))
    print("my_repo " + str(gist.owner.name))
    print("my_repo " + str(gist.owner.login))
    print("my_repo " + str(gist.user))
    print("my_repo " + str(gist.git_pull_url))
    '''

    basepath = os.path.join(my_base_gist, gist.owner.login, gist.id)
    if basepath in my_key:
        print("skipping gist repo " + gist.owner.login + ' ' + gist.id)
        continue
    my_repos.append({
                        'name': gist.id,
                        'full_name': gist.owner.login,
                        'clone_url': gist.git_pull_url,
                        'git_url': gist.git_pull_url,
                        'size': repo.size,
                        'path': basepath
                    })
    my_key.append(basepath)

for follow in g.get_user().get_following():
    print("Following: %s:%s:%s" % (follow, follow.login, follow.name))
    # TODO, get user repository and bulk subscribe
    for repo in follow.get_repos('all'):
        basepath = os.path.join(my_base, repo.full_name)
        if basepath in my_key:
            print("skipping folow repo " + repo.full_name)
            continue
        print("follow repo " + repo.full_name)
        if repo.size > repo_max:
            continue
        my_repos.append({
            'name': repo.name,
            'full_name': repo.full_name,
            'clone_url': repo.clone_url,
            'git_url': repo.git_url,
            'size': repo.size,
            'path': basepath
        })
        my_key.append(basepath)

'''
for org in g.get_user().get_orgs():
    print(org)
'''

for repo in g.get_user().get_repos():
    basepath = os.path.join(my_base, repo.full_name)
    if basepath in my_key:
        print("skipping my repo " + repo.full_name)
        continue
    print("my_repo " + repo.full_name)
    my_repos.append({
        'name': repo.name,
        'full_name': repo.full_name,
        'clone_url': repo.clone_url,
        'git_url': repo.git_url,
        'size': repo.size,
        'path': basepath
    })
    my_key.append(basepath)

for star in g.get_user().get_starred():
    basepath = os.path.join(my_base, star.full_name)
    if basepath in my_key:
        print("skipping star repo " + star.full_name)
        continue
    print("Star repo " + star.full_name)
    my_repos.append({
        'name': star.name,
        'full_name': star.full_name,
        'clone_url': star.clone_url,
        'git_url': star.git_url,
        'size': repo.size,
        'path': basepath
    })
    my_key.append(basepath)

for watch in g.get_user().get_watched():
    basepath = os.path.join(my_base, watch.full_name)
    if basepath in my_key:
        print("skipping watch repo " + watch.full_name)
        continue
    print("watch repo " + watch.full_name)
    my_repos.append({
        'name': watch.name,
        'full_name': watch.full_name,
        'clone_url': watch.clone_url,
        'git_url': watch.git_url,
        'size': repo.size,
        'path': basepath
    })
    my_key.append(basepath)

# print(my_repos)
# print(my_key)

# sys.exit(1)

print("clone")
for repo in my_repos:

    print("---")
    print(repo)
    # The interresting stuff now, we take a Git image.
    basepath = repo['path']
    if not os.path.isdir(basepath):
        print("error: Folder do not exist %s" % str(basepath))
        os.makedirs(basepath)

    gitbasepath = os.path.join(basepath, '.git')
    if not os.path.isdir(gitbasepath):
        print("error: Folder do not exist %s" % str(gitbasepath))
        try:
            # repo = Repo(basepath).clone(repo['clone_url'])
            os.system("git clone %s %s" % (repo['clone_url'], basepath))
        except Exception as e:
            print("Git repo clone failed:%s:%s" % (basepath, str(e)))

dt_date = datetime.now()
print ("The Current date is:" ,dt_date)
print("In specified format:", dt_date.strftime('_%Y_%m_%d'))
extra_date = dt_date.strftime('_%Y_%m_%d')

print("pull")
for repo in my_key:

    print("---")
    print(pformat(repo))

    try:
        repo = repo.decode()
    except (UnicodeDecodeError, AttributeError):
        pass
    git_out = ''
    try:
        git_out = subprocess.check_output("git pull || true", shell=True, stderr=subprocess.STDOUT, cwd=repo, timeout=60)
    except subprocess.TimeoutExpired as exc:
        print("Command timed out: {}".format(exc))
        git_out = "Command timed out: {}".format(exc)
    except Exception as e:
        print("Git repo pull failed:%s:%s" % (repo, str(e)))
        if git_out == '':
            git_out = "Git repo pull failed:%s:%s" % (repo, str(e))
        else:
            git_out = str(git_out) + "Git repo pull failed:%s:%s" % (repo, str(e))

    if isinstance(git_out, str):
        d_git_out = git_out
    else:
        d_git_out = git_out.decode()
    print("d_git_out: " + str(d_git_out))

    if d_git_out == 'Already up to date.\n':
        print('OK, next one')
        continue

    if 'fatal: refusing to merge unrelated histories' in d_git_out \
        or 'hint: Pulling without specifying how to reconcile divergent branches is' in d_git_out \
        or 'error: Your local changes to the following files would be overwritten by merge' in d_git_out:

        print('got some known unrelated errors.')
        # print(d_git_out)
        try:
            git_clone = subprocess.check_output("git config --get remote.origin.url || true", shell=True, stderr=subprocess.STDOUT, cwd=repo, timeout=60)
        except Exception as e:
            print("Git repo clone remote url failed:%s:%s" % (repo, str(e)))
        print(git_clone)
        d_git_clone = git_clone.decode()
        print(d_git_clone)
        print(repo)
        new_path = os.path.join('unrelated', repo + extra_date)
        print("from: " + str(repo) + " to " + str(new_path))
        if not os.path.isdir(new_path):
            shutil.move(repo, new_path)
        if os.path.isdir(repo):
            print("error: Folder exist, moved have failed %s" % str(repo))
        else:
            basepath = os.path.dirname(repo)
            print("info: Folder basepath exist %s" % str(basepath))
            try:
                git_clone = subprocess.check_output("git clone %s %s || true" % (d_git_clone, repo), shell=True, stderr=subprocess.STDOUT, cwd=basepath)
            except Exception as e:
                print("Git repo clone failed:%s:%s:%s" % (repo, basepath, str(e)))
                sys.exit(1)
            print(git_clone)

        # sys.exit(1)
        continue

    if 'Command timed out' in d_git_out and 'timed out after 60 seconds' in d_git_out:
        print('got some known timeout errors.')
        print(d_git_out)
        new_path = os.path.join('vanished', repo + extra_date)
        print("from: " + str(repo) + " to " + str(new_path))
        if not os.path.isdir(new_path):
            shutil.move(repo, new_path)
        if os.path.isdir(repo):
            print("error: Folder exist, moved have failed %s" % str(repo))
        # sys.exit(1)
        continue

    # print(git_out)

# error: Your local changes to the following files would be overwritten by merge
# fatal: unable to auto-detect email address (got \'smthing@somewhere.(none)\')\n'
