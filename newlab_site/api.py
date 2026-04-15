import frappe
import re
from frappe.utils import formatdate
from frappe.utils.file_manager import save_file
import json
import base64
from frappe.auth import LoginManager
from frappe.utils import get_request_site_address
import zipfile
import io
import os
from frappe.utils import get_site_path
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
import urllib.parse
from urllib.parse import unquote, urlparse, parse_qs
from frappe.utils import today
try:
    import pdfplumber
except ImportError:
    pass

def _get(doc, field):
    """Helper to safely get field value"""
    return getattr(doc, field, "") or ""

def _list_from_text(text):
    """Convert newline separated text to list"""
    if not text: return []
    return [t.strip() for t in text.split('\n') if t.strip()]

def _list_from_comma(text):
    """Convert comma separated text to list"""
    if not text: return []
    return [t.strip() for t in text.split(',') if t.strip()]

@frappe.whitelist(allow_guest=True)
def get_landing_page():
    doc = frappe.get_single("SS Landing Page")
    
    # --- 1. Hero Section ---
    hero_indicators_ar = []
    hero_indicators_en = []
    for row in (doc.hero_indicators or []):
        if row.text_ar: hero_indicators_ar.append(row.text_ar)
        if row.text_en: hero_indicators_en.append(row.text_en)

    hero_images = [row.image for row in (doc.hero_images or []) if row.image]

    hero = {
        "kicker_en": _get(doc, "hero_kicker_en"),
        "kicker_ar": _get(doc, "hero_kicker_ar"),
        "title_en": _get(doc, "hero_title_en"),
        "title_ar": _get(doc, "hero_title_ar"),
        "accent_en": _get(doc, "hero_accent_en"),
        "accent_ar": _get(doc, "hero_accent_ar"),
        "description_en": _get(doc, "hero_description_en"),
        "description_ar": _get(doc, "hero_description_ar"),
        "primaryCta_en": _get(doc, "hero_cta_1_en"),
        "primaryCta_ar": _get(doc, "hero_cta_1_ar"),
        "primaryCtaUrl": _get(doc, "hero_cta_1_url"),
        "secondaryCta_en": _get(doc, "hero_cta_2_en"),
        "secondaryCta_ar": _get(doc, "hero_cta_2_ar"),
        "secondaryCtaUrl": _get(doc, "hero_cta_2_url"),
        "statusIndicators_en": hero_indicators_en,
        "statusIndicators_ar": hero_indicators_ar,
        "slideshowImages": hero_images
    }

    # --- 2. About Section ---
    about_cards = []
    for card in (doc.about_cards or []):
        about_cards.append({
            "tag_en": _get(card, "tag_en"),
            "tag_ar": _get(card, "tag_ar"),
            "title_en": _get(card, "title_en"),
            "title_ar": _get(card, "title_ar"),
            "description_en": _get(card, "desc_en"),
            "description_ar": _get(card, "desc_ar"),
            "image": _get(card, "image"),
            "badges_en": _list_from_comma(_get(card, "badges_en")),
            "badges_ar": _list_from_comma(_get(card, "badges_ar"))
        })

    about = {
        "badge_en": _get(doc, "about_badge_en"),
        "badge_ar": _get(doc, "about_badge_ar"),
        "title_en": _get(doc, "about_title_en"),
        "title_ar": _get(doc, "about_title_ar"),
        "description_en": _get(doc, "about_desc_en"),
        "description_ar": _get(doc, "about_desc_ar"),
        "cards": about_cards
    }

    # --- 3. Workflow Section ---
    highlights = []
    for h in (doc.wf_highlights or []):
        highlights.append({
            "title_en": _get(h, "title_en"),
            "title_ar": _get(h, "title_ar"),
            "description_en": _get(h, "desc_en"),
            "description_ar": _get(h, "desc_ar"),
            "icon": _get(h, "icon")
        })

    gallery = []
    for g in (doc.wf_gallery or []):
        gallery.append({
            "src": _get(g, "image"),
            "alt_en": _get(g, "alt_en"),
            "alt_ar": _get(g, "alt_ar")
        })

    workflow = {
        "badge_en": _get(doc, "wf_badge_en"),
        "badge_ar": _get(doc, "wf_badge_ar"),
        "title_en": _get(doc, "wf_title_en"),
        "title_ar": _get(doc, "wf_title_ar"),
        "subtitle_en": _get(doc, "wf_subtitle_en"),
        "subtitle_ar": _get(doc, "wf_subtitle_ar"),
        "coverImage": _get(doc, "wf_cover"),
        "highlights": highlights,
        "qualityBullets_en": _list_from_text(_get(doc, "wf_quality_en")),
        "qualityBullets_ar": _list_from_text(_get(doc, "wf_quality_ar")),
        "galleryImages": gallery,
        "cta": {
            "title_en": _get(doc, "wf_cta_title_en"),
            "title_ar": _get(doc, "wf_cta_title_ar"),
            "description_en": _get(doc, "wf_cta_desc_en"),
            "description_ar": _get(doc, "wf_cta_desc_ar"),
            "buttonLabel_en": _get(doc, "wf_cta_btn_en"),
            "buttonLabel_ar": _get(doc, "wf_cta_btn_ar"),
            "buttonUrl": _get(doc, "wf_cta_url")
        }
    }

    # --- 4. Packages Section ---
    pkg_items = []
    for p in (doc.packages or []):
        pkg_items.append({
            "id": _get(p, "package_id"),
            "name_en": _get(p, "name_en"),
            "name_ar": _get(p, "name_ar"),
            "price_en": _get(p, "price_en"),
            "price_ar": _get(p, "price_ar"),
            "isFeatured": bool(p.is_featured),
            "icon": _get(p, "icon"),
            "features_en": _list_from_text(_get(p, "features_en")),
            "features_ar": _list_from_text(_get(p, "features_ar"))
        })

    packages = {
        "badge_en": _get(doc, "pkg_badge_en"),
        "badge_ar": _get(doc, "pkg_badge_ar"),
        "title_en": _get(doc, "pkg_title_en"),
        "title_ar": _get(doc, "pkg_title_ar"),
        "subtitle_en": _get(doc, "pkg_subtitle_en"),
        "subtitle_ar": _get(doc, "pkg_subtitle_ar"),
        "items": pkg_items
    }

    # --- 5. Stats Section ---
    counters = []
    for c in (doc.stats_counters or []):
        # Convert value to number if possible, else string
        val = _get(c, "value")
        try:
            val = float(val) if '.' in val else int(val)
        except:
            pass
            
        counters.append({
            "value": val,
            "suffix": _get(c, "suffix"),
            "label_en": _get(c, "label_en"),
            "label_ar": _get(c, "label_ar"),
            "color": _get(c, "color")
        })

    stats = {
        "title_en": _get(doc, "stats_title_en"),
        "title_ar": _get(doc, "stats_title_ar"),
        "subtitle_en": _get(doc, "stats_subtitle_en"),
        "subtitle_ar": _get(doc, "stats_subtitle_ar"),
        "counters": counters
    }

    # --- 6. Partners Section ---
    partners_list = []
    for ptr in (doc.partners or []):
        partners_list.append({
            "name_en": _get(ptr, "partner_name_en"),
            "name_ar": _get(ptr, "partner_name_ar"),
            "logo": _get(ptr, "logo")
        })

    # --- 7. Locations Section ---
    branches = []
    for loc in (doc.locations or []):
        branches.append({
            "id": int(loc.branch_id or 0),
            "name_en": _get(loc, "name_en"),
            "name_ar": _get(loc, "name_ar"),
            "address_en": _get(loc, "address_en"),
            "address_ar": _get(loc, "address_ar"),
            "phone": _get(loc, "phone"),
            "lat": float(loc.latitude or 0.0),
            "lng": float(loc.longitude or 0.0),
            "isMain": bool(loc.is_main)
        })

    locations = {
        "title_en": _get(doc, "loc_title_en"),
        "title_ar": _get(doc, "loc_title_ar"),
        "subtitle_en": _get(doc, "loc_subtitle_en"),
        "subtitle_ar": _get(doc, "loc_subtitle_ar"),
        "branches": branches
    }

    # --- Final Construct ---
    return {
        "hero": hero,
        "about": about,
        "workflow": workflow,
        "packages": packages,
        "stats": stats,
        "partners": partners_list,
        "locations": locations
    }



















