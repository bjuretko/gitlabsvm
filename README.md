# gitlabsvm - Gitlab Secret Variables Management

A convenient CLI around [python-gitlab](https://github.com/python-gitlab/python-gitlab) to deal with [gitlab secret variables](https://docs.gitlab.com/ee/ci/variables/).

# Disclaimer

Warning: The script does not ask for any confirmation on write operations. Be careful !
<b>
Big Warning: There is a bug with Gitlab to modify / delete variables sharing the same keyname.
See https://gitlab.com/gitlab-org/gitlab-ee/issues/7673 for more information.
</b>

# Install

```bash
pip install -r requirements.txt
# pipenv install
./gitlabsvm.py --help
```

To access the Gitlab-API you need to create a Personal Access Token (PAT) on https://gitlab.com/profile/personal_access_tokens.

You can use [gogpat](https://github.com/solidnerd/gogpat/) from @solidnerd as well (if not using 2FA).

Then create or edit a [~/.python-gitlab.cfg](python-gitlab.cfg) config file in your home directory 
or a `.python-gitlab.cfg` in the cwd with the following contents

  ```ini
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
  ```

  Put your PAT at the key '`private_token`'. 
  _Restrict the user and permissions to personal use only, as the PAT allows global access to your gitlab API with full usage rights._

# Usage

```
  gitlabsvm.py get <project> [--key=<key> --key=<key>] [--environment=<env>] [--protected=<true|false>]
  gitlabsvm.py set <project> --key=<key> --value=<value> [--environment=<env>] [--protected=<true|false>]
  gitlabsvm.py del <project> [--key=<key> --key=<key>] [--environment=<env>] [--protected=<true|false>]
  gitlabsvm.py export <project> [--csv] [--file]
  gitlabsvm.py exportgroup <group> [--csv] [--file]
  gitlabsvm.py import <project> --filename=<filename.json>
  gitlabsvm.py (-h | --help)
  gitlabsvm.py --version

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  <project>                     Project name including groups, e.g. groupname/project.
  <group>                       Groupname, e.g. groupname
  --key=<key>                   The Key-Name of the secret variable (this is not unique)
  --environment=<env>           The target environment
  --protected=<true|false>      Only valid for protected branches
  --value=<value>               The JSON-encoded value of the variable
  --file                        Write to file

  ```

# Examples

```bash
  ./gitlabsvm.py set myorg/mysubgroup/myproject --key=Key1 --value=123 --protected=1 --environment="Testenv"

  ./gitlabsvm.py del myorg/mysubgroup/myproject --key=Key1 --key=Key2 --protected=1 --environment="Testenv"

  ./gitlabsvm.py exportgroup myorg --file
```