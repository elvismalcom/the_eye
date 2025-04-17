from app import app, db, bcrypt
from flask import render_template, request, redirect, url_for, flash, send_file
from models import User, Article, Comment
from flask_login import login_required, login_user, logout_user, current_user
from PIL import Image, ImageDraw, ImageFont
import os
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet

@app.route('/', defaults={'page': 1})
@app.route('/page/<int:page>')
def home(page):
    per_page = 10
    category = request.args.get('category')
    continent = request.args.get('continent')
    search = request.args.get('search')
    articles = Article.query.order_by(Article.date_posted.desc())

    if category and category != 'Home':
        articles = articles.filter_by(category=category)
    if continent:
        articles = articles.filter_by(continent=continent)
    if search:
        search_term = f'%{search}%'
        articles = articles.filter(
            (Article.title.ilike(search_term)) |
            (Article.content.ilike(search_term)) |
            (Article.summary.ilike(search_term)) |
            (Article.country.ilike(search_term)) |
            (Article.category.ilike(search_term))
        )

    total_articles = articles.count()
    articles = articles.paginate(page=page, per_page=per_page, error_out=False)
    for article in articles.items:
        article.image_list = json.loads(article.image_files) if article.image_files else []
    return render_template('index.html', articles=articles.items, pagination=articles, total_articles=total_articles)

@app.route('/article/<int:article_id>', methods=['GET', 'POST'])
def article_detail(article_id):
    article = Article.query.get_or_404(article_id)
    article.views += 1
    db.session.commit()
    if request.method == 'POST' and current_user.is_authenticated:
        if 'content' in request.form:
            content = request.form['content']
            comment = Comment(content=content, user_id=current_user.id, article_id=article.id)
            db.session.add(comment)
            db.session.commit()
        elif 'like' in request.form:
            article.likes += 1
            db.session.commit()
        elif 'dislike' in request.form:
            article.dislikes += 1
            db.session.commit()
    comments = Comment.query.filter_by(article_id=article_id).all()
    article.image_list = json.loads(article.image_files) if article.image_files else []
    return render_template('article.html', article=article, comments=comments)

@app.route('/article/<int:article_id>/download_image/<string:image_name>')
def download_image(article_id, image_name):
    article = Article.query.get_or_404(article_id)
    image_list = json.loads(article.image_files) if article.image_files else []
    if image_name in image_list:
        img_path = os.path.join(app.static_folder, 'images', image_name)
        img = Image.open(img_path).convert("RGBA")
        watermark = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        text = "Created by xAI"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        position = (img.width - text_width - 10, img.height - text_height - 10)
        draw.text(position, text, font=font, fill=(255, 255, 255, 128))
        watermarked_img = Image.alpha_composite(img, watermark)
        buffer = BytesIO()
        watermarked_img.save(buffer, format="PNG")
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"{image_name}_watermarked.png", mimetype='image/png')
    return redirect(url_for('article_detail', article_id=article_id))

@app.route('/article/<int:article_id>/download_pdf')
def download_pdf(article_id):
    article = Article.query.get_or_404(article_id)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph(article.title, styles['Title']),
             Paragraph(article.summary, styles['BodyText']),
             Paragraph(article.content, styles['BodyText'])]
    if article.image_files:
        image_list = json.loads(article.image_files)
        for image_name in image_list:
            img_path = os.path.join(app.static_folder, 'images', image_name)
            story.append(ReportLabImage(img_path, width=400, height=225))
    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{article.title}.pdf", mimetype='application/pdf')

@app.route('/download-apk')
def download_apk():
    apk_path = os.path.join(app.static_folder, 'apks', 'the-eye.apk')
    if os.path.exists(apk_path):
        return send_file(apk_path, as_attachment=True, download_name='the-eye.apk')
    else:
        flash('APK not found. Please contact support.')
        return redirect(url_for('home'))

