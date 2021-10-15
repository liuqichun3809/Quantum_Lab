import getpass

from . import _bootstrap, db
from .config import config, config_file
from ruamel import yaml
import pymongo


def getRegisterInfo():
    """Request the registration information.
    """
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
    """Save registration information to the database.
    """
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
    db_list = get_database()
    print('The following databases already exist:')
    print(db_list)
    recent_db = config['db']['db']
    if config['db']['db'] != database:
        config['db']['db'] = database
        yamlpath = config_file()
        with open(yamlpath, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, Dumper=yaml.RoundTripDumper)
        if database in db_list:
            print(f'You have switch from database {recent_db} to {database}.'
                  'Please restart this Jupyter kernel to load it.')
        else:
            print(f'You have created a new database {database}. '
                  'Please restart this Jupyter kernel to load it.')
    else:
        print(f'The database is already {database}".')


def get_database():
    myclient = pymongo.MongoClient('mongodb://localhost:27017')
    print('The most recent database is {}.'.format(config['db']['db']))
    return myclient.database_names()


def drop_collection(database=None, collection=['']):
    # drop collection=[''] in database,
    # if database is None, collection=[''] in recent database will be dropped
    myclient = pymongo.MongoClient('mongodb://localhost:27017')
    recent_db = config['db']['db']
    if database is None or database == recent_db:
        mydb = myclient[recent_db]
        print(
            f'Drop the collection {collection} in database {recent_db} (y/[n])?'
        )
        ConfirmInfo = getConfirmInfo()
        if ConfirmInfo == 'y':
            print('Drop off confirmed')
            col_list = mydb.list_collection_names()
            for col in collection:
                if col in col_list:
                    mydb[col].drop()
                    print(f'Collection {col} drop successfully.')
                else:
                    print(f'Collection {col} failed to drop, it does not exist.')
    elif database in myclient.database_names():
        mydb = myclient[database]
        print(
                f'The current database is {recent_db}, but the collection given is in database {database}.'
        )
        print('Are you sure (y/[n])?')
        ConfirmInfo = getConfirmInfo()
        if ConfirmInfo == 'y':
            print('Drop off confirmed')
            col_list = mydb.list_collection_names()
            for col in collection:
                if col in col_list:
                    mydb[col].drop()
                    print(f'Collection {col} dropped successfully.')
                else:
                    print('Collection {col} not found.')
    else:
        print('The database does not exist, collections failed to drop.')


def getConfirmInfo() -> str:
    ConfirmInfo = str(input('Your choice > '))
    return ConfirmInfo


def get_collection_info(database=None):
    # get the whole collections in (recent) database
    myclient = pymongo.MongoClient('mongodb://localhost:27017')
    recent_db = config['db']['db']
    if database is None:
        database = recent_db
    if database in myclient.database_names():
        mydb = myclient[recent_db]
        col_list = mydb.list_collection_names()
        print(f'The database {database} has following collections: {col_list}')
        return col_list
    else:
        print(f'Database {database} does not exist.')
        return None