@frappe.whitelist(allow_guest=True)
def get_medical_tests_data():
    """
    Returns the categories and tests in the exact requested JSON format.
    """
    
    # 1. Fetch Categories
    categories_records = frappe.get_all(
        "SS Test Category",
        fields=["category_id as id", "name_en as name", "name_ar as nameAr"],
        order_by="creation asc"
    )
    
    # Prepend the "All" category programmatically
    categories_list = [
        {
            "id": "all",
            "name": "All",
            "nameAr": "الكل"
        }
    ]
    categories_list.extend(categories_records)

    # 2. Fetch Tests
    tests_records = frappe.get_all(
        "SS Medical Test",
        fields=[
            "name as id", # Assuming the document name (which is the code due to autoname) is the ID
            "name_en as name",
            "name_ar as nameAr",
            "code",
            "category as categoryId",
            "turnaround_time_en as turnaroundTime",
            "turnaround_time_ar as turnaroundTimeAr",
            "requires_fasting as requiresFasting",
            "description_en as description",
            "description_ar as descriptionAr"
        ],
        order_by="creation desc"
    )

    # Clean up output (convert 0/1 to boolean for requiresFasting)
    tests_list = []
    for t in tests_records:
        tests_list.append({
            "id": t.id,
            "name": t.name or "",
            "nameAr": t.nameAr or "",
            "code": t.code or "",
            "categoryId": t.categoryId or "",
            "turnaroundTime": t.turnaroundTime or "",
            "turnaroundTimeAr": t.turnaroundTimeAr or "",
            "requiresFasting": bool(t.requiresFasting),
            "description": t.description or "",
            "descriptionAr": t.descriptionAr or ""
        })

    # 3. Construct Final JSON Structure
    return {
        "message": {
            "categories": categories_list,
            "tests": tests_list
        }
    }











def _text_to_list(text):
    """دالة مساعدة لتحويل النص المتعدد الأسطر إلى مصفوفة (List)"""
    if not text:
        return []
    # يفصل النص بناءً على السطر الجديد ويزيل المسافات الفارغة
    return [line.strip() for line in text.split('\n') if line.strip()]

@frappe.whitelist(allow_guest=True)
def get_lab_equipment():
    # جلب جميع الأجهزة المسجلة
    equipments = frappe.get_all(
        "SS Lab Equipment",
        fields=["*"],
        order_by="creation asc"
    )
    
    eq_list = []
    
    for eq in equipments:
        eq_list.append({
            "id": eq.equipment_id or "",
            "category": eq.category or "",
            "image": eq.image or "",
            "accuracy": float(eq.accuracy or 0.0),
            "status": eq.status or "online",
            "name": eq.name_en or "",
            "nameAr": eq.name_ar or "",
            "manufacturer": eq.manufacturer_en or "",
            "manufacturerAr": eq.manufacturer_ar or "",
            "speed": eq.speed_en or "",
            "speedAr": eq.speed_ar or "",
            "description": eq.description_en or "",
            "descriptionAr": eq.description_ar or "",
            "features": _text_to_list(eq.features_en),
            "featuresAr": _text_to_list(eq.features_ar),
            "relatedTests": _text_to_list(eq.related_tests_en),
            "relatedTestsAr": _text_to_list(eq.related_tests_ar),
        })
        
    # بناء الهيكل المطلوب
    return {
        "message": {
            "equipment": eq_list
        }
    }




















@frappe.whitelist(allow_guest=True)
def get_certificates():
    # جلب جميع الشهادات من قاعدة البيانات
    certificates_records = frappe.get_all(
        "SS Certificate",
        fields=[
            "certificate_id as id",
            "title_en as title",
            "title_ar as titleAr",
            "issuer_en as issuer",
            "issuer_ar as issuerAr",
            "year",
            "image"
        ],
        order_by="creation asc" # يمكنك تغييرها إلى "year desc" إذا أردت ترتيبها من الأحدث للأقدم
    )
    
    # تنظيف وتجهيز البيانات (لضمان عدم وجود قيم None)
    cert_list = []
    for cert in certificates_records:
        cert_list.append({
            "id": str(cert.id or ""),
            "title": cert.title or "",
            "titleAr": cert.titleAr or "",
            "issuer": cert.issuer or "",
            "issuerAr": cert.issuerAr or "",
            "year": str(cert.year or ""),
            "image": cert.image or ""
        })

    # إرجاع الهيكل المطلوب
    return {
        "message": {
            "certificates": cert_list
        }
    }











