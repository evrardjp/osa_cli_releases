#!/usr/bin/env bash
# Requires: Perl, git-review, tox, and osa-toolkit from https://github.com/evrardjp/osa_toolkit installed
# This doesn't work on fish shell anymore.
set -o errexit
set -o nounset


WORKDIR="${WORKDIR:-/tmp/releases}"
REPOS_GIT_URL="https://github.com/openstack"
OSA_FOLDER=${WORKDIR}/openstack-ansible
RELEASES_FOLDER=${WORKDIR}/releases
RELEASINGLOG=${WORKDIR}/releasing.log
RELEASECOMMITMSG=${WORKDIR}/commitmsg_releases.txt
OACOMMITMSG=${WORKDIR}/commitmsg_OA.txt

function cleanupenv {
  unset BRANCH
  unset CURRENT_RELEASE
  unset RELEASE_CHANGEID
  unset release_changeid
  unset NEXT_RELEASE
  unset next_release
}

function cleanup {
  rm -rf ${RELEASES_FOLDER}
  rm -rf ${OSA_FOLDER}
}

function clone {
  mkdir -p ${WORKDIR}
  cd $WORKDIR
  git clone ${REPOS_GIT_URL}/releases.git
  git clone ${REPOS_GIT_URL}/openstack-ansible.git
}

function new_release {
  local BRANCHNAME=$1
  cd $RELEASES_FOLDER
  tox -e venv -- new-release $BRANCHNAME openstack-ansible bugfix | tee -a ${RELEASINGLOG}
}

function ask_ready_to_review {
  local folder=$1
  local commitmsgfile=$2
  echo "Please checkout a new branch, edit the files, git add, and git commit -F ${commitmsgfile} in $folder."
  read -rp $'Are you ready to send review? (Y/n) : ' -ei $'Y' key;
  if [[ "$key" == "Y" ]]
  then
    cd $folder
    git review -f -t release_osa | tee -a ${RELEASINGLOG}
    cd -
  else
    echo "Not Ready, not sending review. Please send review manually."
    exit 1
  fi
}

function parse_release_log {
  export CURRENT_RELEASE=$(perl -n -e'/going from.*to (.*)$/ && print "$1\n"' ${RELEASINGLOG} | tail -n 1)
  echo "Release OpenStack-Ansible ${BRANCH}/${CURRENT_RELEASE}" > ${RELEASECOMMITMSG}
}

function parse_gitreview_log {
  export RELEASE_CHANGEID=$(perl -n -e '/remote.*(https.*review.openstack.org\/\d+)/ && print "$1\n"' ${RELEASINGLOG} | tail -n 1)
  echo "Found git review url: $RELEASE_CHANGEID"
}

function write_commit_msg {
  cat > ${OACOMMITMSG} << EOCOMMIT
Bump version to ${next_release:-'next release'}

Depends-On: ${RELEASE_CHANGEID}
EOCOMMIT
}

function rollback_time {
  cd $1
  git checkout -- . || true
  git reset HEAD^ --hard || true
  git pull
}

function release_branch {
  cleanupenv
  export BRANCH=$1

  #################
  # Releases repo #
  #################

  rollback_time ${WORKDIR}/releases # In case something was wrongly done on master, come back in time.
  git checkout -b release_osa       # Create a new branch for doing the release
  new_release $BRANCH               # Uses's releases' tox tool to produce a release.
  parse_release_log                 # Get current's code version by parsing "next release" element from releases repo
  ask_ready_to_review ${WORKDIR}/releases ${RELEASECOMMITMSG} # Wait for user editions and confirmations before git review -f
  parse_gitreview_log               # Get review change id for the depends on.
#  If you already did the releases folder part, just comment out the
#  above section, and export the release change details for the
#  depends on, like this:
#  export RELEASE_CHANGEID="https://review.openstack.org/#/c/584787/"
  rollback_time ${WORKDIR}/releases # In case something was wrongly done on master, come back in time.

  ##########################
  # OpenStack-Ansible repo #
  ##########################

  # Cleanup the repo. Making sure it looks like a fresh git cloned repo.
  cd $OSA_FOLDER
  git remote rm gerrit || true
  git checkout origin/master
  git branch -D stable/$BRANCH || true

  git checkout -b stable/$BRANCH -t origin/stable/$BRANCH || true # Ensure the work of OSA toolkit is done on the right branch.
  git pull                                                        # Ensure said branch is up to date.

  osa releases bump_release_number | tee -a ${RELEASINGLOG}
  export next_release=$(tail -n 1 ${RELEASINGLOG} | cut -d ' ' -f 4)
  git checkout -b release_osa
  write_commit_msg                                                # Prepare an example commit message.
  ask_ready_to_review ${WORKDIR}/openstack-ansible ${OACOMMITMSG} # Wait for user editions and confirmations before git review -f
  rollback_time ${WORKDIR}/openstack-ansible                      # In case something was wrongly done on master, come back in time
}


cleanup
clone

release_branch rocky
release_branch queens
release_branch pike
#release_branch ocata
