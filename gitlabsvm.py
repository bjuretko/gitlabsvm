#!/usr/local/bin/python
"""gitlabsvm - Manage GitLab Secret Variables.
   Author: Benedict Juretko
   License: MIT
Usage:
  gitlabsvm.py [-v | -vv] [--gitlab=<string>] get <project> [--key=<string> --key=<string>] [--environment=<string>] [--protected=<bool>]
  gitlabsvm.py [-v | -vv] [--gitlab=<string>] set <project> --key=<string> --value=<string> [--environment=<string>] [--protected=<bool>]
  gitlabsvm.py [-v | -vv] [--gitlab=<string>] del <project> [--key=<string> --key=<string>] [--environment=<string>] [--protected=<bool>]
  gitlabsvm.py [-v | -vv] [--gitlab=<string>] exportgroup <group> [--all] [--csv] [--file]
  gitlabsvm.py [-v | -vv] [--gitlab=<string>] export <project> [--csv] [--file]
  gitlabsvm.py [-v | -vv] [--gitlab=<string>] import <project/group> <filename.json>
  gitlabsvm.py (-h | --help)
  gitlabsvm.py --version

Arguments:
  get <project>                 Get 1 or more project variables.
  set <project>                 Change or create a project variable
  del <project>                 Remove 1 or more project variables.
  exportgroup <group>           Print group variables, use --all to include all subprojects as well
  export <project>              Print project variables, use --csv to export comma separated values

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  -v                            Verbose logging output
  <project>                     Project name including groups, e.g. groupname/project.
  <group>                       Groupname, e.g. groupname
  --key=<string>                The Key-Name of the secret variable (this is not unique)
  --environment=<string>        The target environment name, like staging or production
  --protected=<bool>            Only valid for protected branches
  --value=<string>              The JSON-escaped value of the variable
  --file                        Write output to file with a timestamped filename
  --all                         Include all sub projects in output
  --gitlab=<string>             Gitlab instance from ~/.python-gitlab.cfg or URL. Defaults to gitlab and https://www.gitlab.com respectively

Examples:
  ./gitlabsvm.py set myorg/mysubgroup/myproject --key=Key1 --value=123 --protected=1 --environment="Testenv"
  ./gitlabsvm.py del myorg/mysubgroup/myproject --key=Key1 --key=Key2 --protected=1 --environment="Testenv"
  ./gitlabsvm.py get myorg/mysubgroup/myproject

First use:
  To access the Gitlab-API you need to create a Personal Access Token (PAT) on
  https://gitlab.com/profile/personal_access_tokens

  Then create or edit a ~/.python-gitlab.cfg config file in your home directory 
  or a .python-gitlab.cfg in the cwd with the following contents
     [global]
     default = gitlab
     ssl_verify = true
     timeout = 60

     [gitlab]
     url = https://gitlab.com
     # PAT personal accesss token to API
     private_token = v************+Q
     api_version = 4
     timeout = 120

  Put your PAT at the key 'private_token'. Set the owner and permissions 
  to 600.
"""
import sys
from docopt import docopt

import os
import inspect

# uncomment the following lines to allow debugging of python-gitlab submodule
# cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"python-gitlab")))
# if cmd_subfolder not in sys.path:
#    sys.path.insert(0, cmd_subfolder)

# import gitlab  # http://python-gitlab.readthedocs.io/en/stable/install.html

import gitlab
import csv
import json
import logging
from datetime import datetime
from os.path import exists, expanduser