@app.route('/admin/upload', methods=['GET', 'POST'])
@login_required
def upload_article():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('home'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        continent = request.form['continent']
        country = request.form['country']
        summary = request.form['summary']
        is_hot = 'is_hot' in request.form

        image_files = []
        if 'images' in request.files:
            images = request.files.getlist('images')
            for image in images:
                if image and image.filename:
                    filename = image.filename
                    filepath = os.path.join(app.static_folder, 'images', filename)
                    image.save(filepath)
                    img = Image.open(filepath)
                    img = img.resize((400, 225), Image.Resampling.LANCZOS)
                    img.save(filepath, quality=85)
                    image_files.append(filename)

        video_file = None
        if 'video' in request.files:
            video = request.files['video']
            if video and video.filename:
                video_file = video.filename
                video.save(os.path.join(app.static_folder, 'videos', video_file))

        article = Article(
            title=title,
            content=content,
            category=category,
            continent=continent,
            country=country,
            summary=summary,
            image_files=json.dumps(image_files) if image_files else None,
            video_file=video_file,
            is_hot=is_hot,
            author_id=current_user.id
        )
        db.session.add(article)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('upload.html')

@app.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('home'))
    articles = Article.query.filter_by(author_id=current_user.id).all()
    for article in articles:
        article.image_list = json.loads(article.image_files) if article.image_files else []
    
    admin_activities = []
    if current_user.is_master:
        admins = User.query.filter_by(is_admin=True).all()
        for admin in admins:
            admin_articles = Article.query.filter_by(author_id=admin.id).all()
            for article in admin_articles:
                article.image_list = json.loads(article.image_files) if article.image_files else []
                article.comment_count = Comment.query.filter_by(article_id=article.id).count()
            admin_activities.append({
                'admin': admin,
                'articles': admin_articles
            })

    if current_user.is_master and request.method == 'POST':
        if 'add_admin' in request.form:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            if User.query.filter_by(username=username).first():
                flash('Username already exists.')
            elif User.query.filter_by(email=email).first():
                flash('Email already registered.')
            else:
                new_admin = User(
                    username=username,
                    email=email,
                    password=hashed_password,
                    is_admin=True,
                    is_active=True
                )
                db.session.add(new_admin)
                db.session.commit()
                flash(f'Admin "{username}" added successfully. They can now log in to upload and edit articles.')
        elif 'delete_admin' in request.form:
            admin_id = request.form['admin_id']
            admin = User.query.get_or_404(admin_id)
            if not admin.is_master:
                article_count = Article.query.filter_by(author_id=admin.id).count()
                if article_count > 0:
                    flash(f'Admin "{admin.username}" has {article_count} articles, which will be deleted.')
                db.session.delete(admin)  # Cascade deletes articles due to models.py
                db.session.commit()
                flash('Admin and their articles deleted successfully.')
            else:
                flash('Cannot delete master admin.')
        elif 'deactivate_admin' in request.form:
            admin_id = request.form['admin_id']
            admin = User.query.get_or_404(admin_id)
            if not admin.is_master:
                admin.is_active = False
                db.session.commit()
                flash('Admin deactivated successfully.')
            else:
                flash('Cannot deactivate master admin.')
        elif 'reactivate_admin' in request.form:
            admin_id = request.form['admin_id']
            admin = User.query.get_or_404(admin_id)
            if not admin.is_master:
                admin.is_active = True
                db.session.commit()
                flash('Admin reactivated successfully.')
            else:
                flash('Master admin is already active.')
    admins = User.query.filter_by(is_admin=True).all() if current_user.is_master else []
    return render_template('admin_dashboard.html', articles=articles, admins=admins, admin_activities=admin_activities)

@app.route('/admin/edit/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('home'))
    article = Article.query.get_or_404(article_id)
    if article.author_id != current_user.id and not current_user.is_master:
        flash('You can only edit your own articles.')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        article.title = request.form['title']
        article.content = request.form['content']
        article.category = request.form['category']
        article.continent = request.form['continent']
        article.country = request.form['country']
        article.summary = request.form['summary']
        article.is_hot = 'is_hot' in request.form
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_article.html', article=article)

@app.route('/admin/delete/<int:article_id>', methods=['POST'])
@login_required
def delete_article(article_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('home'))
    article = Article.query.get_or_404(article_id)
    if article.author_id != current_user.id and not current_user.is_master:
        flash('You can only delete your own articles.')
        return redirect(url_for('admin_dashboard'))
    db.session.delete(article)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password) and user.is_active:
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your credentials or account status.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.')
        else:
            user = User(username=username, email=email, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('home'))
    return render_template('register.html')