# Briefing

## Main components
- Flask - Backend support
- Bootstrap - Frontend support
- SQLite - Light weight, disk access management
- Gunicorn - Development server
- Supervisor - Process monitor
- Nginx - HTTP server

## Scheduled tasks
- Update dictionary for search engine whooshee
```
(venv) $ flask shell
>>> from app import whooshee
>>> whooshee.reindex()
```
- Update translation files
```
(venv) $ pybabel extract -F babel.cfg -k _l -o messages.pot .
(venv) $ pybabel init -i messages.pot -d app/translations -l zh
creating catalog app/translations/es/LC_MESSAGES/messages.po based on messages.pot
(venv) $ pybabel compile -d app/translations
compiling catalog app/translations/es/LC_MESSAGES/messages.po to
app/translations/zh/LC_MESSAGES/messages.mo
```
- Update project by Git
```
(venv) $ git pull                              # download the new version
# to abandon your local changes type these:
# git reset --hard
# git pull
# or you wanna backup all changes:
# git stash
# git pull
# git stash pop
(venv) $ flask db migrate -m 'comment'         # migrate if needed
(venv) $ flask db upgrade                      # upgrade the database
```

## Server Init Checking
```
$ passwd # change default account password
$ vi /etc/profile # prompt timeout setup, add this line
export TMOUT=600
$ vi /etc/sysctl.conf # Ping forbidden, add this line
net.ipv4.icmp_echo_ignore_all=1
$ vi /etc/pam.d/system-auth # sys lockup in case of login failure
auth required  pam_tally2.so onerr=fail deny=5 unlock_time=300
$ usermod -G wheel  win2user #把win2user 加到whell组 限制su为root的用户，
$ vi /etc/pam.d/su # add these lines
auth required  pam_wheel.so use_uid
auth required pam_wheel.so group=wheel
authconfig --passminlen=8 --update # limit the password length
grep "^minlen" /etc/security/pwquality.conf # 8 will appear here
#开启系统日志、开启防火墙
```

## Deployment on CentOS 7
To setup the website on a clean CentOS 7 system, follow these lines"
```
$ yum -y install python3 python3-venv python3-dev
# python-venv may be included in python. try python3-devel as alternative
$ yum -y install supervisor nginx git
# yum -y install epel-release
# incase you do not have the source for nginx/supervisor
~$ cd /home
$ git clone https://github.com/ian-quinn/pancake.git
$ cd pancake
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```
requirements.txt lists all dependencies:
```
Flask==1.1.1
# Werkzeug 0.16.0 # Click 7.0 # Jinja2 2.10.1 # itsdangerous 1.1.0 
# MarkupSafe 1.1.1
Flask-WTF==0.14.2
# WTForms 2.2.1
Flask-SQLAlchemy==2.4.0
# SQLALchemy 1.3.8
Flask-Migrate==2.5.2
# Mako 1.1.0 # alembic 1.1.0 # python-dateutil 2.8.0 
# python-editor 1.0.4 # six 1.12.0
Flask-Babel==0.12.2
# Babel 2.7.0 # pytz 2019.2
Flask-Moment==0.9.0
Flask-SimpleMDE==0.3.0
Flask-Dropzone==1.5.4
Flask-Login==0.4.1
Flask-HTTPAuth==3.3.0
Flask-whooshee==0.7.0
# Whoosh-2.7.4 # blinker-1.4
Flask-mail==0.9.1
Flask-Avatars==0.2.2
Flask-Bootstrap==3.3.7.1
# dominate 2.4.0 # visitor 0.1.3
elasticsearch==7.1.0
beautifulsoup4==4.8.2
mistune==0.8.4
Pillow==6.1.0
python-dotenv==0.10.3
pypinyin==0.35.4
PyJWT==1.7.1
```
Should any parsing error happen, check if all the packages follow the corresponding version in this list. During installation, Werkzeug may be updated to 1.0.0 which is not supported by Flask-WTF, so you have to degrade it to 0.16.0.
```
# initiate database
(venv) $ flask db init
(venv) $ flask db migrate -m 'init'
(venv) $ flask db upgrade
(venv) $ flask run
# check if FLASK operates on port 5000. Ctrl~C to quit
(venv) $ pip install gunicorn
(venv) $ gunicorn -b localhost:8000 -w 4 pan:app
# check if Gunicorn works fine. Ctrl~C to quit
(venv) $ deactivate
$ chmod o+w /etc/supervisord.d
$ cp /home/pancake/deployment/supervisor/pancake.ini /etc/supervisord.d/pancake.ini
# configure Supervisor. this may not be the directory in your case
$ chmod o+w /etc/nginx/conf.d
$ cp /home/pancake/deployment/nginx/pancake.conf /etc/nginx/conf.d/pancake.conf
# configure Nginx. this may not be your configuration path
$ mkdir certs
$ openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
$ -keyout certs/key.pem -out certs/cert.pem
$ cd\
# add self-signed SSL certificate under /home/pancake
$ systemctl restart supervisord
$ systemctl restart nginx
```
The Nginx should be running right now and expose your website via 443 port (https). Something else need to check in case of various different server settings. Useful commands for you to do that:
```
$ supervisorctl # get in console to check applications hosted
pan				RUNNING		pid 2581, uptime 1:02:50
supervisor> Ctrl~C
$ curl 'localhost:8000' # check running stat of Supervisord
$ curl 'localhost' # check if application is exposed to port 80 by Nginx
$ nginx -t # check parsing errors of nginx.conf
```