@frappe.whitelist(allow_guest=True)
def get_news():
    # جلب الأخبار من قاعدة البيانات وترتيبها من الأحدث للأقدم
    news_records = frappe.get_all(
        "SS News Article",
        fields=[
            "news_id as id",
            "title_en as title",
            "title_ar as titleAr",
            "excerpt_en as excerpt",
            "excerpt_ar as excerptAr",
            "publish_date",
            "read_time_en as readTime",
            "read_time_ar as readTimeAr",
            "image"
        ],
        order_by="publish_date desc"
    )
    
    news_list = []
    for news in news_records:
        news_list.append({
            "id": news.id or "",
            "title": news.title or "",
            "titleAr": news.titleAr or "",
            "excerpt": news.excerpt or "",
            "excerptAr": news.excerptAr or "",
            # تحويل كائن التاريخ إلى نص بصيغة YYYY-MM-DD
            "publishDate": str(news.publish_date) if news.publish_date else "",
            "readTime": news.readTime or "",
            "readTimeAr": news.readTimeAr or "",
            "image": news.image or ""
        })

    # إرجاع الهيكل المطلوب
    return {
        "message": {
            "news": news_list
        }
    }    













@frappe.whitelist(allow_guest=True)
def get_videos():
    # جلب جميع الفيديوهات من قاعدة البيانات
    videos_records = frappe.get_all(
        "SS Videos",
        fields=[
            "video_id as id",
            "title_en as title",
            "title_ar as titleAr",
            "duration_en as duration",
            "duration_ar as durationAr",
            "url"
        ],
        order_by="creation desc"
    )
    
    video_list = []
    for vid in videos_records:
        video_list.append({
            "id": vid.id or "",
            "title": vid.title or "",
            "titleAr": vid.titleAr or "",
            "duration": vid.duration or "",
            "durationAr": vid.durationAr or "",
            "url": vid.url or ""
        })

    return {
        "message": {
            "videos": video_list
        }
    }










@frappe.whitelist(allow_guest=True)
def get_articles():
    # جلب المقالات من الأحدث للأقدم
    articles_records = frappe.get_all(
        "SS Article",
        fields=[
            "article_id as id",
            "title_en as title",
            "title_ar as titleAr",
            "excerpt_en as excerpt",
            "excerpt_ar as excerptAr",
            "content_en as content",
            "content_ar as contentAr",
            "image",
            "author_en as author",
            "author_ar as authorAr",
            "read_time_en as readTime",
            "read_time_ar as readTimeAr",
            "category_en as category",
            "category_ar as categoryAr",
            "date",
            "is_featured as isFeatured"
        ],
        order_by="date desc"
    )
    
    articles_list = []
    for art in articles_records:
        articles_list.append({
            "id": art.id or "",
            "title": art.title or "",
            "titleAr": art.titleAr or "",
            "excerpt": art.excerpt or "",
            "excerptAr": art.excerptAr or "",
            "content": art.content or "",
            "contentAr": art.contentAr or "",
            "image": art.image or "",
            "author": art.author or "",
            "authorAr": art.authorAr or "",
            "readTime": art.readTime or "",
            "readTimeAr": art.readTimeAr or "",
            "category": art.category or "",
            "categoryAr": art.categoryAr or "",
            "date": str(art.date) if art.date else "",
            "isFeatured": bool(art.isFeatured)
        })

    # إرجاع الهيكل المتداخل المطلوب
    return {
        "message": {
            "articles": articles_list
        }
    }










@frappe.whitelist(allow_guest=True)
def get_contact_info():
    # 1. إيقاف التحقق من الصلاحيات مؤقتاً ليتمكن الـ Guest من جلب البيانات
    original_ignore_permissions = frappe.flags.ignore_permissions
    frappe.flags.ignore_permissions = True
    
    try:
        # جلب الدوك تايب المفرد (الآن لن يظهر خطأ الصلاحيات)
        doc = frappe.get_single("SS Contact Settings")
        
        # تحويل حقل الهواتف النصي إلى مصفوفة (Array) عبر فصل الأسطر
        phones_list = []
        if doc.phones:
            phones_list = [p.strip() for p in doc.phones.split('\n') if p.strip()]
            
        # تجهيز مصفوفة أوقات العمل
        working_hours_list = []
        for row in (doc.working_hours or []):
            wh_obj = {
                "days": row.days_en or "",
                "daysAr": row.days_ar or "",
                "hours": row.hours or ""
            }
            
            if row.is_emergency:
                wh_obj["isEmergency"] = True
                
            working_hours_list.append(wh_obj)

        # بناء كائن معلومات التواصل
        contact_info = {
            "address": doc.address_en or "",
            "addressAr": doc.address_ar or "",
            "phones": phones_list,
            "email": doc.email or "",
            "workingHours": working_hours_list
        }

        return {
            "message": {
                "contactInfo": contact_info
            }
        }
        
    finally:
        # 2. إعادة إعدادات الصلاحيات لحالتها الأصلية دائماً (حتى لو حدث خطأ)
        frappe.flags.ignore_permissions = original_ignore_permissions







