# What is Wurstgulasch?
Wurstgulasch aims to be a decentral (kind of) social blog application, i.e. a social "network" minus the annoying parts. 

Features include:
  * Easy setup
  * Posting, reposting and following
  * Designed with extensibility in mind (Add new content types easily!)

Planned Features (decreasingly ordered by importance):
  * Replies, Reply-Threads
  * Bookmarklets (repost from another instance, follow a user from another instance, ...)
  * Notifications via E-Mail and XMPP

# Installation

## Dependencies

wurstgulasch depends on:
  * werkzeug
  * jinja2
  * PIL
  * sqlalchemy
  * wtforms
  * beaker


## Development instance

1. Clone the git repo

   ```
   $ git clone https://github.com/SFTtech/wurstgulasch.git
   ```
   
2. Initialize the Database

   ```
   $ ./wurstgulasch.py initdb
   ```

3. Run the server

   ```
   $ ./wurstgulasch.py runserver
   ```
   
4. You're Done! Point your favorite browser at http://localhost:5000 and ejoy! The admin login is ```admin``` with the password ```admin```.
   
## Production instance

**Waning**: You should not use Wurstgulasch in production or encourage your friends to use it in any other way than experimantation. This is because the project is still in a very early stage of development which means that API, UI and Database are very likely to be changed beyond recogintion let alone compatibility with future versions.

Now that we have this out of the way, there are two major options for running wurstgulasch, both of which have their advantages and disadvantages:

### WSGI

Wurstgulasch is built on top of the Werkzeug WSGI Toolkit, so WSGI is it's native habitat. Unfortunately, of the major webservers only Apache supports WSGI (with ```mod_wsgi```).

If you run apache, you probably already know what to do, so here's the vhosts file (tested on a Funtoo machine)

```
 <VirtualHost *>
     ServerName example.com

     WSGIDaemonProcess wurstgulasch user=http group=http processes=1 threads=1
     WSGIScriptAlias / /srv/http/wurstgulasch/wurstgulasch.wsgi

     Alias /static /srv/http/wurstgulasch/static
     Alias /assets /srv/http/wurstgulasch/assets

     <Directory /srv/http/wurstgulasch>
         WSGIProcessGroup wurstgulasch
         WSGIApplicationGroup %{GLOBAL}
         Order deny,allow
         Allow from all
     </Directory>
 </VirtualHost>
```

### FCGI

If you don't run apache, this is currently your best shot. Here's the deal: You run a WSGI-enabled webserver with a FCGI Socket that magically connects to your Webserver. Sounds stupid and wasteful in terms of RAM? That's because it is. Anyways, install ```flup``` and somehow point your Webserver at the ```wurstgulasch.fcgi``` file. Good Luck!


# Hacking
Naturally, Wurstgulasch is nowhere near being complete. But since it's in pure Python, participating is really easy.

Just edit any python file, the werkzeug webserver will see it and restart the application. If it doesn't, you made a serious boo-boo in the top-level namespace (In this case, you'll find a fairly explicit stack trace in the terminal you started it from

If something fails during a request, due to its nature, the Server will continue running and give you an interactive shell in the context of the occurred error IN YOUR EFF'IN BROWSER! How awesome is that?

If you want to mess around with the internals (especially the database), you can also run the werkzeug shell.

```
$ ./wurstgulasch.py shell
```
Now, you have an interactive Werkzeug Shell with the following context:
  * A ready-to-go ```Wurstgulasch```-Object called ```wurstgulasch```
  * The ```model``` module already included as ```model```
