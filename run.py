from Config.api import CreateApi
from Source.main import MainHandler
from Source.test import Test
from Source.userauth import UserAuth
from Source.warehouse import Warehouse
from Source.users import Users
from Source.project import Project
from Source.colors import Colors
from Source.norex import Norex
from Source.sawoperator import Sawoperator
from Source.purchasing import Purchase
from Source.issue import Issue
from Source.edittag import Edittag
from Source.replacement import Replacement
from Source.browse import Browse
from Source.emptystorage import EmptyStorage
from Source.rejection import Rejection
from Source.logs import LogEndPoint
from Source.util import Util

app = CreateApi.create_api()
api = CreateApi.get_api()

api.add_resource(MainHandler, '/')
api.add_resource(UserAuth, '/userauth')
api.add_resource(Purchase, '/purchasing')
api.add_resource(Warehouse, '/warehouse')
api.add_resource(Test, '/test')
api.add_resource(Users, '/users')
api.add_resource(Project, '/projects')
api.add_resource(Colors, '/colors')
api.add_resource(Norex, '/norex')
api.add_resource(Sawoperator, '/sawoperator')
api.add_resource(Issue, '/issue')
api.add_resource(Edittag, '/edittag')
api.add_resource(Replacement, '/replacement')
api.add_resource(Browse, '/browse')
api.add_resource(EmptyStorage, '/emptystorage')
api.add_resource(Rejection, '/rejection')
api.add_resource(LogEndPoint, '/logs')
api.add_resource(Util, '/utilities')

# SERVER_HOST = '10.10.40.187'
# SERVER_PORT = 5000

if __name__ == '__main__':
    # app.run(debug=False, host=SERVER_HOST, port=SERVER_PORT)
    app.run()
