#!/usr/bin/env python3
"""
A build tool for Python Lambda Functions.

Solomon Bothwell
http://www.github.com/ssbothwell
ssbothwell@gmail.com

## How to Use:

# Scaffold a project
$ build_lambda project_name --scaffold
or
$ build_lambda project_name -s

# Package a build
$ build_lambda project_name -p
or
$ build_lambda project_name --package

# Deploy a build
$ build_lambda project_name -d
or
$ build_lambda project_name -d

Commands can be combined:
$ build_lambda project_name -p -d

AWS deployment details should be set in a config.yaml
file in your project home directory. Alternatively,
Deploy mode can be operated in interactive mode with a
'-i' flag:
$ build_lambda project_name -d -i 

"""
import sys
import os
import argparse
import pathlib
import shutil
import yaml
import subprocess
from functools import reduce


def copy_tree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        print(d)
        if os.path.isdir(s):
            copy_tree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)


def scaffold(project: str) -> None:
    """ Create a project scaffold """
    
    # Paths
    project_path = os.path.abspath(project)
    src_path     = f'{project_path}/src'
    build_path   = f'{project_path}/build'
    dist_path    = f'{project_path}/dist'
    venv_path    = f'{project_path}/venv'
    native_path  = f'{project_path}/native_libs'

    # Create folders
    os.mkdir(project_path)
    os.mkdir(src_path)
    os.mkdir(dist_path)
    os.mkdir(build_path)
    os.mkdir(native_path)
   
    # Create config.yaml
    with open(f'{project_path}/config.yaml', 'a') as f:
        f.write(f'region:\n')
        f.write(f'function-name: {project}\n')
        f.write(f'zip-file: {project}.zip\n')
        f.write(f'role:\n')
        f.write(f'handler: src.lambda_function.lambda_handler\n')
        f.write(f'runtime: python3.6\n')
        f.write(f'profile: default\n')
        f.write(f'timeout: 10\n')
        f.write(f'memory-size: 1024\n')
    f.close()

    # Create lambda_function.py
    with open(f'{src_path}/lambda_function.py', 'a') as f:
        f.write('"""\n')
        f.write('AWS Lambda Function\n')
        f.write('\n')
        f.write('"""\n')
        f.write('import boto3\n')
        f.write('\n')
        f.write('\n')
        f.write('def lambda_handler(event, context):\n')
        f.write('    """ docstring """\n')
        f.write('\n')
        f.write('    return')
    f.close() 

    # Create src/__init__.py
    with open(f'{src_path}/__init__.py', 'w+') as f:
        f.write('')
    f.close()

    # Create dist/__init__.py
    with open(f'{dist_path}/__init__.py', 'w+') as f:
        f.write('')
    f.close()

    # Create virtualenv
    subprocess.call(['virtualenv', venv_path])


def build_package(project: str, args: dict) -> None:
    """ Update build """

    project_path = os.path.abspath(args.project)

    if not os.path.exists(project_path):
        return 'Error: Please enter a valid directory'

    if not os.path.exists(f'{project_path}/src'):
        return "Error: Project does not have a valid 'src/' dir"

    if not args.virtualenv:
        venv = 'venv'
    else:
        venv = f'/{args.virtualenv}'

    # Generate `dist` and `build` dirs if not present
    pathlib.Path(project_path + '/dist').mkdir(exist_ok=True) 
    pathlib.Path(project_path + '/build').mkdir(exist_ok=True) 

    src_path    = f'{project_path}/src'
    build_path  = f'{project_path}/build'
    dist_path   = f'{project_path}/dist'
    venv_path   = f'{project_path}/{venv}'
    native_path = f'{project_path}/native_libs'

    # Copy lambda src to `dist`
    print('### Copying lambda src to `dist/src`...', end='')
    if not os.path.exists(f'{dist_path}/src'):
        os.mkdir(f'{dist_path}/src')
    copy_tree(src_path, f'{dist_path}/src')
    print('...Complete ###')

    # Copy pip modules to `dist`
    if os.path.exists(venv_path):
        print('### Copying pip modules to `dist/`...', end='')
        for folder in os.listdir(f'{venv_path}/lib'):
            copy_tree(f'{venv_path}/lib/{folder}/site-packages', dist_path) 
        print('...Complete')

    # Copy native libraries
    if os.path.exists(native_path):
        print('### Copying native libraries to `dist/`...', end='')
        for folder in os.listdir(native_path):
            copy_tree(native_path, dist_path) 
        print('...Complete')

    # Create an __init__.py file in `dist`
    if not os.path.isfile('f{dist_path}/__init__.py'):
        f = open(dist_path + '/__init__.py', 'w+')
        f.close()
    
    # Rename prior build
    if os.listdir(build_path):
        current_path = f'{build_path}/{project}.zip' 
        if os.path.exists(current_path):
            prior_version = len(os.listdir(build_path))
            prior_path = f'{build_path}/{project}-{prior_version}.zip'
            os.rename(current_path, prior_path)
    
    # Zip new build
    print('### Zipping Build Package...', end='')
    shutil.make_archive(project, 'zip', dist_path)
    shutil.move(f'./{project}.zip', f'{build_path}/send_images.zip')
    print('...Complete')


def parse_config(config_path: str) -> list:
    with open(config_path, 'r') as stream:
        try:
            config_dict = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    args = list(reduce(lambda a, b: a + b, config_dict.items()))
    
    for i, el in enumerate(args):
        if i % 2 == 0:
            args[i] = '--' + el 

    return ['aws', 'lambda'] + args


def deploy_project(project: str, command: list, interactive: bool) -> None:
    """ Deploy project to AWS """
    
    if interactive:
        region        = str(input("region: "))
        function_name = str(input("function-name: "))
        zip_file      = str(input("zip-file: "))
        role          = str(input("role: "))
        handler       = str(input("handler: "))
        runtime       = str(input("runtime: "))
        profile       = str(input("profile: "))
        timeout       = str(input("timeout: "))
        memory_size   = str(input("memory-size: "))

        command = ['~/.local/bin/aws', 'lambda', 
                   '--region', region,
                   '--function-name', function_name,
                   '--zip-file', zip_file,
                   '--role', role,
                   '--handler', handler,
                   '--runtime', runtime,
                   '--profile', profile,
                   '--timeout', timeout,
                   '--memory-size', memory_size
                  ]
    
    subprocess.call(command)


def main() -> None:
    parser = argparse.ArgumentParser()
    
    # Add Parsers
    parser.add_argument('project', help='Project Root')
    parser.add_argument('-s', '--scaffold', help='Scaffold a new project', nargs='?', const=True, default=False,)
    parser.add_argument('-d', '--deploy', help='Deploy package to AWS', nargs='?', const=True, default=False)
    parser.add_argument('-v', '--virtualenv', help='Virtualenv dir', default='venv')
    parser.add_argument('-i', '--interactive', help='Interactive aws cli config', nargs='?', const=True, default=False)
    
    args = parser.parse_args()
    project = args.project

    if args.scaffold:
        return scaffold(project)
    
    # Generate project.zip
    build_package(project, args)
    
    if args.deploy:
        config = parse_config(f'{project}/config.yaml')

        deploy_project(project, config, args.interactive)
    
    return 'Done!' 


if __name__ == '__main__':
    print(main())