@frappe.whitelist(allow_guest=True)
def submit_contact(name=None, phone=None, subject=None, message=None):
    """
    يستقبل طلبات POST من نموذج الاتصال في الموقع مع حماية Rate Limiting
    """
    
    # 1. جلب عنوان الـ IP الخاص بالزائر
    user_ip = frappe.local.request_ip
    
    # 2. إنشاء مفتاح فريد لهذا الـ IP في الـ Cache
    cache_key = f"contact_form_limit:{user_ip}"
    
    # 3. جلب عدد محاولات الإرسال السابقة لهذا الـ IP (الافتراضي 0)
    request_count = frappe.cache().get_value(cache_key) or 0
    
    # --- إعدادات الحماية ---
    MAX_REQUESTS = 3         # الحد الأقصى للرسائل المسموح بها
    EXPIRE_IN_SECONDS = 900  # مدة الحظر بالثواني (900 ثانية = 15 دقيقة)
    # -----------------------

    # 4. التحقق مما إذا كان الزائر قد تجاوز الحد المسموح
    if int(request_count) >= MAX_REQUESTS:
        return {
            "status": "error",
            "message": "You have sent too many messages. Please try again after 15 minutes.",
            "messageAr": "لقد أرسلت عدداً كبيراً من الرسائل. يرجى المحاولة مرة أخرى بعد 15 دقيقة."
        }

    # 5. التحقق من وجود جميع الحقول المطلوبة (Validation)
    if not name or not phone or not subject or not message:
        return {
            "status": "error",
            "message": "Please fill all required fields.",
            "messageAr": "يرجى تعبئة جميع الحقول المطلوبة."
        }
    
    try:
        # 6. حفظ الرسالة في قاعدة البيانات
        doc = frappe.get_doc({
            "doctype": "SS Contact Message",
            "sender_name": name,
            "phone": phone,
            "subject": subject,
            "message": message,
            "status": "Pending"
        })
        
        doc.insert(ignore_permissions=True)
        
        # 7. تحديث العداد في الـ Cache بعد نجاح الإرسال، مع ضبط وقت الانتهاء
        frappe.cache().set_value(cache_key, int(request_count) + 1, expires_in_sec=EXPIRE_IN_SECONDS)
        
        # 8. إرجاع رسالة النجاح
        return {
            "status": "success",
            "message": "Your message has been sent successfully!",
            "messageAr": "تم إرسال رسالتك بنجاح وسيتواصل معك فريقنا قريباً."
        }
        
    except Exception as e:
        frappe.log_error(title="Contact Form Submission Error", message=frappe.get_traceback())
        return {
            "status": "error",
            "message": "An internal error occurred. Please try again later.",
            "messageAr": "حدث خطأ في النظام أثناء إرسال رسالتك. يرجى المحاولة لاحقاً."
        }














@frappe.whitelist(allow_guest=True)
def submit_home_visit(name=None, phone=None, locationType=None, address=None, date=None, timeSlot=None, selectedTests=None, prescriptionFile=None):
    """
    يستقبل طلبات الحجز بصيغة JSON، بما في ذلك ملف الروشتة كـ Base64
    """
    
    # --- 1. حماية الـ Rate Limiting (لمنع السبام) ---
    user_ip = frappe.local.request_ip
    cache_key = f"home_visit_limit:{user_ip}"
    request_count = frappe.cache().get_value(cache_key) or 0
    
    MAX_REQUESTS = 3         # 3 حجوزات كحد أقصى
    EXPIRE_IN_SECONDS = 900  # كل 15 دقيقة
    
    if int(request_count) >= MAX_REQUESTS:
        return {
            "status": "error",
            "message": "Too many booking requests. Please try again after 15 minutes.",
            "messageAr": "لقد قمت بإرسال طلبات حجز كثيرة. يرجى المحاولة بعد 15 دقيقة."
        }

    # --- 2. التحقق من البيانات الأساسية ---
    if not name or not phone or not date or not timeSlot:
        return {
            "status": "error",
            "message": "Please fill all required fields (Name, Phone, Date, Time).",
            "messageAr": "يرجى تعبئة جميع الحقول الإلزامية (الاسم، الهاتف، التاريخ، الوقت)."
        }
        
    try:
        # معالجة الفحوصات المختارة (تحويلها من مصفوفة إلى نص مقروء مفصول بفواصل)
        tests_text = ""
        if selectedTests:
            if isinstance(selectedTests, str):
                try:
                    selected_list = json.loads(selectedTests)
                    tests_text = ", ".join(selected_list)
                except:
                    tests_text = selectedTests
            elif isinstance(selectedTests, list):
                tests_text = ", ".join(selectedTests)

        # --- 3. إنشاء مستند الحجز الأساسي ---
        doc = frappe.get_doc({
            "doctype": "SS Home Visit Booking",
            "patient_name": name,
            "phone": phone,
            "location_type": locationType or "home",
            "address": address,
            "booking_date": date,
            "time_slot": timeSlot,
            "selected_tests": tests_text,
            "status": "Pending"
        })
        # إدراج المستند بصلاحيات تخطي للزوار
        doc.insert(ignore_permissions=True)
        
        # --- 4. معالجة ملف الروشتة (Base64) ---
        actual_file_data = prescriptionFile or frappe.form_dict.get("prescription_file")
        if actual_file_data:
            try:
                # التحقق مما إذا كان النص يحتوي على الهيدر (data:image/jpeg;base64,)
                if "base64," in actual_file_data:
                    file_parts = actual_file_data.split("base64,", 1)
                    encoded_data = file_parts[1]
                    
                    # استخراج الامتداد
                    try:
                        extension = file_parts[0].split("/")[1].split(";")[0]
                        if extension == "jpeg":
                            extension = "jpg"
                    except:
                        extension = "png"
                else:
                    encoded_data = actual_file_data
                    extension = "png"

                file_name = f"prescription_{doc.name}.{extension}"
                
                # === الحل هنا: تحويل النص المشفر إلى Bytes ===
                # سيقوم بتحويل الـ Base64 String إلى Bytes Object
                decoded_bytes = base64.b64decode(encoded_data)
                
                # إنشاء ملف جديد في نظام Frappe وتمرير الـ Bytes مباشرة
                saved_file = frappe.get_doc({
                    "doctype": "File",
                    "file_name": file_name,
                    "attached_to_doctype": doc.doctype,
                    "attached_to_name": doc.name,
                    "attached_to_field": "prescription_file",
                    "content": decoded_bytes,  # <-- نمرر البيانات الثنائية هنا
                    "is_private": 0
                })
                
                # الحفظ وتخطي الصلاحيات للزوار
                saved_file.insert(ignore_permissions=True)
                
                # تأكيد ربط مسار الملف بحقل الروشتة
                doc.db_set("prescription_file", saved_file.file_url)
                
            except Exception as file_error:
                frappe.log_error(title="File Save Error - Home Visit", message=str(file_error) + "\n" + frappe.get_traceback())
        # --- 6. الرد بالنجاح ---
        return {
            "status": "success",
            "message": "Your booking has been received successfully. We will contact you soon.",
            "messageAr": "تم استلام طلب الحجز الخاص بك بنجاح. سنتواصل معك لتأكيد الموعد قريباً."
        }
        
    except Exception as e:
        # تسجيل الأخطاء العامة في حال فشل إنشاء الحجز من الأساس
        frappe.log_error(title="Home Visit Booking Error", message=frappe.get_traceback())
        return {
            "status": "error",
            "message": "An error occurred while processing your booking. Please try again.",
            "messageAr": "حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى."
        }








