#-*- coding=utf-8 -*-
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from app import app, db, login_manager
from app.models import *
from sqlalchemy import func as SQLfunc
import logging

manager = Manager(app)
migrate = Migrate(app, db)
app.jinja_env.globals['User'] = User
app.jinja_env.globals['AD600'] = AD600
app.jinja_env.globals['PioneerNeed'] = PioneerNeed
app.jinja_env.globals['FriendUrl'] = FriendUrl
app.jinja_env.globals['ViewHistory'] = ViewHistory
app.jinja_env.globals['Post'] = Post
app.jinja_env.globals['onlineTag'] = onlineTag
app.jinja_env.globals['SQLfunc'] = SQLfunc
app.jinja_env.globals['db'] = db


def make_shell_context():
    return dict(app=app, db=db, IP=IP, ID=ID, Context=Context, Post=Post, clPost=clPost, Role=Role, User=User, FriendUrl=FriendUrl)

manager.add_command('Shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
def deploy():
    db.create_all()
    print "please input admin's email:"
    email=raw_input()
    print "please input admin's password:"
    password=raw_input()
    User.insert_admin(email=123456@qq.com,password=123456)
    FriendUrl.insert_url()


if __name__ == '__main__':
    manager.run()
    # app.run(host='0.0.0.0',debug=True)
