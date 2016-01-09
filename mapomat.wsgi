from mapomat import create_app

application = create_app()

# Get better logs in apache by propagation exceptions
# AFAIK they will NOT be shown to the user by mod_wsgi
application.config['PROPAGATE_EXCEPTIONS']=True

if __name__ == "__main__":
    application.run(debug=True)