@frappe.whitelist(allow_guest=True)
def get_about_page():
    doc = frappe.get_single("SS About Page")
    
    # --- 1. Hero ---
    hero = {
        "title": doc.hero_title_en or "",
        "titleAr": doc.hero_title_ar or "",
        "subtitle": doc.hero_subtitle_en or "",
        "subtitleAr": doc.hero_subtitle_ar or "",
        "badge": doc.hero_badge_en or "",
        "badgeAr": doc.hero_badge_ar or "",
        "image": doc.hero_image or ""  # تمت إضافة الصورة الرئيسية هنا
    }

    # --- 2. Story & Pillars ---
    pillars_list = []
    for p in (doc.story_pillars or []):
        pillars_list.append({
            "id": p.pillar_id or "",
            "title": p.title_en or "",
            "titleAr": p.title_ar or ""
        })

    story = {
        "headline": doc.story_headline_en or "",
        "headlineAr": doc.story_headline_ar or "",
        "subheadline": doc.story_subheadline_en or "",
        "subheadlineAr": doc.story_subheadline_ar or "",
        "body": doc.story_body_en or "",
        "bodyAr": doc.story_body_ar or "",
        "image1": doc.story_image_1 or "", # تمت إضافة الصورة الأولى
        "image2": doc.story_image_2 or "", # تمت إضافة الصورة الثانية
        "image3": doc.story_image_3 or "", # تمت إضافة الصورة الثالثة
        "pillars": pillars_list
    }

    # --- 3. Values ---
    values_list = []
    for v in (doc.values_items or []):
        values_list.append({
            "id": v.value_id or "",
            "title": v.title_en or "",
            "titleAr": v.title_ar or "",
            "description": v.description_en or "",
            "descriptionAr": v.description_ar or ""
        })

    values = {
        "title": doc.values_title_en or "",
        "titleAr": doc.values_title_ar or "",
        "items": values_list
    }

    # --- 4. CTA ---
    cta = {
        "title": doc.cta_title_en or "",
        "titleAr": doc.cta_title_ar or "",
        "bookButton": doc.cta_book_btn_en or "",
        "bookButtonAr": doc.cta_book_btn_ar or "",
        "exploreButton": doc.cta_explore_btn_en or "",
        "exploreButtonAr": doc.cta_explore_btn_ar or "",
        "bookLink": doc.cta_book_link or "/book",
        "exploreLink": doc.cta_explore_link or "/tests"
    }

    # --- 5. Return Final Structure ---
    return {
        "status": "success",
        "data": {
            "hero": hero,
            "story": story,
            "values": values,
            "cta": cta
        }
    }















@frappe.whitelist(allow_guest=True)
def get_chat_widget():
    # جلب إعدادات أداة المحادثة
    doc = frappe.get_single("SS Chat Widget Settings")
    
    # تجهيز قائمة الفروع
    branches_list = []
    for branch in (doc.branches or []):
        branches_list.append({
            "id": branch.branch_id or "",
            "name_en": branch.name_en or "",
            "name_ar": branch.name_ar or "",
            "whatsapp_number": branch.whatsapp_number or ""
        })
        
    # تجهيز زر الإجراء
    action_button = {
        "text_en": doc.action_text_en or "",
        "text_ar": doc.action_text_ar or "",
        "link_en": doc.action_link_en or "",
        "link_ar": doc.action_link_ar or ""
    }
    
    # إرجاع الهيكل النهائي
    # Frappe سيقوم بوضع هذه النتيجة داخل كائن "message" تلقائياً
    return {
        "title_en": doc.title_en or "",
        "title_ar": doc.title_ar or "",
        "branches": branches_list,
        "action_button": action_button
    }









@frappe.whitelist(allow_guest=True)
def get_quizzes():
    quizzes_records = frappe.get_all("SS Quiz", pluck="name", order_by="creation desc")
    quizzes_list = []
    
    for quiz_name in quizzes_records:
        doc = frappe.get_doc("SS Quiz", quiz_name)
        
        questions_list = []
        for q in (doc.questions or []):
            options_list = []
            
            # فحص الخيارات الأربعة، إذا كان النص الإنجليزي موجوداً، نعتبر الخيار موجوداً
            for i in range(1, 5):
                label_en = q.get(f"opt{i}_label_en")
                if label_en:
                    options_list.append({
                        "label_en": label_en,
                        "label_ar": q.get(f"opt{i}_label_ar") or "",
                        "value": q.get(f"opt{i}_value") or "",
                        "points": q.get(f"opt{i}_points") or 0
                    })
            
            questions_list.append({
                "id": q.question_id,
                "text_en": q.text_en or "",
                "text_ar": q.text_ar or "",
                "options": options_list
            })
            
        recommendation = {
            "title_en": doc.rec_title_en or "",
            "title_ar": doc.rec_title_ar or "",
            "description_en": doc.rec_desc_en or "",
            "description_ar": doc.rec_desc_ar or "",
            "test_id": doc.rec_test_id or ""
        }
        
        quizzes_list.append({
            "id": doc.quiz_id or "",
            "title_en": doc.title_en or "",
            "title_ar": doc.title_ar or "",
            "description_en": doc.description_en or "",
            "description_ar": doc.description_ar or "",
            "threshold": doc.threshold or 0,
            "questions": questions_list,
            "recommendation": recommendation
        })

    return {
        "message": {
            "quizzes": quizzes_list
        }
    }








