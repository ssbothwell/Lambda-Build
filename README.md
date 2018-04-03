#A build tool for Python Lambda Functions.

Solomon Bothwell
http://www.github.com/ssbothwell
ssbothwell@gmail.com

## How to Use:

### Scaffold a project
`$ build_lambda project_name --scaffold`
or
`$ build_lambda project_name -s`

### Package a build
`$ build_lambda project_name -b`
or
`$ build_lambda project_name --build`

### Deploy a build
`$ build_lambda project_name -d`
or
`$ build_lambda project_name -d`

Commands can be combined:
`$ build_lambda project_name -p -d`

AWS deployment details should be set in a config.yaml
file in your project home directory. Alternatively,
Deploy mode can be operated in interactive mode with a
'-i' flag:
`$ build_lambda project_name -d -i`
