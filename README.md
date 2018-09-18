# gitlabsvm - Gitlab Secret Variables Management

A convenient CLI around [python-gitlab](https://github.com/python-gitlab/python-gitlab) to deal with secret variables.

# Disclaimer

Warning: The script does not ask for any confirmation on write operations. Be careful !

# Install

```bash
pip install -r requirements.txt
./gitlabsvm.py --help
```

To access the Gitlab-API you need to create a Personal Access Token (PAT) on https://gitlab.com/profile/personal_access_tokens

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
  You can use the file 
# Usage

```
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

  ```