@frappe.whitelist(allow_guest=True)
def get_seo_metadata(route=None, locale=None):
    """
    يجلب بيانات الـ SEO للصفحة المطلوبة بناءً على الـ Route
    """
    
    # 1. التحقق من إرسال المسار
    if not route:
        return {
            "status": "error",
            "message": "Route parameter is missing."
        }
        
    # 2. التحقق من وجود بيانات لهذه الصفحة في قاعدة البيانات
    if not frappe.db.exists("SS SEO Metadata", route):
        return {
            "status": "error",
            "message": f"No SEO metadata found for route: {route}"
        }
        
    try:
        # 3. جلب المستند
        doc = frappe.get_doc("SS SEO Metadata", route)
        
        # 4. بناء هيكل البيانات المرجعة (Dynamic payload based on locale)
        seo_data = {
            "og_image": doc.og_image or ""
        }
        
        # إذا طلب الفرونت اند اللغة العربية فقط
        if locale == 'ar':
            seo_data["title_ar"] = doc.title_ar or ""
            seo_data["description_ar"] = doc.description_ar or ""
            seo_data["keywords_ar"] = doc.keywords_ar or ""
            
        # إذا طلب الفرونت اند اللغة الإنجليزية فقط
        elif locale == 'en':
            seo_data["title_en"] = doc.title_en or ""
            seo_data["description_en"] = doc.description_en or ""
            seo_data["keywords_en"] = doc.keywords_en or ""
            
        # إذا لم يتم تحديد لغة، نرجع كل البيانات (كما في مثالك)
        else:
            seo_data["title_ar"] = doc.title_ar or ""
            seo_data["title_en"] = doc.title_en or ""
            seo_data["description_ar"] = doc.description_ar or ""
            seo_data["description_en"] = doc.description_en or ""
            seo_data["keywords_ar"] = doc.keywords_ar or ""
            seo_data["keywords_en"] = doc.keywords_en or ""

        # 5. إرجاع الرد النهائي
        return {
            "status": "success",
            "seo": seo_data
        }
        
    except Exception as e:
        frappe.log_error(title=f"SEO Fetch Error for {route}", message=frappe.get_traceback())
        return {
            "status": "error",
            "message": "Internal Server Error"
        }








@frappe.whitelist(allow_guest=True)
def portal_login(phone_number, password):
    try:
        user_email = frappe.db.get_value("User", {"mobile_no": phone_number}, "name")

        if not user_email:
            frappe.local.response["http_status_code"] = 404
            return {"status": "error", "message": "رقم الهاتف غير مسجل."}

        # 1. المصادقة (Authentication): هل كلمة المرور صحيحة؟
        frappe.local.login_manager = LoginManager()
        frappe.local.login_manager.authenticate(user_email, password)
        
        # 2. التفويض (Authorization): هل يمتلك الصلاحية لدخول هذه البوابة؟
        roles = frappe.get_roles(user_email)
        
        # التحقق مما إذا كان المستخدم يملك أحد الدورين المطلوبين
        allowed_roles = ["Lab Center", "Lab Patient"]
        user_type = None
        
        if "Lab Center" in roles:
            user_type = "Center"
        elif "Lab Patient" in roles:
            user_type = "Patient"
        
        # إذا لم يكن مريضاً ولا مركزاً، نرفض دخوله للبوابة حتى لو كانت كلمة المرور صحيحة
        if not user_type:
            # مهم جداً: مسح الجلسة التي تم إنشاؤها في الخطوة 1 لأننا لن نسمح له بالاستمرار
            frappe.local.login_manager.logout() 
            frappe.local.response["http_status_code"] = 403 # Forbidden
            return {"status": "error", "message": "عذراً، هذا الحساب لا يملك صلاحية الوصول لبوابة النتائج."}

        # إذا نجح في كل الاختبارات، نقوم بإنشاء الجلسة النهائية
        frappe.local.login_manager.post_login()

        return {
            "status": "success",
            "message": "تم تسجيل الدخول بنجاح.",
            "data": {"user_type": user_type, "full_name": frappe.get_value("User", user_email, "full_name")}
        }

    except frappe.exceptions.AuthenticationError:
        frappe.local.response["http_status_code"] = 401
        return {"status": "error", "message": "كلمة المرور غير صحيحة."}












@frappe.whitelist(allow_guest=True)
def portal_logout():
    """
    API مخصص لتسجيل الخروج وإتلاف الجلسة
    """
    # التحقق مما إذا كان المستخدم ضيفاً بالفعل (غير مسجل الدخول)
    if frappe.session.user == "Guest":
        return {
            "status": "success",
            "message": "لا يوجد جلسة نشطة، أنت غير مسجل الدخول."
        }

    try:
        # إتلاف الجلسة من قاعدة بيانات Frappe
        frappe.local.login_manager.logout()
        
        # حفظ التغييرات في قاعدة البيانات (حذف سجل الجلسة)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "تم تسجيل الخروج بنجاح وإتلاف الجلسة أمنياً."
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        return {"status": "error", "message": "حدث خطأ أثناء محاولة تسجيل الخروج."}








@frappe.whitelist()
def get_results(search_term="", from_date="", to_date="", branch="", limit_start=0, limit_page_length=20):
    user = frappe.session.user
    roles = frappe.get_roles(user)
    
    # 1. التحقق من الصلاحية
    if "Lab Center" not in roles and "Lab Patient" not in roles:
        frappe.local.response["http_status_code"] = 403
        return {"status": "error", "message": "غير مصرح لك بالوصول لهذه البيانات."}

    # 2. بناء فلاتر البحث الأساسية (أهم فلتر هو حصر البيانات بمالكها)
    filters = {
        "owner_user": user
    }

    # إضافة فلتر الفرع إن وجد
    if branch:
        filters["branch"] = branch

    # إضافة فلتر التاريخ إن وجد (نطاق زمني)
    if from_date and to_date:
        filters["result_date"] = ["between", [from_date, to_date]]
    elif from_date:
        filters["result_date"] = [">=", from_date]

    # 3. بناء استعلام البحث النصي (رقم الزيارة أو اسم المريض)
    or_filters = {}
    if search_term:
        or_filters = {
            "name": ["like", f"%{search_term}%"], # رقم الزيارة (Naming Series)
            "patient_name": ["like", f"%{search_term}%"]
        }

    # 4. جلب البيانات من قاعدة البيانات
    results = frappe.get_all(
        "Lab Result",
        filters=filters,
        or_filters=or_filters,
        fields=["name", "patient_name", "branch", "result_date", "is_read", "result_pdf"],
        order_by="creation desc", # الأحدث أولاً
        limit_start=limit_start,
        limit_page_length=limit_page_length
    )

    # 5. جلب إجمالي العدد (لأغراض الـ Pagination في الواجهة الأمامية)
    # ✅ السطر الجديد الصحيح
    total_count = len(frappe.get_all(
        "Lab Result",
        filters=filters,
        or_filters=or_filters,
        fields=["name"],       # جلب الاسم فقط لتقليل استهلاك الذاكرة
        limit_page_length=0    # 0 تعني تجاوز الـ Pagination لجلب كل السجلات المطابقة بغرض تعدادها
    ))

    return {
        "status": "success",
        "data": results,
        "total_count": total_count
    }



