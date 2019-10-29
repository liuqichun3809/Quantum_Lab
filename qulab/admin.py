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
    db_list = get_database()
    print('The following databases are already exist:')
    print(db_list)
    recent_db = config['db']['db']
    if config['db']['db'] != database:
        config['db']['db'] = database
        yamlpath = config_file()
        with open(yamlpath, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, Dumper=yaml.RoundTripDumper)
        if database in db_list:
            print('You have switch from database "%s" to "%s", please restart this jupyter server to use it.' % (recent_db, database))
        else:
            print('You have created a new database "%s", please restart this jupyter server to use it.' % database)
    else:
        print('Your recent selected database already is "%s".' % database)
        
def get_database():
    myclient = pymongo.MongoClient('mongodb://localhost:27017')
    print('The recent database is "%s".' % config['db']['db'])
    return myclient.database_names()

def drop_collection(database=None, collection=['',]):
    # drop collection=['',] in database, 
    # if database is None, collection=['',] in recent database will be drop
    myclient = pymongo.MongoClient('mongodb://localhost:27017')
    recent_db = config['db']['db']
    if database is None or database == recent_db:
        mydb = myclient[recent_db]
        print('You are going to drop the collection "%s" in recent database "%s".' % (collection, recent_db))
        print('Type in "y" to continue, or anyother words to quit.')
        ConfirmInfo = getConfirmInfo()
        if ConfirmInfo == 'y':
            col_list = mydb.list_collection_names()
            for col in collection:
                if col in col_list:
                    mydb[col].drop()
                    print('Collection "%s" drop successfully.' % col)
                else:
                    print('Collection "%s" drop failed, it is not exist.' % col)
    elif database in myclient.database_names():
        mydb = myclient[database]
        print('You are using database "%s", but going to drop collections in database "%s".' % (recent_db, database))
        print('Type in "y" to continue, or anyother words to quit.')
        ConfirmInfo = getConfirmInfo()
        if ConfirmInfo == 'y':
            col_list = mydb.list_collection_names()
            for col in collection:
                if col in col_list:
                    mydb[col].drop()
                    print('Collection "%s" drop successfully.' % col)
                else:
                    print('Collection "%s" drop failed, it is not exist.' % col)
    else:
        print('The database is not exist, collections drop failed.')
        
def getConfirmInfo():
    ConfirmInfo = input('Your choice > ')
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
        print('The database "%s" has following collections: "%s"' % (database, col_list))
        return col_list
    else:
        print('Dstabase "%s" is not exist.' % database)
        return None