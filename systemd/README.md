systemd scripts
=====

These units are highly opinionated and assume that you're running this on CoreOS.

You should have an `/etc/environment` file that, at the very least, looks like:

```
COREOS_PRIVATE_IPV4=<IP_OF_MACHINE>
TEMPLATE_LIB_GIT_URL=<SSH URL OF REPO FOR JENKINS JOB BUILDER TEMPLATE LIB>
TEMPLATE_GIT_URL=<SSH URL OF REPO FOR EXISTING JOBS>
GITHUB_DOMAIN=<github.com OR your corp git URL>
```
