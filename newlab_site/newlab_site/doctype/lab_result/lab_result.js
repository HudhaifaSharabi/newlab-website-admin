// Copyright (c) 2026, Simsaar and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Lab Result", {
// 	refresh(frm) {

// 	},
// });
// Copyright (c) 2026, Simsaar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Lab Result', {
    refresh: function(frm) {
        // ... (أكوادك السابقة هنا) ...

        // 1. إنشاء الزر وتحديد الإجراء عند الضغط عليه
        let new_btn = frm.add_custom_button(__('إدخال جديد'), function() {
            // الإجراء: فتح صفحة لإنشاء سجل جديد من نفس الدوكتايب
            // يمكنك تغيير 'Lab Result' لأي دوكتايب آخر تريد أن يفتحه الزر
            frappe.new_doc('Lab Result'); 
        });

        // 2. تطبيق الألوان المطلوبة على الزر
        new_btn.css({
            'background-color': '#1a658d',
            'color': 'white',
            'font-weight': 'bold',
            'border': 'none' // لإزالة الحدود الافتراضية للزر
        });

        // 3. (اختياري) إزالة الكلاس الافتراضي لضمان عدم تداخل ألوان النظام
        new_btn.removeClass('btn-default');
        frm.toggle_display('patient_name', true);
        
        if (frm.doc.owner_user) {
            check_user_role_and_toggle(frm);
        } else {
            frm.set_df_property('patient_name', 'reqd', 0);
        }
    },
    setup: function(frm) {
        frm.set_query('owner_user', function() {
            return {
                query: 'newlab_site.api.get_lab_users_query'
            };
        });
    },
    
    owner_user: function(frm) {
        check_user_role_and_toggle(frm);
    }
});

function check_user_role_and_toggle(frm) {
    if (!frm.doc.owner_user) {
        frm.toggle_display('patient_name', true);
        frm.set_df_property('patient_name', 'reqd', 0);
        return;
    }

    // استدعاء دالة البايثون لتجاوز قيود الصلاحيات
    frappe.call({
        method: 'newlab_site.api.check_user_role',
        args: {
            user: frm.doc.owner_user,
            role: 'Lab Center'
        },
        callback: function(r) {
            let is_center = r.message;

            if (is_center) {
                frm.toggle_display('patient_name', true);
                frm.set_df_property('patient_name', 'reqd', 1);
            } else {
                frm.toggle_display('patient_name', false);
                frm.set_df_property('patient_name', 'reqd', 0);
                frm.set_value('patient_name', ''); 
            }
        }
    });
}