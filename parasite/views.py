from parasite import parasite

@parasite.route('/')
@parasite.route('/index')
def index():
    return "Hello, World!"