
### What is this repository for? ###
This is the base python base repo for any project to kickstart (Qudo Data Science team).
There are 2 major components to this:
* Flask App: REST APIs

### How do I get set up? ###

#### Local
Create & Activate a Virtual Environment
```bash
pip install virtualenv
virtualenv ~/Projects/venv/pythia-backend -p python3.11
source ~/Projects/venv/pythia-backend/bin/activate
```
Installing Requirements
```bash
make install
```
Setup Redis (Broker)
```bash
brew install redis
brew services start redis
```
Set Environment Variables
```bash
export OPENAI_API_KEY='your_openai_api_key_here'
export MONGO_PRIVATE_KEY='your_mongo_private_key_here'
export mongodb_password='your_mongodb_password_here'
export jwt_secret_key="jwt_secret_key"
export QUDO_ENV='env_you_are_running'
export PYTHONPATH='full_path_repository'
```
Start the Flask Application
```bash
flask run
```


#### Local Docker
```commandline
docker-compose -f build
docker-compose up
```

### How to run tests
Install The App as a python package
```commandline
pip install -e .
```

Run the Tests
```commandline
pytest
```

Get the coverage Report
```commandline
coverage run -m pytest
coverage report
```


### Contribution guidelines ###

* Writing tests
    * Ensure that the code coverage is > 90%
* Code review
    * Create a Feature / Hotfix Branch
    * Start your commit messages with the Monday Ticket ID
        * [ZOHO-111]: Setting up the unit tests
    * Add 2 Reviewers
* Other guidelines
