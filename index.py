#coding:utf-8
from flask import Flask,request,render_template,redirect,flash,current_app,session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
import os
import datetime
import markdown as markdown

#================== init app ================
app = Flask(__name__)

class MyConfig(object):
    DEBUG = True
    SECRET_KEY = os.urandom(16)
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024    #允许上传文件大小 2MB

    SQLALCHEMY_DATABASE_URI = 'sqlite:///'+os.path.join(app.root_path,'./data/data.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    ADMINNAME = "admin"
    ADMINPW = generate_password_hash("adminpw")



app.config.from_object(MyConfig)
db = SQLAlchemy(app)
#================== Modles ===================

class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer,primary_key=True)
    category = db.Column(db.String(20),nullable=False)  # *
    createTime = db.Column(db.DateTime) # *
    title = db.Column(db.String(200),nullable=False)    # *
    headerImg = db.Column(db.String(255),nullable=False)    # *
    weather = db.Column(db.String(20),nullable=False)   # *
    thinking = db.Column(db.Text,nullable=False)    # *
    doLocation = db.Column(db.String(50),nullable=False)    # *
    content = db.Column(db.Text)    # *
    scan = db.Column(db.Integer)    # *
    doTime = db.Column(db.Date) # movie,music
    score = db.Column(db.Float) # movie,music
    tags = db.Column(db.String(100))    # *

'''
class Tag(db.Model):
    __tablename__ == "tag"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50))
'''

class WebInfo(db.Model):
    __tablename__ = "websiteConfig"
    id = db.Column(db.Integer,primary_key=True)
    myInfo = db.Column(db.Text,nullable=False)
    bgm = db.Column(db.String(255))
    blogName = db.Column(db.String(40))
#================== forms ===================

#================== template func ================
def showTime(dt):
    '''在模板显示datetime日期格式，2019-08-28 15:45'''
    try:
        dt = str(dt)
        result = dt.split(" ")[0]+" "+":".join(dt.split(" ")[1].split(":")[:2])
    except:
        result = ""
    return result

def get_visitor():
    '''获取浏览者'''
    try:
        with open(os.path.join(app.root_path,"data/visitor.txt")) as f:
            visitor = int(f.read())
    except:
        visitor = 1
    with open(os.path.join(app.root_path,"data/visitor.txt"),"w") as f:
        f.write(str(visitor + 1))
    return visitor
tagsDict = {
        "lifeTime":"路过",
        "movie":"影音",
}

app.add_template_global(showTime,"showTime")
app.add_template_global(get_visitor,"get_visitor")
app.add_template_global(tagsDict,"tagsDict")
app.add_template_global(markdown,"markdown")
#=================== route =======================
from functools import wraps
#管理员登录
def is_login(func):
    @wraps(func)
    def inner(*args,**kwargs):
        #user = session.get('userName')
        if not session.get('userName'):
            return redirect('/login')
        return func(*args,**kwargs)
    return inner

@app.route("/")
def index():
    def get_tags():
        tags = set([i.tags.strip() for i in Post.query.all() if i.tags])
        result = []
        for i in tags:
            tagList = i.split(" ")
            if len(tagList) > 1:
                for j in tagList:
                    if j.strip():
                        result.append(j.strip())
            else:
                if tagList[0].strip():
                    result.append(tagList[0].strip())
        return set(result)
    page = int(request.args.get("page",1))
    postPages = Post.query.order_by(Post.createTime.desc()).paginate(page,5,error_out=False)
    return render_template("index.html",**locals())

@app.route("/about")
def about():
    webInfo = WebInfo.query.first_or_404()
    return render_template("about.html",**locals())

@app.route("/timeMachine")
def time_machine():
    times = Post.query.all()
    years = list(set([str(i.createTime).split("-")[0] for i in times]))
    years.sort(reverse=True)
    get_article_by_year = lambda year : Post.query.filter(Post.createTime.like('%s%%'%year)).order_by(Post.createTime.desc()).all()
    return render_template("timeMachine.html",**locals())

@app.route("/tags")
def tags():
    tag = request.args.get("tag",None)
    posts = Post.query.filter(Post.tags.like("%%%s%%"%tag)).order_by(Post.createTime.desc()).all()
    return render_template("postFilter.html",**locals())

@app.route("/search")
def search():
    searchValue = request.args.get("searchValue","").strip()
    if not searchValue:
        error = "搜索内容不能为空"
    elif "%" in searchValue:
        error = "注意你的关键字哦"
    else:
        #posts = Post.query.filter(Post.title.like("%%%s%%"%searchValue),Post.content.like("%%%s%%"%searchValue)).order_by(Post.createTime.desc()).all()
        posts = list(db.engine.execute("SELECT * FROM post WHERE title LIKE '%{}%' OR content LIKE '%{}%' ORDER BY createTime desc".format(searchValue,searchValue)))
    return render_template("search.html",**locals())