**Firewall** If firewall cannot be dismentled and must be set, make sure all ports are served:
```
$ systemctl start firewalld
$ firewall-cmd --zone=public --list-ports # if None add these
$ firewall-cmd --zone=public --add-port=22/tcp --permanent
$ firewall-cmd --zone=public --add-port=80/tcp --permanent
$ firewall-cmd --zone=public --add-port=443/tcp --permanent
# make sure the service is on
$ firewall-cmd --get-services # if only ssh and dhcpv6-client you need:
$ firewall-cmd --permanent --add-service=http
$ firewall-cmd --permanent --add-service=ftp
$ firewall-cmd --list-services
# commands you may find useful
$ systemctl disable firewalld # temporarily shut down for test
$ systemctl status firewalld
$ systemctl restart firewalld.service
```
**SELinux**
```
# Allow file access to certain directory may not work for flask app... should disable it directly
# chcon -R -t httpd_sys_content_t /home/pancake/
$ /usr/sbin/sestatus # check the status of SELinux
$ vi /etc/selinux/config
config $ SELINUX=disabled
```
**Port** Gunicorn may mal-function when port 8000 is possessed by another process, just kill it anyway. For example:
```
$ netstat -tulpn
Proto Recv-Q Send-Q Local Address  Foreign Address State  PID/Program name
tcp   0      0      127.0.0.1:8000 0.0.0.0:*       LISTEN 1100/python3
...   ...    ...    ...            ...             ...    ...
$ kill -9 1100
# to check status of all ports use netstat. install net-tools if it not works
# yum -y install net-tools
$ netstat -plunt
```
**Server** Make sure your virtual server opens ports: `22`, `80`, `443`

Afterwards:
```
$ systemctl enable supervisord
Created symlink from /etc/systemd/system/multi-user.target.wants/supervisord.service to /usr/lib/systemd/system/supervisord.service.
$ systemctl enable nginx
```
Supervisord log file by default: /var/log/supervisor/supervisord.log
Supervisord conf file: /etc/supervisord.conf

--------

Configuration details:
```
# /etc/supervisord.d/pancake.ini
[program:pan]
command=/home/pancake/venv/bin/gunicorn -b localhost:8000 -w 4 pan:app
directory=/home/pancake
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
```
```
# /etc/nginx/conf.d/pancake_443.conf
# http {} upper level settings
client_max_body_size 500m;
client_max_body_size 200m;
client_header_timeout 60; 
client_body_timeout 60;
proxy_connect_timeout 60;
proxy_send_timeout 60;
proxy_read_timeout 60;
keepalive_timeout 1200;

server {
    # listen on port 80 (http)
    listen 80;
    server_name bsim.tongji.edu.cn;
    # write access and error logs to /var/log
    access_log /var/log/pan_access.log;
    error_log /var/log/pan_error.log;
    location / {
        # forward application requests to the gunicorn server
        proxy_pass http://localhost:8000;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /static {
        # handle static files directly, without forwarding to the application
        alias /home/pancake/app/static;
        expires 30d;
    }
}

```

## Future plans
More extensions are in development to add more functions, which will be deployed on Aliyun ECS. 
- **Pancake** is for caching sample models or mature tutorials, just like [Hydra](https://hydrashare.github.io/hydra/). All projects displayed in pigeon holes stored with sample files, videos and comments supported.
- **Spaghetti** is a dynamic battery chart to show the relationships among platform, engine, software and plugins, powered by javascripts. The information will be grabbed automatically from official websites.
- **Marshball** will be a cloud energy simulation platform for testing. A WebGL modeling interface helps with your basic modeling and teaching work.

## Updates log
**Bugs**
- [x] .docx files are skimed out in the Bookshelf page. + Restrict file types uploading and retrieving
- [x] Posts cannot be accessed by browser on portable devices showing Internal Server Error. Locale toggle will not appear on certain browsers like 360. + Reprogram the logic of function `get_locale()`
- [x] Baidu map API failed. + Use img for stable access.
- [x] Bootstrap Calendar showing the last year. + Filter events within 6 months at server side
- [ ] Cannot retrieve text via Ajax when it is too long, Post page
- [x] Add Optional validator to Profile settings, google scholar url
- [x] Pagination buttons spread out of the div
- [x] Some flashes are not assigned with types

**Uplifts**
- [x] Downsize some vendor dependencies: moment.js and phoswipe.js. Remove sidebarScroll.js
- [x] Support blocking documents of projects by adding Document Model. Add project category selection.
- [x] Easy visiting. Update favicon.ico, stop carousels, cancel animation sliding...
- [x] Add thumbnails to photos under News and Album +
- [ ] Cancel lazy-loading and use scroll-loading, add thumbnails, People page
- [ ] Refurbishment of Homepage
- [ ] Refurbishment of Profile page
- [x] Add additional Album page with grid view
- [x] Allow citation input on Pub page and download on search result page
- [ ] Multiple highlights of whooshee's search result
- [ ] Reconstruction blueprint for further extension of modules
- [ ] Consider sub-page loading papers
- [x] Allow to change information of papers
- [x] Cancel restrictions on paper submit