if __name__ == '__main__':
    arguments = docopt(__doc__, version='0.0.2')
    logging.basicConfig(
        stream=sys.stderr, level=30 - (arguments["-v"] * 10))
    logging.debug(gitlab.__version__)
    logging.debug(arguments)

    # check if we have config file /etc/python-gitlab.cfg or ~/.python-gitlab.cfg
    configfile_exists = os.path.exists(os.path.join(expanduser(
        "~"), ".python-gitlab.cfg")) or os.path.exists("/etc/python-gitlab.cfg")

    # handle used gitlab instance from arg or default value
    # if we have no config file instance = https://www.gitlab.com
    # else instance = gitlab from config file
    gitlabinstance = arguments['--gitlab']
    if not gitlabinstance:
        gitlabinstance = 'gitlab' if configfile_exists else "https://www.gitlab.com"

    gitlab_no_config_instance = gitlabinstance.startswith("https://")

    if not gitlab_no_config_instance and not configfile_exists:
        logging.error(
            "--gitlab argument is pointing to a config-file entry [%s], but there is no config file available.", gitlabinstance)
        sys.exit(255)

    gl = None
    try:
        if gitlab_no_config_instance:
            # if using gitlab by url -> get accesstoken (PAT) from user
            # by env-var $GITLABPAT or stdin/readline
            gitlabpat = os.environ["GITLABPAT"] if os.environ.has_key(
                "GITLABPAT") else ''
            while not gitlabpat:
                try:
                    gitlabpat = raw_input(
                        "Enter gitlab private access token: ")
                except EOFError:
                    break
            #gitlabpat = gitlabpat.strip()
            logging.debug("Using gitlab instance %s with PAT %s", gitlabinstance, gitlabpat)
            gl = gitlab.Gitlab(
                gitlabinstance, private_token=gitlabpat, timeout=120)
        else:
            gl = gitlab.Gitlab.from_config(gitlabinstance)
    except ValueError:
        logging.error(
            "Failed to communicate with gitlab server. In most cases this is an invalid private access token (PAT).")
        sys.exit(254)

    projects = []
    if arguments['exportgroup']:
        g = gl.groups.get(arguments['<group>'])
        g_variables = g.variables.list()
        logging.debug("Group Variables: %s", g_variables)
        #gl.projects.list(visibility='private', as_list=False)
        group_info = {'groupId': g._attrs["id"],
                      'namespace': g._attrs["path"]}
        try:
            filename_prefix = g._attrs["path"].replace('/', '_')
            filename_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename_suffix = "csv" if arguments['--csv'] else "json"
            outputfile = open("%s_%s.%s" % (filename_prefix, filename_timestamp,
                                            filename_suffix), 'w') if arguments['--file'] else sys.stdout
            if arguments['--csv']:
                with outputfile as csvfile:
                    writer = csv.DictWriter(csvfile, [u'groupId', u'namespace', u'protected',
                                                        u'key', u'value'], delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                    writer.writeheader()
                    for gv in g_variables:
                        sv = dict((k, v) for d in (gv._attrs, group_info)
                                    for k, v in d.items())
                        writer.writerow(sv)
            else:
                svs = [dict((k, v) for d in (gv._attrs, group_info)
                            for k, v in d.items()) for gv in g_variables]
                outputfile.write(json.dumps(svs))
        except Exception as e:
            logging.exception("Error getting secret variables: %s", e)
        if arguments["--all"]:
            projects = g.projects.list(all=True)
    else:
        # TODO: support multiple projects
        projects.append(gl.projects.get(arguments['<project>']))

    for pg in projects:
        p = gl.projects.get(pg.id)

        project_info = {'projectId': p.id, 'namespace': p.path_with_namespace}

        logging.info("Project Id: %d, Namespace: %s",
                     p.id, p.path_with_namespace)
        if arguments['export'] or arguments['exportgroup']:
            try:
                p_variables = p.variables.list(all=True)
                filename_prefix = p.path_with_namespace.replace('/', '_')
                filename_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename_suffix = "csv" if arguments['--csv'] else "json"
                outputfile = open("%s_%s.%s" % (filename_prefix, filename_timestamp,
                                                filename_suffix), 'w') if arguments['--file'] else sys.stdout
                if arguments['--csv']:
                    with outputfile as csvfile:
                        writer = csv.DictWriter(csvfile, [u'projectId', u'namespace', u'protected', u'environment_scope',
                                                          u'key', u'value'], delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                        writer.writeheader()
                        for pv in p_variables:
                            sv = dict((k, v) for d in (pv._attrs, project_info)
                                      for k, v in d.items())
                            writer.writerow(sv)
                else:
                    svs = [dict((k, v) for d in (pv._attrs, project_info)
                                for k, v in d.items()) for pv in p_variables]
                    outputfile.write(json.dumps(svs))
                logging.info("exported %d secret variables.", len(p_variables))
            except Exception as e:
                logging.exception("Error getting secret variables: %s", e)

        if arguments['import']:
            print "Not yet implemented"

        if arguments['get'] or arguments['set'] or arguments['del']:
            try:
                p_variables = p.variables.list(all=True)
                filtered_variables = []
                for pv in p_variables:
                    if len(arguments['--key']) > 0 and (not (pv.key in arguments['--key'])):
                        continue
                    if not (arguments['--environment'] is None) and (pv.environment_scope != arguments['--environment']):
                        continue
                    if not (arguments['--protected'] is None) and (pv.protected != (arguments['--protected'] in ['true', '1', 'True', 'y', 'yes'])):
                        continue
                    filtered_variables.append(pv)
                logging.debug("Filtered SVs: %s", filtered_variables)
                if arguments['get']:
                    print json.dumps([dict(pv._attrs)
                                      for pv in filtered_variables])
                elif arguments['del']:
                    map(lambda k: p.variables.delete(k.key), filtered_variables)
                    logging.info("Deleted %d variables: %s", len(
                        filtered_variables), filtered_variables)
                elif arguments['set']:
                    if len(filtered_variables) > 1:
                        logging.critical("There are more than one secret variables under this key: %s",
                                         [dict(pv._attrs) for pv in filtered_variables])
                        sys.exit(1)
                    elif len(filtered_variables) == 1:
                        pv = filtered_variables[0]
                        pv.value = arguments['--value']
                        pv.save()
                        logging.info("Updated variable %s", pv)
                    else:
                        p.variables.create(
                            {'key': arguments['--key'][0], 'value': arguments['--value'], 'protected': arguments['--protected'], 'environment_scope': arguments['--environment'] if arguments['--environment'] != None else '*'})
                        logging.info("Created variable %s",
                                     arguments['--key'][0])
            except Exception as e:
                logging.exception("Error getting secret variables: %s", e)
