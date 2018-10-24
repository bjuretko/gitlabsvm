# gitlabsvm - Gitlab Secret Variables Management

A convenient CLI around [python-gitlab](https://github.com/python-gitlab/python-gitlab) to deal with [gitlab secret variables](https://docs.gitlab.com/ee/ci/variables/).

# Disclaimer

> Warning: The script does not ask for any confirmation on write operations. Be careful !
> <b>Big Warning: There is a bug with Gitlab to modify / delete  variables sharing the same keyname.
  See https://gitlab.com/gitlab-org/gitlab-ee/issues/7673 for more information.</b>

# Install

```bash
pip install -r requirements.txt
# pipenv install
./gitlabsvm.py --help
```

To access the Gitlab-API you need to create a Personal Access Token (PAT) on https://gitlab.com/profile/personal_access_tokens.

You can use [gogpat](https://github.com/solidnerd/gogpat/) from @solidnerd as well (if not using 2FA).

You can use the PAT from stdin or the environment variable `GITLABPAT`. With MacOS you can use the keychain to create a generic password entry with the PAT and reuse it like:

```bash
security find-generic-password -s GITLABPAT -g 2>&1 | grep "password" | cut -d \" -f 2 | ./gitlabsvm.py get myorg/group/project
```

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
  As an alternative you can leave the `private_token` empty and use the osx keychain as seen in the [examples](#examples).

# Usage

```
  gitlabsvm.py [-v] [--gitlab=<string>] get <project> [--key=<string> --key=<string>] [--environment=<string>] [--protected=<bool>]
  gitlabsvm.py [-v] [--gitlab=<string>] set <project> --key=<string> --value=<string> [--environment=<string>] [--protected=<bool>]
  gitlabsvm.py [-v] [--gitlab=<string>] del <project> [--key=<string> --key=<string>] [--environment=<string>] [--protected=<bool>]
  gitlabsvm.py [-v] [--gitlab=<string>] exportgroup <group> [--all] [--csv] [--file]
  gitlabsvm.py [-v] [--gitlab=<string>] export <project> [--csv] [--file]
  gitlabsvm.py [-v] [--gitlab=<string>] import <project/group> <filename.json>
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

  ```

# Examples

## Set individual variables

```bash
  ./gitlabsvm.py set myorg/mysubgroup/myproject --key=Key1 --value=123 --protected=1 --environment="Testenv"

  ./gitlabsvm.py del myorg/mysubgroup/myproject --key=Key1 --key=Key2 --protected=1 --environment="Testenv"
```

## Export all project variables to a csv file

```bash
  ./gitlabsvm.py export myorg/group/project --csv > project.csv
```

## Export all project variables of the staging environment to a csv file

```bash
  ./gitlabsvm.py get myorg/group/project --environment staging | | jq -SMcr '(map(keys) | add | unique) as $cols | map(. as $row | $cols | map($row[.])) as $rows | $cols, $rows[] | @csv'
```

## Export group variables as json on stdout

```bash
  ./gitlabsvm.py exportgroup myorg/group
```

## Import variables from a .env-file

```bash
while IFS='=' read -r n v
do
  # trim input
  n=$(echo -e $n | sed -e 's/^[[:space:]]*//' -e 's/^export *//')
  [[ $n != "#"* ]] && eval gitlabsvm.py \
      set myorg/mysubgroup/myproject \
      --key "$n" --value "$v" \
      --protected true \
      --environment staging
done<myenvfile.env
```

## Export project variables to a .env-file

```bash
gitlabsvm.py get myorg/mysubgroup/myproject --environment staging | jq -SMc '.[] | "\(.key)=$\(.value | @sh)"' | xargs -L 1 echo
```

You can prefix variables with the environment name, which may be helpful when transfering from a payed to a free plan (without environments in the CI)

```bash
gitlabsvm.py get myorg/mysubgroup/myproject --environment staging | jq -SMc --arg e staging '.[] | "\($e|ascii_upcase)_\(.key)=$\(.value | @sh)"' | xargs -L 1 echo
```

## Use another gitlab instance by url with a PAT from osx keychain

```bash
security find-generic-password -s GITLABPAT -g 2>&1 | grep "password" | cut -d \" -f 2 | ./gitlabsvm.py --gitlab https://gitlab.mycompany.net get myorg/group/project
```

# Similar projects

[temando/gitlab-ci-variables-cli](https://github.com/temando/gitlab-ci-variables-cli): CLI tool to allow setting bulk project variables on Gitlab CI (nodejs application)

- does not use a API wrapper, so no explict handling of pageviews and rate-limiting
- does not support multiple gitlab environments (EE feature)
- Good: has a write-protection mode
