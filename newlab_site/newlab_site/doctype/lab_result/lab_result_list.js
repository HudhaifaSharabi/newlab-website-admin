// المسار: apps/newlab_site/newlab_site/.../doctype/lab_result/lab_result_list.js

frappe.listview_settings["Lab Result"] = {
	refresh: function (listview) {
		let btn = listview.page.add_inner_button(__("رفع نتائج جماعي"), function () {
			// 1. التحقق: إذا لم تكن النافذة موجودة مسبقاً، قم بإنشائها (تُنشأ مرة واحدة فقط)
			if (!listview.bulk_upload_dialog) {
				let d = new frappe.ui.Dialog({
					title: "الرفع الذكي لنتائج المختبر (PDF)",
					fields: [
						{
							label: "العميل (المركز / الطبيب)",
							fieldname: "owner_user",
							fieldtype: "Link",
							options: "User",
							reqd: 1,
						},
						{
							label: "الفرع (تلقائي)",
							fieldname: "branch",
							fieldtype: "Link",
							options: "Lab Branch",
							reqd: 1,
							read_only: 1,
						},
						{
							fieldtype: "HTML",
							fieldname: "upload_area",
							options: `
                                <div id="custom_upload_zone" style="padding: 40px 20px; border: 2px dashed #1a658d; text-align: center; border-radius: 12px; margin-top: 15px; background: #f4f8fa; cursor: pointer; transition: all 0.3s ease;">
                                    <svg style="width: 50px; height: 50px; fill: #1a658d; margin-bottom: 12px; transition: fill 0.3s;" id="upload_icon" viewBox="0 0 640 512" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M144 480C64.5 480 0 415.5 0 336c0-62.8 40.2-116.2 96.2-135.9c-.1-2.7-.2-5.4-.2-8.1c0-88.4 71.6-160 160-160c59.3 0 111 32.2 138.7 80.2C409.9 102 428.3 96 448 96c53 0 96 43 96 96c0 12.2-2.3 23.8-6.4 34.6C596 238.4 640 290.1 640 352c0 70.7-57.3 128-128 128H144zm79-217c-9.4 9.4-9.4 24.6 0 33.9s24.6 9.4 33.9 0l39-39V392c0 13.3 10.7 24 24 24s24-10.7 24-24V257.9l39 39c9.4 9.4 24.6 9.4 33.9 0s9.4-24.6 0-33.9l-80-80c-9.4-9.4-24.6-9.4-33.9 0l-80 80z"></path>
                                    </svg>
                                    <h4 id="upload_title" style="color: #1a658d; margin-bottom: 5px; font-weight: bold; font-size: 16px;">اضغط هنا أو اسحب الملفات</h4>
                                    <p style="color: #6c757d; font-size: 13px; margin: 0;">يُسمح برفع ملفات PDF المتعددة</p>
                                    <div id="file_count_msg" style="margin-top: 15px; font-weight: bold; color: #155724; background: #d4edda; padding: 6px 15px; border-radius: 50px; display: none; font-size: 13px; border: 1px solid #c3e6cb;"></div>
                                    <input type="file" id="bulk_pdf_uploader" multiple accept="application/pdf" style="display: none;">
                                </div>
                            `,
						},
					],
					primary_action_label: "بدء الاستخراج والرفع",
					primary_action: function (values) {
						// قراءة الملفات من النافذة الحالية حصراً
						let fileInput = d.$wrapper.find("#bulk_pdf_uploader")[0];
						let files = fileInput.files;

						if (files.length === 0) {
							frappe.msgprint("الرجاء اختيار ملفات PDF أولاً");
							return;
						}

						frappe.dom.freeze("جاري الرفع واستخراج بيانات المرضى... ⏳");
						let promises = [];

						for (let i = 0; i < files.length; i++) {
							let formData = new FormData();
							formData.append("file", files[i]);
							formData.append("owner_user", values.owner_user);
							formData.append("branch", values.branch);

							let promise = fetch(
								"/api/method/newlab_site.api.bulk_upload_lab_results",
								{
									method: "POST",
									headers: { "X-Frappe-CSRF-Token": frappe.csrf_token },
									body: formData,
								},
							).then((res) => res.json());

							promises.push(promise);
						}

						Promise.all(promises)
							.then((results) => {
								frappe.dom.unfreeze();
								d.hide(); // إخفاء النافذة بعد النجاح بدلاً من إغلاقها نهائياً
								frappe.show_alert({
									message: `تم رفع ومعالجة ${files.length} ملف بنجاح!`,
									indicator: "green",
								});
								listview.refresh();
							})
							.catch((err) => {
								frappe.dom.unfreeze();
								frappe.msgprint(
									"حدث خطأ أثناء الاتصال بالخادم. يرجى المحاولة لاحقاً.",
								);
							});
					},
				});

				// حفظ النافذة في متغير القائمة لكي نستخدمها لاحقاً ولا نصنع غيرها
				listview.bulk_upload_dialog = d;

				// إعداد التفاعلات (ألوان السحب والإفلات)
				setTimeout(() => {
					let uploadZone = d.$wrapper.find("#custom_upload_zone")[0];
					let fileInput = d.$wrapper.find("#bulk_pdf_uploader")[0];
					let fileMsg = d.$wrapper.find("#file_count_msg")[0];
					let icon = d.$wrapper.find("#upload_icon")[0];
					let title = d.$wrapper.find("#upload_title")[0];

					if (uploadZone && fileInput) {
						uploadZone.onclick = () => fileInput.click();
						fileInput.onclick = (e) => e.stopPropagation();

						fileInput.onchange = function () {
							if (this.files.length > 0) {
								uploadZone.style.borderColor = "#28a745";
								uploadZone.style.background = "#f0fff4";
								icon.style.fill = "#28a745";
								title.style.color = "#28a745";
								fileMsg.style.display = "inline-block";
								fileMsg.innerHTML = `✅ تم اختيار ${this.files.length} ملفات جاهزة للرفع`;
							} else {
								uploadZone.style.borderColor = "#1a658d";
								uploadZone.style.background = "#f4f8fa";
								icon.style.fill = "#1a658d";
								title.style.color = "#1a658d";
								fileMsg.style.display = "none";
							}
						};

						uploadZone.ondragover = function (e) {
							e.preventDefault();
							this.style.background = "#e2eff5";
							this.style.borderColor = "#0d4261";
						};
						uploadZone.ondragleave = function (e) {
							e.preventDefault();
							if (fileInput.files.length === 0) {
								this.style.background = "#f4f8fa";
								this.style.borderColor = "#1a658d";
							}
						};
						uploadZone.ondrop = function (e) {
							e.preventDefault();
							fileInput.files = e.dataTransfer.files;
							fileInput.dispatchEvent(new Event("change"));
						};
					}
				}, 400);

				// تلوين زر النافذة
				d.get_primary_btn().css({
					"background-color": "#1a658d",
					color: "white",
					"border-color": "#1a658d",
					"font-weight": "bold",
				});
			}

			// 2. هذه الخطوة هي سر الإصلاح (تفريغ النافذة القديمة قبل إظهارها)
			let d = listview.bulk_upload_dialog;

			let fileInput = d.$wrapper.find("#bulk_pdf_uploader")[0];
			if (fileInput) fileInput.value = ""; // مسح الملفات المرفوعة سابقاً

			let uploadZone = d.$wrapper.find("#custom_upload_zone")[0];
			let fileMsg = d.$wrapper.find("#file_count_msg")[0];
			let icon = d.$wrapper.find("#upload_icon")[0];
			let title = d.$wrapper.find("#upload_title")[0];

			if (uploadZone) {
				// إرجاع الألوان الزرقاء وإخفاء رسالة النجاح
				uploadZone.style.borderColor = "#1a658d";
				uploadZone.style.background = "#f4f8fa";
				icon.style.fill = "#1a658d";
				title.style.color = "#1a658d";
				fileMsg.style.display = "none";
			}

			// 3. تحديث الفرع في حال تغير المستخدم
			frappe.db.get_value("User", frappe.session.user, "branch").then((r) => {
				if (r.message && r.message.branch) {
					d.set_value("branch", r.message.branch);
				} else {
					d.get_field("branch").df.read_only = 0;
					d.get_field("branch").refresh();
				}
			});

			d.show();
		});

		// تلوين الزر الرئيسي في القائمة
		btn.css({
			"background-color": "#1a658d",
			color: "white",
			"border-color": "#1a658d",
			"font-weight": "bold",
		});
		btn.hover(
			function () {
				$(this).css("color", "white");
			},
			function () {
				$(this).css("color", "white");
			},
		);
	},
};
