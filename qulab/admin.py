import getpass

from . import _bootstrap, db
from .config import config, config_file
from ruamel import yaml
import pymongo


def getRegisterInfo():
    username = input('User Name > ')
    password = getpass.getpass(prompt='Password > ')
    password2 = getpass.getpass(prompt='Repeat Password > ')
    if password != password2:
        print('Error')
        return
    email = input('E-mail > ')
    fullname = input('Full Name > ')
    return username, password, email, fullname


@_bootstrap.require_db_connection
def register():
    username, password, email, fullname = getRegisterInfo()
    user = db.update.newUser(name=username, email=email, fullname=fullname)
    user.password = password
    user.save()
    print('Success.')


@_bootstrap.authenticated
def uploadDriver(path):
    db.update.uploadDriver(path, _bootstrap.get_current_user())


@_bootstrap.authenticated
def setInstrument(name, host, address, driver):
    db.update.setInstrument(name, host, address, driver)


def set_database(database):
    print('The following databases are already existed:')
    print(get_database())
    if config['db']['db'] != database:
        config['db']['db'] = database
        yamlpath = config_file()
        with open(yamlpath, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, Dumper=yaml.RoundTripDumper)
        print('You have created a new database "%s", please restart this jupyter server to use it.' % database)
    else:
        print('Your recent selected database already is "%s".' % database)
        
def get_database():
    myclient = pymongo.MongoClient('mongodb://localhost:27017')
    print('The recent database is "%s".' % config['db']['db'])
    return myclient.database_names()