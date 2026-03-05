from flask import Flask, request, jsonify, session as flask_session, abort, send_from_directory, redirect
from flask_cors import CORS
from datetime import datetime, timedelta, date
import requests
import os
import json
import uuid
import hashlib
import hmac
import user_agents
import secrets
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, MentorProfile, OTPCode, University, Faculty, FacultyStat
from models import Subscription, Session, Payment, Notification, Withdrawal
from models import AuthToken, LoginSession, MentorPoint, MentorCertificate, MentorDocument
from models import News, Material

load_dotenv()

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from wtforms import TextAreaField

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')

CORS(app, supports_credentials=True, origins=["http://localhost:5000", "http://127.0.0.1:5000", "*"])
db.init_app(app)

# ============================================
# ADMIN PANEL - TEMPLATESIZ
# ============================================

class UserAdmin(ModelView):
    """Foydalanuvchilar"""
    can_export = True
    can_view_details = True
    create_modal = True
    edit_modal = True
    details_modal = True
    
    column_list = ['id', 'full_name', 'phone', 'telegram_id', 'role', 'is_active', 'created_at']
    column_searchable_list = ['full_name', 'phone', 'telegram_id']
    column_filters = ['role', 'is_active']
    column_sortable = ['id', 'created_at', 'full_name']
    column_default_sort = ('created_at', True)
    
    column_labels = {
        'id': 'ID',
        'full_name': 'Ism',
        'phone': 'Telefon',
        'telegram_id': 'Telegram',
        'role': 'Rol',
        'is_active': 'Faol',
        'created_at': 'Qo\'shilgan'
    }
    
    column_formatters = {
        'role': lambda v, c, m, p: {
            'student': '🎓 Student',
            'mentor': '👨‍🏫 Mentor',
            'admin': '⚡ Admin',
            'superadmin': '👑 Super Admin'
        }.get(m.role, m.role),
        'is_active': lambda v, c, m, p: '✅ Ha' if m.is_active else '❌ Yo\'q',
        'created_at': lambda v, c, m, p: m.created_at.strftime('%d.%m.%Y %H:%M') if m.created_at else '-'
    }
    
    form_columns = ['full_name', 'phone', 'telegram_id', 'username', 'role', 'is_active', 'avatar_url']
    
    form_args = {
        'role': {
            'choices': [
                ('student', '🎓 Student'),
                ('mentor', '👨‍🏫 Mentor'),
                ('admin', '⚡ Admin'),
                ('superadmin', '👑 Super Admin')
            ]
        }
    }
    
    @action('activate', '✅ Faollashtirish', 'Tanlanganlarni faollashtirish?')
    def action_activate(self, ids):
        users = User.query.filter(User.id.in_(ids)).all()
        for user in users:
            user.is_active = True
        db.session.commit()
        return f"{len(users)} ta foydalanuvchi faollashtirildi"
    
    @action('deactivate', '❌ Bloklash', 'Tanlanganlarni bloklash?')
    def action_deactivate(self, ids):
        users = User.query.filter(User.id.in_(ids)).all()
        for user in users:
            user.is_active = False
        db.session.commit()
        return f"{len(users)} ta foydalanuvchi bloklandi"

class MentorAdmin(ModelView):
    """Mentorlar"""
    column_list = ['id', 'user_name', 'university', 'faculty', 'is_verified', 'balance', 'rating']
    column_searchable_list = ['university', 'faculty']
    column_filters = ['is_verified', 'university']
    
    column_labels = {
        'user_name': 'Mentor',
        'university': 'Universitet',
        'faculty': 'Fakultet',
        'is_verified': 'Tasdiqlangan',
        'balance': 'Balans',
        'rating': 'Reyting'
    }
    
    def _user_name(view, context, model, name):
        user = db.session.get(User, model.user_id)
        return user.full_name if user else '-'
    
    column_formatters = {
        'user_name': _user_name,
        'is_verified': lambda v, c, m, p: '✅ Ha' if m.is_verified else '⏳ Kutilmoqda',
        'balance': lambda v, c, m, p: f"{m.balance or 0:,} so'm",
        'rating': lambda v, c, m, p: f"⭐ {m.rating or 0}/5"
    }
    
    @action('verify', '✅ Tasdiqlash', 'Mentorlarni tasdiqlash?')
    def action_verify(self, ids):
        mentors = MentorProfile.query.filter(MentorProfile.id.in_(ids)).all()
        for mentor in mentors:
            mentor.is_verified = True
            mentor.verified_at = datetime.utcnow()
        db.session.commit()
        return f"{len(mentors)} ta mentor tasdiqlandi"

