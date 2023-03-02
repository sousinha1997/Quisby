# Install from sources
1) First activate the environment using the command 
`source venv/bin/activate`
 
2) Install requirement
`pip install -r requirements.txt`

3) Run the project using the command 
`python manage.py runserver` 


# Build container and use
1. Build container 
`podman build . -t pquisby-api`

2. Run container
`podman run -itd -p 8000:8000 localhost/pquisby-api`


Note: In both the above setups please add credentials.json in root dir for google auth



