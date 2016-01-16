# mapomatv2

Welcome to Map-o-Mat, a little application to display map overlays created with data from the [yelp database challenge](http://www.yelp.com/dataset_challenge)

You can check it out [here](http://www.afternoondelight.de/mapomat) or follow the guide below to run it on your own server

1. Basic setup

  This guide follows the [flask documentation](http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/), but is a little more explicit.
  We will:

  * use a separate user and group for security reasons
  * install all requirements and the app in a virtual environment
  * run it with apache2 and mod_wsgi

2. User and directory setup

  For our example we created a user *mapomat* and added him to a new group *mapomat*. We also created a home directory for the user at /home/mapomat

  In this directory we create a python virtual environment in *venv* and clone this repository into *src*

  **Complete structure**
  ```
  /home
      /mapomat
          /venv
          /src
              /mapomat.wsgi
              ...
  ```

3. Install requirements and app in virtual environment

  ```
  cd /home/mapomat
  source venv/bin/activate

  cd src
  pip install -r requirements.txt
  pip install ./
  ```

  At this point make sure that all the directories and sub directories belong to the user mapomat. If necessary:

  ```
  cd /home
  sudo chown -R mapomat:mapomat mapomat
  ```

4. Configure apache

  The easiest way to run a flask on apache is mod_wsgi, so first make sure it is installed

  Then create a config file in /etc/apache2/sites-available to configure mod_wsgi (and link it to our virtual environment instead of the default python)

  Example:

  **/etc/apache2/sites-available/mapomat**
  ```
  <VirtualHost *>
      WSGIDaemonProcess mapomat \
          python-path=/home/mapomat/venv/lib/python2.7/site-packages \
          user=mapomat group=mapomat
      WSGIScriptAlias /mapomat /home/mapomat/src/mapomat.wsgi

      <Directory /home/mapomat/src>
          WSGIProcessGroup mapomat
          WSGIApplicationGroup %{GLOBAL}
          Order deny,allow
          Allow from all
      </Directory>
  </VirtualHost>
  ```

  If you prefer to deliver the app somewhere else than *yourdomain*/mapomat, adjust the *WSGIScriptAlias* above


  *Our server only had python 2 available, but you can run it with python 3 as well, just change the python-path in the config above*

  Now use apache2 tools to enable the site

  ```
  a2ensite mapomat
  service apache 2 restart
  ```