class UniversityAdmin(ModelView):
    """Universitetlar"""
    column_list = ['short_name', 'full_name', 'is_active', 'sort_order']
    column_searchable_list = ['short_name', 'full_name']
    column_filters = ['is_active']
    
    column_labels = {
        'short_name': 'Qisqa nom',
        'full_name': 'To\'liq nom',
        'is_active': 'Faol',
        'sort_order': 'Tartib'
    }
    
    column_formatters = {
        'is_active': lambda v, c, m, p: '✅ Ha' if m.is_active else '❌ Yo\'q'
    }

class FacultyAdmin(ModelView):
    """Fakultetlar"""
    column_list = ['name', 'university_name', 'quota', 'employment_pct', 'is_active']
    column_searchable_list = ['name']
    column_filters = ['is_active', 'university']
    
    column_labels = {
        'name': 'Nomi',
        'university_name': 'Universitet',
        'quota': 'Kvota',
        'employment_pct': 'Ish bilan bandlik',
        'is_active': 'Faol'
    }
    
    def _university_name(view, context, model, name):
        return model.university.short_name if model.university else '-'
    
    column_formatters = {
        'university_name': _university_name,
        'employment_pct': lambda v, c, m, p: f"{m.employment_pct or 0}%",
        'is_active': lambda v, c, m, p: '✅ Ha' if m.is_active else '❌ Yo\'q'
    }

class SessionAdmin(ModelView):
    """Sessiyalar"""
    column_list = ['id', 'student_name', 'mentor_name', 'session_type', 'status', 'scheduled_at']
    column_filters = ['status', 'session_type']
    
    column_labels = {
        'student_name': 'Student',
        'mentor_name': 'Mentor',
        'session_type': 'Turi',
        'status': 'Holat',
        'scheduled_at': 'Vaqt'
    }
    
    def _student_name(view, context, model, name):
        student = db.session.get(User, model.student_id)
        return student.full_name if student else '-'
    
    def _mentor_name(view, context, model, name):
        mentor = db.session.get(MentorProfile, model.mentor_id)
        if mentor:
            user = db.session.get(User, mentor.user_id)
            return user.full_name if user else '-'
        return '-'
    
    column_formatters = {
        'student_name': _student_name,
        'mentor_name': _mentor_name,
        'status': lambda v, c, m, p: {
            'pending': '⏳ Kutilmoqda',
            'confirmed': '✅ Tasdiqlangan',
            'completed': '🎉 Yakunlangan',
            'cancelled': '❌ Bekor'
        }.get(m.status, m.status),
        'session_type': lambda v, c, m, p: {
            'free': '🎁 Bepul',
            'individual': '👤 Individual',
            'group': '👥 Guruh'
        }.get(m.session_type, m.session_type)
    }

class PaymentAdmin(ModelView):
    """To'lovlar"""
    column_list = ['id', 'user_name', 'amount', 'method', 'status', 'created_at']
    column_filters = ['status', 'method']
    
    column_labels = {
        'user_name': 'Foydalanuvchi',
        'amount': 'Summa',
        'method': 'Usul',
        'status': 'Holat',
        'created_at': 'Vaqt'
    }
    
    def _user_name(view, context, model, name):
        user = db.session.get(User, model.user_id)
        return user.full_name if user else '-'
    
    column_formatters = {
        'user_name': _user_name,
        'amount': lambda v, c, m, p: f"{m.amount:,} so'm",
        'status': lambda v, c, m, p: {
            'pending': '⏳ Kutilmoqda',
            'success': '✅ To\'langan',
            'failed': '❌ Xatolik'
        }.get(m.status, m.status)
    }

class SubscriptionAdmin(ModelView):
    """Obunalar"""
    column_list = ['student_name', 'tier', 'status', 'price', 'expires_at']
    column_filters = ['tier', 'status']
    
    column_labels = {
        'student_name': 'Student',
        'tier': 'Tarif',
        'status': 'Holat',
        'price': 'Narx',
        'expires_at': 'Tugash vaqti'
    }
    
    def _student_name(view, context, model, name):
        student = db.session.get(User, model.student_id)
        return student.full_name if student else '-'
    
    column_formatters = {
        'student_name': _student_name,
        'tier': lambda v, c, m, p: {
            'free': '🎁 Bepul',
            'basic': '🔰 Basic',
            'elite': '💎 Elite',
            'group': '👥 Group'
        }.get(m.tier, m.tier),
        'price': lambda v, c, m, p: f"{m.price:,} so'm",
        'status': lambda v, c, m, p: {
            'active': '✅ Faol',
            'pending': '⏳ Kutilmoqda',
            'cancelled': '❌ Bekor'
        }.get(m.status, m.status)
    }

