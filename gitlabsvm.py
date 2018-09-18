#!/usr/local/bin/python
"""gitlabsvm - Manage GitLab Secret Variables.
   Author: Benedict Juretko
   License: MIT
Usage:
  gitlabsvm.py get <project> [--key=<key> --key=<key>] [--environment=<env>] [--protected]
  gitlabsvm.py set <project> --key=<key> --value=<value> [--environment=<env>] [--protected]
  gitlabsvm.py del <project> [--key=<key> --key=<key>] [--environment=<env>] [--protected]
  gitlabsvm.py export <project> [--csv] [--file]
  gitlabsvm.py exportgroup <group> [--csv] [--file]
  gitlabsvm.py import <project> --filename=<filename.json>
  gitlabsvm.py (-h | --help)
  gitlabsvm.py --version

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  <project>                     Project name including groups, e.g. bdstudio/eshop.
  <group>                       Groupname, e.g. bdstudio
  --key=<key>                   The Key-Name of the secret variable (this is not unique)
  --environment=<env>           The target environment [default:'*']
  --protected                   Only valid for protected branches [default:false]
  --value=<value>               The JSON-encoded value of the variable
  --file                        Write to file  [default:projectslug.json]

Examples:
  ./gitlabsvm.py set myorg/mysubgroup/myproject --key=Key1 --value=123 --protected --environment="Testenv"
  ./gitlabsvm.py del myorg/mysubgroup/myproject --key=Key1 --key=Key2 --protected --environment="Testenv"
  ./gitlabsvm.py exportgroup myorg --file

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
from docopt import docopt
import gitlab  # http://python-gitlab.readthedocs.io/en/stable/install.html
import csv
import json
import sys
import logging
from datetime import datetime
from os.path import expanduser

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    arguments = docopt(__doc__, version='0.0.1')
    logging.debug(arguments)

    gl = gitlab.Gitlab.from_config(
        'gitlab', [expanduser("~") + '/.python-gitlab.cfg'])

    projects = []
    if arguments['exportgroup']:
        g = gl.groups.get(arguments['<group>'])
        g_variables = g.variables.list()
        logging.debug("Group Variables: %s", g_variables)
        # gl.projects.list(visibility='private', as_list=False)
        projects = g.projects.list(all=True)
    else:
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
                filename_timestamp = datetime.now().strftime('%Y%m%d%H%M%S"')
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
                    if not (arguments['--protected'] is None) and (pv.protected != arguments['--protected']):
                        continue
                    filtered_variables.append(pv)
                logging.debug("Filtered SVs: %s", filtered_variables)
                if arguments['get']:
                    print json.dumps([dict(pv._attrs) for pv in filtered_variables])
                elif arguments['del']:
                    map(lambda k: p.variables.delete(k.key), filtered_variables)
                    logging.info("Deleted %d variables: %s", len(filtered_variables), filtered_variables)
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
                        logging.info("Created variable %s", arguments['--key'][0])
            except Exception as e:
                logging.exception("Error getting secret variables: %s", e)
