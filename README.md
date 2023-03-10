# PDF Generator API

API Service to generate PDF from HTML using Python + WeasyPrint

Original Dockerfile from [weasyprint-docker-alpine](https://gitlab.com/jamesvl/weasyprint-docker-alpine)

## Requirements

Python 3 https://www.python.org/downloads/

WeasyPrint Installation Guild https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation

## Docker

Run the docker image, exposing port 5001

```
$ docker build -t pdf-generator-api:latest .

$ docker run -p 5001:5001 pdf-generator-api:latest
```

## Window

#### Installing and using virtualenv

```
$ pip install virtualenv

$ python -m venv venv
```

#### Activate virtualenv on Windows, activate script is in the Scripts folder

```
$ venv\Scripts\activate
```

#### Install dependencies

```
$ pip install -r requirements.txt
```

## Linux

#### Installing and using virtualenv

```
$ sudo apt install python3-venv

$ python3 -m venv venv
```

#### Activate virtualenv, activate script is in the Scripts folder

```
$ source ./venv/bin/activate
```

#### Install dependencies

```
$ python3 -m pip install -r requirements.txt
```

## Updating Python Packages On Windows Or Linux

```
# Output a list of installed packages into a requirements file (requirements.txt):
$ pip freeze > requirements.txt

# Edit requirements.txt, and replace all "==" with ">=". Use the "Replace All" command in the editor.
# Upgrade all outdated packages:
$ pip install -r requirements.txt --upgrade
```
