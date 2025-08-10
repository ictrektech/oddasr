import functools
from flask import session,Blueprint
from werkzeug.utils import redirect

bp = Blueprint('jdl_session', __name__, url_prefix='')

def session_required(view_func):
    @functools.wraps(view_func)
    def verify_session(*args,**kwargs):
        
        if session.get("user") == None:
           return redirect('login.html',code=302);
        
        return view_func(*args,**kwargs)

    return verify_session