@app.route("/postDetail/<postId>")
def post_detail(postId):
    try:
        post = Post.query.get(postId)
        post.scan += 1
        tags = post.tags
        db.session.add(post)
        db.session.commit()
    except:
        post = ""
        tag = ""

    def has_prev(pId):   #上一篇
        try:
            postTime = Post.query.get(pId).createTime
            #prevPost = Post.query.filter(Post.createTime < postTime).order_by(Post.createTime.desc()).first()
            prevPost = db.engine.execute("select * from post where createTime < (select createTime from post where id=?) order by createTime desc",(pId,)).fetchone()
        except:
            prevPost = None
        return prevPost
    def has_next(pId):   #下一篇
        try:
            postTime = Post.query.get(pId).createTime
            #nextPost = list(Post.query.filter(Post.createTime > postTime).order_by(Post.createTime)).first()
            nextPost = db.engine.execute("select * from post where createTime > (select createTime from post where id=?) order by createTime asc",(postId,)).fetchone()
        except:
            nextPost = None
        return nextPost
    return render_template("postDetail.html",**locals())
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        userName = request.form["userName"].strip()
        userPw = request.form["userPw"].strip()
        #判断是管理员
        if app.config["ADMINNAME"] == userName and check_password_hash(app.config["ADMINPW"],userPw):
            session["userName"] = userName
            return redirect("/")
        else:
            return "<script>alert('用户名或密码错误');history.go(-1);</script>"
    if session.get("userName",None):
        return redirect("/")
    return render_template("login.html",**locals())

@app.route("/logout")
@is_login
def logout():
    session.pop("userName",None)
    return redirect("/")

@app.route("/admin")
@is_login
def admin():
    return render_template("admin.html",**locals())

#uploadImg
@app.route("/admin/uploadImg",methods=["POST"])
@is_login
def upload_image():
    nowTimeName = datetime.datetime.strftime(datetime.datetime.utcnow()+datetime.timedelta(hours=8),"%Y%m%d%H%M%S")
    f = request.files.get("image")
    fExt = f.filename.split(".")[1]
    imgPath = "static/uploadImages/{}.{}".format(nowTimeName,fExt)
    fName = os.path.join(app.root_path,imgPath)
    f.save(fName)
    import json
    return json.dumps({"data":{"link":"/{}".format(imgPath)}})

@app.route("/adminPostAdd",methods=["GET","POST"])
@is_login
def admin_post_add():
    post = Post()
    today =  datetime.date.today().isoformat()
    if request.method == "POST":
        i = request.form
        post.createTime = datetime.datetime.utcnow()+datetime.timedelta(hours=8)
        post.category = i.get("category")
        post.title = i.get("title")
        post.headerImg = i.get("headerImg")
        post.weather = i.get("weather")
        post.thinking = i.get("thinking")
        post.doLocation = i.get("doLocation")
        post.content = i.get("content")
        post.tags = " ".join([i.strip() for i in i.get("tags").split(" ") if i.strip()])
        post.scan = 0
        if post.category != "lifeTime":
            try:
                post.score = float(i.get("score"))
            except:
                flash("分数必须是数字")
                return redirect("/adminPostAdd")
            try:
                post.doTime = datetime.datetime.strptime(i.get("doTime"),"%Y-%m-%d")
            except:
                flash("日期错误")
                return redirect("/adminPostAdd")
        if post.title and post.headerImg and post.weather and post.thinking and post.doLocation and post.tags:
            db.session.add(post)
            db.session.commit()
            return redirect("/postDetail/{}".format(post.id))
        else:
            flash("数据不能为空")
            return redirect("/adminPostAdd")
    return render_template("adminPostAdd.html",**locals())

@app.route("/adminPostEdit/<postId>",methods=["GET","POST"])
@is_login
def admin_post_edit(postId):
    post = Post.query.get_or_404(postId)
    if request.method == "POST":
        i = request.form
        post.title = i.get("title")
        post.headerImg = i.get("headerImg")
        post.weather = i.get("weather")
        post.thinking = i.get("thinking")
        post.doLocation = i.get("doLocation")
        post.content = i.get("content")
        post.tags = " ".join([i.strip() for i in i.get("tags").split(" ") if i.strip()])
        if post.category != "lifeTime":
            try:
                post.score = float(i.get("score"))
            except:
                flash("分数必须是数字")
                return redirect("/adminPostEdit/{}".format(postId))
            try:
                post.doTime = datetime.datetime.strptime(i.get("doTime"),"%Y-%m-%d")
            except:
                flash("日期错误")
                return redirect("/adminPostEdit/{}".format(postId))
        if post.title and post.headerImg and post.weather and post.thinking and post.doLocation and post.tags:
            db.session.add(post)
            db.session.commit()
        else:
            flash("数据不能为空")
            return redirect("/adminPostEdit/{}".format(postId))
        return redirect("/postDetail/{}".format(postId))
    if post.category == "lifeTime":
        return render_template("adminPostEditLifeTime.html",**locals())
    else:
        return render_template("adminPostEditMovieAndMusic.html",**locals())

@app.route("/adminPostDel/<postId>")
@is_login
def admin_post_del(postId):
    try:
        post = Post.query.get_or_404(postId)
        db.session.delete(post)
        db.session.commit()
        return redirect("/")
    except:
        flash("数据异常")
        return redirect("/postDetail/{}".format(postId))

@app.route("/adminAboutEdit",methods=["GET","POST"])
@is_login
def admin_about_edit():
    about = WebInfo.query.filter(WebInfo.id.like("%%")).first()
    if request.method == "POST":
        about.myInfo = request.form.get("myInfo")
        db.session.add(about)
        db.session.commit()
        return redirect("/about")
    return render_template("adminAboutEdit.html",**locals())

@app.route("/popDiv")
def pip_div():
    return render_template("popDiv.html",**locals())
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")
