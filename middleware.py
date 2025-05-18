import functools
from flask import session, redirect, url_for, flash

# Middleware for authenticated users
def auth(view_func):
    @functools.wraps(view_func)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash("You need to log in to access further.", "error")
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return decorated

# Middleware for guests
def guest(view_func):
    @functools.wraps(view_func)
    def decorated(*args, **kwargs):
        if 'username' in session:
            flash("You are already logged in.", "error")
            return redirect(url_for('dashboard'))
        return view_func(*args, **kwargs)
    return decorated