@frappe.whitelist()
def get_active_branches():
    if frappe.session.user == "Guest":
        frappe.local.response["http_status_code"] = 403
        return {"status": "error", "message": "غير مصرح لك بالوصول."}

    try:
        # اكتفينا بجلب الـ name (اسم الفرع) فقط لضمان عمل الكود
        branches = frappe.get_all(
            "Lab Branch",
            filters={"is_active": 1}, 
            fields=["name"], 
            order_by="name asc"
        )

        return {
            "status": "success",
            "data": branches
        }

    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        return {"status": "error", "message": f"الخطأ الفعلي: {str(e)}"}





@frappe.whitelist()
def mark_as_read(result_name):
    user = frappe.session.user
    
    # 1. جلب المستند للتأكد من وجوده
    if not frappe.db.exists("Lab Result", result_name):
        frappe.local.response["http_status_code"] = 404
        return {"status": "error", "message": "النتيجة غير موجودة."}

    # 2. حماية أمنية: التأكد من أن النتيجة تخص المستخدم الحالي
    owner = frappe.db.get_value("Lab Result", result_name, "owner_user")
    if owner != user:
        frappe.local.response["http_status_code"] = 403
        return {"status": "error", "message": "لا تملك صلاحية تعديل هذه النتيجة."}

    # 3. تحديث الحالة
    frappe.db.set_value("Lab Result", result_name, "is_read", 1)
    
    # 4. حفظ التغييرات في قاعدة البيانات (الخطوة الناقصة)
    frappe.db.commit()
    
    # 5. تفريغ التخزين المؤقت (Cache) للمستند لتحديث الواجهة فوراً
    frappe.cache().delete_key(f"doc:Lab Result:{result_name}")

    return {"status": "success"}






def get_s3_settings():
    s3_doc = frappe.get_single("S3 File Attachment")
    endpoint_url = frappe.conf.get("s3_endpoint_url") or frappe.conf.get("endpoint_url")
    if not endpoint_url:
        frappe.throw("الرجاء التأكد من إضافة مسار endpoint_url في ملف site_config.json")
    return {
        "aws_key": s3_doc.aws_key,
        "aws_secret": s3_doc.aws_secret,
        "bucket_name": s3_doc.bucket_name,
        "region": s3_doc.region_name or "auto", # 👈 قراءة المنطقة من الإعدادات (غالباً auto)
        "endpoint_url": endpoint_url
    }

def get_r2_client(settings):
    return boto3.client(
        's3',
        aws_access_key_id=settings["aws_key"],
        aws_secret_access_key=settings["aws_secret"],
        region_name=settings["region"], # 👈 تمرير المنطقة لتطابق التوقيع مع كلاودفلير
        endpoint_url=settings["endpoint_url"],
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'} # 👈 التوافق الإجباري مع خوادم R2
        )
    )

    
def extract_s3_key(file_url, bucket_name):
    """دالة ذكية لاستخراج المفتاح الصحيح وتجاوز مسارات التطبيق الوسيط"""
    
    # 1. الاكتشاف الذكي: إذا كان الرابط يحتوي على مسار تطبيق S3 الوسيط
    if "frappe_s3_attachment.controller.generate_file" in file_url:
        parsed_url = urlparse(file_url)
        query_params = parse_qs(parsed_url.query)
        # نستخرج قيمة 'key' الصافية من الرابط
        if 'key' in query_params:
            return query_params['key'][0] # سيرجع مساراً نظيفاً مثل: 2026/04/10/Lab Result/...

    # 2. الطريقة الاحتياطية (في حال كان الرابط مباشراً أو عادياً)
    decoded_url = unquote(file_url)
    if decoded_url.startswith("http"):
        parsed = urlparse(decoded_url)
        path = parsed.path.lstrip('/')
    else:
        path = decoded_url.replace('/private/files/', '').replace('/public/files/', '').lstrip('/')
        
    if path.startswith(bucket_name + "/"):
        path = path.replace(bucket_name + "/", "", 1)
        
    return path
@frappe.whitelist()
def download_single_pdf(result_name):
    user = frappe.session.user
    doc = frappe.get_doc("Lab Result", result_name)

    if doc.owner_user != user:
        frappe.throw("غير مصرح لك بالوصول لهذه النتيجة", frappe.PermissionError)

    settings = get_s3_settings()
    s3_client = get_r2_client(settings)

    # استخدام الدالة الجديدة لاستخراج المفتاح الكامل
    file_key = extract_s3_key(doc.result_pdf, settings["bucket_name"])

    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings["bucket_name"], 'Key': file_key},
            ExpiresIn=600 
        )
        
        if not doc.is_read:
            doc.db_set('is_read', 1)
            frappe.db.commit()

        return {"status": "success", "download_url": presigned_url}
    except ClientError as e:
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def download_bulk_zip(result_names):
    if isinstance(result_names, str):
        result_names = json.loads(result_names)

    user = frappe.session.user
    settings = get_s3_settings()
    s3_client = get_r2_client(settings)
    zip_buffer = io.BytesIO()
    files_added = 0 # عداد للتحقق من إضافة الملفات للـ ZIP

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for name in result_names:
            doc = frappe.get_doc("Lab Result", name)
            if doc.owner_user != user or not doc.result_pdf: 
                continue

            # استخدام الدالة الجديدة لاستخراج المفتاح الكامل
            file_key = extract_s3_key(doc.result_pdf, settings["bucket_name"])
            # استبدل السطر القديم بهذا:
            try:
                response = s3_client.get_object(Bucket=settings["bucket_name"], Key=file_key)
                file_data = response['Body'].read()
                
                patient_name = doc.patient_name.replace(" ", "_") if doc.patient_name else "Result"
                zip_file.writestr(f"{doc.name}_{patient_name}.pdf", file_data)
                files_added += 1
                
                if not doc.is_read:
                    doc.db_set('is_read', 1)
            except Exception as e:
                # تسجيل الخطأ في لوحة تحكم Frappe لتسهيل اكتشافه مستقبلاً
                frappe.log_error(message=str(e), title=f"S3 ZIP Error for {name}")
                continue

    if files_added == 0:
        frappe.local.response["http_status_code"] = 404
        return {"status": "error", "message": "تعذر العثور على أي ملفات صالحة للتحميل."}

    frappe.db.commit()
    zip_buffer.seek(0)
    frappe.local.response.filename = "Bulk_Results.zip"
    frappe.local.response.filecontent = zip_buffer.getvalue()
    frappe.local.response.type = "download"