class NewsAdmin(ModelView):
    """Yangiliklar"""
    column_list = ['title', 'created_at', 'is_published']
    column_searchable_list = ['title']
    
    column_labels = {
        'title': 'Sarlavha',
        'created_at': 'Vaqt',
        'is_published': 'Chop etilgan'
    }
    
    form_overrides = {
        'content': TextAreaField
    }
    
    column_formatters = {
        'is_published': lambda v, c, m, p: '✅ Ha' if m.is_published else '❌ Yo\'q'
    }

# Dashboard uchun inline HTML
@app.route('/superadmin/dashboard')
def admin_dashboard():
    stats = {
        'users': User.query.count(),
        'students': User.query.filter_by(role='student').count(),
        'mentors': MentorProfile.query.count(),
        'verified_mentors': MentorProfile.query.filter_by(is_verified=True).count(),
        'universities': University.query.count(),
        'sessions': Session.query.count(),
        'pending_mentors': MentorProfile.query.filter_by(is_verified=False).count(),
        'today_sessions': Session.query.filter(
            db.func.date(Session.created_at) == date.today()
        ).count()
    }
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Super Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background: #f5f5f5; }}
            .stats-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 20px;
                transition: 0.3s;
            }}
            .stats-card:hover {{ transform: translateY(-5px); }}
            .stats-number {{ font-size: 2.5em; font-weight: bold; }}
            .navbar {{ background: #2c3e50 !important; }}
            .navbar-brand {{ color: white !important; font-size: 1.5em; }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark mb-4">
            <div class="container-fluid">
                <span class="navbar-brand">👑 ConnectU Super Admin</span>
                <div>
                    <a href="/superadmin" class="btn btn-outline-light btn-sm">Admin panel</a>
                </div>
            </div>
        </nav>
        
        <div class="container-fluid">
            <div class="row mb-4">
                <div class="col-12">
                    <h1>Dashboard</h1>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-3">
                    <div class="stats-card">
                        <div class="stats-number">{stats['users']}</div>
                        <div>Jami foydalanuvchilar</div>
                        <small>🎓 Student: {stats['students']} | 👨‍🏫 Mentor: {stats['mentors']}</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                        <div class="stats-number">{stats['mentors']}</div>
                        <div>Mentorlar</div>
                        <small>✅ Tasdiqlangan: {stats['verified_mentors']}</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                        <div class="stats-number">{stats['sessions']}</div>
                        <div>Sessiyalar</div>
                        <small>📅 Bugun: {stats['today_sessions']}</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                        <div class="stats-number">{stats['universities']}</div>
                        <div>Universitetlar</div>
                        <small>🏛 Fakultetlar bilan</small>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0">⚡ Tezkor harakatlar</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <a href="/superadmin/user/new/" class="btn btn-outline-primary">➕ Yangi foydalanuvchi</a>
                                <a href="/superadmin/mentorprofile/new/" class="btn btn-outline-success">➕ Yangi mentor</a>
                                <a href="/superadmin/university/new/" class="btn btn-outline-info">➕ Yangi universitet</a>
                                <a href="/superadmin/news/new/" class="btn btn-outline-warning">📰 Yangilik qo'shish</a>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-warning">
                            <h5 class="mb-0">⏳ Kutilayotganlar</h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-group">
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    Tasdiqlanmagan mentorlar
                                    <span class="badge bg-primary rounded-pill">{stats['pending_mentors']}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    Kutilayotgan to'lovlar
                                    <span class="badge bg-primary rounded-pill">0</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0">📊 Modellar ro'yxati</h5>
                        </div>
                        <div class="card-body">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Model</th>
                                        <th>Soni</th>
                                        <th>Amallar</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>👥 Foydalanuvchilar</td>
                                        <td>{stats['users']}</td>
                                        <td><a href="/superadmin/user/" class="btn btn-sm btn-primary">Ko'rish</a></td>
                                    </tr>
                                    <tr>
                                        <td>👨‍🏫 Mentorlar</td>
                                        <td>{stats['mentors']}</td>
                                        <td><a href="/superadmin/mentorprofile/" class="btn btn-sm btn-primary">Ko'rish</a></td>
                                    </tr>
                                    <tr>
                                        <td>🏛 Universitetlar</td>
                                        <td>{stats['universities']}</td>
                                        <td><a href="/superadmin/university/" class="btn btn-sm btn-primary">Ko'rish</a></td>
                                    </tr>
                                    <tr>
                                        <td>📚 Fakultetlar</td>
                                        <td>{Faculty.query.count()}</td>
                                        <td><a href="/superadmin/faculty/" class="btn btn-sm btn-primary">Ko'rish</a></td>
                                    </tr>
                                    <tr>
                                        <td>📅 Sessiyalar</td>
                                        <td>{stats['sessions']}</td>
                                        <td><a href="/superadmin/session/" class="btn btn-sm btn-primary">Ko'rish</a></td>
                                    </tr>
                                    <tr>
                                        <td>💳 Obunalar</td>
                                        <td>{Subscription.query.count()}</td>
                                        <td><a href="/superadmin/subscription/" class="btn btn-sm btn-primary">Ko'rish</a></td>
                                    </tr>
                                    <tr>
                                        <td>💰 To'lovlar</td>
                                        <td>{Payment.query.count()}</td>
                                        <td><a href="/superadmin/payment/" class="btn btn-sm btn-primary">Ko'rish</a></td>
                                    </tr>
                                    <tr>
                                        <td>📰 Yangiliklar</td>
                                        <td>{News.query.count()}</td>
                                        <td><a href="/superadmin/news/" class="btn btn-sm btn-primary">Ko'rish</a></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

# Admin panel yaratish - template_mode PARAMETRISIZ!
admin = Admin(
    app, 
    name="👑 ConnectU Super Admin", 
    url="/superadmin"
    # template_mode olib tashlandi!
)

# Modellarni qo'shish
admin.add_view(UserAdmin(User, db.session, name="👥 Foydalanuvchilar"))
admin.add_view(MentorAdmin(MentorProfile, db.session, name="👨‍🏫 Mentorlar"))
admin.add_view(UniversityAdmin(University, db.session, name="🏛 Universitetlar"))
admin.add_view(FacultyAdmin(Faculty, db.session, name="📚 Fakultetlar"))
admin.add_view(ModelView(FacultyStat, db.session, name="📊 Statistika"))
admin.add_view(SessionAdmin(Session, db.session, name="📅 Sessiyalar"))
admin.add_view(SubscriptionAdmin(Subscription, db.session, name="💳 Obunalar"))
admin.add_view(PaymentAdmin(Payment, db.session, name="💰 To'lovlar"))
admin.add_view(ModelView(Withdrawal, db.session, name="💵 Pul yechish"))
admin.add_view(NewsAdmin(News, db.session, name="📰 Yangiliklar"))
admin.add_view(ModelView(Material, db.session, name="📁 Materiallar"))
admin.add_view(ModelView(OTPCode, db.session, name="🔐 OTP Kodlar"))
admin.add_view(ModelView(LoginSession, db.session, name="🔑 Login sessiyalar"))
admin.add_view(ModelView(AuthToken, db.session, name="🎟 Tokenlar"))

# ============================================
# ASOSIY ROUTELAR
# ============================================

with app.app_context():
    db.create_all()

BOT_TOKEN = Config.BOT_TOKEN
MINI_APP_URL = "http://localhost:5000"

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return redirect('/superadmin')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory('uploads', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/health')
def health():
    return 'OK', 200

def send_telegram_message(telegram_id, text):
    print(f"📱 TELEGRAM: {telegram_id} -> {text}")
    return True

# ============================================
# SIZNING BARCHA API ROUTELARINGIZ SHU YERDA
# ============================================
# @app.route('/api/telegram-login', methods=['POST'])
# @app.route('/api/send-otp', methods=['POST'])
# ... va hokazo

if __name__ == '__main__':
    print("="*60)
    print("🚀 ConnectU Super Admin Panel ishga tushmoqda...")
    print("="*60)
    print(f"👑 Super Admin: http://localhost:5000/superadmin")
    print(f"📊 Dashboard: http://localhost:5000/superadmin/dashboard")
    print("="*60)
    app.run(host='127.0.0.1', port=5000, debug=True)