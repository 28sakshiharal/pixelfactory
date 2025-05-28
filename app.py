from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from forms import RegisterForm, LoginForm, JobForm, ApplyForm
from models import db, User, Job, Application
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobportal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

csrf = CSRFProtect(app)
db.init_app(app)
# db = SQLAlchemy(app)

@app.before_request
def create_tables():
        db.create_all()

@app.route('/')
def index():
    jobs = Job.query.all()
    return render_template('index.html', jobs=jobs)
    # search_query = request.args.get('search', '')
    # if search_query:
    #     jobs = Job.query.filter(Job.title.ilike(f'%{search_query}%')).all()
    # else:
    #     jobs = Job.query.all()
    # return render_template('index.html', jobs=jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_pw, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Logged in successfully', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    jobs = Job.query.all() if user.role == 'seeker' else None
    return render_template('dashboard.html', user=user, jobs=jobs)

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if session.get('role') != 'employer':
        flash('Only employers can post jobs', 'danger')
        return redirect(url_for('dashboard'))
    form = JobForm()
    if form.validate_on_submit():
        job = Job(title=form.title.data, description=form.description.data,
                  salary=form.salary.data, location=form.location.data, company=form.company.data)
        db.session.add(job)
        db.session.commit()
        flash('Job posted', 'success')
        return redirect(url_for('index'))
    return render_template('post_job.html', form=form)

@app.route('/my-jobs')
def my_jobs():
    if session.get('role') != 'employer':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    jobs = Job.query.filter_by(company=session['user_id']).all()
    return render_template('my_jobs.html', jobs=jobs)

@app.route('/job/<int:job_id>', methods=['GET', 'POST'])
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    form = ApplyForm()
    if form.validate_on_submit() and session.get('role') == 'seeker':
        application = Application(cover_letter=form.cover_letter.data, user_id=session['user_id'], job_id=job_id)
        db.session.add(application)
        db.session.commit()
        flash('Application submitted', 'success')
    return render_template('job_detail.html', job=job, form=form)

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        flash('Admin access only', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    print("Users data", users)
    jobs = Job.query.all()
    print("Jobs", jobs)
    return render_template('admin.html', users=users, jobs=jobs)

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin':
        flash('Admin access only', 'danger')
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete_job/<int:job_id>')
def delete_job(job_id):
    if session.get('role') != 'admin':
        flash('Admin access only', 'danger')
        return redirect(url_for('dashboard'))
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted', 'success')
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)