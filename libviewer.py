
import os
import mimetypes
import hashlib
from PIL import Image
import time
from threading import Thread, Lock, activeCount
import Cookie
from imagemanager import Manager

ver = 1.99
part = '/var/www/site'
db = '/var/www/sqlitedb/images.sqlite'

starttime = time.time()

manager = Manager()

def putdata(form):    
    cookie = Cookie.SimpleCookie()
    try: cookie.load(os.environ['HTTP_COOKIE'])
    except: pass
    if form.has_key('d'):
        value = form['d'].value
        mimetypes.init()
        print "Content-type: text/html; charset=utf8\n\n";
        print '''
<html>
	<head>
		<title>Index of ''' + str(value) + '''</title>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
		<link href="/styles/mainst.css" rel="stylesheet" type="text/css">
        <script type="text/javascript" src="/scripts/sabari.js"></script>
		<style>a img{border: 0px;}</style>
	</head>
	<body>
		<h1>Index of ''' + str(value) + '''</h1>
		<hr>
		<table>
		    <tr>
		        <td class="t1" valign="top" align="center" >
			        <a href=".."><img src="/icon/back.png" width="165" height="165" alt="Parent"><br>Parent Directory</a>
		        </td>
'''
        content = os.listdir(part+value)
        files = []
        td, tr = 1, 0
        try: cols = cookie['viewcols'].value
        except: cols = 4            
        for filename in content:
            if filename.find('.') == 0: continue
            if os.path.isfile(part+value+'/'+filename):
                files.append(filename)
            else:
                if td > cols: td = 0
                print '<td class="' + str(td) + '" valign="top" align="center">'
                print '<a href="' + os.path.join(value,filename) + '/"><img src="/icon/folder.png" width="165" height="165" alt="Dir">'
                print '<br>' + filename + '</a></td>' 
                if td == cols: print '</tr><tr>'
                td += 1
        for filename in files:
            #if filename.find('.') == 0: continue
            if td > cols: td = 0
            filetype = mimetypes.guess_type(filename)[0]
            print '<td valign="top" align="center">' 
            print '<a href="' + os.path.join(value,filename) + '" target="_blank">'
            if filetype and filetype.find('image') >= 0 and filetype.find('djvu') < 0:
                hval = hashlib.md5(os.path.join(value,filename)).hexdigest()
                result, imtype = imagework(hval, filename, part+value)                
                if result == 'ext':
                    print '<img src="/cache/' + hval + imtype + '" alt="img" name="' + hval + '">'
                else:
                    print 'Thumbinal creation.';
            else:
                if filetype:
                    filetype = filetype.replace('/', '-')
                else:
                    filetype = 'text-plain'
                print '<img src="/icon/' + filetype + '.png" width="165" height="165"><br>' + filename
            print '</a></td>'
            if td == cols: print '</tr><tr>'
            td += 1
        print '''</tr>        
</table><hr><p class="ft">
<span style="color: red;">At the end of the month site will be closed presumably for 2-3 weeks <s>due to aids</s> for maintenance
<br>Access to video files temporarily closed</span><br/>
Sabari v %s<br>
Time: %0.5f s.<br>
Original <a href="http://code.google.com/p/sabari/">script</a> by 
<a href="mailto:anthony@adsorbtion.org\">Sir Anthony</a></p>
''' % (ver, time.time() - starttime)     
    while activeCount() > 1: pass
    manager.commit(db)


class ImageCreator(Thread):
    
    lock = Lock()

    def __init__ (self, filename, fpath, spath):
        Thread.__init__(self)
        self.spath = spath
        self.filepath = fpath
        self.filename = filename

    def run(self):
        maxsize = 200
        ext = '.jpg'
        with open(os.path.join(self.filepath, self.filename)) as f:
            im = Image.open(f)
            format = im.format        
            if not format: format = 'JPEG'
            if format == 'PNG': ext = '.png'
            if format == 'GIF': ext = '.gif'
            w,h = im.size
            if h > w:
                w = (float(w)/float(h))*maxsize
                h = maxsize
            else:
                h = (float(h)/float(w))*maxsize
                w = maxsize
            im.thumbnail((int(w),int(h)), Image.ANTIALIAS)
            try: im.save(self.spath + ext, format)
            #TODO: debug
            except IOError: return
            sha1 = hashlib.sha1(f.read()).hexdigest()
            with self.lock:
                manager.addToBase(self.filename, self.filepath, sha1)

def imagework(hval, filename, path):
    cpath = '/var/www/cache/' + hval
    for ext in ('.jpg', '.png', '.gif'):
        if os.path.isfile(cpath + ext):
            return 'ext', ext    
    ImageCreator(filename, path, cpath).start()
    return 'crt', None