@frappe.whitelist(allow_guest=True)
def get_ticker_messages():
    """
    API لجلب عبارات الشريط العلوي من إعدادات البوابة.
    يقوم بتحويل النص المتعدد الأسطر إلى مصفوفة (Array) لسهولة الاستخدام في React.
    """
    try:
        # قراءة الحقل من الـ Single DocType
        # نستخدم get_single_value لأنها أسرع ولا تتطلب جلب المستند كاملاً
        messages_text = frappe.db.get_single_value("Result Settings", "ticker_messages")
        
        # إذا كان الحقل فارغاً، نرجع مصفوفة فارغة
        if not messages_text:
            return {"status": "success", "data": []}
            
        # تقسيم النص بناءً على النزول لسطر جديد، مع تجاهل الأسطر الفارغة
        # strip() تقوم بإزالة المسافات الزائدة من بداية ونهاية كل عبارة
        messages_list = [msg.strip() for msg in messages_text.split('\n') if msg.strip()]
        
        return {
            "status": "success",
            "data": messages_list
        }
        
    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        return {"status": "error", "message": f"حدث خطأ أثناء جلب الإعدادات: {str(e)}"}












import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_lab_users_query(doctype, txt, searchfield, start, page_len, filters):
    # أضفنا حقل mobile_no في الـ SELECT لكي يظهر في القائمة المنسدلة
    # وأضفنا شروط البحث برقم الجوال أو الهاتف الثابت في الـ WHERE
    sql = """
        SELECT DISTINCT 
            `tabUser`.name, 
            `tabUser`.full_name, 
            `tabUser`.mobile_no
        FROM `tabUser`
        JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name
        WHERE `tabHas Role`.role IN ('Lab Center', 'Lab Patient')
        AND `tabUser`.enabled = 1
        AND (
            `tabUser`.name LIKE %(txt)s 
            OR `tabUser`.full_name LIKE %(txt)s
            OR IFNULL(`tabUser`.mobile_no, '') LIKE %(txt)s
            OR IFNULL(`tabUser`.phone, '') LIKE %(txt)s
        )
        ORDER BY `tabUser`.name ASC
        LIMIT %(start)s, %(page_len)s
    """
    
    return frappe.db.sql(sql, {
        'txt': '%' + txt + '%',
        'start': start,
        'page_len': page_len
    })


@frappe.whitelist()
def change_user_password(old_password, new_password):
    user = frappe.session.user
    
    if user == "Guest":
        frappe.throw(_("يجب تسجيل الدخول لتغيير كلمة المرور"))
        
    try:
        frappe.utils.password.check_password(user, old_password)
    except frappe.AuthenticationError:
        frappe.throw(_("كلمة المرور القديمة غير صحيحة"))
        
    # ⚠️ السر هنا: إخبار النظام بالسماح بحفظ البيانات حتى لو كان الطلب GET
    frappe.flags.read_only = False
    
    user_doc = frappe.get_doc("User", user)
    user_doc.new_password = new_password
    user_doc.save(ignore_permissions=True)
    
    # إجبار قاعدة البيانات على حفظ التغييرات فوراً
    frappe.db.commit()
    
    return {"status": "success", "message": "تم تغيير كلمة المرور بنجاح"}




@frappe.whitelist()
def check_user_role(user, role):
    # نستخدم frappe.db.exists للتحقق السريع في قاعدة البيانات مباشرة
    is_role_exist = frappe.db.exists('Has Role', {
        'parent': user,
        'role': role
    })
    return bool(is_role_exist)








@frappe.whitelist()
def bulk_upload_lab_results():
    owner_user = frappe.form_dict.get('owner_user')
    branch = frappe.form_dict.get('branch')

    if "file" not in frappe.request.files:
        frappe.throw("لم يتم إرسال ملف")

    file_data = frappe.request.files["file"]
    file_content = file_data.read()
    file_name = file_data.filename

    patient_name = "غير معروف"

    # 1. الاستخراج الذكي البصري
    try:
        pdf_stream = io.BytesIO(file_content)
        with pdfplumber.open(pdf_stream) as pdf:
            # هذا الأمر يسحب النص بنفس الترتيب الذي تراه في الشاشة
            extracted_text = pdf.pages[0].extract_text()
            
        if extracted_text:
            # إصلاح الحروف المدمجة في الـ PDF
            extracted_text = extracted_text.replace('ﻼ', 'لا').replace('ﻻ', 'لا')

            # الكود الآن بسيط جداً: ابحث عن Patient Name، وخذ النص العربي الذي يليه مباشرة!
            # سيتجاهل النقطتين والمسافات ويأخذ الاسم الصافي فقط
            match = re.search(r"Patient\s*Name[^\u0600-\u06FF]*([\u0600-\u06FF\s]{5,})", extracted_text, re.IGNORECASE)
            
            if match:
                raw_name = match.group(1).strip()
                clean_name = re.sub(r'\s+', ' ', raw_name)
                
                # ---------------------------------------------------------
                # ⚠️ التعديل تم هنا (عكس النص وتنظيفه)
                patient_name = clean_name[::-1].strip()
                patient_name = patient_name.strip(' :.')
                # ---------------------------------------------------------
    except Exception as e:
        frappe.log_error(f"PDF Parse Error: {str(e)}", "Bulk Lab Uploader")

    # 2. إنشاء سجل Lab Result جديد كلياً
    doc = frappe.get_doc({
        "doctype": "Lab Result",
        "owner_user": owner_user,
        "branch": branch,
        "patient_name": patient_name,
        "result_date": today(),
        "is_read": 0
    })
    doc.insert(ignore_permissions=True)

    # 3. حفظ الملف في التخزين وربطه بالسجل
    saved_file = save_file(
        file_name,
        file_content,
        "Lab Result",
        doc.name,
        is_private=0 
    )

    doc.db_set('result_pdf', saved_file.file_url)
    frappe.db.commit()

    return {"status": "success", "patient": patient_name, "doc": doc.name}