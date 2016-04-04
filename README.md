# CI Jenkins

barebones CI jenkins setup that provides github integrations

# Purpose

Want [TravisCI](https://travis-ci.com/)-like integrations with Github? Don't have the money or will to set it up? This [JenkinsCI](https://jenkins-ci.org/) configuration repo is your solution!

##### How this repo aims to achive this:

- provide an automatable means for creating jobs on the fly for your github repositories using [chamberlain](https://github.com/behance/chamberlain) & [jenkins-job-builder](https://github.com/openstack-infra/jenkins-job-builder)
- abstract away the setup of [github pullrequest builder plugin](https://github.com/janinko/ghprb)

##### Things that this repo requires that you must provide:
- a private SSH key that can pull your repositories
    - must reside within `$JENKINS_USER_HOME/.ssh/id_rsa`
- an admin [access token](https://developer.github.com/v3/oauth/) from github with the following scopes

    <img src="https://github.com/adobe-platform/ci-jenkins/blob/master/docs/permissions.jpg" width="50%">

Once you have both of those, just run the `provision` job. If you have user security on, provide a userid & token (in your Jenkins account user profile).

# Configuration & Environment Variables

| Var | Value | Purpose|
| ------------- | ------------- | ------------- |
| `PROVISIONER` | `true` or `""` | Whether this instance is provisioning templates or not. |
| `GITHUB_DOMAIN` | URL to github | Any URL, defaults to `github.com`. Used to clone repos in the `provision-repo` job |
| `TEMPLATE_DIR` | Defaults to `$JENKINS_HOME/templates` | Where provisioner instances cache, commit & push templates from (copied from `~/.chamberlain/workspace`) |
| `TEMPLATE_GIT_URL` | A git SSH URL | Repo that is used to cache provisioned projects. |
| `TEMPLATE_LIB_GIT_URL` | A git SSH URL | Lib repository for chamberlain templates. |
| `DEVELOPMENT` | `true` or `""` | Whether you're developing or not; switch that turns off `self-update` |
| `hostname` command (`--hostname` flag for docker) | Actual address of your jenkins server, WITH the port (no `http` or `https`) | This is SPECIFICALLY for jenkins job builder, so that the Github PullRequest Builder plugin uses the correct URL for webhooks |

# Mesos integration

Instances can be launched with Mesos integration so that jobs will be executed on a specified Mesos cluster.  You'll need to launch the Docker image tagged with `:mesos` to use the Mesos integration.  You can either launch a standalone Jenkins master node, or launch a master in your Mesos cluster via Marathon.  Sample Marathon app definitions can be found in the [mesos/marathon](mesos/marathon) directory.  The standalone Jenkins master with Mesos integration requires several environment variables:

| Var | Value | Required? | Purpose |
| ------------- | ------------- | ------------- | ------------- |
| `JENKINS_FRAMEWORK_NAME` | (e.g., `jenkins`)| Required | This is the name the Jenkins framework gets registered as in your Mesos cluster |
| `JENKINS_MESOS_MASTER` | (e.g., `zk://zk.mymesoscluster.org:2181/mesos`) | Required | This is the zookeeper URL for the Mesos cluster's ensemble |
| `JENKINS_HOST` | (e.g., the returned value of `hostname -i`) | Required | This is the IP address of the standalone Jenkins master |
| `JENKINS_PORT` | defaults to 8080 | Optional | Modify to assign an alternate port for Jenkins |

Jobs intended to be executed on Mesos should have the `<assignedNode>` value (the "Restrict where this project can be run" parameter via the web UI) set to 'mesos'.  By default, jobs executed on the Mesos cluster are run using the Docker containerizer, and the docker image itself includes [Docker-in-Docker](https://github.com/jpetazzo/dind), plus a few common language runtimes.  More details can be found in the [mesos/dind-agent](mesos/dind-agent) directory of this repo.

You can modify the configuration of the Mesos integration in the [mesos/conf/jenkins/clouds.xml](mesos/conf/jenkins/clouds.xml) file.  The `<master>` and `<jenkinsURL>` values are modified at launch time based on the environment variables passed, and will be overwritten if modified.

# Concepts

This configuration runs in one of two modes: a provisioner or reader. Which one it runs as depends on the `PROVISIONER` environment variable. You can configure that in the global settings.

#### Provisioner Instances

Instances that come up as provisioners do one thing: provision job templates & save them to `TEMPLATE_GIT_URL`. It should be expected that they only run the `provision-repo` job. This job will run `chamberlain`'s `gh-sync` command, which will create a jenkins job project with metadata pulled from github. Example of a generated project:

```
- project
    ghprauth: '{ghprauth}'
    ghurl: https://github.com/awesome/repo
    gitauth: '{gitauth}'
    jobs: ['ci-{repo}']
    name: local-awesome/repoci-{repo}
    repo: repo
    sshurl: git@github.com:awesome/repo.git
```

This is where the `TEMPLATE_LIB_GIT_URL` environment variable comes into play. Note the job template name, `ci-{repo}`. It is expected that this name references the name of an actual jenkins job builder template. So, a lib template with that name should exist in `TEMPLATE_LIB_GIT_URL`.

The project that is generated is highly opinionated to work with the github pullrequest builder plugin. So for example, you would get the most benefits from a lib template that looks something like:

```
- job-template:
    name: 'ci-{repo}'
    project-type: freestyle
    concurrent: true
    node: docker-ci
    wrappers:
        - workspace-cleanup
    properties:
        - github:
            url: '{ghurl}'
    scm:
        - git:
            url: '{sshurl}'
            credentials-id: '{gitauth}'
            skip-tag: true
    triggers:
        - github-pull-request:
            github-hooks: true
            allow-whitelist-orgs-as-admins: true
            org-list:
                - "awesome"
            trigger-phrase: "retest"
            auth-id: '{ghprauth}'
            status-context: ci-jenkins
    builders:
        - shell: make ci

```

The `gitauth` & `ghprauth` are internal IDs of secret credentials that are created via the `provision` job.

#### Reader Instances

Instances that have `PROVISONER=""` will come up as reader instances. All they do is run the `update-templates` job every minute, polling on `TEMPLATE_LIB_GIT_URL` & `TEMPLATE_GIT_URL` for changes and use jenkins-job-builder itself to provision itself. Theoretically, you don't even need a provisioner instance, you can just directly push to `TEMPLATE_GIT_URL` and this instance will automatically update itself.

These are also the instances that were designed to run the tests themselves, preferably using SSH slaves (hint: use the `node` parameter, as shown in the example template above).

# Step-By-Step Setup

##### Things to have
- a repo where you can store your job templates (where your repo-specific jobs are placed)
- a library repo for jenkins job builder templates (templates that your repo-specific jobs are based on)
- an automation user in github
- an SSH key for that user
- an OAuth token for that user with the permissions show above

##### Manual Steps
1. Get a machine, clone this repo into where your jenkins home *should* be
    - e.g. `git clone git@github.com:adobe-platform/ci-jenkins /var/lib/jenkins`
2. Bring up! Make sure that you have a private RSA SSH key in `<jenkins_user_home>/.ssh` for an automation user (used for the [GitSCM Plugin](https://wiki.jenkins-ci.org/display/JENKINS/Git+Plugin))
    - for static instances running CentOS, you're going to need a few things. The `cent` target in the [`Makefile`](https://github.com/adobe-platform/ci-jenkins/blob/master/Makefile#L42) will do this. For other systems where you are running this natively you'll have to tweak the commands a bit. Having a chef script do this may be nice...
    - for dynamic instances, the [docker image](https://hub.docker.com/r/adobeplatform/ci-jenkins/<Paste>) should be enough to get your started. However, this use case is still a bit experimental as it does not persist configs or secrets and these steps will be hard to automate.
3. Setup any security that you need, create an automation user that has permission to trigger jobs, SCM, etc. Login as that user & get its ID & API token (username @ top-right -> configure -> `Show API Token`)
4. Set up global configs (`Manage Jenkins` -> `Configure System`)
    - `GITHUB_DOMAIN` - defaults to `github.com` but can be replaced with your corp instance
    - `PROVISIONER` - reference the [concepts section](https://github.com/adobe-platform/ci-jenkins#concepts)
    - `TEMPLATE_GIT_URL` - SSH URL of the repo that this instance will write/cache to
    - `TEMPLATE_LIB_GIT_URL` - library job templates for chamberlain
5. Run the `provision` job.
    - `username` is the userID that you obtained in step 3. Leave empty if you skipped step 3.
    - `password` is the API token from step 3 too
    - `orgs` is for chamberlain, but isn't actually required
    - `oauth` your oauth token for an automation user
    - `mesos` Mesos leader URL (with port, NO `http` or `https`)
    - `GHAPIURL` if you're using corp git, provide the API URL (typically `corp.git.com/api/v3`). Used for chamberlain.

The setup for both provisioner & reader instances are pretty much the same, save for the value that you give for `PROVISIONER` (either `true` or leave it blank). If you don't need the provisioner instance, then you can just bring up a reader instance. Just make sure that you have some way of getting jenkins job templates (like the one mentioned in the [provisioner section](https://github.com/adobe-platform/ci-jenkins#provisioner-instances) into `TEMPLATE_GIT_URL`.

##### Systemd

If you're using CoreOS, check [this](https://github.com/adobe-platform/ci-jenkins/tree/master/systemd) out!
