# mapomatv2

How to use:

1. Install everything in a subfolder of /var/www/mapomat (to avoid access problems with apache)
2. Install requirements in virtual environment

    pip install -r requirements.txt

3. Install mapomat itself, too (needed for wsgi)

    pip install ./

4. Edit config to add path where apache will serve the .kml files
