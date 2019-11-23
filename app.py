import os

import graphene

from flask import Flask
from flask_graphql import GraphQLView
from flask_sqlalchemy import SQLAlchemy
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField


app = Flask(__name__)
app.debug = True


basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' +    os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

# Modules
class User(db.Model):
    __tablename__ = 'users'
    uuid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), index=True, unique=True)
    email = db.Column(db.String(256), index=True)
    todos = db.relationship('Todo', backref='doer')
    
    def __repr__(self):
        return '<User %r>' % self.username

class Todo(db.Model):
    __tablename__ = 'todos'
    uuid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), index=True)
    doer_id = db.Column(db.Integer, db.ForeignKey('users.uuid'))
    def __repr__(self):
        return '<Todot %r>' % self.title


# Schema Objects
class TodoObject(SQLAlchemyObjectType):
    class Meta:
        model = Todo
        interfaces = (graphene.relay.Node, )
        
class UserObject(SQLAlchemyObjectType):
   class Meta:
       model = User
       interfaces = (graphene.relay.Node, )
       
class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_todos = SQLAlchemyConnectionField(TodoObject)
    all_users = SQLAlchemyConnectionField(UserObject)
schema = graphene.Schema(query=Query)

class CreateTodo(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        username = graphene.String(required=True)
    todo = graphene.Field(lambda: TodoObject)

    def mutate(self, info, title, username):
        user = User.query.filter_by(username=username).first()
        todo = Todo(title=title)
        if user is not None:
            todo.author = user
        db.session.add(todo)
        db.session.commit()
        return CreateTodo(todo=todo)

class Mutation(graphene.ObjectType):
    create_todo = CreateTodo.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)


# Routes
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True # for having the GraphiQL interface
    )
)
@app.route('/')
def index():
    return '<p> Hello World</p>'
if __name__ == '__main__':
     app.run()